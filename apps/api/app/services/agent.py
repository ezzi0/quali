"""
Real Estate Lead Qualification Agent

Built following OpenAI's Agent SDK best practices:
- Single-agent system with tools
- Structured outputs
- Guardrails (relevance, safety)
- Session memory
- Human-in-the-loop triggers

Production readiness hardening:
- Safe argument parsing (no eval)
- Guardrails enabled (relevance + safety)
- Retries/backoff around OpenAI calls
- Basic state/status events for streaming
"""
import json
import time
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

# NOTE: OpenAI Agents SDK is in beta and not yet publicly released
# For now, we'll use the patterns from their guide with standard OpenAI client
# When SDK is available, this will be updated to use: from agents import Agent, Runner, function_tool

from openai import OpenAI, APIConnectionError, RateLimitError
from pydantic import BaseModel, Field, ValidationError

from ..config import get_settings
from ..logging import get_logger
from ..models.lead import Lead, LeadStatus, LeadSource
from ..services import tools
from ..services.rag import knowledge_search
from ..telemetry import get_tracer, span

settings = get_settings()
logger = get_logger(__name__)


class AgentContext(BaseModel):
    """Context for agent execution"""
    lead_id: Optional[int] = None
    session_id: Optional[str] = None
    # Changed from Dict[str, str] to Dict[str, Any] to support tool_calls
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    tool_call_count: int = 0
    max_tool_calls: int = 10
    state_version: int = 1  # bump if we change slot model


class QualificationAgent:
    """
    Lead Qualification Agent following OpenAI best practices.

    This agent:
    1. Collects lead information through conversation
    2. Uses tools to search inventory and validate data
    3. Scores leads using transparent scoring
    4. Outputs structured LeadQualification
    5. Has guardrails for relevance and safety
    """

    def __init__(self, db: Session):
        self.db = db
        self.tracer = get_tracer("app.services.agent")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_chat_model
        self.request_timeout = 30  # seconds
        self.max_retries = 2
        self.required_fields = [
            "contact_name",
            "persona",
            "budget_max",
            "move_in_date",
            "city",
            "areas",
            "property_type",
            "beds",
            "contact_method",
        ]
        self.min_budget_aed = 300000
        self.deep_dive_budget_aed = 1000000

        # Define instructions (from OpenAI guide: clear, actionable, edge-case aware)
        self.instructions = """You are Abriqot, a real estate qualification assistant for Dubai off-plan buyers and investors.

GOAL: Qualify fit quickly, gather essentials, then finish cleanly.

FIT CHECK (required):
1) Name
2) Buyer or investor (no renters)
3) Budget in AED (must be >= 300k)
4) Timeline (urgency)

MATCHING (once fit):
5) Area(s) in Dubai (if unsure, keep it open)
6) Property type
7) Bedrooms

DEEPER (ask only if needed): financing (cash vs mortgage, pre-approval)

CONTACT:
Collect at least one of email or phone before showing matches.

RULES:
- Ask ONE question at a time.
- Do not show inventory until fit-check + matching fields + contact are complete.
- After saving the lead and qualification, end with: "Thanks [Name]! A specialist will contact you within the next 30 minutes."
"""

        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "save_lead_profile",
                    "description": "Save contact information and lead profile to CRM. Call this FIRST when you have all required information, before scoring.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "integer", "description": "Lead ID"},
                            "contact": {
                                "type": "object",
                                "description": "Contact info: name, email, phone, consent flags",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "consent_email": {"type": "boolean"},
                                    "consent_sms": {"type": "boolean"},
                                    "consent_whatsapp": {"type": "boolean"}
                                }
                            },
                            "profile": {
                                "type": "object",
                                "description": "Lead profile: persona, location, property requirements, budget, timeline, financing",
                                "properties": {
                                    "persona": {"type": "string"},
                                    "city": {"type": "string"},
                                    "areas": {"type": "array", "items": {"type": "string"}},
                                    "property_type": {"type": "string"},
                                    "beds": {"type": "integer"},
                                    "min_size_m2": {"type": "integer"},
                                    "budget_min": {"type": "number"},
                                    "budget_max": {"type": "number"},
                                    "move_in_date": {"type": "string"},
                                    "preapproved": {"type": "boolean"},
                                    "financing_notes": {"type": "string"},
                                    "preferences": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "required": ["lead_id", "contact", "profile"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "knowledge_search",
                    "description": "Search FAQs and objection handlers about Agency 2.0, process, data privacy, etc. Use when user asks questions about the service or raises objections.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "User's question or objection, e.g., 'What is Agency 2.0?', 'Is this a credit check?'"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 3)",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "inventory_search",
                    "description": "Search available properties. Use when user mentions location, type, beds, or budget to show matching options.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name, e.g., Dubai, Abu Dhabi"
                            },
                            "area": {
                                "type": "string",
                                "description": "Specific area/neighborhood"
                            },
                            "property_type": {
                                "type": "string",
                                "description": "Type: apartment, villa, townhouse, studio"
                            },
                            "beds": {
                                "type": "integer",
                                "description": "Number of bedrooms"
                            },
                            "min_price": {
                                "type": "number",
                                "description": "Minimum price in AED"
                            },
                            "max_price": {
                                "type": "number",
                                "description": "Maximum price in AED"
                            },
                            "min_area_m2": {
                                "type": "integer",
                                "description": "Minimum size in square meters"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results to return (default: 5)",
                                "default": 5
                            }
                        },
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "normalize_budget",
                    "description": "Parse budget from natural language text into min/max values. Use when user mentions budget in conversation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Budget text like '150k', '100-200k', '2 million AED'"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "geo_match",
                    "description": "Validate and normalize geographic area names.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of area names to validate"
                            }
                        },
                        "required": ["city", "areas"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "lead_score",
                    "description": "Calculate lead quality score (0-100). Use when you have collected enough information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "profile": {
                                "type": "object",
                                "description": "Lead profile with city, areas, property_type, beds, budget, timeline, etc."
                            },
                            "top_matches": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "Top matching units from inventory_search"
                            },
                            "contact": {
                                "type": "object",
                                "description": "Contact info with email, phone"
                            }
                        },
                        "required": ["profile", "top_matches", "contact"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "persist_qualification",
                    "description": "Save qualification results to database. Call this LAST after scoring.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "integer"},
                            "qualified": {"type": "boolean"},
                            "score": {"type": "integer"},
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "missing_info": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "suggested_next_step": {"type": "string"},
                            "top_matches": {
                                "type": "array",
                                "items": {"type": "object"}
                            }
                        },
                        "required": ["lead_id", "qualified", "score", "reasons", "missing_info", "suggested_next_step"]
                    }
                }
            }
        ]

    def _parse_tool_arguments(self, raw_args: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Safely parse tool arguments from JSON string.

        Returns (arguments_dict, error_message)
        """
        try:
            parsed = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            if not isinstance(parsed, dict):
                return None, "Tool arguments must be a JSON object"
            return parsed, None
        except json.JSONDecodeError as e:
            return None, f"Invalid tool arguments: {str(e)}"

    def _update_collected_from_tool(self, tool_name: str, arguments: Dict[str, Any], tool_result: Any, context: AgentContext) -> None:
        """
        Update collected_data based on tool calls.
        Provides the agent with state for slot-filling.
        """
        collected = context.collected_data

        if tool_name == "save_lead_profile":
            contact = arguments.get("contact", {})
            profile = arguments.get("profile", {})
            if contact:
                collected["contact_name"] = contact.get("name")
                collected["contact_email"] = contact.get("email")
                collected["contact_phone"] = contact.get("phone")
                collected["consent_email"] = contact.get("consent_email")
                collected["consent_sms"] = contact.get("consent_sms")
                collected["consent_whatsapp"] = contact.get("consent_whatsapp")
            if profile:
                collected["persona"] = profile.get("persona")
                collected["city"] = profile.get("city")
                collected["areas"] = profile.get("areas")
                collected["property_type"] = profile.get("property_type")
                collected["beds"] = profile.get("beds")
                collected["budget_min"] = profile.get("budget_min")
                collected["budget_max"] = profile.get("budget_max")
                collected["move_in_date"] = profile.get("move_in_date")
                collected["preapproved"] = profile.get("preapproved")
        elif tool_name == "normalize_budget":
            if isinstance(tool_result, dict):
                collected["budget_min"] = tool_result.get("min") or collected.get("budget_min")
                collected["budget_max"] = tool_result.get("max") or collected.get("budget_max")
        elif tool_name == "geo_match":
            if isinstance(tool_result, list) and tool_result:
                collected["areas"] = tool_result
        elif tool_name == "inventory_search":
            if isinstance(tool_result, list):
                collected["matches"] = tool_result
        elif tool_name == "persist_qualification":
            collected["qualification_saved"] = True

        # Track top matches if provided
        if isinstance(tool_result, dict) and "matches" in tool_result:
            collected["top_matches_count"] = len(tool_result.get("matches", []))

    def _missing_required_fields(self, collected: Dict[str, Any]) -> List[str]:
        """Return list of missing required fields based on collected data."""
        missing = []
        for field in self.required_fields:
            if field == "contact_method":
                if not (collected.get("contact_email") or collected.get("contact_phone")):
                    missing.append(field)
                continue
            if field == "areas" and collected.get("area_unknown"):
                continue
            val = collected.get(field)
            if val is None or val == "" or val == []:
                missing.append(field)
        return missing

    def _state_prompt(self, collected: Dict[str, Any]) -> str:
        """Build a lightweight state summary to steer the model."""
        missing = self._missing_required_fields(collected)
        filled = [f for f in self.required_fields if f not in missing]
        return (
            "STATE UPDATE:\n"
            f"- Missing fields: {missing if missing else 'none'}\n"
            f"- Filled fields: {filled if filled else 'none'}\n"
            "Ask for ONE missing field at a time. If all required fields are filled, proceed to save_lead_profile -> lead_score -> persist_qualification and then finish."
        )

    def _stream_text_completion(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Stream a text-only completion for smoother token-level output.
        Tool use is disabled in this path (tool_choice='none').
        """
        chunks: List[str] = []
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                timeout=self.request_timeout,
            )
            current = ""
            for event in stream:
                delta = event.choices[0].delta
                if delta.content:
                    current += delta.content
                    # Emit small slices to keep UI responsive
                    if len(current) >= 60:
                        chunks.append(current)
                        current = ""
            if current:
                chunks.append(current)
        except Exception as e:
            logger.error("stream_completion_failed", error=str(e))
        return chunks

    def _call_openai_with_retry(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None):
        """Call OpenAI with simple retry/backoff for robustness."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    timeout=self.request_timeout,
                )
            except (APIConnectionError, RateLimitError) as e:
                last_error = e
                backoff = 2 ** attempt
                logger.warning("openai_retry", attempt=attempt + 1, backoff=backoff, error=str(e))
                time.sleep(backoff)
            except Exception as e:
                last_error = e
                logger.error("openai_call_failed", error=str(e))
                break
        raise last_error or RuntimeError("OpenAI call failed without explicit error")  # Propagate after retries

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call"""
        try:
            if tool_name == "save_lead_profile":
                return tools.save_lead_profile(
                    self.db,
                    arguments.get("lead_id"),
                    arguments.get("contact", {}),
                    arguments.get("profile", {})
                )

            elif tool_name == "knowledge_search":
                return knowledge_search(
                    arguments.get("query", ""),
                    arguments.get("top_k", 3)
                )

            elif tool_name == "inventory_search":
                return tools.inventory_search(self.db, arguments)

            elif tool_name == "normalize_budget":
                return tools.normalize_budget(arguments.get("text", ""))

            elif tool_name == "geo_match":
                return tools.geo_match(
                    arguments.get("city", ""),
                    arguments.get("areas", [])
                )

            elif tool_name == "lead_score":
                return tools.lead_score(
                    arguments.get("profile", {}),
                    arguments.get("top_matches", []),
                    arguments.get("contact", {})
                )

            elif tool_name == "persist_qualification":
                return tools.persist_qualification(
                    self.db,
                    arguments.get("lead_id"),
                    arguments
                )

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error("tool_execution_failed", tool=tool_name, error=str(e))
            return {"error": str(e)}

    def _check_relevance_guardrail(self, message: str) -> Dict[str, Any]:
        """
        Relevance guardrail - ensures message is related to real estate qualification.
        Returns dict with 'is_relevant' bool and 'reason' string.
        """
        try:
            response = self._call_openai_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": """You are a relevance classifier for a real estate lead qualification system.

Determine if the user's message is relevant to:
- Real estate (buying, renting, selling properties)
- Property search and requirements
- Budget and financing
- Location preferences
- Qualification questions

Return 'relevant' if the message is related to these topics.
Return 'irrelevant' if the message is completely off-topic (e.g., "What's the weather?", "Tell me a joke", etc.)

Be lenient - conversational messages like greetings, clarifications, or follow-ups are relevant."""
                    },
                    {
                        "role": "user",
                        "content": f"Is this message relevant to real estate qualification?\n\nMessage: {message}\n\nRespond with just 'relevant' or 'irrelevant' and brief reason."
                    }
                ],
                tools=None
            )

            result = response.choices[0].message.content.lower()
            is_relevant = 'relevant' in result

            return {
                "is_relevant": is_relevant,
                "reason": result
            }
        except Exception as e:
            logger.error("relevance_check_failed", error=str(e))
            # Fail open - assume relevant if check fails
            return {"is_relevant": True, "reason": "check_failed"}

    def _check_safety_guardrail(self, message: str) -> Dict[str, Any]:
        """
        Safety guardrail - detects jailbreaks, prompt injections, unsafe content.
        Returns dict with 'is_safe' bool.
        """
        try:
            # Use OpenAI moderation API
            moderation = self.client.moderations.create(input=message)
            result = moderation.results[0]

            is_safe = not result.flagged

            # Also check for common prompt injection patterns
            injection_patterns = [
                "ignore all previous",
                "system:",
                "disregard",
                "override",
                "new instructions",
                "<system>",
                "{{",
                "forget everything"
            ]

            message_lower = message.lower()
            has_injection = any(
                pattern in message_lower for pattern in injection_patterns)

            return {
                "is_safe": is_safe and not has_injection,
                "flagged_categories": [cat for cat, flagged in result.categories if flagged] if not is_safe else [],
                "has_injection_attempt": has_injection
            }
        except Exception as e:
            logger.error("safety_check_failed", error=str(e))
            # Fail closed - assume unsafe if check fails
            return {"is_safe": False, "error": str(e)}

    def _chunk_text(self, text: str, max_len: int = 60) -> List[str]:
        """
        Naive chunker to emit smaller SSE text events for smoother UI streaming.
        """
        if not text:
            return []
        words = text.split()
        chunks = []
        current = []
        for w in words:
            if sum(len(x) + 1 for x in current) + len(w) > max_len:
                chunks.append(" ".join(current))
                current = [w]
            else:
                current.append(w)
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _extract_email_phone(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
        phone_match = re.search(r'\+?\d{10,15}', text.replace(" ", ""))
        email = email_match.group(0) if email_match else None
        phone = phone_match.group(0) if phone_match else None
        return email, phone

    def _extract_persona(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "rent" in lowered:
            return "renter"
        if "invest" in lowered:
            return "investor"
        if "buy" in lowered or "buyer" in lowered or "purchase" in lowered:
            return "buyer"
        return None

    def _extract_property_type(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "apartment" in lowered or "flat" in lowered:
            return "apartment"
        if "villa" in lowered:
            return "villa"
        if "townhouse" in lowered:
            return "townhouse"
        if "studio" in lowered:
            return "studio"
        return None

    def _extract_beds(self, text: str) -> Optional[int]:
        lowered = text.lower()
        if "studio" in lowered:
            return 0
        match = re.search(r'(\d+)\s*(bed|br)', lowered)
        if match:
            return int(match.group(1))
        match = re.search(r'\b(\d+)\b', lowered)
        if match:
            value = int(match.group(1))
            if 0 < value <= 10:
                return value
        return None

    def _extract_timeline(self, text: str, last_question: Optional[str] = None) -> Tuple[Optional[str], Optional[int]]:
        lowered = text.lower()
        if last_question == "timeline":
            plain = text.strip()
            if re.fullmatch(r"\d{1,2}", plain):
                months = int(plain)
                if months <= 3:
                    return "0-3 months", months
                if months <= 6:
                    return "3-6 months", months
                if months <= 12:
                    return "6-12 months", months
                return "12+ months", months
        if any(term in lowered for term in ["asap", "immediate", "right away", "now"]):
            return "ASAP (0-3 months)", 1
        month_match = re.search(r'(\d+)\s*month', lowered)
        if month_match:
            months = int(month_match.group(1))
            return f"In {months} months", months
        year_match = re.search(r'(\d+)\s*year', lowered)
        if year_match:
            months = int(year_match.group(1)) * 12
            return f"In {year_match.group(1)} years", months
        if "this year" in lowered:
            return "Within 12 months", 12
        if "next year" in lowered:
            return "12+ months", 15
        return None, None

    def _extract_budget_from_text(self, text: str, last_question: Optional[str] = None) -> Tuple[Optional[float], Optional[float]]:
        if not re.search(r'\d', text):
            return None, None
        lowered = text.lower()
        if last_question in {"timeline", "beds"}:
            if re.fullmatch(r"\d{1,2}", text.strip()):
                return None, None
            if "month" in lowered or "year" in lowered:
                return None, None
        # Avoid treating phone numbers as budgets
        if re.search(r'\b\d{9,}\b', text):
            return None, None
        has_currency_hint = any(token in lowered for token in ["aed", "dirham", "usd", "$", "k", "m", "million"])
        if not has_currency_hint:
            numbers = re.findall(r'\d+(?:\.\d+)?', lowered)
            if numbers and max(float(n) for n in numbers) < 1000:
                return None, None
        result = tools.normalize_budget(text)
        return result.get("min"), result.get("max")

    def _detect_area_guidance_request(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if not any(term in lowered for term in ["recommend", "suggest", "where would you", "where should", "best area", "best place", "what do you recommend", "where is best"]):
            return None
        if any(term in lowered for term in ["luxury", "luxurious", "premium", "high-end", "upscale", "exclusive"]):
            return "luxury"
        if any(term in lowered for term in ["value", "affordable", "budget", "cheaper", "growth", "return", "roi"]):
            return "value"
        return "general"

    def _detect_persona_clarify_request(self, text: str) -> bool:
        lowered = text.lower()
        return any(
            term in lowered for term in [
                "what's the difference",
                "whats the difference",
                "difference",
                "what do you mean",
                "what's that",
                "how is that different",
                "which is better",
            ]
        )

    def _is_user_question(self, text: str) -> bool:
        lowered = text.strip().lower()
        if "?" in text:
            return True
        question_starts = (
            "what",
            "why",
            "how",
            "where",
            "which",
            "who",
            "whats",
            "what's",
            "can you",
            "could you",
            "do you",
            "should i",
        )
        return lowered.startswith(question_starts)

    def _question_key_to_slot(self, key: Optional[str]) -> Optional[str]:
        if not key:
            return key
        if key.startswith("consent"):
            return None
        if key in {"persona_retry", "persona_clarify"}:
            return "persona"
        if key in {"budget_too_low"}:
            return "budget"
        if key.endswith("_help"):
            return key.replace("_help", "")
        if key.startswith("area_"):
            return "area"
        return key

    def _slot_filled(self, slot: str, data: Dict[str, Any]) -> bool:
        if slot == "name":
            return bool(data.get("contact_name"))
        if slot == "persona":
            return bool(data.get("persona"))
        if slot == "budget":
            return bool(data.get("budget_max"))
        if slot == "timeline":
            return bool(data.get("move_in_date"))
        if slot == "area":
            return bool(data.get("areas")) or bool(data.get("area_unknown"))
        if slot == "property_type":
            return bool(data.get("property_type"))
        if slot == "beds":
            return data.get("beds") is not None
        if slot == "financing":
            return bool(data.get("financing_notes")) or data.get("preapproved") is not None
        if slot == "contact":
            return bool(data.get("contact_email") or data.get("contact_phone"))
        return False

    def _is_area_unknown(self, text: str) -> bool:
        lowered = text.strip().lower()
        if not lowered:
            return False
        unknown_phrases = [
            "not sure",
            "not really",
            "no idea",
            "dont know",
            "don't know",
            "no preference",
            "no prefs",
            "any area",
            "anywhere",
            "open",
            "open to",
            "wherever",
            "doesn't matter",
            "doesnt matter",
            "not decided",
            "unsure",
            "whatever",
        ]
        if lowered in {"any", "either", "all", "no", "none"}:
            return True
        return any(phrase in lowered for phrase in unknown_phrases)

    def _infer_areas_from_text(self, text: str) -> List[str]:
        lowered = text.lower()
        area_map = {
            "marina": "Dubai Marina",
            "dubai marina": "Dubai Marina",
            "downtown": "Downtown Dubai",
            "downtown dubai": "Downtown Dubai",
            "creek": "Dubai Creek Harbour",
            "creek harbour": "Dubai Creek Harbour",
            "business bay": "Business Bay",
            "palm": "Palm Jumeirah",
            "palm jumeirah": "Palm Jumeirah",
            "hills": "Dubai Hills",
            "dubai hills": "Dubai Hills",
            "jvc": "Jumeirah Village Circle",
            "jumeirah village circle": "Jumeirah Village Circle",
            "mbr": "MBR City",
            "mbr city": "MBR City",
            "dubai south": "Dubai South",
            "arabian ranches": "Arabian Ranches",
        }
        matches = []
        for key, name in area_map.items():
            if key in lowered:
                matches.append(name)
        return list(dict.fromkeys(matches))

    def _normalize_areas(self, text: str) -> List[str]:
        raw = text.replace("&", ",").replace(" and ", ",")
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        cleaned = []
        for part in parts:
            if self._is_area_unknown(part):
                continue
            cleaned.append(part.title())
        return cleaned

    def _ingest_message(self, message: str, context: AgentContext) -> None:
        data = context.collected_data
        text = message.strip()
        if not text:
            return

        email, phone = self._extract_email_phone(text)
        if email:
            data["contact_email"] = email
        if phone:
            data["contact_phone"] = phone

        base_question = self._question_key_to_slot(data.get("last_question"))

        if base_question == "name" and not data.get("contact_name"):
            if "@" not in text and not re.search(r'\d', text):
                if 1 <= len(text.split()) <= 4:
                    cleaned = re.sub(r'^(my name is|i am|i\'m)\s+', '', text, flags=re.IGNORECASE)
                    data["contact_name"] = cleaned.strip().title()

        persona = self._extract_persona(text)
        if persona and not data.get("persona"):
            data["persona"] = persona
            data.pop("persona_clarify_requested", None)

        if base_question == "persona" and persona:
            data["persona"] = persona
            if not data.get("city"):
                data["city"] = "Dubai"
            data.pop("persona_clarify_requested", None)
        elif base_question == "persona" and not persona:
            if self._detect_persona_clarify_request(text):
                data["persona_clarify_requested"] = True

        budget_min, budget_max = self._extract_budget_from_text(text, last_question=base_question)
        if budget_max:
            data["budget_min"] = budget_min or 0
            data["budget_max"] = budget_max

        if base_question == "timeline" and not data.get("move_in_date"):
            label, months = self._extract_timeline(text, last_question=base_question)
            if label:
                data["move_in_date"] = label
                data["urgency_months"] = months

        if not data.get("move_in_date"):
            label, months = self._extract_timeline(text)
            if label:
                data["move_in_date"] = label
                data["urgency_months"] = months

        if base_question == "area":
            guidance = self._detect_area_guidance_request(text)
            if guidance:
                data["area_guidance_requested"] = guidance
            elif self._is_area_unknown(text):
                if data.get("area_help_shown"):
                    data["area_unknown"] = True
                    data["areas"] = []
                else:
                    data["area_help_shown"] = True
                data["city"] = data.get("city") or "Dubai"
            else:
                areas = self._infer_areas_from_text(text)
                if not areas:
                    areas = self._normalize_areas(text)
                if areas:
                    data["areas"] = tools.geo_match(data.get("city") or "Dubai", areas)
                    data["city"] = data.get("city") or "Dubai"
                    data.pop("area_unknown", None)

        if "dubai" in text.lower():
            data["city"] = "Dubai"

        property_type = self._extract_property_type(text)
        if property_type and not data.get("property_type"):
            data["property_type"] = property_type

        beds = self._extract_beds(text)
        if beds is not None and data.get("beds") is None:
            data["beds"] = beds

        if base_question == "financing":
            lowered = text.lower()
            if "cash" in lowered:
                data["preapproved"] = True
                data["financing_notes"] = "cash"
            elif "mortgage" in lowered or "loan" in lowered:
                data["financing_notes"] = "mortgage"
                if "pre" in lowered and "approve" in lowered:
                    data["preapproved"] = True
                elif "not" in lowered or "need" in lowered:
                    data["preapproved"] = False

        if base_question and self._slot_filled(base_question, data):
            data.pop("help_requested_for", None)

        if base_question and not self._slot_filled(base_question, data) and self._is_user_question(text):
            if base_question == "persona":
                if self._detect_persona_clarify_request(text):
                    data["persona_clarify_requested"] = True
            elif base_question != "area":
                data["help_requested_for"] = base_question

    def _needs_financing_question(self, data: Dict[str, Any]) -> bool:
        urgency = data.get("urgency_months")
        budget_max = data.get("budget_max") or 0
        persona = data.get("persona")
        return bool(
            (urgency and urgency <= 6)
            or budget_max >= self.deep_dive_budget_aed
            or persona == "investor"
        )

    def _next_action(self, context: AgentContext) -> Tuple[str, Optional[str]]:
        data = context.collected_data

        if not data.get("contact_name"):
            return "ask", "name"

        if data.get("persona_clarify_requested") and not data.get("persona"):
            data.pop("persona_clarify_requested", None)
            return "ask", "persona_clarify"

        help_for = data.get("help_requested_for")
        if help_for and not self._slot_filled(help_for, data):
            data.pop("help_requested_for", None)
            if help_for == "persona":
                return "ask", "persona_clarify"
            if help_for == "area":
                return "ask", "area_help"
            return "ask", f"{help_for}_help"

        if data.get("persona") == "renter":
            return "ask", "persona_retry"

        if not data.get("persona"):
            return "ask", "persona"

        if not data.get("budget_max"):
            return "ask", "budget"

        if (data.get("budget_max") or 0) < self.min_budget_aed:
            return "ask", "budget_too_low"

        if not data.get("move_in_date"):
            return "ask", "timeline"

        if not data.get("areas") and not data.get("area_unknown"):
            if data.get("area_guidance_requested") and not data.get("area_guidance_shown"):
                data["area_guidance_shown"] = True
                return "ask", f"area_guidance_{data.get('area_guidance_requested')}"
            if data.get("area_help_shown"):
                return "ask", "area_help"
            return "ask", "area"

        if not data.get("property_type"):
            return "ask", "property_type"

        if data.get("beds") is None:
            return "ask", "beds"

        if self._needs_financing_question(data) and not data.get("financing_asked"):
            data["financing_asked"] = True
            return "ask", "financing"

        if not (data.get("contact_email") or data.get("contact_phone")):
            return "ask", "contact"

        if not data.get("matches"):
            return "matches", None

        return "finalize", None

    def _question_text(self, key: str) -> str:
        questions = {
            "name": "Welcome to Abriqot. What's your first name?",
            "persona": "Are you buying a home or investing in Dubai off-plan?",
            "persona_retry": "We only work with buyers and investors. Are you buying or investing?",
            "persona_clarify": "Buying = personal use home. Investing = focused on returns/ROI. Which one fits you?",
            "budget": "What budget range in AED works for you? (e.g., 600k-1.2M)",
            "budget_help": "A quick range is enough — even a max helps (e.g., 600k-1.2M). What budget in AED works for you?",
            "budget_too_low": "We focus on opportunities above AED 300k. Is that within your range?",
            "timeline": "When are you looking to buy? (0-3 / 3-6 / 6-12 / 12+ months)",
            "timeline_help": "A rough window is fine. Are you looking in 0-3, 3-6, 6-12, or 12+ months?",
            "area": "Any preferred areas? Quick picks: Marina (rental demand), Downtown (prime), Creek Harbour (growth), Business Bay (value). You can say 'not sure'.",
            "area_help": "Popular picks: Dubai Marina (rental demand), Downtown (prime/brand), Creek Harbour (growth), Business Bay (value). Which fits, or keep it open?",
            "area_guidance_luxury": "For luxury: Downtown (prime/brand), Palm Jumeirah (ultra-luxury), Dubai Hills (newer upscale), and Dubai Marina (lifestyle). Which should I focus on, or keep it open?",
            "area_guidance_value": "For value/growth: Business Bay (value), Creek Harbour (growth), and JVC (price). Which should I focus on, or keep it open?",
            "area_guidance_general": "Happy to recommend. Luxury: Downtown/Palm. Growth: Creek Harbour. Value: Business Bay/JVC. Which direction fits, or keep it open?",
            "property_type": "Which fits best: apartment, villa, townhouse, or studio?",
            "property_type_help": "Apartment = low maintenance, villa = space, townhouse = in-between. Which fits best?",
            "beds": "How many bedrooms do you need? (studio/1/2/3+)",
            "beds_help": "Studio = open plan; 1/2/3+ are common. What do you need?",
            "financing": "How do you plan to pay - cash, mortgage pre-approved, or mortgage needed?",
            "financing_help": "Mortgage pre-approved means the bank confirmed your limit. Are you pre-approved, need a mortgage, or paying cash?",
            "contact": "What's the best email and phone number to reach you? One is enough if you prefer.",
            "contact_help": "You can share either email or phone — which is easiest?",
        }
        return questions.get(key, "Could you share a bit more detail?")

    def _ensure_lead(self, context: AgentContext) -> int:
        if context.lead_id:
            return context.lead_id
        lead = Lead(source=LeadSource.WEB, status=LeadStatus.NEW)
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        context.lead_id = lead.id
        return lead.id

    def _final_message(self, name: Optional[str]) -> str:
        display_name = name or "there"
        return (
            f"Thanks {display_name}! I've saved your details. "
            "A specialist will contact you within the next 30 minutes."
        )

    async def run(
        self,
        message: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Run the agent for one turn.

        Returns dict with:
        - messages: List of message dicts for streaming
        - context: Updated context
        - should_continue: Whether to continue the loop
        - qualification: Final qualification if complete
        """

        run_id = str(uuid.uuid4())
        logger.info("agent_run_start", run_id=run_id)

        with span(self.tracer, "agent.guardrails", {"run_id": run_id}):
            # Guardrail 1: Relevance check
            relevance = self._check_relevance_guardrail(message)
            if not relevance["is_relevant"]:
                logger.warning("irrelevant_message", message=message,
                              reason=relevance["reason"])
                return {
                    "messages": [{
                        "type": "status",
                        "content": "Message not relevant to real estate; gently redirecting."
                    }, {
                        "role": "assistant",
                        "content": "I'm here to help you find the perfect property! Could you tell me what kind of property you're looking for?"
                    }],
                    "context": context,
                    "should_continue": True,
                    "qualification": None
                }

            # Guardrail 2: Safety check (OPTIMIZED - lightweight check only)
            safety = self._check_safety_guardrail(message)
            if not safety["is_safe"]:
                logger.warning("unsafe_message", message=message, safety=safety)
                return {
                    "messages": [{
                        "type": "status",
                        "content": "Message blocked for safety."
                    }, {
                        "role": "assistant",
                        "content": "I'm sorry, I cannot process that message. Let's focus on finding you a great property. What are you looking for?"
                    }],
                    "context": context,
                    "should_continue": True,
                    "qualification": None
                }

        # Add user message to history
        context.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Update collected data from the latest user message
        self._ingest_message(message, context)

        action, payload = self._next_action(context)

        if action == "ask":
            question_key = payload or ""
            question = self._question_text(question_key)
            if question_key == "persona":
                name = context.collected_data.get("contact_name")
                if name:
                    question = f"Nice to meet you, {name}. {question}"
            context.collected_data["last_question"] = self._question_key_to_slot(question_key)
            context.conversation_history.append({
                "role": "assistant",
                "content": question
            })
            return {
                "messages": [{
                    "type": "text",
                    "content": question
                }],
                "context": context,
                "should_continue": True,
                "qualification": None
            }

        if action == "matches":
            data = context.collected_data
            data["last_question"] = None
            area = (data.get("areas") or [None])[0] if data.get("areas") else None
            criteria = {
                "city": data.get("city"),
                "area": area,
                "property_type": data.get("property_type"),
                "beds": data.get("beds"),
                "min_price": data.get("budget_min"),
                "max_price": data.get("budget_max"),
                "limit": 3,
            }
            matches = tools.inventory_search(self.db, {k: v for k, v in criteria.items() if v is not None and v != ""})
            data["matches"] = matches

            context.conversation_history.append({
                "role": "assistant",
                "content": "Here are a few options that match what you shared:"
            })
            context.conversation_history.append({
                "role": "tool",
                "name": "inventory_search",
                "content": str(matches),
            })
            response_messages = [
                {
                    "type": "text",
                    "content": "Here are a few options that match what you shared:"
                },
                {
                    "type": "tool_call",
                    "tool": "inventory_search",
                    "arguments": criteria,
                    "result": matches,
                },
            ]

            if data.get("contact_email") or data.get("contact_phone"):
                lead_id = self._ensure_lead(context)
                contact = {
                    "name": data.get("contact_name"),
                    "email": data.get("contact_email"),
                    "phone": data.get("contact_phone"),
                    "consent_email": bool(data.get("contact_email")),
                    "consent_sms": False,
                    "consent_whatsapp": bool(data.get("contact_phone")),
                }
                profile = {
                    "persona": data.get("persona"),
                    "city": data.get("city"),
                    "areas": data.get("areas") or [],
                    "property_type": data.get("property_type"),
                    "beds": data.get("beds"),
                    "budget_min": data.get("budget_min"),
                    "budget_max": data.get("budget_max"),
                    "move_in_date": data.get("move_in_date"),
                    "preapproved": data.get("preapproved"),
                    "financing_notes": data.get("financing_notes"),
                    "preferences": data.get("preferences", []),
                }
                save_result = tools.save_lead_profile(self.db, lead_id, contact, profile)
                score_result = tools.lead_score(profile, data.get("matches", []), contact)
                persist_payload = {
                    "lead_id": lead_id,
                    "qualified": score_result.get("qualified", False),
                    "score": score_result.get("score", 0),
                    "reasons": score_result.get("reasons", []),
                    "missing_info": self._missing_required_fields(data),
                    "suggested_next_step": "A specialist will contact you within 30 minutes.",
                    "top_matches": data.get("matches", []),
                }
                persist_result = tools.persist_qualification(self.db, lead_id, persist_payload)
                data["qualification_saved"] = True

                final_message = self._final_message(data.get("contact_name"))
                context.conversation_history.append({
                    "role": "assistant",
                    "content": final_message
                })

                response_messages.extend(
                    [
                        {
                            "type": "tool_call",
                            "tool": "save_lead_profile",
                            "arguments": {"lead_id": lead_id, "contact": contact, "profile": profile},
                            "result": save_result,
                        },
                        {
                            "type": "tool_call",
                            "tool": "lead_score",
                            "arguments": {"profile": profile, "top_matches": data.get("matches", []), "contact": contact},
                            "result": score_result,
                        },
                        {
                            "type": "tool_call",
                            "tool": "persist_qualification",
                            "arguments": persist_payload,
                            "result": persist_result,
                        },
                        {
                            "type": "text",
                            "content": final_message,
                        },
                    ]
                )

                return {
                    "messages": response_messages,
                    "context": context,
                    "should_continue": False,
                    "qualification": None,
                }

            return {
                "messages": response_messages,
                "context": context,
                "should_continue": True,
                "qualification": None,
            }

        if action == "finalize":
            data = context.collected_data
            data["last_question"] = None
            if data.get("qualification_saved"):
                final_message = self._final_message(data.get("contact_name"))
                context.conversation_history.append({
                    "role": "assistant",
                    "content": final_message
                })
                return {
                    "messages": [
                        {
                            "type": "text",
                            "content": final_message,
                        }
                    ],
                    "context": context,
                    "should_continue": False,
                    "qualification": None,
                }
            lead_id = self._ensure_lead(context)

            contact = {
                "name": data.get("contact_name"),
                "email": data.get("contact_email"),
                "phone": data.get("contact_phone"),
                "consent_email": bool(data.get("contact_email")),
                "consent_sms": False,
                "consent_whatsapp": bool(data.get("contact_phone")),
            }
            profile = {
                "persona": data.get("persona"),
                "city": data.get("city"),
                "areas": data.get("areas") or [],
                "property_type": data.get("property_type"),
                "beds": data.get("beds"),
                "budget_min": data.get("budget_min"),
                "budget_max": data.get("budget_max"),
                "move_in_date": data.get("move_in_date"),
                "preapproved": data.get("preapproved"),
                "financing_notes": data.get("financing_notes"),
                "preferences": data.get("preferences", []),
            }

            save_result = tools.save_lead_profile(self.db, lead_id, contact, profile)
            score_result = tools.lead_score(profile, data.get("matches", []), contact)
            persist_payload = {
                "lead_id": lead_id,
                "qualified": score_result.get("qualified", False),
                "score": score_result.get("score", 0),
                "reasons": score_result.get("reasons", []),
                "missing_info": self._missing_required_fields(data),
                "suggested_next_step": "A specialist will contact you within 30 minutes.",
                "top_matches": data.get("matches", []),
            }
            persist_result = tools.persist_qualification(self.db, lead_id, persist_payload)
            data["qualification_saved"] = True

            final_message = self._final_message(data.get("contact_name"))
            context.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

            return {
                "messages": [
                    {
                        "type": "tool_call",
                        "tool": "save_lead_profile",
                        "arguments": {"lead_id": lead_id, "contact": contact, "profile": profile},
                        "result": save_result,
                    },
                    {
                        "type": "tool_call",
                        "tool": "lead_score",
                        "arguments": {"profile": profile, "top_matches": data.get("matches", []), "contact": contact},
                        "result": score_result,
                    },
                    {
                        "type": "tool_call",
                        "tool": "persist_qualification",
                        "arguments": persist_payload,
                        "result": persist_result,
                    },
                    {
                        "type": "text",
                        "content": final_message,
                    },
                ],
                "context": context,
                "should_continue": False,
                "qualification": None,
            }

        # Prepare messages for API call
        state_prompt = self._state_prompt(context.collected_data)
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "system", "content": state_prompt}
        ] + context.conversation_history

        run_start = time.time()
        # Call OpenAI with tools
        # Use model default temperature to reduce surprises across providers
        response = self._call_openai_with_retry(messages=messages, tools=self.tools)

        assistant_message = response.choices[0].message
        response_messages = []

        # Handle tool calls
        if assistant_message.tool_calls:
            # Add assistant message with tool calls to history
            context.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                context.tool_call_count += 1

                # Check tool call limit (guardrail)
                if context.tool_call_count > context.max_tool_calls:
                    logger.warning("max_tool_calls_exceeded", context=context, run_id=run_id)
                    return {
                        "messages": [{
                            "role": "assistant",
                            "content": "I've tried my best to help, but I think it would be better if I connect you with one of our specialists. They'll be able to assist you better."
                        }],
                        "context": context,
                        "should_continue": False,
                        "qualification": None,
                        "escalate_to_human": True
                    }

                tool_name = tool_call.function.name
                parsed_args, parse_error = self._parse_tool_arguments(tool_call.function.arguments)
                if parse_error:
                    logger.error("tool_arguments_invalid", tool=tool_name, error=parse_error)
                    response_messages.append({
                        "type": "text",
                        "content": f"Sorry, something went wrong while using {tool_name}. Let's try again."
                    })
                    continue
                arguments = parsed_args

                logger.info("tool_call", tool=tool_name, arguments=arguments)

                # Execute tool
                tool_result = self._execute_tool(tool_name, arguments)
                self._update_collected_from_tool(tool_name, arguments, tool_result, context)

                # Add tool response to history
                context.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                })

                response_messages.append({
                    "type": "tool_call",
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })

            # After tool execution, call model again to get text response
            # May need multiple rounds if it keeps calling tools
            max_followup_rounds = 3

            for round_num in range(max_followup_rounds):
                logger.info("calling_agent_after_tools", round=round_num + 1)

                followup_response = self._call_openai_with_retry(
                    messages=context.conversation_history,
                    tools=self.tools,
                )

                followup_message = followup_response.choices[0].message

                # If it calls more tools, execute them
                if followup_message.tool_calls:
                    context.conversation_history.append({
                        "role": "assistant",
                        "content": followup_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in followup_message.tool_calls
                        ]
                    })

                    for tc in followup_message.tool_calls:
                        context.tool_call_count += 1
                        tool_name = tc.function.name
                        parsed_args, parse_error = self._parse_tool_arguments(tc.function.arguments)
                        if parse_error:
                            logger.error("tool_arguments_invalid", tool=tool_name, error=parse_error)
                            response_messages.append({
                                "type": "text",
                                "content": f"Sorry, something went wrong while using {tool_name}. Let's try again."
                            })
                            continue
                        arguments = parsed_args
                        tool_result = self._execute_tool(tool_name, arguments)

                        context.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tool_name,
                            "content": str(tool_result)
                        })

                        response_messages.append({
                            "type": "tool_call",
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": tool_result
                        })

                    continue  # Try again

                # Got text response!
                if followup_message.content:
                    # Prefer streaming for text-only follow-up
                    streamed_chunks = self._stream_text_completion(context.conversation_history)
                    if not streamed_chunks:
                        streamed_chunks = self._chunk_text(followup_message.content)
                    for chunk in streamed_chunks:
                        context.conversation_history.append({
                            "role": "assistant",
                            "content": chunk
                        })
                        response_messages.append({
                            "type": "text",
                            "content": chunk
                        })
                break

                # No content and no tools - exit loop
                logger.warning("empty_followup_response", round=round_num)
                break

            # Check if qualification was persisted
            qualification_persisted = any(
                msg.get("role") == "tool" and msg.get(
                    "name") == "persist_qualification"
                for msg in context.conversation_history
            )

            return {
                "messages": response_messages,
                "context": context,
                "should_continue": not qualification_persisted,
                "qualification": None
            }

        # No tool calls - final response
        streamed_chunks = self._stream_text_completion(messages) if assistant_message.content else []
        if not streamed_chunks and assistant_message.content:
            streamed_chunks = self._chunk_text(assistant_message.content)

        for chunk in streamed_chunks:
            context.conversation_history.append({
                "role": "assistant",
                "content": chunk
            })
            response_messages.append({
                "type": "text",
                "content": chunk
            })

        # Check if qualification was persisted (end condition)
        qualification_persisted = any(
            msg.get("role") == "tool" and msg.get(
                "name") == "persist_qualification"
            for msg in context.conversation_history
        )

        logger.info(
            "agent_run_complete",
            run_id=run_id,
            duration=round(time.time() - run_start, 3),
            tool_calls=context.tool_call_count,
            missing_fields=self._missing_required_fields(context.collected_data),
            should_continue=not qualification_persisted
        )

        return {
            "messages": response_messages,
            "context": context,
            "should_continue": not qualification_persisted,
            "qualification": None  # Could extract from tool results if needed
        }

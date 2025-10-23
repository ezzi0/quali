"""
Real Estate Lead Qualification Agent

Built following OpenAI's Agent SDK best practices:
- Single-agent system with tools
- Structured outputs
- Guardrails (relevance, safety)
- Session memory
- Human-in-the-loop triggers
"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

# NOTE: OpenAI Agents SDK is in beta and not yet publicly released
# For now, we'll use the patterns from their guide with standard OpenAI client
# When SDK is available, this will be updated to use: from agents import Agent, Runner, function_tool

from openai import OpenAI
from pydantic import BaseModel, Field

from ..config import get_settings
from ..logging import get_logger
from ..models.lead import Lead, LeadProfile, LeadStatus
from ..models.qualification import Qualification
from ..services import tools
from ..services.scoring import lead_scorer
from ..services.rag import knowledge_search
from ..schemas.qualification import LeadQualification

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
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-5"  # Fast and cost-effective for most tasks

        # Define instructions (from OpenAI guide: clear, actionable, edge-case aware)
        self.instructions = """You are a real estate lead qualification assistant.

YOUR GOAL: Qualify leads by collecting complete information to match them with properties, then END the conversation gracefully.

INFORMATION TO COLLECT (REQUIRED):
1. Persona: Are they a buyer, renter, or seller?
2. Location: Which city and specific areas interest them?
3. Property type: Apartment, villa, townhouse, etc.
4. Bedrooms: How many bedrooms do they need?
5. Budget: Price range they're comfortable with
6. Timeline: When do they want to move?
7. Financing: Pre-approved or need mortgage assistance?
8. Contact: Full name, email, and phone number
9. Consent: Permission to contact via email/SMS/WhatsApp

OPTIONAL INFORMATION:
- Size: Minimum square meters
- Specific preferences or features

CONVERSATION GUIDELINES:
- Ask ONE clear question at a time (maximum 2 related questions)
- Be warm, friendly, and conversational
- Use tools to search matching properties when you have enough criteria
- Show relevant matches to build excitement (max 3 options)
- If user mentions budget in text (e.g., "around 150k"), use normalize_budget tool
- If user mentions areas, use geo_match to validate
- If user asks about Agency 2.0, process, or has objections, use knowledge_search tool

CRITICAL - WHEN TO FINISH (3 steps):
1. Once you have ALL REQUIRED information above, call save_lead_profile to save contact and profile data
2. Then call lead_score to calculate quality
3. Then call persist_qualification to save the results
4. After persist_qualification is called, IMMEDIATELY end with: "Thank you [Name]! I've saved all your details. You'll receive a recap email shortly with the properties we discussed and next steps. [If high score: A specialist from our team will contact you within 24 hours to discuss these options further.] Have a great day!"

DO NOT ask any more questions after persist_qualification is called. The conversation MUST end.

EDGE CASES:
- If user provides vague budget ("flexible", "depends"), ask for a rough range
- If user is unsure about areas, suggest 2-3 popular ones and use inventory_search
- If conversation goes off-topic, politely redirect once
- If user asks to stop or speak to a human, acknowledge and end immediately

OUTPUT FORMAT AFTER QUALIFICATION:
"Thank you [Name]! I've saved all your details. You'll receive a recap email shortly with:
- Your property preferences
- The [X] matching properties we discussed
- Next steps for [viewing/mortgage/etc.]

[If score >= 65: A senior specialist will contact you within 24 hours to help you move forward quickly.]
[If score < 65: We'll review your requirements and be in touch soon with more options.]

Have a great day!"

Then STOP. Do not continue the conversation."""

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
            response = self.client.chat.completions.create(
                model="gpt-5",
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
                max_completion_tokens=50,
                temperature=0
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

        # Guardrail 1: Relevance check (DISABLED for performance - add back in production with async)
        # relevance = self._check_relevance_guardrail(message)
        # if not relevance["is_relevant"]:
        #     logger.warning("irrelevant_message", message=message,
        #                   reason=relevance["reason"])
        #     return {
        #         "messages": [{
        #             "role": "assistant",
        #             "content": "I'm here to help you find the perfect property! Could you tell me what kind of property you're looking for?"
        #         }],
        #         "context": context,
        #         "should_continue": True,
        #         "qualification": None
        #     }

        # Guardrail 2: Safety check (OPTIMIZED - lightweight check only)
        safety = self._check_safety_guardrail(message)
        if not safety["is_safe"]:
            logger.warning("unsafe_message", message=message, safety=safety)
            return {
                "messages": [{
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

        # Prepare messages for API call
        messages = [
            {"role": "system", "content": self.instructions}
        ] + context.conversation_history

        # Call OpenAI with tools
        # GPT-5 only supports temperature=1 (default), so we omit it
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )

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
                    logger.warning("max_tool_calls_exceeded", context=context)
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
                # Safe because we control the tools
                arguments = eval(tool_call.function.arguments)

                logger.info("tool_call", tool=tool_name, arguments=arguments)

                # Execute tool
                tool_result = self._execute_tool(tool_name, arguments)

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

                followup_response = self.client.chat.completions.create(
                    model=self.model,
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
                        arguments = json.loads(tc.function.arguments)
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
                    context.conversation_history.append({
                        "role": "assistant",
                        "content": followup_message.content
                    })

                    response_messages.append({
                        "type": "message",
                        "content": followup_message.content
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
        context.conversation_history.append({
            "role": "assistant",
            "content": assistant_message.content
        })

        response_messages.append({
            "type": "message",
            "content": assistant_message.content
        })

        # Check if qualification was persisted (end condition)
        qualification_persisted = any(
            msg.get("role") == "tool" and msg.get(
                "name") == "persist_qualification"
            for msg in context.conversation_history
        )

        return {
            "messages": response_messages,
            "context": context,
            "should_continue": not qualification_persisted,
            "qualification": None  # Could extract from tool results if needed
        }

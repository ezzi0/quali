"""
Creative Generator Service

Generates ad creatives using AI with RAG from brand guidelines and
compliance guardrails for housing regulations.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
import re

from ...config import get_settings
from ...logging import get_logger
from ...models import Creative, Persona, CreativeFormat, CreativeStatus
from ...services.rag import knowledge_search

settings = get_settings()
logger = get_logger(__name__)


class CreativeGeneratorService:
    """
    Generates ad creatives with brand compliance and A/B variants.
    
    Process:
    1. Load persona and brand guidelines via RAG
    2. Generate multiple creative variants
    3. Run compliance checks (housing regulations)
    4. Return approved creatives
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
    
    def generate_creatives(
        self,
        persona_id: int,
        format: CreativeFormat,
        count: int = 3,
        property_context: Optional[Dict[str, Any]] = None
    ) -> List[Creative]:
        """
        Generate creative variants for a persona.
        
        Args:
            persona_id: Target persona
            format: Creative format (image, video, carousel)
            count: Number of variants to generate
            property_context: Optional property details to feature
        
        Returns:
            List of Creative objects
        """
        logger.info("creative_generation_started", 
                   persona_id=persona_id,
                   format=format,
                   count=count)
        
        # 1. Load persona
        persona = self.db.get(Persona, persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # 2. Load brand guidelines via RAG
        brand_context = knowledge_search("brand guidelines tone voice", top_k=2)
        compliance_rules = knowledge_search("housing advertising compliance regulations", top_k=3)
        
        # 3. Generate variants
        creatives = []
        for i in range(count):
            creative = self._generate_single_creative(
                persona=persona,
                format=format,
                variant_num=i + 1,
                brand_context=brand_context,
                compliance_rules=compliance_rules,
                property_context=property_context
            )
            
            if creative:
                creatives.append(creative)
        
        logger.info("creative_generation_completed", creatives_generated=len(creatives))
        
        return creatives
    
    def _generate_single_creative(
        self,
        persona: Persona,
        format: CreativeFormat,
        variant_num: int,
        brand_context: List[Dict],
        compliance_rules: List[Dict],
        property_context: Optional[Dict[str, Any]]
    ) -> Optional[Creative]:
        """Generate a single creative variant"""
        
        # Build prompt
        brand_guidelines = "\n".join([doc["content"] for doc in brand_context])
        compliance = "\n".join([doc["content"] for doc in compliance_rules])
        
        prompt = f"""Generate ad creative for real estate marketing.

PERSONA: {persona.name}
- Description: {persona.description}
- Messaging hooks: {persona.messaging.get('hooks', [])}
- Tone: {persona.messaging.get('tone', 'professional')}

FORMAT: {format.value}

BRAND GUIDELINES:
{brand_guidelines}

COMPLIANCE REQUIREMENTS:
{compliance}
Must NOT discriminate or violate Fair Housing Act.

{f"PROPERTY: {property_context}" if property_context else ""}

Generate variant #{variant_num} with:
1. Compelling headline (max 40 chars)
2. Primary text (max 125 chars for mobile)
3. Description (max 30 chars)
4. Call-to-action (e.g., "Learn More", "Book Viewing")

Return JSON with: headline, primary_text, description, call_to_action
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert real estate copywriter. Generate compliant, compelling ad copy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Higher for creative variance
                response_format={"type": "json_object"}
            )
            
            import json
            creative_data = json.loads(response.choices[0].message.content)
            
            # Run compliance checks
            risk_flags = self._check_compliance(creative_data)
            
            # Create Creative object
            creative = Creative(
                persona_id=persona.id,
                name=f"{persona.name} - {format.value} - Variant {variant_num}",
                format=format,
                status=CreativeStatus.REVIEW if risk_flags.get("compliance_issues") else CreativeStatus.APPROVED,
                headline=creative_data.get("headline", ""),
                primary_text=creative_data.get("primary_text", ""),
                description=creative_data.get("description", ""),
                call_to_action=creative_data.get("call_to_action", "Learn More"),
                media={},  # Populated separately with image/video generation
                risk_flags=risk_flags,
                generation_prompt=prompt,
                model_version="gpt-4",
                generation_params={"temperature": 0.8, "variant": variant_num}
            )
            
            self.db.add(creative)
            self.db.commit()
            
            logger.info("creative_generated",
                       creative_id=creative.id,
                       status=creative.status.value,
                       has_compliance_issues=bool(risk_flags.get("compliance_issues")))
            
            return creative
            
        except Exception as e:
            logger.error("creative_generation_failed", error=str(e))
            return None
    
    def _check_compliance(self, creative_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Check for compliance violations.
        
        Fair Housing Act prohibits discrimination based on:
        - Race, color, national origin
        - Religion
        - Sex, familial status
        - Disability
        
        Also check for:
        - Misleading claims
        - Excessive punctuation
        """
        risk_flags = {
            "compliance_issues": [],
            "warnings": [],
            "toxicity_score": 0.0,
            "readability_grade": 8
        }
        
        # Combine all text
        all_text = " ".join([
            creative_data.get("headline", ""),
            creative_data.get("primary_text", ""),
            creative_data.get("description", "")
        ]).lower()
        
        # Prohibited terms (Fair Housing)
        prohibited_patterns = [
            r'\b(no|only)\s+(children|kids|families)',
            r'\b(perfect\s+for|ideal\s+for)\s+(families|couples|singles)',
            r'\bmature\s+(residents|community)',
            r'\badults?\s+only',
            r'\b(christian|muslim|jewish|hindu)\b',
            r'\b(race|racial|ethnic)\b',
        ]
        
        for pattern in prohibited_patterns:
            if re.search(pattern, all_text):
                risk_flags["compliance_issues"].append(f"Potential discrimination: matched pattern '{pattern}'")
        
        # Misleading claims
        misleading_patterns = [
            r'\b(guaranteed|promise|no\s+risk)\b',
            r'\b(best|#1|top\s+rated)\b',  # Superlatives without proof
        ]
        
        for pattern in misleading_patterns:
            if re.search(pattern, all_text):
                risk_flags["warnings"].append(f"Superlative claim: '{pattern}' - ensure substantiation")
        
        # Excessive punctuation
        if all_text.count('!') > 2:
            risk_flags["warnings"].append("Excessive exclamation marks")
        
        # Check toxicity via OpenAI Moderation API
        try:
            moderation = self.openai_client.moderations.create(input=all_text)
            result = moderation.results[0]
            
            if result.flagged:
                risk_flags["compliance_issues"].append(
                    f"Content flagged by moderation API: {[cat for cat, flagged in result.categories if flagged]}"
                )
            
            # Store score (0-1)
            risk_flags["toxicity_score"] = result.category_scores.hate
            
        except Exception as e:
            logger.warning("moderation_check_failed", error=str(e))
        
        return risk_flags


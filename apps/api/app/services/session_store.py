"""
Session persistence using Redis

Enables:
1. Resume conversations when user returns
2. Session recovery by email/phone
3. Anonymous session tracking
"""
import json
from typing import Dict, Any, Optional
from redis import Redis
from ..logging import get_logger

logger = get_logger(__name__)


class SessionStore:
    """
    Stores agent conversation context in Redis
    
    Sessions can be retrieved by:
    - session_id (UUID)
    - email (if captured)
    - phone (if captured)
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 86400 * 7  # 7 days
    
    def save_session(
        self,
        session_id: str,
        context: Dict[str, Any],
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> None:
        """Save session context to Redis"""
        try:
            # Store by session ID
            key = f"session:{session_id}"
            self.redis.setex(
                key,
                self.ttl,
                json.dumps(context)
            )
            
            # Also index by email if provided
            if email:
                email_key = f"session:email:{email.lower()}"
                self.redis.setex(email_key, self.ttl, session_id)
                logger.info("session_indexed_by_email", session_id=session_id, email=email)
            
            # Also index by phone if provided
            if phone:
                # Normalize phone (remove spaces, dashes)
                normalized_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                phone_key = f"session:phone:{normalized_phone}"
                self.redis.setex(phone_key, self.ttl, session_id)
                logger.info("session_indexed_by_phone", session_id=session_id, phone=phone)
            
            logger.info("session_saved", session_id=session_id)
            
        except Exception as e:
            logger.error("session_save_failed", session_id=session_id, error=str(e))
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session context by session ID"""
        try:
            key = f"session:{session_id}"
            data = self.redis.get(key)
            
            if data:
                context = json.loads(data)
                logger.info("session_retrieved", session_id=session_id)
                return context
            
            return None
        
        except Exception as e:
            logger.error("session_get_failed", session_id=session_id, error=str(e))
            return None
    
    def get_session_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve session by email"""
        try:
            email_key = f"session:email:{email.lower()}"
            session_id = self.redis.get(email_key)
            
            if session_id:
                return self.get_session(session_id)
            
            return None
        
        except Exception as e:
            logger.error("session_get_by_email_failed", email=email, error=str(e))
            return None
    
    def get_session_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Retrieve session by phone"""
        try:
            normalized_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            phone_key = f"session:phone:{normalized_phone}"
            session_id = self.redis.get(phone_key)
            
            if session_id:
                return self.get_session(session_id)
            
            return None
        
        except Exception as e:
            logger.error("session_get_by_phone_failed", phone=phone, error=str(e))
            return None
    
    def extract_contact_from_context(self, context: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Extract email/phone from conversation if mentioned
        Returns: {email: str|None, phone: str|None}
        """
        import re
        
        email = None
        phone = None
        
        # Check collected_data first
        if "collected_data" in context:
            email = context["collected_data"].get("email")
            phone = context["collected_data"].get("phone")
        
        # Also scan conversation history for patterns
        if not email or not phone:
            for msg in context.get("conversation_history", []):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    
                    # Email pattern
                    if not email:
                        email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', content)
                        if email_match:
                            email = email_match.group(0)
                    
                    # Phone pattern (international)
                    if not phone:
                        phone_match = re.search(r'\+?\d{10,15}', content)
                        if phone_match:
                            phone = phone_match.group(0)
        
        return {"email": email, "phone": phone}


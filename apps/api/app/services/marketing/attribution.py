"""
Attribution Service

Handles multi-touch attribution, UTM tracking, and offline conversion uploads
to advertising platforms.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...config import get_settings
from ...logging import get_logger
from ...models import Lead, Campaign, AdSet, Ad, MarketingMetric

settings = get_settings()
logger = get_logger(__name__)


class AttributionService:
    """
    Handles conversion attribution and tracking.
    
    Features:
    1. UTM parameter parsing
    2. Multi-touch attribution
    3. Offline conversion uploads to platforms
    4. Attribution window management
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_attribution(
        self,
        url: Optional[str] = None,
        utm_params: Optional[Dict[str, str]] = None,
        fbclid: Optional[str] = None,
        gclid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse attribution data from URL or tracking parameters.
        
        Args:
            url: Full URL with UTM parameters
            utm_params: Pre-parsed UTM parameters
            fbclid: Facebook click ID
            gclid: Google click ID
        
        Returns:
            Structured attribution data
        """
        attribution = {
            "source": None,
            "medium": None,
            "campaign": None,
            "campaign_id": None,
            "ad_set_id": None,
            "ad_id": None,
            "platform": None,
            "click_id": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Parse URL if provided
        if url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Extract UTM parameters
            attribution["source"] = query_params.get("utm_source", [None])[0]
            attribution["medium"] = query_params.get("utm_medium", [None])[0]
            attribution["campaign"] = query_params.get("utm_campaign", [None])[0]
            attribution["campaign_id"] = query_params.get("utm_id", [None])[0]
            
            # Custom parameters for ad set and ad
            attribution["ad_set_id"] = query_params.get("utm_adset", [None])[0]
            attribution["ad_id"] = query_params.get("utm_ad", [None])[0]
            
            # Platform click IDs
            if "fbclid" in query_params:
                attribution["platform"] = "meta"
                attribution["click_id"] = query_params["fbclid"][0]
            elif "gclid" in query_params:
                attribution["platform"] = "google"
                attribution["click_id"] = query_params["gclid"][0]
        
        # Override with explicit parameters
        if utm_params:
            attribution.update({k: v for k, v in utm_params.items() if v})
        
        if fbclid:
            attribution["platform"] = "meta"
            attribution["click_id"] = fbclid
        
        if gclid:
            attribution["platform"] = "google"
            attribution["click_id"] = gclid
        
        # Determine platform from source if not already set
        if not attribution["platform"] and attribution["source"]:
            source_lower = attribution["source"].lower()
            if "facebook" in source_lower or "instagram" in source_lower:
                attribution["platform"] = "meta"
            elif "google" in source_lower:
                attribution["platform"] = "google"
            elif "tiktok" in source_lower:
                attribution["platform"] = "tiktok"
        
        return attribution
    
    def attribute_lead(
        self,
        lead_id: int,
        attribution_data: Dict[str, Any]
    ) -> None:
        """
        Attribute a lead to a marketing source.
        
        Updates lead.attribution_data and links to campaign/ad_set/ad if found.
        """
        lead = self.db.get(Lead, lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Store raw attribution data
        lead.attribution_data = attribution_data
        
        # Try to link to internal campaign/ad_set/ad
        if attribution_data.get("campaign_id"):
            campaign = self.db.execute(
                select(Campaign).where(
                    Campaign.platform_campaign_id == attribution_data["campaign_id"]
                )
            ).scalar_one_or_none()
            
            if campaign and attribution_data.get("ad_set_id"):
                ad_set = self.db.execute(
                    select(AdSet).where(
                        AdSet.campaign_id == campaign.id,
                        AdSet.platform_adset_id == attribution_data["ad_set_id"]
                    )
                ).scalar_one_or_none()
                
                if ad_set and attribution_data.get("ad_id"):
                    ad = self.db.execute(
                        select(Ad).where(
                            Ad.ad_set_id == ad_set.id,
                            Ad.platform_ad_id == attribution_data["ad_id"]
                        )
                    ).scalar_one_or_none()
                    
                    if ad:
                        # Store internal IDs
                        lead.attribution_data["internal_campaign_id"] = campaign.id
                        lead.attribution_data["internal_ad_set_id"] = ad_set.id
                        lead.attribution_data["internal_ad_id"] = ad.id
        
        self.db.commit()
        
        logger.info("lead_attributed",
                   lead_id=lead_id,
                   platform=attribution_data.get("platform"),
                   campaign=attribution_data.get("campaign"))
    
    def prepare_offline_conversions(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare offline conversion events for platform upload.
        
        Args:
            platform: 'meta', 'google', or 'tiktok'
            start_date: Start of conversion window
            end_date: End of conversion window
        
        Returns:
            List of conversion events formatted for platform API
        """
        # Fetch leads with attribution and qualifications
        query = select(Lead).where(
            Lead.attribution_data.isnot(None)
        )
        
        if start_date:
            query = query.where(Lead.created_at >= start_date)
        if end_date:
            query = query.where(Lead.created_at <= end_date)
        
        leads = self.db.execute(query).scalars().all()
        
        conversions = []
        
        for lead in leads:
            attribution = lead.attribution_data or {}
            
            if attribution.get("platform") != platform:
                continue
            
            # Format based on platform
            if platform == "meta":
                conversion = self._format_meta_conversion(lead, attribution)
            elif platform == "google":
                conversion = self._format_google_conversion(lead, attribution)
            elif platform == "tiktok":
                conversion = self._format_tiktok_conversion(lead, attribution)
            else:
                continue
            
            if conversion:
                conversions.append(conversion)
        
        logger.info("offline_conversions_prepared",
                   platform=platform,
                   count=len(conversions))
        
        return conversions
    
    def _format_meta_conversion(
        self,
        lead: Lead,
        attribution: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Format conversion for Meta Conversions API (CAPI).
        
        https://developers.facebook.com/docs/marketing-api/conversions-api
        """
        if not attribution.get("click_id"):
            return None
        
        contact = lead.contact
        if not contact:
            return None
        
        return {
            "event_name": "Lead",
            "event_time": int(lead.created_at.timestamp()),
            "event_source_url": attribution.get("landing_page", ""),
            "action_source": "website",
            "fbp": attribution.get("fbp"),  # Facebook browser ID
            "fbc": f"fb.1.{int(lead.created_at.timestamp())}.{attribution['click_id']}",
            "user_data": {
                "em": contact.email if contact.email else None,
                "ph": contact.phone if contact.phone else None,
                "fn": contact.name.split()[0] if contact.name else None,
                "ln": contact.name.split()[-1] if contact.name and ' ' in contact.name else None,
            },
            "custom_data": {
                "currency": "AED",
                "value": lead.profile.budget_max if lead.profile else 0
            }
        }
    
    def _format_google_conversion(
        self,
        lead: Lead,
        attribution: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Format conversion for Google Ads Enhanced Conversions.
        
        https://developers.google.com/google-ads/api/docs/conversions/upload-identifiers
        """
        if not attribution.get("click_id"):  # gclid
            return None
        
        contact = lead.contact
        if not contact:
            return None
        
        return {
            "gclid": attribution["click_id"],
            "conversion_action": "Lead",
            "conversion_time": lead.created_at.isoformat(),
            "conversion_value": float(lead.profile.budget_max) if lead.profile and lead.profile.budget_max else 0,
            "currency_code": "AED",
            "user_identifiers": {
                "hashed_email": contact.email if contact.email else None,
                "hashed_phone_number": contact.phone if contact.phone else None,
            }
        }
    
    def _format_tiktok_conversion(
        self,
        lead: Lead,
        attribution: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Format conversion for TikTok Events API.
        
        https://ads.tiktok.com/marketing_api/docs?id=1701890979375106
        """
        contact = lead.contact
        if not contact:
            return None
        
        return {
            "event": "CompleteRegistration",
            "timestamp": lead.created_at.isoformat(),
            "context": {
                "ad": {
                    "callback": attribution.get("click_id")
                },
                "page": {
                    "url": attribution.get("landing_page", "")
                },
                "user": {
                    "email": contact.email if contact.email else None,
                    "phone": contact.phone if contact.phone else None,
                },
            },
            "properties": {
                "currency": "AED",
                "value": float(lead.profile.budget_max) if lead.profile and lead.profile.budget_max else 0
            }
        }


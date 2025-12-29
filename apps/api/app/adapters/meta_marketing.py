"""
Meta Marketing API Adapter

Handles Facebook and Instagram advertising via Meta Marketing API.
Supports campaigns, ad sets, ads, and audience creation with CAPI integration.
"""
from typing import Dict, Any, List, Optional
import time
import httpx
import asyncio
from datetime import datetime

from ..config import get_settings
from ..logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class MetaMarketingAdapter:
    """
    Meta Marketing API client.
    
    Features:
    - Campaign, Ad Set, and Ad CRUD
    - Audience creation and targeting
    - Creative uploads
    - Insights pulling
    - Conversions API (CAPI) for offline events
    
    Docs: https://developers.facebook.com/docs/marketing-apis
    """
    
    BASE_URL = "https://graph.facebook.com/v19.0"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
        pixel_id: Optional[str] = None,
        dry_run: bool = False
    ):
        self.access_token = access_token or settings.meta_access_token
        self.ad_account_id = ad_account_id or settings.meta_ad_account_id
        self.pixel_id = pixel_id or settings.meta_pixel_id
        self.dry_run = dry_run
        
        if not self.access_token:
            logger.warning("meta_no_access_token")

    async def _request_with_retry(self, method: str, url: str, json_body: dict | None = None, max_retries: int = 2, timeout: float = 30.0):
        """
        Simple retry/backoff for Meta API calls to handle transient errors and rate limits.
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(method, url, json=json_body)
                    if response.status_code in (429, 500, 502, 503):
                        raise httpx.HTTPStatusError(
                            f"Meta returned {response.status_code}", request=response.request, response=response
                        )
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                last_error = e
                backoff = 2 ** attempt
                logger.warning("meta_request_retry", attempt=attempt + 1, backoff=backoff, url=url, error=str(e))
                await asyncio.sleep(backoff)
        raise last_error
    
    async def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = "PAUSED",
        budget_daily: Optional[float] = None,
        special_ad_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a campaign.
        
        Args:
            name: Campaign name
            objective: e.g., 'LEAD_GENERATION', 'OUTCOME_TRAFFIC', 'OUTCOME_SALES'
            status: 'ACTIVE', 'PAUSED', 'ARCHIVED'
            budget_daily: Daily budget in cents (e.g., 10000 = $100)
            special_ad_categories: ['HOUSING'] for real estate
        
        Returns:
            {'id': 'campaign_id', ...}
        """
        if self.dry_run:
            logger.info("meta_create_campaign_dry_run", name=name)
            return {"id": f"mock_campaign_{int(time.time())}", "name": name}
        
        params = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or ["HOUSING"],
            "access_token": self.access_token
        }
        
        if budget_daily:
            params["daily_budget"] = int(budget_daily * 100)  # Convert to cents
        
        data = await self._request_with_retry(
            "POST",
            f"{self.BASE_URL}/{self.ad_account_id}/campaigns",
            json_body=params
        )
        
        logger.info("meta_campaign_created", campaign_id=data.get("id"), name=name)
        
        return data
    
    async def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        targeting: Dict[str, Any],
        budget_daily: float,
        billing_event: str = "IMPRESSIONS",
        optimization_goal: str = "LEAD_GENERATION",
        status: str = "PAUSED"
    ) -> Dict[str, Any]:
        """
        Create an ad set.
        
        Args:
            campaign_id: Parent campaign ID
            name: Ad set name
            targeting: Targeting spec (geo, age, interests, etc.)
            budget_daily: Daily budget in dollars
            billing_event: 'IMPRESSIONS', 'LINK_CLICKS'
            optimization_goal: 'LEAD_GENERATION', 'LANDING_PAGE_VIEWS'
            status: 'ACTIVE', 'PAUSED'
        
        Returns:
            {'id': 'adset_id', ...}
        """
        if self.dry_run:
            logger.info("meta_create_adset_dry_run", name=name)
            return {"id": f"mock_adset_{int(time.time())}", "name": name}
        
        params = {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": int(budget_daily * 100),
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            "targeting": targeting,
            "status": status,
            "access_token": self.access_token
        }
        
        data = await self._request_with_retry(
            "POST",
            f"{self.BASE_URL}/{self.ad_account_id}/adsets",
            json_body=params
        )
        
        logger.info("meta_adset_created", adset_id=data.get("id"), name=name)
        
        return data
    
    async def update_ad_set_budget(
        self,
        adset_id: str,
        budget_daily: float,
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
        """
        Update ad set daily budget. Real call unless dry_run is enabled.
        """
        if self.dry_run:
            logger.info("meta_update_adset_budget_dry_run", adset_id=adset_id, budget=budget_daily)
            return {"id": adset_id, "daily_budget": budget_daily}

        params = {
            "daily_budget": int(budget_daily * 100),
            "status": status,
            "access_token": self.access_token
        }

        data = await self._request_with_retry(
            "POST",
            f"{self.BASE_URL}/{adset_id}",
            json_body=params
        )

        logger.info("meta_adset_budget_updated", adset_id=adset_id, budget=budget_daily)
        return data
    
    async def create_ad(
        self,
        adset_id: str,
        name: str,
        creative: Dict[str, Any],
        status: str = "PAUSED"
    ) -> Dict[str, Any]:
        """
        Create an ad.
        
        Args:
            adset_id: Parent ad set ID
            name: Ad name
            creative: Creative spec (image, video, text)
            status: 'ACTIVE', 'PAUSED'
        
        Returns:
            {'id': 'ad_id', ...}
        """
        if self.dry_run:
            logger.info("meta_create_ad_dry_run", name=name)
            return {"id": f"mock_ad_{int(time.time())}", "name": name}
        
        # First create creative
        creative_id = await self._create_creative(creative)
        
        params = {
            "name": name,
            "adset_id": adset_id,
            "creative": {"creative_id": creative_id},
            "status": status,
            "access_token": self.access_token
        }
        
        data = await self._request_with_retry(
            "POST",
            f"{self.BASE_URL}/{self.ad_account_id}/ads",
            json_body=params
        )
        
        logger.info("meta_ad_created", ad_id=data.get("id"), name=name)
        
        return data
    
    async def _create_creative(self, creative: Dict[str, Any]) -> str:
        """Create ad creative and return ID"""
        if self.dry_run:
            return f"mock_creative_{int(time.time())}"
        
        params = {
            **creative,
            "access_token": self.access_token
        }
        
        data = await self._request_with_retry(
            "POST",
            f"{self.BASE_URL}/{self.ad_account_id}/adcreatives",
            json_body=params
        )
        
        return data["id"]
    
    async def get_insights(
        self,
        object_id: str,
        level: str = "campaign",
        time_range: Optional[Dict[str, str]] = None,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pull insights (metrics) for a campaign/adset/ad.
        
        Args:
            object_id: Campaign/AdSet/Ad ID
            level: 'campaign', 'adset', 'ad'
            time_range: {'since': 'YYYY-MM-DD', 'until': 'YYYY-MM-DD'}
            fields: List of metric fields
        
        Returns:
            List of insight data
        """
        if self.dry_run:
            return self._mock_insights(object_id, level)
        
        default_fields = [
            "impressions",
            "reach",
            "clicks",
            "spend",
            "actions",  # Conversions
            "action_values",
            "ctr",
            "cpc",
            "cpp"
        ]
        
        params = {
            "level": level,
            "fields": ",".join(fields or default_fields),
            "access_token": self.access_token
        }
        
        if time_range:
            params["time_range"] = time_range
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/{object_id}/insights",
                params=params
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("data", [])
    
    async def send_conversion_event(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send offline conversion events via Conversions API (CAPI).
        
        Args:
            events: List of conversion events (see attribution.py for format)
        
        Returns:
            {'events_received': N, 'events_dropped': M}
        """
        if self.dry_run:
            logger.info("meta_send_conversions_dry_run", count=len(events))
            return {"events_received": len(events), "events_dropped": 0}
        
        if not self.pixel_id:
            raise ValueError("Pixel ID required for CAPI")
        
        params = {
            "data": events,
            "access_token": self.access_token
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/{self.pixel_id}/events",
                json=params
            )
            response.raise_for_status()
            data = response.json()
        
        logger.info("meta_conversions_sent",
                   received=data.get("events_received"),
                   dropped=data.get("events_dropped"))
        
        return data
    
    def _mock_insights(self, object_id: str, level: str) -> List[Dict[str, Any]]:
        """Generate mock insights for testing"""
        return [{
            "impressions": "12500",
            "reach": "10000",
            "clicks": "450",
            "spend": "250.50",
            "actions": [
                {"action_type": "lead", "value": "35"},
                {"action_type": "link_click", "value": "450"}
            ],
            "ctr": "3.6",
            "cpc": "0.56"
        }]

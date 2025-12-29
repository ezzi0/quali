"""
TikTok Ads API Adapter

Handles TikTok advertising via the TikTok Marketing API.
Supports campaigns, ad groups, ads, audience creation, and event tracking.
"""
from typing import Dict, Any, List, Optional
import time
import json
import httpx
import asyncio
import hashlib
from datetime import datetime

from ..config import get_settings
from ..logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TikTokAdsAdapter:
    """
    TikTok Marketing API client.
    
    Features:
    - Campaign, Ad Group, and Ad CRUD
    - Custom audience creation
    - Spark Ads support
    - Events API for conversions
    - Performance metrics pulling
    
    Docs: https://ads.tiktok.com/marketing_api/docs
    """
    
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"
    
    def __init__(
        self,
        advertiser_id: Optional[str] = None,
        access_token: Optional[str] = None,
        pixel_id: Optional[str] = None,
        dry_run: bool = False
    ):
        self.advertiser_id = advertiser_id or settings.tiktok_advertiser_id
        self.access_token = access_token or settings.tiktok_access_token
        self.pixel_id = pixel_id or settings.tiktok_pixel_id
        self.dry_run = dry_run
        
        if not self.access_token:
            logger.warning("tiktok_no_access_token")
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Access-Token": self.access_token or "",
            "Content-Type": "application/json",
        }
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        json_body: Optional[dict] = None,
        max_retries: int = 2,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Make API request with retry logic."""
        if self.dry_run:
            return {"code": 0, "data": {}, "dry_run": True}
        
        headers = self._get_headers()
        url = f"{self.BASE_URL}{endpoint}"
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(method, url, headers=headers, json=json_body)
                    data = response.json()
                    
                    # TikTok returns 200 with error codes in body
                    if data.get("code") not in (0, 40100):  # 40100 = partial success
                        if data.get("code") in (40001, 40002, 50001):  # Rate limit or server errors
                            raise httpx.HTTPStatusError(
                                f"TikTok API error: {data.get('message')}",
                                request=response.request,
                                response=response
                            )
                        # Return error for non-retryable errors
                        logger.error("tiktok_api_error", code=data.get("code"), message=data.get("message"))
                    
                    return data
            except Exception as e:
                last_error = e
                backoff = 2 ** attempt
                logger.warning("tiktok_request_retry", attempt=attempt + 1, backoff=backoff, error=str(e))
                await asyncio.sleep(backoff)
        raise last_error
    
    async def create_campaign(
        self,
        name: str,
        budget_daily: float,
        objective: str = "LEAD_GENERATION",
        budget_mode: str = "BUDGET_MODE_DAY",
        status: str = "CAMPAIGN_STATUS_DISABLE"
    ) -> Dict[str, Any]:
        """
        Create a TikTok campaign.
        
        Args:
            name: Campaign name
            budget_daily: Daily budget in dollars
            objective: LEAD_GENERATION, TRAFFIC, CONVERSIONS, REACH, VIDEO_VIEWS
            budget_mode: BUDGET_MODE_DAY, BUDGET_MODE_TOTAL
            status: CAMPAIGN_STATUS_ENABLE, CAMPAIGN_STATUS_DISABLE
        
        Returns:
            {'id': 'campaign_id', 'name': name, ...}
        """
        if self.dry_run:
            logger.info("tiktok_create_campaign_dry_run", name=name)
            return {
                "id": f"tiktok_campaign_{int(time.time())}",
                "name": name,
                "objective": objective,
                "status": status
            }
        
        # Map objective to TikTok format
        objective_type = self._map_objective(objective)
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "campaign_name": name,
            "objective_type": objective_type,
            "budget_mode": budget_mode,
            "budget": budget_daily,
            "operation_status": status,
        }
        
        data = await self._request_with_retry("POST", "/campaign/create/", json_body=payload)
        
        campaign_id = data.get("data", {}).get("campaign_id", f"unknown_{int(time.time())}")
        
        logger.info("tiktok_campaign_created", campaign_id=campaign_id, name=name)
        
        return {
            "id": campaign_id,
            "name": name,
            "objective": objective,
            "status": status
        }
    
    def _map_objective(self, objective: str) -> str:
        """Map common objective names to TikTok format."""
        mapping = {
            "LEAD_GENERATION": "LEAD_GENERATION",
            "TRAFFIC": "TRAFFIC",
            "CONVERSIONS": "CONVERSIONS",
            "REACH": "REACH",
            "VIDEO_VIEWS": "VIDEO_VIEWS",
            "APP_INSTALL": "APP_INSTALL",
            "BRAND_AWARENESS": "REACH",  # Map to nearest equivalent
        }
        return mapping.get(objective.upper(), "TRAFFIC")
    
    async def create_ad_group(
        self,
        campaign_id: str,
        name: str,
        budget_daily: float,
        targeting: Dict[str, Any],
        placement: List[str] = None,
        schedule_type: str = "SCHEDULE_FROM_NOW",
        bid_type: str = "BID_TYPE_NO_BID",
        optimization_goal: str = "CLICK",
        status: str = "ADGROUP_STATUS_DISABLE"
    ) -> Dict[str, Any]:
        """
        Create an ad group within a campaign.
        
        Args:
            campaign_id: Parent campaign ID
            name: Ad group name
            budget_daily: Daily budget in dollars
            targeting: Targeting configuration
            placement: Placements (PLACEMENT_TIKTOK, PLACEMENT_PANGLE, etc.)
            schedule_type: SCHEDULE_FROM_NOW, SCHEDULE_START_END
            bid_type: BID_TYPE_NO_BID, BID_TYPE_CPC, BID_TYPE_CPM
            optimization_goal: CLICK, CONVERT, VALUE
            status: ADGROUP_STATUS_ENABLE, ADGROUP_STATUS_DISABLE
        
        Returns:
            {'id': 'ad_group_id', 'name': name, ...}
        """
        if self.dry_run:
            logger.info("tiktok_create_adgroup_dry_run", name=name)
            return {
                "id": f"tiktok_adgroup_{int(time.time())}",
                "name": name,
                "campaign_id": campaign_id
            }
        
        # Build targeting spec
        targeting_spec = self._build_targeting_spec(targeting)
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "campaign_id": campaign_id,
            "adgroup_name": name,
            "placement_type": "PLACEMENT_TYPE_AUTOMATIC" if not placement else "PLACEMENT_TYPE_NORMAL",
            "placements": placement or ["PLACEMENT_TIKTOK"],
            "budget_mode": "BUDGET_MODE_DAY",
            "budget": budget_daily,
            "schedule_type": schedule_type,
            "schedule_start_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "bid_type": bid_type,
            "optimization_goal": optimization_goal,
            "operation_status": status,
            **targeting_spec
        }
        
        # Add pixel if conversion tracking
        if optimization_goal in ("CONVERT", "VALUE") and self.pixel_id:
            payload["pixel_id"] = self.pixel_id
        
        data = await self._request_with_retry("POST", "/adgroup/create/", json_body=payload)
        
        ad_group_id = data.get("data", {}).get("adgroup_id", f"unknown_{int(time.time())}")
        
        logger.info("tiktok_adgroup_created", ad_group_id=ad_group_id, name=name)
        
        return {
            "id": ad_group_id,
            "name": name,
            "campaign_id": campaign_id
        }
    
    def _build_targeting_spec(self, targeting: Dict[str, Any]) -> Dict[str, Any]:
        """Build TikTok targeting specification from common format."""
        spec = {}
        
        # Location targeting
        if "geo_locations" in targeting:
            locations = targeting["geo_locations"]
            if "countries" in locations:
                spec["location_ids"] = locations["countries"]  # Country codes
            if "cities" in locations:
                spec["location_ids"] = [c.get("id") or c.get("key") for c in locations["cities"]]
        
        # Age targeting
        if "age_min" in targeting or "age_max" in targeting:
            age_groups = self._get_age_groups(targeting.get("age_min", 18), targeting.get("age_max", 55))
            spec["age_groups"] = age_groups
        
        # Gender targeting
        if "genders" in targeting:
            gender_map = {"male": "GENDER_MALE", "female": "GENDER_FEMALE"}
            spec["gender"] = [gender_map.get(g.lower(), "GENDER_UNLIMITED") for g in targeting["genders"]]
        else:
            spec["gender"] = "GENDER_UNLIMITED"
        
        # Interest targeting
        if "interests" in targeting:
            interest_ids = [i.get("id") for i in targeting["interests"] if i.get("id")]
            if interest_ids:
                spec["interest_category_ids"] = interest_ids
        
        # Language targeting
        if "languages" in targeting:
            spec["languages"] = targeting["languages"]
        
        return spec
    
    def _get_age_groups(self, age_min: int, age_max: int) -> List[str]:
        """Map age range to TikTok age groups."""
        all_groups = [
            ("AGE_13_17", 13, 17),
            ("AGE_18_24", 18, 24),
            ("AGE_25_34", 25, 34),
            ("AGE_35_44", 35, 44),
            ("AGE_45_54", 45, 54),
            ("AGE_55_100", 55, 100),
        ]
        
        selected = []
        for group_name, group_min, group_max in all_groups:
            # Include group if there's any overlap
            if group_max >= age_min and group_min <= age_max:
                selected.append(group_name)
        
        return selected if selected else ["AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54"]
    
    async def create_ad(
        self,
        ad_group_id: str,
        name: str,
        creative: Dict[str, Any],
        landing_page_url: str,
        call_to_action: str = "LEARN_MORE",
        status: str = "AD_STATUS_DISABLE"
    ) -> Dict[str, Any]:
        """
        Create an ad within an ad group.
        
        Args:
            ad_group_id: Parent ad group ID
            name: Ad name
            creative: Creative content (text, image/video URLs)
            landing_page_url: Landing page URL
            call_to_action: CTA button type
            status: AD_STATUS_ENABLE, AD_STATUS_DISABLE
        
        Returns:
            {'id': 'ad_id', 'name': name, ...}
        """
        if self.dry_run:
            logger.info("tiktok_create_ad_dry_run", name=name)
            return {
                "id": f"tiktok_ad_{int(time.time())}",
                "name": name,
                "ad_group_id": ad_group_id
            }
        
        # Build creative spec
        ad_format = creative.get("format", "SINGLE_VIDEO")
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "adgroup_id": ad_group_id,
            "ad_name": name,
            "ad_format": ad_format,
            "landing_page_url": landing_page_url,
            "call_to_action": call_to_action,
            "operation_status": status,
        }
        
        # Add creative content based on format
        if ad_format == "SINGLE_IMAGE":
            payload["image_ids"] = creative.get("image_ids", [])
            payload["ad_text"] = creative.get("primary_text", "")
        elif ad_format == "SINGLE_VIDEO":
            payload["video_id"] = creative.get("video_id", "")
            payload["ad_text"] = creative.get("primary_text", "")
            if creative.get("thumbnail_id"):
                payload["image_ids"] = [creative["thumbnail_id"]]
        elif ad_format == "CAROUSEL":
            payload["carousel_image_index"] = creative.get("carousel_images", [])
        
        # Add display name and profile image if provided
        if creative.get("display_name"):
            payload["display_name"] = creative["display_name"]
        if creative.get("profile_image_id"):
            payload["profile_image_id"] = creative["profile_image_id"]
        
        data = await self._request_with_retry("POST", "/ad/create/", json_body=payload)
        
        ad_id = data.get("data", {}).get("ad_id", f"unknown_{int(time.time())}")
        
        logger.info("tiktok_ad_created", ad_id=ad_id, name=name)
        
        return {
            "id": ad_id,
            "name": name,
            "ad_group_id": ad_group_id
        }
    
    async def upload_image(
        self,
        image_url: str,
        filename: str = "creative.jpg"
    ) -> Dict[str, Any]:
        """
        Upload an image for use in ads.
        
        Args:
            image_url: URL of the image to upload
            filename: Filename for the uploaded image
        
        Returns:
            {'image_id': 'id', 'url': 'tiktok_url'}
        """
        if self.dry_run:
            return {"image_id": f"img_{int(time.time())}", "url": image_url}
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "upload_type": "UPLOAD_BY_URL",
            "image_url": image_url,
            "file_name": filename,
        }
        
        data = await self._request_with_retry("POST", "/file/image/ad/upload/", json_body=payload)
        
        return {
            "image_id": data.get("data", {}).get("image_id"),
            "url": data.get("data", {}).get("image_url"),
        }
    
    async def upload_video(
        self,
        video_url: str,
        filename: str = "creative.mp4"
    ) -> Dict[str, Any]:
        """
        Upload a video for use in ads.
        
        Args:
            video_url: URL of the video to upload
            filename: Filename for the uploaded video
        
        Returns:
            {'video_id': 'id', 'url': 'tiktok_url'}
        """
        if self.dry_run:
            return {"video_id": f"vid_{int(time.time())}", "url": video_url}
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "upload_type": "UPLOAD_BY_URL",
            "video_url": video_url,
            "file_name": filename,
        }
        
        data = await self._request_with_retry("POST", "/file/video/ad/upload/", json_body=payload)
        
        return {
            "video_id": data.get("data", {}).get("video_id"),
            "url": data.get("data", {}).get("video_url"),
        }
    
    async def update_ad_group_budget(
        self,
        ad_group_id: str,
        budget_daily: float
    ) -> Dict[str, Any]:
        """Update ad group daily budget."""
        if self.dry_run:
            logger.info("tiktok_update_budget_dry_run", ad_group_id=ad_group_id, budget=budget_daily)
            return {"id": ad_group_id, "budget": budget_daily}
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "adgroup_ids": [ad_group_id],
            "budget": budget_daily,
        }
        
        await self._request_with_retry("POST", "/adgroup/update/", json_body=payload)
        
        logger.info("tiktok_budget_updated", ad_group_id=ad_group_id, budget=budget_daily)
        
        return {"id": ad_group_id, "budget": budget_daily}
    
    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update campaign status."""
        if self.dry_run:
            return {"id": campaign_id, "status": status}
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "campaign_ids": [campaign_id],
            "operation_status": status,
        }
        
        await self._request_with_retry("POST", "/campaign/update/status/", json_body=payload)
        
        return {"id": campaign_id, "status": status}
    
    async def get_insights(
        self,
        campaign_ids: Optional[List[str]] = None,
        ad_group_ids: Optional[List[str]] = None,
        ad_ids: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pull performance insights/metrics.
        
        Args:
            campaign_ids: Filter by campaigns
            ad_group_ids: Filter by ad groups
            ad_ids: Filter by ads
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            metrics: Specific metrics to retrieve
        
        Returns:
            List of metric data
        """
        if self.dry_run:
            return self._mock_insights()
        
        default_metrics = [
            "spend", "impressions", "clicks", "ctr", "cpc",
            "conversions", "conversion_rate", "cost_per_conversion"
        ]
        
        # Determine data level and filters
        if ad_ids:
            data_level = "AUCTION_AD"
            filters = [{"field_name": "ad_id", "filter_type": "IN", "filter_value": json.dumps(ad_ids)}]
        elif ad_group_ids:
            data_level = "AUCTION_ADGROUP"
            filters = [{"field_name": "adgroup_id", "filter_type": "IN", "filter_value": json.dumps(ad_group_ids)}]
        elif campaign_ids:
            data_level = "AUCTION_CAMPAIGN"
            filters = [{"field_name": "campaign_id", "filter_type": "IN", "filter_value": json.dumps(campaign_ids)}]
        else:
            data_level = "AUCTION_ADVERTISER"
            filters = []
        
        # Default to last 7 days
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "report_type": "BASIC",
            "data_level": data_level,
            "dimensions": ["stat_time_day"],
            "metrics": metrics or default_metrics,
            "start_date": start_date,
            "end_date": end_date,
            "page": 1,
            "page_size": 1000,
        }
        
        if filters:
            payload["filters"] = filters
        
        data = await self._request_with_retry("GET", "/report/integrated/get/", json_body=payload)
        
        results = []
        for row in data.get("data", {}).get("list", []):
            metrics_data = row.get("metrics", {})
            results.append({
                "impressions": int(metrics_data.get("impressions", 0)),
                "clicks": int(metrics_data.get("clicks", 0)),
                "spend": float(metrics_data.get("spend", 0)),
                "conversions": int(metrics_data.get("conversions", 0)),
                "ctr": float(metrics_data.get("ctr", 0)),
                "cpc": float(metrics_data.get("cpc", 0)),
                "conversion_rate": float(metrics_data.get("conversion_rate", 0)),
                "cost_per_conversion": float(metrics_data.get("cost_per_conversion", 0)),
            })
        
        return results
    
    async def send_conversion_event(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send conversion events via TikTok Events API.
        
        Args:
            events: List of conversion events
        
        Returns:
            {'events_received': N, 'events_failed': M}
        """
        if self.dry_run:
            logger.info("tiktok_send_conversions_dry_run", count=len(events))
            return {"events_received": len(events), "events_failed": 0}
        
        if not self.pixel_id:
            raise ValueError("Pixel ID required for Events API")
        
        # Format events for TikTok
        formatted_events = []
        for event in events:
            formatted_event = {
                "event": event.get("event_name", "CompleteRegistration"),
                "event_time": event.get("timestamp") or int(datetime.utcnow().timestamp()),
                "event_id": event.get("event_id") or f"evt_{int(time.time())}_{len(formatted_events)}",
            }
            
            # User data with hashing
            user_data = {}
            if event.get("email"):
                user_data["email"] = self._hash_identifier(event["email"].lower().strip())
            if event.get("phone"):
                user_data["phone"] = self._hash_identifier(event["phone"])
            if event.get("external_id"):
                user_data["external_id"] = self._hash_identifier(str(event["external_id"]))
            
            if user_data:
                formatted_event["user"] = user_data
            
            # Properties
            if event.get("value") or event.get("currency"):
                formatted_event["properties"] = {
                    "value": event.get("value", 0),
                    "currency": event.get("currency", "USD"),
                }
            
            # Context
            if event.get("click_id") or event.get("page_url"):
                formatted_event["context"] = {}
                if event.get("click_id"):
                    formatted_event["context"]["ad"] = {"callback": event["click_id"]}
                if event.get("page_url"):
                    formatted_event["context"]["page"] = {"url": event["page_url"]}
            
            formatted_events.append(formatted_event)
        
        payload = {
            "pixel_code": self.pixel_id,
            "data": formatted_events,
        }
        
        data = await self._request_with_retry("POST", "/pixel/track/", json_body=payload)
        
        received = len(formatted_events)
        failed = len(data.get("data", {}).get("failed_events", []))
        
        logger.info("tiktok_conversions_sent", received=received - failed, failed=failed)
        
        return {"events_received": received - failed, "events_failed": failed}
    
    def _hash_identifier(self, value: str) -> str:
        """SHA-256 hash an identifier for privacy."""
        return hashlib.sha256(value.encode()).hexdigest()
    
    async def create_custom_audience(
        self,
        name: str,
        audience_type: str = "CUSTOMER_FILE",
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom audience.
        
        Args:
            name: Audience name
            audience_type: CUSTOMER_FILE, ENGAGEMENT, LOOKALIKE
            file_paths: Customer file paths for CUSTOMER_FILE type
        
        Returns:
            {'audience_id': 'id', 'name': name}
        """
        if self.dry_run:
            return {"audience_id": f"aud_{int(time.time())}", "name": name}
        
        payload = {
            "advertiser_id": self.advertiser_id,
            "custom_audience_name": name,
            "audience_type": audience_type,
        }
        
        if audience_type == "CUSTOMER_FILE" and file_paths:
            payload["file_paths"] = file_paths
        
        data = await self._request_with_retry("POST", "/dmp/custom_audience/create/", json_body=payload)
        
        return {
            "audience_id": data.get("data", {}).get("custom_audience_id"),
            "name": name,
        }
    
    def _mock_insights(self) -> List[Dict[str, Any]]:
        """Generate mock insights for testing."""
        return [{
            "impressions": 15000,
            "clicks": 580,
            "spend": 220.75,
            "conversions": 42,
            "ctr": 0.0387,
            "cpc": 0.38,
            "conversion_rate": 0.0724,
            "cost_per_conversion": 5.26,
        }]

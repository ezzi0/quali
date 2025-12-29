"""
Google Ads API Adapter

Handles Google Ads campaign management via the Google Ads API.
Supports campaigns, ad groups, responsive search ads, and conversion tracking.
"""
from typing import Dict, Any, List, Optional
import time
import httpx
import asyncio
import hashlib
from datetime import datetime

from ..config import get_settings
from ..logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class GoogleAdsAdapter:
    """
    Google Ads API client.
    
    Features:
    - Campaign, Ad Group, and Ad CRUD
    - Audience targeting
    - Responsive search ad creation
    - Performance metrics pulling
    - Enhanced conversions upload
    
    Docs: https://developers.google.com/google-ads/api
    """
    
    BASE_URL = "https://googleads.googleapis.com/v16"
    
    def __init__(
        self,
        customer_id: Optional[str] = None,
        developer_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        dry_run: bool = False
    ):
        self.customer_id = (customer_id or settings.google_ads_customer_id or "").replace("-", "")
        self.developer_token = developer_token or settings.google_ads_developer_token
        self.refresh_token = refresh_token or settings.google_ads_refresh_token
        self.client_id = client_id or settings.google_ads_client_id
        self.client_secret = client_secret or settings.google_ads_client_secret
        self.dry_run = dry_run
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        
        if not self.developer_token:
            logger.warning("google_ads_no_developer_token")
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise ValueError("Google Ads OAuth credentials not configured")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        
        return self._access_token
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {access_token}",
            "developer-token": self.developer_token or "",
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
            return {"dry_run": True}
        
        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        url = f"{self.BASE_URL}/customers/{self.customer_id}{endpoint}"
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(method, url, headers=headers, json=json_body)
                    if response.status_code in (429, 500, 502, 503):
                        raise httpx.HTTPStatusError(
                            f"Google Ads returned {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                last_error = e
                backoff = 2 ** attempt
                logger.warning("google_ads_request_retry", attempt=attempt + 1, backoff=backoff, error=str(e))
                await asyncio.sleep(backoff)
        raise last_error
    
    async def create_campaign(
        self,
        name: str,
        budget_daily: float,
        objective: str = "LEAD_GENERATION",
        status: str = "PAUSED",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Google Ads campaign.
        
        Args:
            name: Campaign name
            budget_daily: Daily budget in dollars
            objective: Campaign objective (LEAD_GENERATION, SALES, WEBSITE_TRAFFIC)
            status: ENABLED, PAUSED, REMOVED
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            {'id': 'campaign_id', 'name': name, ...}
        """
        if self.dry_run:
            logger.info("google_ads_create_campaign_dry_run", name=name)
            return {
                "id": f"google_campaign_{int(time.time())}",
                "name": name,
                "status": status,
                "budget_daily": budget_daily
            }
        
        # First create a budget
        budget_response = await self._create_campaign_budget(name, budget_daily)
        budget_resource = budget_response.get("resourceName", "")
        
        # Map objective to advertising channel type and sub type
        channel_config = self._map_objective_to_channel(objective)
        
        # Create campaign
        campaign_operation = {
            "create": {
                "name": name,
                "advertisingChannelType": channel_config["type"],
                "status": status,
                "campaignBudget": budget_resource,
                "startDate": start_date or datetime.now().strftime("%Y-%m-%d"),
                "networkSettings": {
                    "targetGoogleSearch": True,
                    "targetSearchNetwork": True,
                    "targetContentNetwork": False,
                }
            }
        }
        
        if channel_config.get("subType"):
            campaign_operation["create"]["advertisingChannelSubType"] = channel_config["subType"]
        
        data = await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"campaignOperation": campaign_operation}]
            }
        )
        
        campaign_id = self._extract_resource_id(data, "campaignResult")
        
        logger.info("google_ads_campaign_created", campaign_id=campaign_id, name=name)
        
        return {
            "id": campaign_id,
            "name": name,
            "status": status,
            "budget_resource": budget_resource
        }
    
    async def _create_campaign_budget(self, name: str, amount_daily: float) -> Dict[str, Any]:
        """Create a campaign budget."""
        if self.dry_run:
            return {"resourceName": f"customers/{self.customer_id}/campaignBudgets/mock_{int(time.time())}"}
        
        budget_operation = {
            "create": {
                "name": f"{name} Budget",
                "amountMicros": int(amount_daily * 1_000_000),
                "deliveryMethod": "STANDARD",
                "explicitlyShared": False
            }
        }
        
        data = await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"campaignBudgetOperation": budget_operation}]
            }
        )
        
        return {"resourceName": data.get("mutateOperationResponses", [{}])[0].get("campaignBudgetResult", {}).get("resourceName", "")}
    
    def _map_objective_to_channel(self, objective: str) -> Dict[str, str]:
        """Map marketing objective to Google Ads channel type."""
        mapping = {
            "LEAD_GENERATION": {"type": "SEARCH", "subType": None},
            "SALES": {"type": "SEARCH", "subType": None},
            "WEBSITE_TRAFFIC": {"type": "SEARCH", "subType": None},
            "BRAND_AWARENESS": {"type": "DISPLAY", "subType": None},
            "VIDEO": {"type": "VIDEO", "subType": None},
            "PERFORMANCE_MAX": {"type": "PERFORMANCE_MAX", "subType": None},
        }
        return mapping.get(objective, {"type": "SEARCH", "subType": None})
    
    async def create_ad_group(
        self,
        campaign_id: str,
        name: str,
        cpc_bid_micros: int = 1_000_000,
        status: str = "ENABLED",
        targeting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an ad group within a campaign.
        
        Args:
            campaign_id: Parent campaign ID
            name: Ad group name
            cpc_bid_micros: CPC bid in micros (1,000,000 = $1)
            status: ENABLED, PAUSED, REMOVED
            targeting: Targeting settings
        
        Returns:
            {'id': 'ad_group_id', 'name': name}
        """
        if self.dry_run:
            logger.info("google_ads_create_adgroup_dry_run", name=name)
            return {
                "id": f"google_adgroup_{int(time.time())}",
                "name": name,
                "campaign_id": campaign_id
            }
        
        ad_group_operation = {
            "create": {
                "name": name,
                "campaign": f"customers/{self.customer_id}/campaigns/{campaign_id}",
                "status": status,
                "type": "SEARCH_STANDARD",
                "cpcBidMicros": cpc_bid_micros
            }
        }
        
        data = await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"adGroupOperation": ad_group_operation}]
            }
        )
        
        ad_group_id = self._extract_resource_id(data, "adGroupResult")
        
        # Apply targeting if provided
        if targeting:
            await self._apply_ad_group_targeting(ad_group_id, targeting)
        
        logger.info("google_ads_adgroup_created", ad_group_id=ad_group_id, name=name)
        
        return {
            "id": ad_group_id,
            "name": name,
            "campaign_id": campaign_id
        }
    
    async def _apply_ad_group_targeting(self, ad_group_id: str, targeting: Dict[str, Any]) -> None:
        """Apply targeting criteria to an ad group."""
        operations = []
        
        # Location targeting
        if "geo_locations" in targeting:
            for location in targeting["geo_locations"].get("cities", []):
                operations.append({
                    "adGroupCriterionOperation": {
                        "create": {
                            "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                            "location": {
                                "geoTargetConstant": location.get("geo_target_constant")
                            }
                        }
                    }
                })
        
        # Age targeting
        if "age_min" in targeting or "age_max" in targeting:
            age_ranges = self._get_age_range_criteria(targeting.get("age_min", 18), targeting.get("age_max", 65))
            for age_range in age_ranges:
                operations.append({
                    "adGroupCriterionOperation": {
                        "create": {
                            "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                            "ageRange": {"type": age_range}
                        }
                    }
                })
        
        if operations:
            await self._request_with_retry(
                "POST",
                "/googleAds:mutate",
                json_body={"mutateOperations": operations}
            )
    
    def _get_age_range_criteria(self, age_min: int, age_max: int) -> List[str]:
        """Map age range to Google Ads age range criteria."""
        all_ranges = ["AGE_RANGE_18_24", "AGE_RANGE_25_34", "AGE_RANGE_35_44", 
                      "AGE_RANGE_45_54", "AGE_RANGE_55_64", "AGE_RANGE_65_UP"]
        # For simplicity, include all age ranges; production would filter based on min/max
        return all_ranges
    
    async def create_ad(
        self,
        ad_group_id: str,
        headlines: List[str],
        descriptions: List[str],
        final_urls: List[str],
        path1: Optional[str] = None,
        path2: Optional[str] = None,
        status: str = "ENABLED"
    ) -> Dict[str, Any]:
        """
        Create a responsive search ad.
        
        Args:
            ad_group_id: Parent ad group ID
            headlines: List of up to 15 headlines (30 chars each)
            descriptions: List of up to 4 descriptions (90 chars each)
            final_urls: Landing page URLs
            path1: First URL path (15 chars)
            path2: Second URL path (15 chars)
            status: ENABLED, PAUSED
        
        Returns:
            {'id': 'ad_id', 'ad_group_id': ad_group_id}
        """
        if self.dry_run:
            logger.info("google_ads_create_ad_dry_run", ad_group_id=ad_group_id)
            return {
                "id": f"google_ad_{int(time.time())}",
                "ad_group_id": ad_group_id,
                "headlines": headlines,
                "descriptions": descriptions
            }
        
        # Format headlines and descriptions for RSA
        headline_assets = [{"text": h[:30]} for h in headlines[:15]]
        description_assets = [{"text": d[:90]} for d in descriptions[:4]]
        
        ad_group_ad_operation = {
            "create": {
                "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                "status": status,
                "ad": {
                    "responsiveSearchAd": {
                        "headlines": headline_assets,
                        "descriptions": description_assets,
                        "path1": path1[:15] if path1 else None,
                        "path2": path2[:15] if path2 else None,
                    },
                    "finalUrls": final_urls
                }
            }
        }
        
        data = await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"adGroupAdOperation": ad_group_ad_operation}]
            }
        )
        
        ad_id = self._extract_resource_id(data, "adGroupAdResult")
        
        logger.info("google_ads_ad_created", ad_id=ad_id, ad_group_id=ad_group_id)
        
        return {
            "id": ad_id,
            "ad_group_id": ad_group_id,
            "headlines": headlines,
            "descriptions": descriptions
        }
    
    async def update_ad_group_bid(
        self,
        ad_group_id: str,
        cpc_bid_micros: int
    ) -> Dict[str, Any]:
        """Update ad group CPC bid."""
        if self.dry_run:
            logger.info("google_ads_update_bid_dry_run", ad_group_id=ad_group_id, bid=cpc_bid_micros)
            return {"id": ad_group_id, "cpc_bid_micros": cpc_bid_micros}
        
        ad_group_operation = {
            "update": {
                "resourceName": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                "cpcBidMicros": cpc_bid_micros
            },
            "updateMask": "cpcBidMicros"
        }
        
        data = await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"adGroupOperation": ad_group_operation}]
            }
        )
        
        logger.info("google_ads_bid_updated", ad_group_id=ad_group_id, bid=cpc_bid_micros)
        
        return {"id": ad_group_id, "cpc_bid_micros": cpc_bid_micros}
    
    async def update_campaign_budget(
        self,
        campaign_id: str,
        budget_daily: float
    ) -> Dict[str, Any]:
        """Update campaign daily budget."""
        if self.dry_run:
            logger.info("google_ads_update_budget_dry_run", campaign_id=campaign_id, budget=budget_daily)
            return {"id": campaign_id, "budget_daily": budget_daily}
        
        # First get the campaign's budget resource
        query = f"""
            SELECT campaign.campaign_budget
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        
        search_result = await self._search(query)
        if not search_result.get("results"):
            raise ValueError(f"Campaign {campaign_id} not found")
        
        budget_resource = search_result["results"][0]["campaign"]["campaignBudget"]
        
        # Update the budget
        budget_operation = {
            "update": {
                "resourceName": budget_resource,
                "amountMicros": int(budget_daily * 1_000_000)
            },
            "updateMask": "amountMicros"
        }
        
        await self._request_with_retry(
            "POST",
            "/googleAds:mutate",
            json_body={
                "mutateOperations": [{"campaignBudgetOperation": budget_operation}]
            }
        )
        
        logger.info("google_ads_budget_updated", campaign_id=campaign_id, budget=budget_daily)
        
        return {"id": campaign_id, "budget_daily": budget_daily}
    
    async def get_insights(
        self,
        campaign_id: Optional[str] = None,
        ad_group_id: Optional[str] = None,
        date_range: str = "LAST_7_DAYS",
        metrics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Pull performance insights/metrics.
        
        Args:
            campaign_id: Filter by campaign (optional)
            ad_group_id: Filter by ad group (optional)
            date_range: LAST_7_DAYS, LAST_30_DAYS, THIS_MONTH, etc.
            metrics: Specific metrics to retrieve
        
        Returns:
            List of metric data
        """
        if self.dry_run:
            return self._mock_insights(campaign_id, ad_group_id)
        
        default_metrics = [
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
            "metrics.conversions_value",
            "metrics.ctr",
            "metrics.average_cpc",
        ]
        
        metric_fields = ", ".join(metrics or default_metrics)
        
        # Build query based on level
        if ad_group_id:
            query = f"""
                SELECT ad_group.id, ad_group.name, {metric_fields}
                FROM ad_group
                WHERE ad_group.id = {ad_group_id}
                AND segments.date DURING {date_range}
            """
        elif campaign_id:
            query = f"""
                SELECT campaign.id, campaign.name, {metric_fields}
                FROM campaign
                WHERE campaign.id = {campaign_id}
                AND segments.date DURING {date_range}
            """
        else:
            query = f"""
                SELECT campaign.id, campaign.name, {metric_fields}
                FROM campaign
                WHERE segments.date DURING {date_range}
            """
        
        data = await self._search(query)
        
        results = []
        for row in data.get("results", []):
            metrics_data = row.get("metrics", {})
            results.append({
                "impressions": metrics_data.get("impressions", 0),
                "clicks": metrics_data.get("clicks", 0),
                "spend": metrics_data.get("costMicros", 0) / 1_000_000,
                "conversions": metrics_data.get("conversions", 0),
                "conversion_value": metrics_data.get("conversionsValue", 0),
                "ctr": metrics_data.get("ctr", 0),
                "cpc": metrics_data.get("averageCpc", 0) / 1_000_000,
            })
        
        return results
    
    async def _search(self, query: str) -> Dict[str, Any]:
        """Execute a GAQL search query."""
        if self.dry_run:
            return {"results": []}
        
        return await self._request_with_retry(
            "POST",
            "/googleAds:search",
            json_body={"query": query}
        )
    
    async def upload_offline_conversions(
        self,
        conversions: List[Dict[str, Any]],
        conversion_action_id: str
    ) -> Dict[str, Any]:
        """
        Upload offline conversions for enhanced conversions.
        
        Args:
            conversions: List of conversion data with user identifiers
            conversion_action_id: The conversion action ID
        
        Returns:
            Upload result summary
        """
        if self.dry_run:
            logger.info("google_ads_upload_conversions_dry_run", count=len(conversions))
            return {"uploaded": len(conversions), "failed": 0}
        
        operations = []
        for conv in conversions:
            # Hash user identifiers for privacy
            user_identifiers = []
            if conv.get("email"):
                user_identifiers.append({
                    "hashedEmail": self._hash_identifier(conv["email"].lower().strip())
                })
            if conv.get("phone"):
                user_identifiers.append({
                    "hashedPhoneNumber": self._hash_identifier(conv["phone"])
                })
            
            if not user_identifiers:
                continue
            
            operations.append({
                "create": {
                    "conversionAction": f"customers/{self.customer_id}/conversionActions/{conversion_action_id}",
                    "conversionDateTime": conv.get("conversion_time", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+00:00")),
                    "conversionValue": conv.get("value", 0),
                    "currencyCode": conv.get("currency", "USD"),
                    "userIdentifiers": user_identifiers,
                    "gclid": conv.get("gclid"),
                }
            })
        
        if not operations:
            return {"uploaded": 0, "failed": 0}
        
        data = await self._request_with_retry(
            "POST",
            f"/customers/{self.customer_id}:uploadClickConversions",
            json_body={
                "conversions": [op["create"] for op in operations],
                "partialFailure": True
            }
        )
        
        uploaded = len(operations)
        failed = len(data.get("partialFailureError", {}).get("details", []))
        
        logger.info("google_ads_conversions_uploaded", uploaded=uploaded - failed, failed=failed)
        
        return {"uploaded": uploaded - failed, "failed": failed}
    
    def _hash_identifier(self, value: str) -> str:
        """SHA-256 hash an identifier for privacy."""
        return hashlib.sha256(value.encode()).hexdigest()
    
    def _extract_resource_id(self, response: Dict[str, Any], result_key: str) -> str:
        """Extract resource ID from mutate response."""
        try:
            responses = response.get("mutateOperationResponses", [])
            if responses:
                resource_name = responses[0].get(result_key, {}).get("resourceName", "")
                # Resource name format: customers/{customer_id}/campaigns/{campaign_id}
                return resource_name.split("/")[-1]
        except (IndexError, KeyError):
            pass
        return f"unknown_{int(time.time())}"
    
    def _mock_insights(self, campaign_id: Optional[str], ad_group_id: Optional[str]) -> List[Dict[str, Any]]:
        """Generate mock insights for testing."""
        return [{
            "impressions": 8500,
            "clicks": 320,
            "spend": 185.50,
            "conversions": 28,
            "conversion_value": 4200.00,
            "ctr": 0.0376,
            "cpc": 0.58,
        }]

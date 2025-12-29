"""
Metrics Sync Worker

Syncs performance metrics from advertising platforms (Meta, Google, TikTok).
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...deps import get_db
from ...models import Campaign, AdSet, Ad, MarketingMetric, CampaignPlatform
from ...adapters.meta_marketing import MetaMarketingAdapter
from ...adapters.google_ads import GoogleAdsAdapter
from ...adapters.tiktok_ads import TikTokAdsAdapter
from ...config import get_settings
from ...logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


async def sync_metrics_job(lookback_days: int = 1):
    """
    Sync metrics from all advertising platforms.
    
    Schedule: Every 15 minutes
    Duration: ~2-5 minutes
    
    Args:
        lookback_days: Number of days to sync
    """
    logger.info("metrics_sync_job_started", lookback_days=lookback_days)
    
    db: Session = next(get_db())
    
    try:
        # Sync Meta campaigns
        meta_synced = await sync_meta_metrics(db, lookback_days)
        
        # Sync Google campaigns
        google_synced = await sync_google_metrics(db, lookback_days)
        
        # Sync TikTok campaigns
        tiktok_synced = await sync_tiktok_metrics(db, lookback_days)
        
        logger.info("metrics_sync_job_completed",
                   meta_synced=meta_synced,
                   google_synced=google_synced,
                   tiktok_synced=tiktok_synced)
        
        return {
            "status": "success",
            "meta_synced": meta_synced,
            "google_synced": google_synced,
            "tiktok_synced": tiktok_synced
        }
        
    except Exception as e:
        logger.error("metrics_sync_job_failed", error=str(e))
        raise
    
    finally:
        db.close()


async def sync_meta_metrics(db: Session, lookback_days: int) -> int:
    """Sync metrics from Meta for all active campaigns."""
    
    # Get Meta campaigns
    campaigns = db.execute(
        select(Campaign).where(Campaign.platform == CampaignPlatform.META)
    ).scalars().all()
    
    if not campaigns:
        return 0
    
    # Check if credentials are available
    dry_run = not (settings.meta_access_token and settings.meta_ad_account_id)
    adapter = MetaMarketingAdapter(dry_run=dry_run)
    synced_count = 0
    
    for campaign in campaigns:
        try:
            platform_id = campaign.platform_campaign_id
            if not platform_id:
                continue
            
            # Define time range
            time_range = {
                "since": (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d"),
                "until": datetime.utcnow().strftime("%Y-%m-%d")
            }
            
            # Fetch insights
            insights = await adapter.get_insights(
                object_id=platform_id,
                level="campaign",
                time_range=time_range
            )
            
            for insight in insights:
                synced_count += _process_meta_insight(db, campaign, insight)
            
            # Also sync ad set level
            for ad_set in campaign.ad_sets:
                if ad_set.platform_adset_id:
                    adset_insights = await adapter.get_insights(
                        object_id=ad_set.platform_adset_id,
                        level="adset",
                        time_range=time_range
                    )
                    for insight in adset_insights:
                        synced_count += _process_meta_insight(
                            db, campaign, insight, ad_set_id=ad_set.id
                        )
            
            db.commit()
            
        except Exception as e:
            logger.error("meta_campaign_sync_failed",
                       campaign_id=campaign.id,
                       error=str(e))
    
    return synced_count


def _process_meta_insight(
    db: Session,
    campaign: Campaign,
    insight: dict,
    ad_set_id: int = None,
    ad_id: int = None
) -> int:
    """Process and store a Meta insight."""
    try:
        date_str = insight.get("date_start", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # Extract actions (conversions)
        actions = insight.get("actions", [])
        leads = sum(int(a["value"]) for a in actions if a.get("action_type") == "lead")
        conversions = sum(int(a["value"]) for a in actions if a.get("action_type") in ["purchase", "complete_registration"])
        
        # Create or update metric
        metric = MarketingMetric(
            date=datetime.strptime(date_str, "%Y-%m-%d").date(),
            campaign_id=campaign.id,
            ad_set_id=ad_set_id,
            ad_id=ad_id,
            platform="meta",
            channel=insight.get("publisher_platform", "facebook"),
            impressions=int(insight.get("impressions", 0)),
            reach=int(insight.get("reach", 0)),
            clicks=int(insight.get("clicks", 0)),
            leads=leads,
            closed_won=conversions,
            spend=float(insight.get("spend", 0)),
            ctr=float(insight.get("ctr", 0)) if insight.get("ctr") else None,
            cpc=float(insight.get("cpc", 0)) if insight.get("cpc") else None,
            platform_data=insight
        )
        
        db.merge(metric)
        return 1
        
    except Exception as e:
        logger.warning("meta_insight_processing_failed", error=str(e))
        return 0


async def sync_google_metrics(db: Session, lookback_days: int) -> int:
    """Sync metrics from Google Ads for all active campaigns."""
    
    # Get Google campaigns
    campaigns = db.execute(
        select(Campaign).where(Campaign.platform == CampaignPlatform.GOOGLE)
    ).scalars().all()
    
    if not campaigns:
        return 0
    
    # Check if credentials are available
    dry_run = not (settings.google_ads_developer_token and settings.google_ads_customer_id)
    adapter = GoogleAdsAdapter(dry_run=dry_run)
    synced_count = 0
    
    # Determine date range
    date_range = "LAST_7_DAYS" if lookback_days <= 7 else "LAST_30_DAYS"
    
    for campaign in campaigns:
        try:
            platform_id = campaign.platform_campaign_id
            if not platform_id:
                continue
            
            # Fetch insights
            insights = await adapter.get_insights(
                campaign_id=platform_id,
                date_range=date_range
            )
            
            for insight in insights:
                synced_count += _process_google_insight(db, campaign, insight)
            
            # Sync ad group level
            for ad_set in campaign.ad_sets:
                if ad_set.platform_adset_id:
                    adgroup_insights = await adapter.get_insights(
                        ad_group_id=ad_set.platform_adset_id,
                        date_range=date_range
                    )
                    for insight in adgroup_insights:
                        synced_count += _process_google_insight(
                            db, campaign, insight, ad_set_id=ad_set.id
                        )
            
            db.commit()
            
        except Exception as e:
            logger.error("google_campaign_sync_failed",
                       campaign_id=campaign.id,
                       error=str(e))
    
    return synced_count


def _process_google_insight(
    db: Session,
    campaign: Campaign,
    insight: dict,
    ad_set_id: int = None,
    ad_id: int = None
) -> int:
    """Process and store a Google Ads insight."""
    try:
        # Google insights may have date in segments
        date_str = insight.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # Create or update metric
        metric = MarketingMetric(
            date=datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else datetime.utcnow().date(),
            campaign_id=campaign.id,
            ad_set_id=ad_set_id,
            ad_id=ad_id,
            platform="google",
            channel="google_search",  # Default, could be parsed from insight
            impressions=int(insight.get("impressions", 0)),
            reach=0,  # Google doesn't provide reach in the same way
            clicks=int(insight.get("clicks", 0)),
            leads=int(insight.get("conversions", 0)),
            closed_won=0,  # Would need to map conversion types
            spend=float(insight.get("spend", 0)),
            ctr=float(insight.get("ctr", 0)) if insight.get("ctr") else None,
            cpc=float(insight.get("cpc", 0)) if insight.get("cpc") else None,
            platform_data=insight
        )
        
        db.merge(metric)
        return 1
        
    except Exception as e:
        logger.warning("google_insight_processing_failed", error=str(e))
        return 0


async def sync_tiktok_metrics(db: Session, lookback_days: int) -> int:
    """Sync metrics from TikTok Ads for all active campaigns."""
    
    # Get TikTok campaigns
    campaigns = db.execute(
        select(Campaign).where(Campaign.platform == CampaignPlatform.TIKTOK)
    ).scalars().all()
    
    if not campaigns:
        return 0
    
    # Check if credentials are available
    dry_run = not (settings.tiktok_access_token and settings.tiktok_advertiser_id)
    adapter = TikTokAdsAdapter(dry_run=dry_run)
    synced_count = 0
    
    # Date range
    start_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    for campaign in campaigns:
        try:
            platform_id = campaign.platform_campaign_id
            if not platform_id:
                continue
            
            # Fetch insights
            insights = await adapter.get_insights(
                campaign_ids=[platform_id],
                start_date=start_date,
                end_date=end_date
            )
            
            for insight in insights:
                synced_count += _process_tiktok_insight(db, campaign, insight)
            
            # Sync ad group level
            for ad_set in campaign.ad_sets:
                if ad_set.platform_adset_id:
                    adgroup_insights = await adapter.get_insights(
                        ad_group_ids=[ad_set.platform_adset_id],
                        start_date=start_date,
                        end_date=end_date
                    )
                    for insight in adgroup_insights:
                        synced_count += _process_tiktok_insight(
                            db, campaign, insight, ad_set_id=ad_set.id
                        )
            
            db.commit()
            
        except Exception as e:
            logger.error("tiktok_campaign_sync_failed",
                       campaign_id=campaign.id,
                       error=str(e))
    
    return synced_count


def _process_tiktok_insight(
    db: Session,
    campaign: Campaign,
    insight: dict,
    ad_set_id: int = None,
    ad_id: int = None
) -> int:
    """Process and store a TikTok insight."""
    try:
        date_str = insight.get("stat_time_day", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # Create or update metric
        metric = MarketingMetric(
            date=datetime.strptime(date_str[:10], "%Y-%m-%d").date() if isinstance(date_str, str) else datetime.utcnow().date(),
            campaign_id=campaign.id,
            ad_set_id=ad_set_id,
            ad_id=ad_id,
            platform="tiktok",
            channel="tiktok",
            impressions=int(insight.get("impressions", 0)),
            reach=int(insight.get("reach", 0)) if insight.get("reach") else 0,
            clicks=int(insight.get("clicks", 0)),
            leads=int(insight.get("conversions", 0)),
            closed_won=0,
            spend=float(insight.get("spend", 0)),
            ctr=float(insight.get("ctr", 0)) if insight.get("ctr") else None,
            cpc=float(insight.get("cpc", 0)) if insight.get("cpc") else None,
            conversion_rate=float(insight.get("conversion_rate", 0)) if insight.get("conversion_rate") else None,
            platform_data=insight
        )
        
        db.merge(metric)
        return 1
        
    except Exception as e:
        logger.warning("tiktok_insight_processing_failed", error=str(e))
        return 0


async def sync_ad_level_metrics(db: Session, lookback_days: int = 1) -> int:
    """Sync ad-level metrics for detailed creative analysis."""
    synced = 0
    
    # Get all active ads
    ads = db.execute(
        select(Ad).where(Ad.status.in_(["active", "paused"]))
    ).scalars().all()
    
    for ad in ads:
        if not ad.platform_ad_id:
            continue
        
        ad_set = ad.ad_set
        if not ad_set:
            continue
        
        campaign = ad_set.campaign
        if not campaign:
            continue
        
        try:
            platform = campaign.platform.value
            
            if platform == "meta":
                adapter = MetaMarketingAdapter(dry_run=True)
                insights = await adapter.get_insights(
                    object_id=ad.platform_ad_id,
                    level="ad"
                )
                for insight in insights:
                    synced += _process_meta_insight(
                        db, campaign, insight,
                        ad_set_id=ad_set.id, ad_id=ad.id
                    )
            
            # Similar for Google and TikTok...
            
        except Exception as e:
            logger.warning("ad_metrics_sync_failed",
                         ad_id=ad.id,
                         error=str(e))
    
    db.commit()
    return synced


if __name__ == "__main__":
    # For manual execution
    import asyncio
    asyncio.run(sync_metrics_job(lookback_days=7))

"""
Metrics Sync Worker

Syncs performance metrics from advertising platforms.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...deps import get_db
from ...models import Campaign, AdSet, Ad, MarketingMetric
from ...adapters.meta_marketing import MetaMarketingAdapter
from ...logging import get_logger

logger = get_logger(__name__)


def sync_metrics_job(lookback_days: int = 1):
    """
    Sync metrics from advertising platforms.
    
    Schedule: Every 15 minutes
    Duration: ~2-5 minutes
    
    Args:
        lookback_days: Number of days to sync
    """
    logger.info("metrics_sync_job_started", lookback_days=lookback_days)
    
    db: Session = next(get_db())
    
    try:
        # Sync Meta campaigns
        meta_synced = sync_meta_metrics(db, lookback_days)
        
        # TODO: Sync Google and TikTok when implemented
        
        logger.info("metrics_sync_job_completed",
                   meta_synced=meta_synced)
        
        return {
            "status": "success",
            "meta_synced": meta_synced
        }
        
    except Exception as e:
        logger.error("metrics_sync_job_failed", error=str(e))
        raise
    
    finally:
        db.close()


async def sync_meta_metrics(db: Session, lookback_days: int) -> int:
    """Sync metrics from Meta for all active campaigns"""
    
    # Get Meta campaigns
    campaigns = db.execute(
        select(Campaign).where(Campaign.platform == "meta")
    ).scalars().all()
    
    if not campaigns:
        return 0
    
    adapter = MetaMarketingAdapter(dry_run=True)  # TODO: Make configurable
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
                # Parse and store metrics
                date_str = insight.get("date_start", datetime.utcnow().strftime("%Y-%m-%d"))
                
                # Extract actions (conversions)
                actions = insight.get("actions", [])
                leads = sum(int(a["value"]) for a in actions if a["action_type"] == "lead")
                
                # Upsert metric
                metric = MarketingMetric(
                    date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                    campaign_id=campaign.id,
                    platform="meta",
                    channel="facebook",  # TODO: Parse from insight
                    impressions=int(insight.get("impressions", 0)),
                    reach=int(insight.get("reach", 0)),
                    clicks=int(insight.get("clicks", 0)),
                    leads=leads,
                    spend=float(insight.get("spend", 0)),
                    ctr=float(insight.get("ctr", 0)),
                    cpc=float(insight.get("cpc", 0)),
                    platform_data=insight
                )
                
                db.merge(metric)
                synced_count += 1
            
            db.commit()
            
        except Exception as e:
            logger.error("campaign_metrics_sync_failed",
                       campaign_id=campaign.id,
                       error=str(e))
    
    return synced_count


if __name__ == "__main__":
    # For manual execution
    import asyncio
    asyncio.run(sync_metrics_job(lookback_days=7))


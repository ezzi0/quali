"""
Budget Optimization Worker

Runs hourly to optimize budget allocation across active campaigns.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...deps import get_db
from ...models import Campaign, CampaignStatus
from ...services.marketing.budget_optimizer import BudgetOptimizerService
from ...logging import get_logger

logger = get_logger(__name__)


def optimize_budgets_job(auto_apply: bool = False):
    """
    Hourly job to optimize campaign budgets.
    
    Schedule: Every hour
    Duration: ~1-2 minutes
    
    Args:
        auto_apply: If True, automatically apply recommendations
    """
    logger.info("budget_optimization_job_started", auto_apply=auto_apply)
    
    db: Session = next(get_db())
    
    try:
        # Get active campaigns
        campaigns = db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalars().all()
        
        if not campaigns:
            logger.info("no_active_campaigns")
            return {"status": "success", "campaigns_optimized": 0}
        
        service = BudgetOptimizerService(db)
        total_recommendations = 0
        total_applied = 0
        
        for campaign in campaigns:
            try:
                recommendations = service.optimize_campaign_budget(
                    campaign_id=campaign.id,
                    lookback_days=7,
                    volatility_cap=0.20
                )
                
                total_recommendations += len(recommendations)
                
                if auto_apply and recommendations:
                    applied = service.apply_recommendations(
                        recommendations,
                        auto_approve=True
                    )
                    total_applied += applied
                    
                    logger.info("budget_optimized",
                               campaign_id=campaign.id,
                               recommendations=len(recommendations),
                               applied=applied)
                
            except Exception as e:
                logger.error("campaign_optimization_failed",
                           campaign_id=campaign.id,
                           error=str(e))
        
        logger.info("budget_optimization_job_completed",
                   campaigns_processed=len(campaigns),
                   total_recommendations=total_recommendations,
                   total_applied=total_applied)
        
        return {
            "status": "success",
            "campaigns_processed": len(campaigns),
            "total_recommendations": total_recommendations,
            "total_applied": total_applied
        }
        
    except Exception as e:
        logger.error("budget_optimization_job_failed", error=str(e))
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    # For manual execution
    optimize_budgets_job(auto_apply=False)


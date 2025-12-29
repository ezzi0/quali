"""
Learning Cycle Worker

Runs the learning and adaptation cycle for marketing campaigns.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from ...deps import get_db
from ...services.marketing.learning_service import LearningService
from ...services.marketing.experiment_runner import ExperimentRunnerService
from ...services.marketing.lead_persona_matcher import LeadPersonaMatcherService
from ...logging import get_logger

logger = get_logger(__name__)


def run_learning_job(
    lookback_days: int = 7,
    auto_apply: bool = True
):
    """
    Run the learning and adaptation cycle.
    
    Schedule: Daily at 6 AM
    Duration: ~5-15 minutes
    
    Args:
        lookback_days: Number of days of data to analyze
        auto_apply: Whether to automatically apply learnings
    """
    logger.info("learning_job_started", 
               lookback_days=lookback_days,
               auto_apply=auto_apply)
    
    db: Session = next(get_db())
    
    try:
        # Run main learning cycle
        learning_service = LearningService(db)
        learning_result = learning_service.run_learning_cycle(
            lookback_days=lookback_days,
            auto_apply=auto_apply
        )
        
        # Check experiment stopping rules
        experiment_service = ExperimentRunnerService(db)
        experiments_to_stop = experiment_service.run_experiment_checks()
        
        experiments_stopped = 0
        if auto_apply:
            for exp in experiments_to_stop:
                try:
                    experiment_service.stop_experiment(
                        exp["experiment_id"],
                        reason="; ".join(exp.get("reasons", ["Auto-stop"]))
                    )
                    experiments_stopped += 1
                except Exception as e:
                    logger.warning("experiment_stop_failed",
                                 experiment_id=exp["experiment_id"],
                                 error=str(e))
        
        # Match unassigned leads to personas
        lead_matcher = LeadPersonaMatcherService(db)
        lead_matches = lead_matcher.batch_match_leads(auto_assign=auto_apply)
        leads_matched = sum(
            1 for matches in lead_matches.values()
            if matches and matches[0].is_strong_match
        )
        
        logger.info("learning_job_completed",
                   personas_analyzed=learning_result.personas_analyzed,
                   creatives_analyzed=learning_result.creatives_analyzed,
                   actions_taken=len(learning_result.actions_taken),
                   experiments_stopped=experiments_stopped,
                   leads_matched=leads_matched)
        
        return {
            "status": "success",
            "cycle_id": learning_result.cycle_id,
            "personas_analyzed": learning_result.personas_analyzed,
            "creatives_analyzed": learning_result.creatives_analyzed,
            "actions_taken": len(learning_result.actions_taken),
            "experiments_checked": len(experiments_to_stop),
            "experiments_stopped": experiments_stopped,
            "leads_matched": leads_matched,
            "improvements": learning_result.improvements
        }
        
    except Exception as e:
        logger.error("learning_job_failed", error=str(e))
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    # For manual execution
    run_learning_job(lookback_days=7, auto_apply=False)


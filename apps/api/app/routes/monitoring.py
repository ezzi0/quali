"""Monitoring endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
from ..auth import require_staff_user
from ..monitoring import run_monitoring_checks, HealthMonitor, AlertManager

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    System health check.
    
    Returns comprehensive health status of all components.
    """
    monitor = HealthMonitor(db)
    return monitor.check_system_health()


@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Get current system alerts.
    
    Returns list of active alerts for budget anomalies,
    performance issues, and attribution problems.
    """
    alert_manager = AlertManager(db)
    alerts = alert_manager.generate_alerts()
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "high_severity": sum(1 for a in alerts if a["severity"] == "high"),
        "medium_severity": sum(1 for a in alerts if a["severity"] == "medium"),
    }


@router.get("/monitoring")
async def run_monitoring(
    db: Session = Depends(get_db),
    _user = Depends(require_staff_user),
):
    """
    Run full monitoring suite.
    
    Executes all health checks and alert detection.
    Should be called periodically (every 5 minutes recommended).
    """
    return run_monitoring_checks(db)

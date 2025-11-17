"""
Monitoring and Alerting System

Provides health checks, performance monitoring, and alert triggers
for the marketing and CRM system.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .config import get_settings
from .logging import get_logger
from .models import (
    Campaign, AdSet, MarketingMetric,
    Lead, Qualification,
    CampaignStatus
)

settings = get_settings()
logger = get_logger(__name__)


class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Comprehensive health check.
        
        Returns:
            Health status with component checks
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Database check
        try:
            self.db.execute(select(func.count()).select_from(Lead))
            health["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "degraded"
        
        # Campaign health
        try:
            active_campaigns = self.db.execute(
                select(func.count()).select_from(Campaign).where(
                    Campaign.status == CampaignStatus.ACTIVE
                )
            ).scalar()
            
            health["components"]["campaigns"] = {
                "status": "healthy",
                "active_count": active_campaigns
            }
        except Exception as e:
            health["components"]["campaigns"] = {"status": "error", "error": str(e)}
        
        # Lead qualification health
        try:
            recent_leads = self.db.execute(
                select(func.count()).select_from(Lead).where(
                    Lead.created_at >= datetime.utcnow() - timedelta(hours=24)
                )
            ).scalar()
            
            health["components"]["leads"] = {
                "status": "healthy",
                "last_24h": recent_leads
            }
        except Exception as e:
            health["components"]["leads"] = {"status": "error", "error": str(e)}
        
        return health


class PerformanceMonitor:
    """Performance and anomaly detection"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_budget_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect budget overspend or underspend anomalies.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Get active campaigns
        campaigns = self.db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalars().all()
        
        for campaign in campaigns:
            if not campaign.budget_daily:
                continue
            
            # Check today's spend
            today_spend = campaign.spend_today
            budget = float(campaign.budget_daily)
            
            # Overspend (>110% of budget)
            if today_spend > budget * 1.1:
                anomalies.append({
                    "type": "budget_overspend",
                    "severity": "high",
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "budget": budget,
                    "actual_spend": today_spend,
                    "overspend_pct": ((today_spend / budget) - 1) * 100
                })
            
            # Significant underspend (<50% by 6pm)
            hour = datetime.utcnow().hour
            if hour >= 18 and today_spend < budget * 0.5:
                anomalies.append({
                    "type": "budget_underspend",
                    "severity": "medium",
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "budget": budget,
                    "actual_spend": today_spend,
                    "underspend_pct": (1 - (today_spend / budget)) * 100
                })
        
        return anomalies
    
    def detect_performance_anomalies(self, lookback_days: int = 7) -> List[Dict[str, Any]]:
        """
        Detect performance anomalies (CVR drops, CPA spikes).
        
        Args:
            lookback_days: Days to analyze
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        
        # Get campaigns with ad sets
        campaigns = self.db.execute(
            select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
        ).scalars().all()
        
        for campaign in campaigns:
            # Calculate average CVR for last 7 days
            metrics = self.db.execute(
                select(MarketingMetric).where(
                    MarketingMetric.campaign_id == campaign.id,
                    MarketingMetric.date >= cutoff_date
                )
            ).scalars().all()
            
            if not metrics:
                continue
            
            # Calculate metrics
            total_leads = sum(m.leads for m in metrics)
            total_closed = sum(m.closed_won for m in metrics)
            total_spend = sum(float(m.spend) for m in metrics)
            
            if total_leads > 0:
                cvr = total_closed / total_leads
                cpa = total_spend / total_closed if total_closed > 0 else 0
                
                # CVR dropped below 2%
                if cvr < 0.02 and total_leads > 20:
                    anomalies.append({
                        "type": "low_cvr",
                        "severity": "high",
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "cvr": cvr,
                        "leads": total_leads,
                        "conversions": total_closed
                    })
                
                # CPA above $500
                if cpa > 500 and total_closed > 0:
                    anomalies.append({
                        "type": "high_cpa",
                        "severity": "medium",
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "cpa": cpa,
                        "spend": total_spend,
                        "conversions": total_closed
                    })
        
        return anomalies
    
    def check_attribution_health(self) -> Dict[str, Any]:
        """
        Check attribution tracking health.
        
        Returns:
            Attribution health metrics
        """
        # Recent leads (last 24h)
        recent_leads = self.db.execute(
            select(Lead).where(
                Lead.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).scalars().all()
        
        if not recent_leads:
            return {
                "status": "no_data",
                "total_leads": 0,
                "attributed": 0,
                "attribution_rate": 0
            }
        
        # Count attributed leads
        attributed = sum(1 for lead in recent_leads if lead.attribution_data)
        attribution_rate = attributed / len(recent_leads) if recent_leads else 0
        
        status = "healthy"
        if attribution_rate < 0.5:
            status = "degraded"
        if attribution_rate < 0.2:
            status = "unhealthy"
        
        return {
            "status": status,
            "total_leads": len(recent_leads),
            "attributed": attributed,
            "attribution_rate": attribution_rate,
            "warning": "Low attribution rate" if attribution_rate < 0.5 else None
        }


class AlertManager:
    """Alert generation and notification"""
    
    def __init__(self, db: Session):
        self.db = db
        self.health_monitor = HealthMonitor(db)
        self.perf_monitor = PerformanceMonitor(db)
    
    def generate_alerts(self) -> List[Dict[str, Any]]:
        """
        Generate all alerts.
        
        Returns:
            List of alerts to be sent
        """
        alerts = []
        
        # Budget anomalies
        budget_anomalies = self.perf_monitor.detect_budget_anomalies()
        for anomaly in budget_anomalies:
            alerts.append({
                "type": "budget_anomaly",
                "severity": anomaly["severity"],
                "title": f"Budget {anomaly['type'].replace('_', ' ').title()}",
                "message": self._format_budget_alert(anomaly),
                "data": anomaly,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Performance anomalies
        perf_anomalies = self.perf_monitor.detect_performance_anomalies()
        for anomaly in perf_anomalies:
            alerts.append({
                "type": "performance_anomaly",
                "severity": anomaly["severity"],
                "title": f"Performance Issue: {anomaly['type'].upper()}",
                "message": self._format_performance_alert(anomaly),
                "data": anomaly,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Attribution health
        attribution = self.perf_monitor.check_attribution_health()
        if attribution["status"] in ["degraded", "unhealthy"]:
            alerts.append({
                "type": "attribution",
                "severity": "medium" if attribution["status"] == "degraded" else "high",
                "title": "Low Attribution Rate",
                "message": f"Only {attribution['attribution_rate']*100:.1f}% of recent leads have attribution data. Check tracking pixels and UTM parameters.",
                "data": attribution,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def _format_budget_alert(self, anomaly: Dict[str, Any]) -> str:
        """Format budget anomaly alert message"""
        if anomaly["type"] == "budget_overspend":
            return (
                f"Campaign '{anomaly['campaign_name']}' has overspent by "
                f"{anomaly['overspend_pct']:.1f}%. "
                f"Budget: ${anomaly['budget']:.2f}, "
                f"Actual: ${anomaly['actual_spend']:.2f}. "
                f"Consider pausing or reducing budget."
            )
        else:
            return (
                f"Campaign '{anomaly['campaign_name']}' is underspending by "
                f"{anomaly['underspend_pct']:.1f}%. "
                f"Budget: ${anomaly['budget']:.2f}, "
                f"Actual: ${anomaly['actual_spend']:.2f}. "
                f"Check campaign settings and targeting."
            )
    
    def _format_performance_alert(self, anomaly: Dict[str, Any]) -> str:
        """Format performance anomaly alert message"""
        if anomaly["type"] == "low_cvr":
            return (
                f"Campaign '{anomaly['campaign_name']}' has low conversion rate "
                f"({anomaly['cvr']*100:.1f}%) with {anomaly['leads']} leads and "
                f"{anomaly['conversions']} conversions. Review creative and targeting."
            )
        else:
            return (
                f"Campaign '{anomaly['campaign_name']}' has high CPA "
                f"(${anomaly['cpa']:.2f}) after spending ${anomaly['spend']:.2f} "
                f"for {anomaly['conversions']} conversions. Consider optimization."
            )


def run_monitoring_checks(db: Session) -> Dict[str, Any]:
    """
    Run all monitoring checks and return results.
    
    This should be called periodically (e.g., every 5 minutes).
    
    Returns:
        Monitoring results with health and alerts
    """
    health_monitor = HealthMonitor(db)
    alert_manager = AlertManager(db)
    
    health = health_monitor.check_system_health()
    alerts = alert_manager.generate_alerts()
    
    # Log alerts
    for alert in alerts:
        logger.warning(
            "monitoring_alert",
            alert_type=alert["type"],
            severity=alert["severity"],
            title=alert["title"],
            data=alert["data"]
        )
    
    return {
        "health": health,
        "alerts": alerts,
        "alert_count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


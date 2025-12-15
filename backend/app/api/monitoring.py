"""
Monitoring API endpoints
Handles system monitoring, metrics, and health checks
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..services.monitoring_service import monitoring_service

router = APIRouter()


@router.get("/health")
async def get_system_health():
    """Get current system health status"""
    try:
        health = monitoring_service.get_system_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/health")
async def get_servers_health(server_id: Optional[int] = Query(None)):
    """Get server health status"""
    try:
        health = monitoring_service.get_server_health(server_id)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary(hours: int = Query(24, ge=1, le=168)):
    """Get metrics summary for the specified time period"""
    try:
        summary = monitoring_service.get_metrics_summary(hours)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts():
    """Get current active alerts"""
    try:
        alerts = monitoring_service.get_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """Get Prometheus metrics in text format"""
    try:
        metrics = monitoring_service.get_prometheus_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_monitoring():
    """Start the monitoring service"""
    try:
        await monitoring_service.start_monitoring()
        return {"message": "Monitoring service started", "status": "active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_monitoring():
    """Stop the monitoring service"""
    try:
        await monitoring_service.stop_monitoring()
        return {"message": "Monitoring service stopped", "status": "inactive"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_monitoring_status():
    """Get monitoring service status"""
    try:
        return {
            "active": monitoring_service.monitoring_active,
            "system_metrics_count": len(monitoring_service.system_metrics),
            "server_metrics_count": sum(len(metrics) for metrics in monitoring_service.server_metrics.values()),
            "task_metrics_count": len(monitoring_service.task_metrics),
            "active_alerts": len(monitoring_service.active_alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
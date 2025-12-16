"""Analytics endpoints for forecasts and anomaly insights."""

from fastapi import APIRouter, HTTPException, Query

from ..services.analytics_service import analytics_service

router = APIRouter()


@router.get("/forecast")
async def get_forecast(
    hours: int = Query(24, ge=1, le=168),
    horizon: int = Query(6, ge=1, le=48),
    tenant: str | None = Query(None),
    server_id: int | None = Query(None),
    task_type: str | None = Query(None),
):
    try:
        return analytics_service.forecast(
            hours=hours,
            horizon=horizon,
            tenant=tenant,
            server_id=server_id,
            task_type=task_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/anomalies")
async def get_anomalies():
    try:
        return analytics_service.get_anomalies()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/recommendations")
async def get_recommendations():
    try:
        return analytics_service.get_recommendations()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

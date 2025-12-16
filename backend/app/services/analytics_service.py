"""
Analytics service for forecasting, anomaly detection, and recommendations.
Uses lightweight heuristics to provide chart-ready series for the dashboard
without external ML dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

from .monitoring_service import monitoring_service
from .websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsPoint:
    timestamp: datetime
    load: float
    success_rate: float
    metadata: Dict[str, Any]


@dataclass
class ForecastPoint:
    timestamp: datetime
    load: float
    lower: float
    upper: float
    success_rate: float


@dataclass
class AnomalyRecord:
    timestamp: datetime
    metric: str
    value: float
    threshold: float
    severity: str
    context: Dict[str, Any]


class AnalyticsService:
    """Provides forecasting and anomaly insights for monitoring metrics."""

    def __init__(self):
        self.history: List[AnalyticsPoint] = []
        self.anomalies: List[AnomalyRecord] = []
        self.notification_channels = {
            "websocket": True,
            "email": False,
            "webhook": False,
        }

    def _collect_history(self, hours: int, tenant: Optional[str], server_id: Optional[int], task_type: Optional[str]) -> List[AnalyticsPoint]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        points: List[AnalyticsPoint] = []

        for system_metric in monitoring_service.system_metrics:
            if system_metric.timestamp < cutoff:
                continue

            # Aggregate server success rates for the timestamp
            success_rates = []
            for metrics_list in monitoring_service.server_metrics.values():
                for server_metric in metrics_list:
                    if server_metric.timestamp.date() != system_metric.timestamp.date():
                        continue
                    if server_id and server_metric.server_id != server_id:
                        continue
                    success_rates.append(server_metric.success_rate)

            point = AnalyticsPoint(
                timestamp=system_metric.timestamp,
                load=system_metric.cpu_percent,
                success_rate=mean(success_rates) if success_rates else 1.0,
                metadata={
                    "tenant": tenant or "default",
                    "server_id": server_id,
                    "task_type": task_type,
                },
            )
            points.append(point)

        # Persist a limited history for future requests
        self.history = (self.history + points)[-500:]
        return points

    def _build_forecast(self, points: List[AnalyticsPoint], horizon: int) -> List[ForecastPoint]:
        if not points:
            now = datetime.utcnow()
            return [
                ForecastPoint(
                    timestamp=now + timedelta(hours=idx + 1),
                    load=0.0,
                    lower=0.0,
                    upper=0.0,
                    success_rate=1.0,
                )
                for idx in range(horizon)
            ]

        loads = [p.load for p in points]
        rates = [p.success_rate for p in points]

        load_slope = (loads[-1] - loads[0]) / max(len(loads) - 1, 1)
        rate_slope = (rates[-1] - rates[0]) / max(len(rates) - 1, 1)

        recent_load = loads[-1]
        recent_rate = rates[-1]

        forecast: List[ForecastPoint] = []
        for step in range(1, horizon + 1):
            projected_load = max(0.0, min(100.0, recent_load + load_slope * step))
            projected_rate = max(0.0, min(1.0, recent_rate + rate_slope * step))
            band = max(5.0, stdev(loads) if len(loads) > 1 else 5.0)
            forecast.append(
                ForecastPoint(
                    timestamp=points[-1].timestamp + timedelta(hours=step),
                    load=projected_load,
                    lower=max(0.0, projected_load - band),
                    upper=min(100.0, projected_load + band),
                    success_rate=projected_rate,
                )
            )
        return forecast

    def _detect_anomalies(self, points: List[AnalyticsPoint], sensitivity: float, filters: Dict[str, Any]) -> List[AnomalyRecord]:
        if len(points) < 3:
            return []

        loads = [p.load for p in points]
        rates = [p.success_rate for p in points]

        load_mean = mean(loads)
        load_std = stdev(loads) if len(loads) > 1 else 0
        rate_mean = mean(rates)
        rate_std = stdev(rates) if len(rates) > 1 else 0

        new_anomalies: List[AnomalyRecord] = []
        latest = points[-1]

        if load_std and latest.load > load_mean + sensitivity * load_std:
            new_anomalies.append(
                AnomalyRecord(
                    timestamp=latest.timestamp,
                    metric="cpu_load",
                    value=latest.load,
                    threshold=load_mean + sensitivity * load_std,
                    severity="critical" if latest.load > 90 else "warning",
                    context=filters,
                )
            )

        if rate_std and latest.success_rate < max(0.0, rate_mean - sensitivity * rate_std):
            new_anomalies.append(
                AnomalyRecord(
                    timestamp=latest.timestamp,
                    metric="success_rate",
                    value=latest.success_rate,
                    threshold=max(0.0, rate_mean - sensitivity * rate_std),
                    severity="critical" if latest.success_rate < 0.7 else "warning",
                    context=filters,
                )
            )

        if new_anomalies:
            self.anomalies.extend(new_anomalies)
            self.anomalies = self.anomalies[-200:]
            for anomaly in new_anomalies:
                self._notify(anomaly)
        return new_anomalies

    def _notify(self, anomaly: AnomalyRecord):
        payload = {
            "type": "analytics_alert",
            "metric": anomaly.metric,
            "severity": anomaly.severity,
            "value": anomaly.value,
            "threshold": anomaly.threshold,
            "timestamp": anomaly.timestamp.isoformat(),
            "context": anomaly.context,
        }
        if self.notification_channels.get("websocket"):
            try:
                # Fire and forget; FastAPI will manage event loop
                websocket_manager.enqueue_broadcast(payload)
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Error broadcasting analytics alert", exc_info=exc)

        if self.notification_channels.get("email"):
            logger.info("Email alert would be sent", extra=payload)
        if self.notification_channels.get("webhook"):
            logger.info("Webhook alert would be posted", extra=payload)

    def _build_recommendations(self, points: List[AnalyticsPoint], anomalies: List[AnomalyRecord]) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []
        if not points:
            return recommendations

        avg_load = mean(p.load for p in points)
        avg_success = mean(p.success_rate for p in points)

        if avg_load > 75:
            recommendations.append(
                {
                    "title": "Scale compute",
                    "detail": "Sustained high CPU load detected; consider scaling worker nodes or throttling heavy tasks.",
                    "impact": "high",
                }
            )

        if avg_success < 0.9:
            recommendations.append(
                {
                    "title": "Improve reliability",
                    "detail": "Success rate trending below 90%; review failing servers and retry policies.",
                    "impact": "medium",
                }
            )

        for anomaly in anomalies[-3:]:
            recommendations.append(
                {
                    "title": f"Investigate {anomaly.metric}",
                    "detail": f"Anomaly detected at {anomaly.timestamp.isoformat()} with value {anomaly.value:.2f}.",
                    "impact": anomaly.severity,
                }
            )
        return recommendations

    def forecast(self, hours: int = 24, horizon: int = 6, tenant: Optional[str] = None, server_id: Optional[int] = None, task_type: Optional[str] = None) -> Dict[str, Any]:
        filters = {
            "tenant": tenant,
            "server_id": server_id,
            "task_type": task_type,
        }
        points = self._collect_history(hours, tenant, server_id, task_type)
        forecast_points = self._build_forecast(points, horizon)
        anomalies = self._detect_anomalies(points, sensitivity=2.5, filters=filters)
        recommendations = self._build_recommendations(points, anomalies)

        return {
            "filters": filters,
            "historical": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "load": p.load,
                    "success_rate": p.success_rate,
                    "metadata": p.metadata,
                }
                for p in points
            ],
            "forecast": [asdict(p) for p in forecast_points],
            "anomalies": [asdict(a) for a in anomalies],
            "recommendations": recommendations,
            "summary": {
                "average_load": mean([p.load for p in points]) if points else 0.0,
                "average_success_rate": mean([p.success_rate for p in points]) if points else 1.0,
                "confidence": 0.85 if points else 0.5,
            },
        }

    def get_anomalies(self) -> Dict[str, Any]:
        return {
            "total": len(self.anomalies),
            "anomalies": [
                {
                    **asdict(a),
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in self.anomalies
            ],
        }

    def get_recommendations(self) -> Dict[str, Any]:
        return {"recommendations": self._build_recommendations(self.history, self.anomalies)}


analytics_service = AnalyticsService()

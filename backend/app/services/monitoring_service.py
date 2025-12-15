"""
Monitoring Service
Comprehensive monitoring and logging system for Hisper
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import structlog
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import psutil

from ..models.mcp_server import MCPServer
from ..models.task import Task
from .mcp_client import mcp_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int
    active_tasks: int
    healthy_servers: int
    total_servers: int


@dataclass
class ServerMetrics:
    """MCP Server metrics"""
    server_id: int
    server_name: str
    timestamp: datetime
    status: str
    response_time_ms: Optional[float]
    success_rate: float
    total_requests: int
    failed_requests: int
    last_error: Optional[str]


@dataclass
class TaskMetrics:
    """Task execution metrics"""
    task_id: int
    timestamp: datetime
    status: str
    duration_ms: Optional[float]
    server_id: Optional[int]
    success: bool
    error_message: Optional[str]


class MonitoringService:
    """
    Comprehensive monitoring service for system health, performance, and metrics
    """
    
    def __init__(self):
        # Prometheus metrics
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        
        # In-memory metrics storage
        self.system_metrics: deque = deque(maxlen=1000)
        self.server_metrics: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self.task_metrics: deque = deque(maxlen=1000)
        
        # Counters and statistics
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Alerts
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "server_response_time_ms": 5000.0,
            "server_error_rate": 0.1  # 10%
        }
        
        self.active_alerts = []
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # System metrics
        self.cpu_usage = Gauge(
            'hisper_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'hisper_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'hisper_disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
        
        # Server metrics
        self.server_requests_total = Counter(
            'hisper_server_requests_total',
            'Total server requests',
            ['server_id', 'server_name', 'status'],
            registry=self.registry
        )
        
        self.server_response_time = Histogram(
            'hisper_server_response_time_seconds',
            'Server response time in seconds',
            ['server_id', 'server_name'],
            registry=self.registry
        )
        
        self.active_servers = Gauge(
            'hisper_active_servers',
            'Number of active servers',
            registry=self.registry
        )
        
        self.healthy_servers = Gauge(
            'hisper_healthy_servers',
            'Number of healthy servers',
            registry=self.registry
        )
        
        # Task metrics
        self.task_executions_total = Counter(
            'hisper_task_executions_total',
            'Total task executions',
            ['status', 'priority'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'hisper_task_duration_seconds',
            'Task execution duration in seconds',
            ['status', 'priority'],
            registry=self.registry
        )
        
        self.active_tasks = Gauge(
            'hisper_active_tasks',
            'Number of active tasks',
            registry=self.registry
        )
    
    async def start_monitoring(self):
        """Start the monitoring service"""
        if self.monitoring_active:
            logger.warning("Monitoring service already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")
    
    async def stop_monitoring(self):
        """Stop the monitoring service"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring_active:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect server metrics
                await self._collect_server_metrics()
                
                # Check for alerts
                await self._check_alerts()
                
                # Update Prometheus metrics
                self._update_prometheus_metrics()
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error("Error in monitoring loop", error=str(e))
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Application metrics
            active_connections = len(mcp_client.active_connections)
            
            # Create metrics object
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                active_connections=active_connections,
                active_tasks=0,  # Will be updated by task service
                healthy_servers=0,  # Will be updated by server health checks
                total_servers=0
            )
            
            self.system_metrics.append(metrics)
            
            logger.debug(
                "System metrics collected",
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                active_connections=active_connections
            )
            
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
    
    async def _collect_server_metrics(self):
        """Collect MCP server metrics"""
        try:
            healthy_count = 0
            total_count = len(mcp_client.active_connections)
            
            for server_id in mcp_client.active_connections.keys():
                try:
                    # Perform health check
                    start_time = time.time()
                    health_result = await mcp_client.health_check(server_id)
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    is_healthy = health_result.get("healthy", False)
                    if is_healthy:
                        healthy_count += 1
                    
                    # Get server info (this would come from database in real implementation)
                    server_name = f"server_{server_id}"
                    
                    # Calculate success rate (simplified)
                    total_requests = self.request_counts.get(server_id, 0)
                    failed_requests = self.error_counts.get(server_id, 0)
                    success_rate = (total_requests - failed_requests) / max(total_requests, 1)
                    
                    metrics = ServerMetrics(
                        server_id=server_id,
                        server_name=server_name,
                        timestamp=datetime.utcnow(),
                        status="healthy" if is_healthy else "unhealthy",
                        response_time_ms=response_time_ms,
                        success_rate=success_rate,
                        total_requests=total_requests,
                        failed_requests=failed_requests,
                        last_error=health_result.get("error")
                    )
                    
                    self.server_metrics[server_id].append(metrics)
                    
                except Exception as e:
                    logger.error(f"Error collecting metrics for server {server_id}", error=str(e))
            
            # Update system metrics with server counts
            if self.system_metrics:
                latest_metrics = self.system_metrics[-1]
                latest_metrics.healthy_servers = healthy_count
                latest_metrics.total_servers = total_count
            
        except Exception as e:
            logger.error("Error collecting server metrics", error=str(e))
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            current_alerts = []
            
            if self.system_metrics:
                latest_metrics = self.system_metrics[-1]
                
                # CPU alert
                if latest_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
                    current_alerts.append({
                        "type": "cpu_high",
                        "message": f"High CPU usage: {latest_metrics.cpu_percent:.1f}%",
                        "severity": "warning",
                        "timestamp": datetime.utcnow()
                    })
                
                # Memory alert
                if latest_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
                    current_alerts.append({
                        "type": "memory_high",
                        "message": f"High memory usage: {latest_metrics.memory_percent:.1f}%",
                        "severity": "warning",
                        "timestamp": datetime.utcnow()
                    })
                
                # Disk alert
                if latest_metrics.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
                    current_alerts.append({
                        "type": "disk_high",
                        "message": f"High disk usage: {latest_metrics.disk_usage_percent:.1f}%",
                        "severity": "critical",
                        "timestamp": datetime.utcnow()
                    })
            
            # Server alerts
            for server_id, metrics_list in self.server_metrics.items():
                if metrics_list:
                    latest_server_metrics = metrics_list[-1]
                    
                    # Response time alert
                    if (latest_server_metrics.response_time_ms and 
                        latest_server_metrics.response_time_ms > self.alert_thresholds["server_response_time_ms"]):
                        current_alerts.append({
                            "type": "server_slow",
                            "message": f"Slow server response: {latest_server_metrics.server_name} ({latest_server_metrics.response_time_ms:.0f}ms)",
                            "severity": "warning",
                            "timestamp": datetime.utcnow(),
                            "server_id": server_id
                        })
                    
                    # Error rate alert
                    if latest_server_metrics.success_rate < (1 - self.alert_thresholds["server_error_rate"]):
                        current_alerts.append({
                            "type": "server_errors",
                            "message": f"High error rate: {latest_server_metrics.server_name} ({(1-latest_server_metrics.success_rate)*100:.1f}%)",
                            "severity": "critical",
                            "timestamp": datetime.utcnow(),
                            "server_id": server_id
                        })
            
            # Update active alerts
            self.active_alerts = current_alerts
            
            # Log new alerts
            for alert in current_alerts:
                if alert not in self.active_alerts:
                    logger.warning(
                        "New alert triggered",
                        alert_type=alert["type"],
                        message=alert["message"],
                        severity=alert["severity"]
                    )
            
        except Exception as e:
            logger.error("Error checking alerts", error=str(e))
    
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics with latest data"""
        try:
            if self.system_metrics:
                latest = self.system_metrics[-1]
                self.cpu_usage.set(latest.cpu_percent)
                self.memory_usage.set(latest.memory_percent)
                self.disk_usage.set(latest.disk_usage_percent)
                self.active_servers.set(latest.total_servers)
                self.healthy_servers.set(latest.healthy_servers)
            
        except Exception as e:
            logger.error("Error updating Prometheus metrics", error=str(e))
    
    def record_server_request(self, server_id: int, server_name: str, success: bool, response_time_ms: float):
        """Record a server request for metrics"""
        try:
            self.request_counts[server_id] += 1
            
            if not success:
                self.error_counts[server_id] += 1
            
            # Update response times
            if server_id not in self.response_times:
                self.response_times[server_id] = deque(maxlen=100)
            self.response_times[server_id].append(response_time_ms)
            
            # Update Prometheus metrics
            status = "success" if success else "error"
            self.server_requests_total.labels(
                server_id=str(server_id),
                server_name=server_name,
                status=status
            ).inc()
            
            self.server_response_time.labels(
                server_id=str(server_id),
                server_name=server_name
            ).observe(response_time_ms / 1000.0)
            
            logger.debug(
                "Server request recorded",
                server_id=server_id,
                server_name=server_name,
                success=success,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            logger.error("Error recording server request", error=str(e))
    
    def record_task_execution(self, task_id: int, status: str, priority: str, duration_ms: Optional[float], success: bool, error_message: Optional[str] = None):
        """Record a task execution for metrics"""
        try:
            metrics = TaskMetrics(
                task_id=task_id,
                timestamp=datetime.utcnow(),
                status=status,
                duration_ms=duration_ms,
                server_id=None,
                success=success,
                error_message=error_message
            )
            
            self.task_metrics.append(metrics)
            
            # Update Prometheus metrics
            self.task_executions_total.labels(
                status=status,
                priority=priority
            ).inc()
            
            if duration_ms:
                self.task_duration.labels(
                    status=status,
                    priority=priority
                ).observe(duration_ms / 1000.0)
            
            logger.debug(
                "Task execution recorded",
                task_id=task_id,
                status=status,
                success=success,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error("Error recording task execution", error=str(e))
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            if not self.system_metrics:
                return {"status": "unknown", "message": "No metrics available"}
            
            latest = self.system_metrics[-1]
            
            # Determine overall health
            health_issues = []
            
            if latest.cpu_percent > self.alert_thresholds["cpu_percent"]:
                health_issues.append(f"High CPU usage: {latest.cpu_percent:.1f}%")
            
            if latest.memory_percent > self.alert_thresholds["memory_percent"]:
                health_issues.append(f"High memory usage: {latest.memory_percent:.1f}%")
            
            if latest.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
                health_issues.append(f"High disk usage: {latest.disk_usage_percent:.1f}%")
            
            if health_issues:
                status = "degraded"
                message = "; ".join(health_issues)
            else:
                status = "healthy"
                message = "All systems operational"
            
            return {
                "status": status,
                "message": message,
                "timestamp": latest.timestamp.isoformat(),
                "metrics": asdict(latest),
                "active_alerts": len(self.active_alerts)
            }
            
        except Exception as e:
            logger.error("Error getting system health", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def get_server_health(self, server_id: Optional[int] = None) -> Dict[str, Any]:
        """Get server health status"""
        try:
            if server_id:
                # Get specific server health
                if server_id not in self.server_metrics or not self.server_metrics[server_id]:
                    return {"status": "unknown", "message": "No metrics available"}
                
                latest = self.server_metrics[server_id][-1]
                return {
                    "server_id": server_id,
                    "status": latest.status,
                    "response_time_ms": latest.response_time_ms,
                    "success_rate": latest.success_rate,
                    "total_requests": latest.total_requests,
                    "failed_requests": latest.failed_requests,
                    "last_error": latest.last_error,
                    "timestamp": latest.timestamp.isoformat()
                }
            else:
                # Get all servers health summary
                healthy_servers = 0
                total_servers = len(self.server_metrics)
                server_statuses = {}
                
                for sid, metrics_list in self.server_metrics.items():
                    if metrics_list:
                        latest = metrics_list[-1]
                        server_statuses[sid] = {
                            "status": latest.status,
                            "response_time_ms": latest.response_time_ms,
                            "success_rate": latest.success_rate
                        }
                        if latest.status == "healthy":
                            healthy_servers += 1
                
                return {
                    "total_servers": total_servers,
                    "healthy_servers": healthy_servers,
                    "unhealthy_servers": total_servers - healthy_servers,
                    "servers": server_statuses
                }
                
        except Exception as e:
            logger.error("Error getting server health", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for the specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # System metrics summary
            recent_system_metrics = [
                m for m in self.system_metrics 
                if m.timestamp > cutoff_time
            ]
            
            system_summary = {}
            if recent_system_metrics:
                cpu_values = [m.cpu_percent for m in recent_system_metrics]
                memory_values = [m.memory_percent for m in recent_system_metrics]
                
                system_summary = {
                    "cpu": {
                        "avg": sum(cpu_values) / len(cpu_values),
                        "max": max(cpu_values),
                        "min": min(cpu_values)
                    },
                    "memory": {
                        "avg": sum(memory_values) / len(memory_values),
                        "max": max(memory_values),
                        "min": min(memory_values)
                    }
                }
            
            # Task metrics summary
            recent_task_metrics = [
                m for m in self.task_metrics 
                if m.timestamp > cutoff_time
            ]
            
            task_summary = {
                "total_tasks": len(recent_task_metrics),
                "successful_tasks": sum(1 for m in recent_task_metrics if m.success),
                "failed_tasks": sum(1 for m in recent_task_metrics if not m.success)
            }
            
            if recent_task_metrics:
                durations = [m.duration_ms for m in recent_task_metrics if m.duration_ms]
                if durations:
                    task_summary["avg_duration_ms"] = sum(durations) / len(durations)
                    task_summary["max_duration_ms"] = max(durations)
            
            return {
                "period_hours": hours,
                "system": system_summary,
                "tasks": task_summary,
                "alerts": len(self.active_alerts),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error getting metrics summary", error=str(e))
            return {"error": str(e)}
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error("Error generating Prometheus metrics", error=str(e))
            return ""
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current active alerts"""
        return self.active_alerts.copy()
    
    async def cleanup(self):
        """Cleanup monitoring service"""
        await self.stop_monitoring()
        logger.info("Monitoring service cleanup completed")


# Global monitoring service instance
monitoring_service = MonitoringService()
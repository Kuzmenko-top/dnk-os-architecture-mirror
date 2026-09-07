# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_monitoring_health_check"
# purpose: "Comprehensive Health Check Engine: liveness, readiness, and deep subsystem diagnostics"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

from pydantic import BaseModel, Field

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("dnk.monitoring.health")


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status and diagnostics for an individual system component."""
    name: str
    status: HealthStatus
    response_time_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SystemHealthReport(BaseModel):
    """Aggregated system health report across all probed subsystems."""
    status: HealthStatus
    version: str = "5.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("DNK_ENV", "production"))
    uptime_seconds: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    components: Dict[str, ComponentHealth] = Field(default_factory=dict)
    system_metrics: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckRegistry:
    """Registry and coordinator for system health probes and diagnostic checks."""

    def __init__(self, service_version: str = "5.0.0"):
        self.service_version = service_version
        self._start_time = time.time()
        self._checkers: Dict[str, Callable[[], Awaitable[ComponentHealth]]] = {}
        self._register_default_checkers()

    @property
    def uptime_seconds(self) -> float:
        """Calculates total process uptime in seconds."""
        return round(time.time() - self._start_time, 2)

    def register(self, name: str, checker_fn: Callable[[], Awaitable[ComponentHealth]]) -> None:
        """Register a custom asynchronous component health checker."""
        self._checkers[name] = checker_fn

    def _register_default_checkers(self) -> None:
        """Registers system core checkers: Memory, Disk, Database, Redis."""
        self.register("memory", self._check_memory)
        self.register("disk", self._check_disk)
        self.register("database", self._check_database)
        self.register("redis", self._check_redis)

    async def _check_memory(self) -> ComponentHealth:
        """Probes host/container virtual memory availability."""
        t0 = time.perf_counter()
        details: Dict[str, Any] = {}
        status = HealthStatus.HEALTHY
        err: Optional[str] = None

        if psutil:
            try:
                mem = psutil.virtual_memory()
                details = {
                    "total_mb": round(mem.total / (1024 * 1024), 2),
                    "available_mb": round(mem.available / (1024 * 1024), 2),
                    "percent_used": mem.percent,
                }
                if mem.percent > 95.0:
                    status = HealthStatus.UNHEALTHY
                    err = f"Memory usage critical: {mem.percent}%"
                elif mem.percent > 85.0:
                    status = HealthStatus.DEGRADED
            except Exception as exc:
                status = HealthStatus.DEGRADED
                err = f"Failed to probe memory: {str(exc)}"
        else:
            details = {"info": "psutil not installed"}

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(
            name="memory",
            status=status,
            response_time_ms=elapsed_ms,
            details=details,
            error=err,
        )

    async def _check_disk(self) -> ComponentHealth:
        """Probes host/container storage space."""
        t0 = time.perf_counter()
        details: Dict[str, Any] = {}
        status = HealthStatus.HEALTHY
        err: Optional[str] = None

        if psutil:
            try:
                disk = psutil.disk_usage("/")
                details = {
                    "total_gb": round(disk.total / (1024 ** 3), 2),
                    "free_gb": round(disk.free / (1024 ** 3), 2),
                    "percent_used": disk.percent,
                }
                if disk.percent > 95.0:
                    status = HealthStatus.UNHEALTHY
                    err = f"Disk usage critical: {disk.percent}%"
                elif disk.percent > 88.0:
                    status = HealthStatus.DEGRADED
            except Exception as exc:
                status = HealthStatus.DEGRADED
                err = f"Failed to probe disk: {str(exc)}"
        else:
            details = {"info": "psutil not installed"}

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(
            name="disk",
            status=status,
            response_time_ms=elapsed_ms,
            details=details,
            error=err,
        )

    async def _check_database(self) -> ComponentHealth:
        """Probes primary database and replica pools connectivity."""
        t0 = time.perf_counter()
        status = HealthStatus.HEALTHY
        details: Dict[str, Any] = {}
        err: Optional[str] = None

        try:
            from apps.api.db.database import db_manager
            db_health = await asyncio.wait_for(db_manager.check_health(), timeout=2.0)
            details = db_health
            if not db_health.get("master", {}).get("healthy", False):
                status = HealthStatus.DEGRADED
                err = "Database master reported uninitialized or unhealthy"
        except ImportError:
            details = {"driver": "sqlite/mock", "note": "Database module not available"}
        except asyncio.TimeoutError:
            status = HealthStatus.UNHEALTHY
            err = "Database health check timed out (>2.0s)"
        except Exception as exc:
            # Graceful degrade if DB is not actively running in tests/mock mode
            status = HealthStatus.DEGRADED
            err = f"Database probe warning: {str(exc)}"
            details = {"error": str(exc)}

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(
            name="database",
            status=status,
            response_time_ms=elapsed_ms,
            details=details,
            error=err,
        )

    async def _check_redis(self) -> ComponentHealth:
        """Probes distributed Redis caching / broker cluster."""
        t0 = time.perf_counter()
        status = HealthStatus.HEALTHY
        details: Dict[str, Any] = {}
        err: Optional[str] = None

        try:
            from apps.api.services.redis_client import redis_client
            client = redis_client.get_client()
            if client and hasattr(client, "ping"):
                ping_res = client.ping()
                if asyncio.iscoroutine(ping_res):
                    await asyncio.wait_for(ping_res, timeout=1.5)
                details = {"ping": "pong", "connected": True, "is_cluster": getattr(redis_client, "is_cluster", False)}
            else:
                details = {"connected": False, "note": "Redis client not initialized"}
                status = HealthStatus.DEGRADED
        except ImportError:
            details = {"type": "mock", "note": "Redis client module not loaded"}
        except asyncio.TimeoutError:
            status = HealthStatus.DEGRADED
            err = "Redis ping timed out (>1.5s)"
        except Exception as exc:
            status = HealthStatus.DEGRADED
            err = f"Redis probe notice: {str(exc)}"
            details = {"connected": False, "error": str(exc)}

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        return ComponentHealth(
            name="redis",
            status=status,
            response_time_ms=elapsed_ms,
            details=details,
            error=err,
        )

    async def check_liveness(self) -> Dict[str, Any]:
        """
        Fast Kubernetes liveness probe.
        Checks if the HTTP server process is running and accepting events.
        """
        return {
            "status": "healthy",
            "service": "dnk_os",
            "version": self.service_version,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_readiness(self) -> SystemHealthReport:
        """
        Kubernetes readiness probe.
        Verifies core operational dependencies (database, storage).
        """
        return await self.check_all()

    async def check_all(self) -> SystemHealthReport:
        """Executes all registered health probes concurrently."""
        tasks = {name: checker() for name, checker in self._checkers.items()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        components: Dict[str, ComponentHealth] = {}
        overall_status = HealthStatus.HEALTHY

        for name, res in zip(tasks.keys(), results):
            if isinstance(res, Exception):
                logger.error("Health check '%s' raised exception: %s", name, res)
                comp = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    error=str(res),
                )
            elif isinstance(res, ComponentHealth):
                comp = res
            else:
                comp = ComponentHealth(
                    name=name,
                    status=HealthStatus.HEALTHY,
                )

            components[name] = comp

            # Evaluate system overall status
            if comp.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif comp.status == HealthStatus.DEGRADED and overall_status != HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.DEGRADED

        # Collect host system summary metrics if available
        system_metrics: Dict[str, Any] = {
            "uptime_seconds": self.uptime_seconds,
        }
        if psutil:
            try:
                system_metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
                system_metrics["memory_percent"] = psutil.virtual_memory().percent
            except Exception:
                pass

        return SystemHealthReport(
            status=overall_status,
            version=self.service_version,
            uptime_seconds=self.uptime_seconds,
            components=components,
            system_metrics=system_metrics,
        )


# Global singleton instance
health_registry = HealthCheckRegistry()

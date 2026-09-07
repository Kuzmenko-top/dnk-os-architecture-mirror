# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_multi_region_deployer"
# purpose: "Multi-Region Deployment Engine & Region Health Lifecycle Management (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class MultiRegionDeployer:
    """Manages Multi-Region Cloud Deployments (AWS, GCP, Azure) and region health state."""

    def __init__(self):
        self._regions: Dict[str, Dict[str, Any]] = {}
        self._health_metrics: Dict[str, List[Dict[str, Any]]] = {}

        # Default initial seed regions
        self._seed_default_regions()

    def _seed_default_regions(self):
        default_regions = [
            {
                "id": str(uuid.uuid4()),
                "region_name": "us-east-1",
                "cloud_provider": "aws",
                "is_primary": True,
                "is_active": True,
                "health_check_endpoint": "https://us-east-1.api.dnk.internal/health",
                "failover_priority": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "region_name": "eu-west-1",
                "cloud_provider": "aws",
                "is_primary": False,
                "is_active": True,
                "health_check_endpoint": "https://eu-west-1.api.dnk.internal/health",
                "failover_priority": 2,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "region_name": "ap-southeast-1",
                "cloud_provider": "aws",
                "is_primary": False,
                "is_active": True,
                "health_check_endpoint": "https://ap-southeast-1.api.dnk.internal/health",
                "failover_priority": 3,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "region_name": "us-central1",
                "cloud_provider": "gcp",
                "is_primary": False,
                "is_active": True,
                "health_check_endpoint": "https://us-central1.gcp.dnk.internal/health",
                "failover_priority": 4,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "region_name": "europe-west1",
                "cloud_provider": "gcp",
                "is_primary": False,
                "is_active": True,
                "health_check_endpoint": "https://europe-west1.gcp.dnk.internal/health",
                "failover_priority": 5,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        for r in default_regions:
            self._regions[r["region_name"]] = r
            self._health_metrics[r["region_name"]] = []

    def list_regions(self, active_only: bool = False) -> List[Dict[str, Any]]:
        regions = list(self._regions.values())
        if active_only:
            regions = [r for r in regions if r.get("is_active")]
        return sorted(regions, key=lambda x: x.get("failover_priority", 0))

    def get_region(self, region_name: str) -> Optional[Dict[str, Any]]:
        return self._regions.get(region_name)

    def register_region(
        self,
        region_name: str,
        cloud_provider: str,
        health_check_endpoint: str,
        is_primary: bool = False,
        is_active: bool = True,
        failover_priority: int = 0,
    ) -> Dict[str, Any]:
        if is_primary:
            for r in self._regions.values():
                r["is_primary"] = False

        record = {
            "id": str(uuid.uuid4()),
            "region_name": region_name,
            "cloud_provider": cloud_provider,
            "is_primary": is_primary,
            "is_active": is_active,
            "health_check_endpoint": health_check_endpoint,
            "failover_priority": failover_priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._regions[region_name] = record
        if region_name not in self._health_metrics:
            self._health_metrics[region_name] = []
        return record

    def update_region(self, region_name: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        region = self._regions.get(region_name)
        if not region:
            return None

        if updates.get("is_primary"):
            for r in self._regions.values():
                r["is_primary"] = False

        for k, v in updates.items():
            if k in region and k != "id" and k != "region_name":
                region[k] = v
        region["updated_at"] = datetime.now(timezone.utc).isoformat()
        return region

    def delete_region(self, region_name: str) -> bool:
        if region_name in self._regions:
            del self._regions[region_name]
            self._health_metrics.pop(region_name, None)
            return True
        return False

    def record_health_metric(
        self,
        region_name: str,
        latency_p50_ms: int,
        latency_p95_ms: int,
        latency_p99_ms: int,
        error_rate: float,
        request_count: int,
    ) -> Dict[str, Any]:
        # Health score formula: (1 - error_rate) * max(0.0, 1.0 - (p95_ms / 1000.0))
        error_factor = max(0.0, min(1.0, 1.0 - float(error_rate)))
        latency_factor = max(0.0, min(1.0, 1.0 - (float(latency_p95_ms) / 1000.0)))
        health_score = round(error_factor * latency_factor, 4)

        metric = {
            "id": str(uuid.uuid4()),
            "region_name": region_name,
            "metric_time": datetime.now(timezone.utc).isoformat(),
            "latency_p50_ms": latency_p50_ms,
            "latency_p95_ms": latency_p95_ms,
            "latency_p99_ms": latency_p99_ms,
            "error_rate": float(error_rate),
            "request_count": request_count,
            "health_score": health_score,
        }
        if region_name not in self._health_metrics:
            self._health_metrics[region_name] = []
        self._health_metrics[region_name].append(metric)

        # Keep last 100 metrics
        if len(self._health_metrics[region_name]) > 100:
            self._health_metrics[region_name] = self._health_metrics[region_name][-100:]

        return metric

    def get_latest_health_metric(self, region_name: str) -> Optional[Dict[str, Any]]:
        metrics = self._health_metrics.get(region_name, [])
        if metrics:
            return metrics[-1]
        return None

    def trigger_liveness_check(self, region_name: str) -> Dict[str, Any]:
        region = self._regions.get(region_name)
        if not region:
            return {"healthy": False, "status": "not_found", "health_score": 0.0}

        # Simulated ping check
        is_active = region.get("is_active", True)
        if not is_active:
            return {"healthy": False, "status": "inactive", "health_score": 0.0}

        # Record healthy liveness metric
        metric = self.record_health_metric(
            region_name=region_name,
            latency_p50_ms=25,
            latency_p95_ms=45,
            latency_p99_ms=90,
            error_rate=0.001,
            request_count=1500,
        )

        return {
            "healthy": True,
            "status": "healthy",
            "region_name": region_name,
            "health_score": metric["health_score"],
            "metric": metric,
        }

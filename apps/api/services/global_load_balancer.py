# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_global_load_balancer"
# purpose: "Global Server Load Balancer (GSLB) Routing Engine & Failover Handler (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from apps.api.services.multi_region_deployer import MultiRegionDeployer


class GlobalLoadBalancer:
    """Calculates global DNS routing targets and manages failover policies across regions."""

    def __init__(self, deployer: Optional[MultiRegionDeployer] = None):
        self.deployer = deployer or MultiRegionDeployer()
        self._gslb_config = {
            "id": str(uuid.uuid4()),
            "dns_provider": "route53",  # 'route53', 'cloud_dns', 'cloudflare'
            "routing_policy": "latency",  # 'geolocation', 'latency', 'weighted', 'failover'
            "health_check_interval_seconds": 30,
            "failover_threshold": 3,
            "ttl_seconds": 60,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_config(self) -> Dict[str, Any]:
        return self._gslb_config

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in updates.items():
            if k in self._gslb_config and k != "id":
                self._gslb_config[k] = v
        self._gslb_config["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._gslb_config

    def calculate_routing_target(
        self,
        client_country: Optional[str] = None,
        client_continent: Optional[str] = None,
        client_latencies: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Calculates optimal target region according to active routing policy and health status."""
        active_regions = self.deployer.list_regions(active_only=True)
        if not active_regions:
            return {
                "status": "error",
                "message": "No active regions available",
                "target_region": None,
                "routing_policy": self._gslb_config["routing_policy"],
            }

        # Enrich with latest health metrics
        healthy_regions = []
        for r in active_regions:
            r_name = r["region_name"]
            metric = self.deployer.get_latest_health_metric(r_name)
            health_score = metric["health_score"] if metric else 1.0
            p95_latency = metric["latency_p95_ms"] if metric else 50
            if health_score >= 0.3:  # Only route to healthy regions
                healthy_regions.append({
                    "region": r,
                    "health_score": health_score,
                    "p95_latency": p95_latency,
                })

        if not healthy_regions:
            # Fallback to primary region if all health scores low
            primary = next((r for r in active_regions if r.get("is_primary")), active_regions[0])
            return {
                "status": "failover_fallback",
                "target_region": primary["region_name"],
                "reason": "All regions failed health checks; routing to primary fallback",
                "routing_policy": self._gslb_config["routing_policy"],
            }

        policy = self._gslb_config["routing_policy"]

        if policy == "failover":
            # Primary first, then by failover_priority
            sorted_by_priority = sorted(healthy_regions, key=lambda x: (not x["region"].get("is_primary"), x["region"].get("failover_priority", 0)))
            target = sorted_by_priority[0]["region"]["region_name"]
            return {
                "status": "ok",
                "target_region": target,
                "routing_policy": "failover",
                "healthy_region_count": len(healthy_regions),
            }

        elif policy == "geolocation":
            # Geolocation matching
            country = (client_country or "").upper()
            continent = (client_continent or "").upper()

            if continent in ["NA", "AMER"] or country in ["US", "CA", "MX"]:
                preferred = "us-east-1"
            elif continent in ["EU"] or country in ["UK", "DE", "FR", "UA"]:
                preferred = "eu-west-1"
            elif continent in ["AS", "OC"] or country in ["SG", "JP", "AU"]:
                preferred = "ap-southeast-1"
            else:
                preferred = "us-east-1"

            target_region = next((item["region"]["region_name"] for item in healthy_regions if item["region"]["region_name"] == preferred), healthy_regions[0]["region"]["region_name"])
            return {
                "status": "ok",
                "target_region": target_region,
                "routing_policy": "geolocation",
                "geo_matched": preferred,
            }

        elif policy == "weighted":
            # Weighted distribution based on failover_priority inverse or equal
            sorted_weighted = sorted(healthy_regions, key=lambda x: (-x["health_score"], x["p95_latency"]))
            target = sorted_weighted[0]["region"]["region_name"]
            return {
                "status": "ok",
                "target_region": target,
                "routing_policy": "weighted",
                "healthy_region_count": len(healthy_regions),
            }

        else:  # Default 'latency'
            if client_latencies:
                # Find healthy region with minimum client-reported latency
                sorted_by_client = sorted(healthy_regions, key=lambda x: client_latencies.get(x["region"]["region_name"], 9999))
                target = sorted_by_client[0]["region"]["region_name"]
            else:
                # Internal p95 latency
                sorted_by_p95 = sorted(healthy_regions, key=lambda x: x["p95_latency"])
                target = sorted_by_p95[0]["region"]["region_name"]

            return {
                "status": "ok",
                "target_region": target,
                "routing_policy": "latency",
                "healthy_region_count": len(healthy_regions),
            }

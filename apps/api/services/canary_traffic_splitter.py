# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canary_traffic_splitter"
# purpose: "Dynamic Traffic Splitting & Ingress Manifest Generator for Blue/Green & Canary (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import hashlib
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TrafficRoutingDecision(BaseModel):
    selected_target: str  # 'blue', 'green', 'canary'
    target_service: str
    target_percentage: int
    is_canary: bool
    hash_bucket: int
    routing_reason: str
    headers: Dict[str, str] = Field(default_factory=dict)


class CanaryTrafficSplitter:
    """
    High-performance, deterministic traffic splitting engine for Blue/Green & Canary rollouts.
    Provides consistent client hashing, header overrides, and ingress config generation
    (Nginx Ingress, Istio VirtualService, Custom Ingress).
    """

    def __init__(
        self,
        blue_service_name: str,
        green_service_name: str,
        canary_percentage: int = 0,
        active_environment: str = "blue",
        canary_enabled: bool = False,
    ) -> None:
        self.blue_service_name = blue_service_name
        self.green_service_name = green_service_name
        self.canary_percentage = max(0, min(100, canary_percentage))
        self.active_environment = active_environment if active_environment in ("blue", "green") else "blue"
        self.canary_enabled = canary_enabled

    def calculate_hash_bucket(self, identifier: str) -> int:
        """
        Deterministically maps an identifier (IP, user ID, session ID) to a bucket [0, 99].
        Uses SHA-256 for uniform hash distribution.
        """
        if not identifier:
            return 0
        digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
        # Take first 8 hex characters and modulo 100
        return int(digest[:8], 16) % 100

    def route_request(
        self,
        client_identifier: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> TrafficRoutingDecision:
        """
        Evaluates incoming request against canary weight, header overrides, and sticky identifiers.
        """
        headers = headers or {}
        cookies = cookies or {}

        # 1. Check explicit header override
        canary_header = headers.get("X-Canary", "").strip().lower()
        if canary_header == "always" or canary_header == "true":
            target_env = "green" if self.active_environment == "blue" else "blue"
            target_svc = self.green_service_name if target_env == "green" else self.blue_service_name
            return TrafficRoutingDecision(
                selected_target=target_env,
                target_service=target_svc,
                target_percentage=100,
                is_canary=True,
                hash_bucket=0,
                routing_reason="header_override_always",
                headers={"X-DNK-Target-Environment": target_env, "X-DNK-Canary": "true"},
            )
        elif canary_header == "never" or canary_header == "false":
            target_env = self.active_environment
            target_svc = self.blue_service_name if target_env == "blue" else self.green_service_name
            return TrafficRoutingDecision(
                selected_target=target_env,
                target_service=target_svc,
                target_percentage=0,
                is_canary=False,
                hash_bucket=0,
                routing_reason="header_override_never",
                headers={"X-DNK-Target-Environment": target_env, "X-DNK-Canary": "false"},
            )

        # 2. Check canary enabled and weight
        if not self.canary_enabled or self.canary_percentage <= 0:
            target_env = self.active_environment
            target_svc = self.blue_service_name if target_env == "blue" else self.green_service_name
            return TrafficRoutingDecision(
                selected_target=target_env,
                target_service=target_svc,
                target_percentage=0,
                is_canary=False,
                hash_bucket=0,
                routing_reason="canary_disabled_or_zero_weight",
                headers={"X-DNK-Target-Environment": target_env, "X-DNK-Canary": "false"},
            )

        if self.canary_percentage >= 100:
            target_env = "green" if self.active_environment == "blue" else "blue"
            target_svc = self.green_service_name if target_env == "green" else self.blue_service_name
            return TrafficRoutingDecision(
                selected_target=target_env,
                target_service=target_svc,
                target_percentage=100,
                is_canary=True,
                hash_bucket=0,
                routing_reason="canary_100_percent",
                headers={"X-DNK-Target-Environment": target_env, "X-DNK-Canary": "true"},
            )

        # 3. Deterministic hashing for sticky percentage distribution
        ident = (
            client_identifier
            or cookies.get("dnk_session_id")
            or headers.get("X-User-ID")
            or headers.get("X-Forwarded-For", "default-client")
        )
        bucket = self.calculate_hash_bucket(ident)

        if bucket < self.canary_percentage:
            # Route to candidate / canary environment
            target_env = "green" if self.active_environment == "blue" else "blue"
            target_svc = self.green_service_name if target_env == "green" else self.blue_service_name
            is_canary = True
            reason = f"hash_bucket_{bucket}_in_canary_range_{self.canary_percentage}"
        else:
            # Route to baseline active environment
            target_env = self.active_environment
            target_svc = self.blue_service_name if target_env == "blue" else self.green_service_name
            is_canary = False
            reason = f"hash_bucket_{bucket}_in_baseline_range_{100 - self.canary_percentage}"

        return TrafficRoutingDecision(
            selected_target=target_env,
            target_service=target_svc,
            target_percentage=self.canary_percentage,
            is_canary=is_canary,
            hash_bucket=bucket,
            routing_reason=reason,
            headers={
                "X-DNK-Target-Environment": target_env,
                "X-DNK-Canary": "true" if is_canary else "false",
                "X-DNK-Hash-Bucket": str(bucket),
            },
        )

    def generate_nginx_ingress_annotations(
        self,
        ingress_name: str,
        service_port: int = 8000,
    ) -> Dict[str, Any]:
        """
        Generates Kubernetes Ingress manifest annotations for Nginx Ingress Canary.
        """
        candidate_env = "green" if self.active_environment == "blue" else "blue"
        candidate_service = self.green_service_name if candidate_env == "green" else self.blue_service_name
        baseline_service = self.blue_service_name if self.active_environment == "blue" else self.green_service_name

        annotations: Dict[str, str] = {
            "kubernetes.io/ingress.class": "nginx",
        }

        canary_manifest: Dict[str, Any] = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{ingress_name}-canary",
                "annotations": {
                    "nginx.ingress.kubernetes.io/canary": "true" if self.canary_enabled else "false",
                    "nginx.ingress.kubernetes.io/canary-weight": str(self.canary_percentage if self.canary_enabled else 0),
                    "nginx.ingress.kubernetes.io/canary-by-header": "X-Canary",
                    "nginx.ingress.kubernetes.io/canary-by-header-value": "always",
                },
            },
            "spec": {
                "rules": [
                    {
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": candidate_service if self.canary_enabled else baseline_service,
                                            "port": {"number": service_port},
                                        }
                                    },
                                }
                            ]
                        }
                    }
                ]
            },
        }

        return canary_manifest

    def generate_istio_virtual_service(
        self,
        host: str,
        virtual_service_name: str,
        service_port: int = 8000,
    ) -> Dict[str, Any]:
        """
        Generates Istio VirtualService configuration with weighted routing for Blue/Green/Canary.
        """
        active_weight = 100 - self.canary_percentage if self.canary_enabled else 100
        canary_weight = self.canary_percentage if self.canary_enabled else 0

        routes: List[Dict[str, Any]] = [
            {
                "destination": {
                    "host": self.blue_service_name if self.active_environment == "blue" else self.green_service_name,
                    "subset": self.active_environment,
                    "port": {"number": service_port},
                },
                "weight": active_weight,
            }
        ]

        if self.canary_enabled and canary_weight > 0:
            candidate_env = "green" if self.active_environment == "blue" else "blue"
            candidate_service = self.green_service_name if candidate_env == "green" else self.blue_service_name
            routes.append(
                {
                    "destination": {
                        "host": candidate_service,
                        "subset": candidate_env,
                        "port": {"number": service_port},
                    },
                    "weight": canary_weight,
                }
            )

        return {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "VirtualService",
            "metadata": {
                "name": virtual_service_name,
            },
            "spec": {
                "hosts": [host],
                "http": [
                    {
                        "match": [{"headers": {"X-Canary": {"exact": "always"}}}],
                        "route": [
                            {
                                "destination": {
                                    "host": self.green_service_name if self.active_environment == "blue" else self.blue_service_name,
                                    "subset": "green" if self.active_environment == "blue" else "blue",
                                    "port": {"number": service_port},
                                },
                                "weight": 100,
                            }
                        ],
                    },
                    {
                        "route": routes,
                    },
                ],
            },
        }

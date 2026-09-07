# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_global_load_balancer"
# purpose: "Unit tests for GSLB Routing Policies: Latency, Geolocation, Weighted & Failover (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.multi_region_deployer import MultiRegionDeployer
from apps.api.services.global_load_balancer import GlobalLoadBalancer


def test_gslb_config_update():
    deployer = MultiRegionDeployer()
    gslb = GlobalLoadBalancer(deployer=deployer)
    cfg = gslb.get_config()
    assert cfg["dns_provider"] == "route53"

    updated = gslb.update_config({"routing_policy": "geolocation", "ttl_seconds": 30})
    assert updated["routing_policy"] == "geolocation"
    assert updated["ttl_seconds"] == 30


def test_gslb_routing_latency_policy():
    deployer = MultiRegionDeployer()
    gslb = GlobalLoadBalancer(deployer=deployer)
    gslb.update_config({"routing_policy": "latency"})

    # Record metrics: ap-southeast-1 has lowest p95 latency
    deployer.record_health_metric("us-east-1", 30, 80, 150, 0.0, 1000)
    deployer.record_health_metric("eu-west-1", 20, 60, 100, 0.0, 1000)
    deployer.record_health_metric("ap-southeast-1", 10, 25, 50, 0.0, 1000)

    route = gslb.calculate_routing_target()
    assert route["status"] == "ok"
    assert route["target_region"] == "ap-southeast-1"
    assert route["routing_policy"] == "latency"


def test_gslb_routing_geolocation_policy():
    deployer = MultiRegionDeployer()
    gslb = GlobalLoadBalancer(deployer=deployer)
    gslb.update_config({"routing_policy": "geolocation"})

    # European user client -> eu-west-1
    route_eu = gslb.calculate_routing_target(client_country="DE", client_continent="EU")
    assert route_eu["target_region"] == "eu-west-1"

    # Asian user client -> ap-southeast-1
    route_asia = gslb.calculate_routing_target(client_country="SG", client_continent="AS")
    assert route_asia["target_region"] == "ap-southeast-1"


def test_gslb_routing_failover_policy():
    deployer = MultiRegionDeployer()
    gslb = GlobalLoadBalancer(deployer=deployer)
    gslb.update_config({"routing_policy": "failover"})

    # Primary us-east-1 is active
    route = gslb.calculate_routing_target()
    assert route["target_region"] == "us-east-1"

    # Deactivate us-east-1 => failover to next active region by priority
    deployer.update_region("us-east-1", {"is_active": False})
    failover_route = gslb.calculate_routing_target()
    assert failover_route["target_region"] != "us-east-1"
    assert failover_route["status"] == "ok"

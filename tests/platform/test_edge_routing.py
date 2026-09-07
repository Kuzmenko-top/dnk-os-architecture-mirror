# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_edge_routing"
# purpose: "Unit tests for Edge Routing Rules, Propagation & Worker Script Generation (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.edge_routing_manager import EdgeRoutingManager


def test_edge_rule_creation_and_matching():
    edge = EdgeRoutingManager()
    rule = edge.create_rule(
        rule_name="EU Traffic Rule",
        geo_match_type="continent",
        geo_values=["EU"],
        target_region="eu-west-1",
        priority=10,
        enabled=True,
    )
    assert rule["rule_name"] == "EU Traffic Rule"
    assert rule["id"] is not None

    match = edge.match_rule(country="DE", continent="EU")
    assert match is not None
    assert match["target_region"] == "eu-west-1"


def test_edge_rule_priority_ordering():
    edge = EdgeRoutingManager()
    edge.create_rule("General NA Rule", "continent", ["NA"], "us-east-1", priority=1)
    edge.create_rule("Specific US Rule", "country", ["US"], "us-central1", priority=100)

    # US request should match highest priority rule (priority=100 => us-central1)
    match_us = edge.match_rule(country="US", continent="NA")
    assert match_us is not None
    assert match_us["target_region"] == "us-central1"

    # CA request should match general NA rule
    match_ca = edge.match_rule(country="CA", continent="NA")
    assert match_ca is not None
    assert match_ca["target_region"] == "us-east-1"


def test_cloudflare_worker_script_generation():
    edge = EdgeRoutingManager()
    edge.create_rule("APAC Rule", "continent", ["AS"], "ap-southeast-1", priority=10)
    worker_js = edge.generate_cloudflare_worker_script()
    assert "addEventListener('fetch'" in worker_js
    assert "ap-southeast-1" in worker_js
    assert "CF-IPCountry" in worker_js

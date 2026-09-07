# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_canary_traffic_splitter"
# purpose: "Unit & Integration Tests for Dynamic Canary Traffic Splitting (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.canary_traffic_splitter import (
    CanaryTrafficSplitter,
    TrafficRoutingDecision,
)


def test_traffic_splitter_disabled_or_zero_weight():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=0,
        active_environment="blue",
        canary_enabled=False,
    )
    decision = splitter.route_request(client_identifier="user-123")
    assert decision.selected_target == "blue"
    assert decision.target_service == "dnk-api-blue"
    assert decision.is_canary is False
    assert decision.routing_reason == "canary_disabled_or_zero_weight"


def test_traffic_splitter_header_override_always_and_never():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=10,
        active_environment="blue",
        canary_enabled=True,
    )

    # Always override
    decision_always = splitter.route_request(
        client_identifier="user-baseline-hash",
        headers={"X-Canary": "always"},
    )
    assert decision_always.selected_target == "green"
    assert decision_always.is_canary is True
    assert decision_always.routing_reason == "header_override_always"

    # Never override
    decision_never = splitter.route_request(
        client_identifier="user-canary-hash",
        headers={"X-Canary": "never"},
    )
    assert decision_never.selected_target == "blue"
    assert decision_never.is_canary is False
    assert decision_never.routing_reason == "header_override_never"


def test_traffic_splitter_100_percent():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=100,
        active_environment="blue",
        canary_enabled=True,
    )
    decision = splitter.route_request(client_identifier="any-user")
    assert decision.selected_target == "green"
    assert decision.is_canary is True
    assert decision.routing_reason == "canary_100_percent"


def test_traffic_splitter_deterministic_hash_distribution():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=25,
        active_environment="blue",
        canary_enabled=True,
    )

    canary_count = 0
    total_clients = 1000

    for i in range(total_clients):
        client_id = f"client-id-{i}"
        # Test stickiness: repeat route for same client
        d1 = splitter.route_request(client_identifier=client_id)
        d2 = splitter.route_request(client_identifier=client_id)
        assert d1.selected_target == d2.selected_target
        assert d1.hash_bucket == d2.hash_bucket

        if d1.is_canary:
            canary_count += 1

    # In uniform SHA-256 distribution over 1000 samples, 25% should be between 20% and 30%
    observed_percentage = (canary_count / total_clients) * 100
    assert 20.0 <= observed_percentage <= 30.0


def test_nginx_ingress_annotations_generation():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=15,
        active_environment="blue",
        canary_enabled=True,
    )

    manifest = splitter.generate_nginx_ingress_annotations(
        ingress_name="dnk-api-ingress",
        service_port=8000,
    )
    assert manifest["apiVersion"] == "networking.k8s.io/v1"
    assert manifest["metadata"]["name"] == "dnk-api-ingress-canary"
    assert manifest["metadata"]["annotations"]["nginx.ingress.kubernetes.io/canary"] == "true"
    assert manifest["metadata"]["annotations"]["nginx.ingress.kubernetes.io/canary-weight"] == "15"
    assert manifest["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"] == "dnk-api-green"


def test_istio_virtual_service_generation():
    splitter = CanaryTrafficSplitter(
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        canary_percentage=30,
        active_environment="blue",
        canary_enabled=True,
    )

    vs = splitter.generate_istio_virtual_service(
        host="api.dnk-e.com",
        virtual_service_name="dnk-api-vs",
        service_port=8000,
    )
    assert vs["apiVersion"] == "networking.istio.io/v1alpha3"
    assert vs["metadata"]["name"] == "dnk-api-vs"
    http_routes = vs["spec"]["http"]
    weighted_route = http_routes[1]["route"]
    assert len(weighted_route) == 2
    assert weighted_route[0]["weight"] == 70  # blue
    assert weighted_route[1]["weight"] == 30  # green

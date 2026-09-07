# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_multi_region_deployment"
# purpose: "Unit and Integration tests for Multi-Region Deployer, Region CRUD, Liveness & Health Scoring (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.multi_region_deployer import MultiRegionDeployer
from apps.api.db.models.platform_region import PlatformRegionModel
from apps.api.db.models.platform_region_health_metric import PlatformRegionHealthMetricModel


def test_seed_regions_initialization():
    deployer = MultiRegionDeployer()
    regions = deployer.list_regions()
    assert len(regions) >= 5
    region_names = [r["region_name"] for r in regions]
    assert "us-east-1" in region_names
    assert "eu-west-1" in region_names
    assert "ap-southeast-1" in region_names
    assert "us-central1" in region_names
    assert "europe-west1" in region_names


def test_register_new_region():
    deployer = MultiRegionDeployer()
    new_reg = deployer.register_region(
        region_name="sa-east-1",
        cloud_provider="aws",
        health_check_endpoint="https://sa-east-1.api.dnk.internal/health",
        is_primary=False,
        is_active=True,
        failover_priority=10,
    )
    assert new_reg["region_name"] == "sa-east-1"
    assert deployer.get_region("sa-east-1") is not None
    assert len(deployer.list_regions()) == 6


def test_primary_region_uniqueness():
    deployer = MultiRegionDeployer()
    # Setting new region as primary should unset prior primary
    deployer.register_region(
        region_name="eu-west-1-new-primary",
        cloud_provider="aws",
        health_check_endpoint="https://eu.api.dnk.internal/health",
        is_primary=True,
    )
    primary_regions = [r for r in deployer.list_regions() if r["is_primary"]]
    assert len(primary_regions) == 1
    assert primary_regions[0]["region_name"] == "eu-west-1-new-primary"


def test_health_score_calculation():
    deployer = MultiRegionDeployer()
    # 0% error rate, 50ms p95 latency => health_score = 1.0 * (1 - 0.05) = 0.95
    metric = deployer.record_health_metric(
        region_name="us-east-1",
        latency_p50_ms=20,
        latency_p95_ms=50,
        latency_p99_ms=100,
        error_rate=0.0,
        request_count=1000,
    )
    assert metric["health_score"] == 0.95
    latest = deployer.get_latest_health_metric("us-east-1")
    assert latest is not None
    assert latest["health_score"] == 0.95


def test_trigger_liveness_check():
    deployer = MultiRegionDeployer()
    res = deployer.trigger_liveness_check("us-east-1")
    assert res["healthy"] is True
    assert res["status"] == "healthy"
    assert res["health_score"] > 0.9

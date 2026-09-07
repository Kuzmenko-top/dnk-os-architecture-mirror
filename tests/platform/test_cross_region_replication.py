# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_cross_region_replication"
# purpose: "Unit tests for Cross-Region Database & Cache Replication & Lag Health Tracking (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.cross_region_replication import CrossRegionReplicationManager


def test_seed_replication_streams():
    mgr = CrossRegionReplicationManager()
    streams = mgr.list_streams()
    assert len(streams) >= 4
    source_regions = [s["source_region"] for s in streams]
    assert "us-east-1" in source_regions


def test_record_replication_lag():
    mgr = CrossRegionReplicationManager()
    # Create or update stream with lag=2s (healthy)
    updated = mgr.record_lag("us-east-1", "eu-west-1", lag_seconds=2)
    assert updated["lag_seconds"] == 2
    assert updated["status"] == "healthy"

    # Update with lag=45s (lagging)
    updated_lagging = mgr.record_lag("us-east-1", "eu-west-1", lag_seconds=45)
    assert updated_lagging["status"] == "lagging"

    # Update with lag=120s (broken)
    updated_broken = mgr.record_lag("us-east-1", "eu-west-1", lag_seconds=120)
    assert updated_broken["status"] == "broken"


def test_aggregate_replication_metrics():
    mgr = CrossRegionReplicationManager()
    mgr.record_lag("us-east-1", "eu-west-1", lag_seconds=1)
    mgr.record_lag("us-east-1", "ap-southeast-1", lag_seconds=3)

    metrics = mgr.get_aggregate_replication_lag()
    assert metrics["total_streams"] >= 4
    assert "max_lag_seconds" in metrics
    assert "avg_lag_seconds" in metrics
    assert metrics["overall_status"] in ["healthy", "lagging", "broken"]

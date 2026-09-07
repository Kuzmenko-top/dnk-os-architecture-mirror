# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-HEALTH-001-INCIDENT-ENGINE-PHASE2"
# purpose: "Unit tests for HealthMetricAggregator & IncidentDetectionEngine (DNK-HEALTH-001 Phase 2)"
# canonical_source: true
# alters_files: ["tests/health/test_incident_detection_engine.py"]
# triggers_tasks: ["DNK-HEALTH-001-PHASE2"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.db.models import HealthMetricRule
from apps.api.services.health_metric_aggregator import HealthMetricAggregator
from apps.api.services.incident_detection_engine import IncidentDetectionEngine


def test_metric_aggregator_statistical_computations():
    agg = HealthMetricAggregator(max_samples_per_series=50)
    ws = "ws-prod"
    svc = "dnk_api_gateway"
    metric = "cpu_usage_pct"

    # Feed 10 values: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
    for v in [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]:
        agg.record_metric(ws, svc, metric, v)

    stats = agg.compute_statistics(ws, svc, metric)
    assert stats["count"] == 10.0
    assert stats["mean"] == 55.0
    assert stats["min"] == 10.0
    assert stats["max"] == 100.0
    assert stats["latest"] == 100.0
    assert stats["p95"] == 100.0
    assert stats["stddev"] > 0.0

    # Service snapshot generation
    snapshot = agg.generate_service_snapshot(ws, svc, active_incidents_count=0.0)
    assert snapshot.service_name == svc
    assert snapshot.status == "HEALTHY"
    assert snapshot.cpu_usage_pct == 100.0


def test_incident_engine_rule_registration_and_evaluation():
    agg = HealthMetricAggregator()
    engine = IncidentDetectionEngine(aggregator=agg)
    ws = "ws-prod"
    svc = "dnk_database"
    metric = "p95_latency_ms"

    rule = HealthMetricRule(
        workspace_id=ws,
        service_name=svc,
        metric_name=metric,
        comparator=">",
        warning_threshold=200.0,
        critical_threshold=500.0,
        consecutive_breaches_required=2,
        evaluation_window_seconds=60,
    )
    rule_id = engine.register_rule(rule)
    assert rule_id is not None
    assert len(engine.list_rules(ws)) == 1

    # First breach (warning): should not trigger incident yet because consecutive_breaches_required=2
    incidents = engine.evaluate_metric(ws, svc, metric, 250.0)
    assert len(incidents) == 0

    # Second breach (warning): should trigger WARNING incident
    incidents = engine.evaluate_metric(ws, svc, metric, 260.0)
    assert len(incidents) == 1
    assert incidents[0].severity == "WARNING"
    assert incidents[0].status == "OPEN"
    assert incidents[0].observed_value == 260.0

    # Third breach (critical): should trigger CRITICAL incident
    incidents = engine.evaluate_metric(ws, svc, metric, 600.0)
    assert len(incidents) == 1
    assert incidents[0].severity == "CRITICAL"


def test_incident_engine_statistical_anomaly_detection():
    agg = HealthMetricAggregator()
    engine = IncidentDetectionEngine(aggregator=agg)
    ws = "ws-prod"
    svc = "dnk_worker"
    metric = "jobs_processed_per_sec"

    # Feed normal values around 100
    for _ in range(20):
        agg.record_metric(ws, svc, metric, 100.0)

    # Anomaly check before outlier
    anomaly = engine.detect_statistical_anomaly(ws, svc, metric, z_threshold=3.0)
    assert anomaly is None

    # Inject slight variance, then outlier
    for v in [98.0, 102.0, 99.0, 101.0, 100.0]:
        agg.record_metric(ws, svc, metric, v)

    # Extreme outlier (500.0)
    agg.record_metric(ws, svc, metric, 500.0)
    anomaly = engine.detect_statistical_anomaly(ws, svc, metric, z_threshold=2.0)
    assert anomaly is not None
    assert anomaly["is_anomaly"] is True
    assert anomaly["z_score"] >= 2.0


def test_incident_resolution_and_cleanup():
    agg = HealthMetricAggregator()
    engine = IncidentDetectionEngine(aggregator=agg)
    ws = "ws-prod"
    svc = "dnk_cache"
    metric = "memory_usage_pct"

    rule = HealthMetricRule(
        workspace_id=ws,
        service_name=svc,
        metric_name=metric,
        comparator=">",
        warning_threshold=80.0,
        critical_threshold=95.0,
        consecutive_breaches_required=1,
    )
    engine.register_rule(rule)

    incidents = engine.evaluate_metric(ws, svc, metric, 96.0)
    assert len(incidents) == 1
    inc_id = incidents[0].to_dict()["id"]
    assert len(engine.get_active_incidents(ws)) == 1

    resolved = engine.resolve_incident(inc_id)
    assert resolved is not None
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None
    assert len(engine.get_active_incidents(ws)) == 0

# --- DNK-MRH-HEADER ---
# mrh_id: "tests_worker_test_queue_telemetry"
# purpose: "Unit Tests for Queue Telemetry Metrics Collector (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.queue_telemetry_service import QueueTelemetryService


def test_calculate_p95_latency():
    telemetry = QueueTelemetryService()
    samples = [10.0, 15.0, 20.0, 25.0, 100.0, 150.0, 200.0]
    p95 = telemetry.calculate_p95_latency(samples)
    assert p95 >= 150.0


def test_calculate_saturation_pct():
    telemetry = QueueTelemetryService()
    assert telemetry.calculate_saturation_pct(2, 10) == 20.0
    assert telemetry.calculate_saturation_pct(10, 10) == 100.0
    assert telemetry.calculate_saturation_pct(12, 10) == 100.0
    assert telemetry.calculate_saturation_pct(0, 0) == 0.0


def test_get_queue_telemetry():
    telemetry = QueueTelemetryService()
    queue_id = "queue-p0"

    res = telemetry.get_queue_telemetry(
        queue_id=queue_id,
        current_depth=45,
        latency_samples_ms=[12.0, 18.0, 25.0, 90.0],
        active_workers=4,
        max_workers=10,
        processed_last_minute=120,
    )

    assert res["queue_id"] == queue_id
    assert res["queue_depth"] == 45
    assert res["saturation_pct"] == 40.0
    assert res["throughput_tps"] == 2.0  # 120 / 60
    assert res["latency_p95_ms"] >= 25.0

    cached = telemetry.get_cached_telemetry(queue_id)
    assert cached == res

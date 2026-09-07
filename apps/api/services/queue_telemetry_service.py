# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_queue_telemetry_service"
# purpose: "Queue Telemetry Service for Real-time Depth, Latency p95, Saturation & Worker Health (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta


class QueueTelemetryService:
    """
    Collects and calculates queue telemetry metrics:
    - Queue Depth (current pending tasks)
    - Latency (p50, p95, p99 in milliseconds)
    - Saturation Percentage (active_workers / max_workers * 100)
    - Throughput (tasks processed per second)
    """

    def __init__(self):
        self._metrics_cache: Dict[str, Dict[str, Any]] = {}

    def calculate_p95_latency(self, latency_samples_ms: List[float]) -> float:
        if not latency_samples_ms:
            return 0.0
        sorted_samples = sorted(latency_samples_ms)
        idx = math.ceil(0.95 * len(sorted_samples)) - 1
        idx = max(0, min(idx, len(sorted_samples) - 1))
        return round(float(sorted_samples[idx]), 2)

    def calculate_saturation_pct(self, active_workers: int, max_workers: int) -> float:
        if max_workers <= 0:
            return 0.0
        pct = (active_workers / max_workers) * 100.0
        return round(min(100.0, max(0.0, pct)), 2)

    def get_queue_telemetry(
        self,
        queue_id: str,
        current_depth: int,
        latency_samples_ms: Optional[List[float]] = None,
        active_workers: int = 0,
        max_workers: int = 10,
        processed_last_minute: int = 0,
    ) -> Dict[str, Any]:
        samples = latency_samples_ms or []
        p95 = self.calculate_p95_latency(samples)
        p50 = round(float(sorted(samples)[len(samples) // 2]), 2) if samples else 0.0
        saturation = self.calculate_saturation_pct(active_workers, max_workers)
        throughput_tps = round(processed_last_minute / 60.0, 2)

        telemetry = {
            "queue_id": queue_id,
            "queue_depth": max(0, current_depth),
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "saturation_pct": saturation,
            "active_workers": active_workers,
            "max_workers": max_workers,
            "throughput_tps": throughput_tps,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._metrics_cache[queue_id] = telemetry
        return telemetry

    def get_cached_telemetry(self, queue_id: str) -> Optional[Dict[str, Any]]:
        return self._metrics_cache.get(queue_id)

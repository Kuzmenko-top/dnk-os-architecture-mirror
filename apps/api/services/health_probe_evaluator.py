# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_health_probe_evaluator"
# purpose: "Health Probe & SLO Watchdog Evaluator for Blue/Green & Canary Deployments (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProbeExecutionResult(BaseModel):
    probe_type: str  # 'liveness', 'readiness', 'startup', 'slo'
    target_environment: str  # 'blue', 'green', 'canary'
    endpoint_path: str
    is_healthy: bool
    status_code: Optional[int] = None
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SLOMetricSnapshot(BaseModel):
    environment: str
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    error_rate: float  # e.g. 0.005 = 0.5%
    request_count: int
    saturation_percentage: float = 0.0  # CPU/RAM utilization 0-100%
    snapshot_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SLOEvaluationResult(BaseModel):
    environment: str
    is_compliant: bool
    violations: List[str] = Field(default_factory=list)
    latency_p95_ok: bool = True
    latency_p99_ok: bool = True
    error_rate_ok: bool = True
    saturation_ok: bool = True
    score: float = 1.0  # 0.0 to 1.0


class HealthProbeEvaluator:
    """
    Evaluator for container lifecycle probes (liveness, readiness, startup)
    and custom Service Level Objective (SLO) thresholds during deployment.
    """

    def __init__(
        self,
        slo_latency_p95_max_ms: float = 200.0,
        slo_latency_p99_max_ms: float = 500.0,
        slo_error_rate_threshold: float = 0.01,  # 1.0%
        slo_saturation_max: float = 85.0,  # 85%
        failure_threshold: int = 3,
    ):
        self.slo_latency_p95_max_ms = slo_latency_p95_max_ms
        self.slo_latency_p99_max_ms = slo_latency_p99_max_ms
        self.slo_error_rate_threshold = slo_error_rate_threshold
        self.slo_saturation_max = slo_saturation_max
        self.failure_threshold = failure_threshold
        self.consecutive_failures: Dict[str, int] = {}
        self.history: List[ProbeExecutionResult] = []

    def evaluate_probe_response(
        self,
        probe_type: str,
        target_environment: str,
        endpoint_path: str,
        status_code: int,
        response_time_ms: float,
        timeout_seconds: float = 5.0,
    ) -> ProbeExecutionResult:
        """
        Evaluates a single HTTP probe response against HTTP 2xx-3xx and timeout limits.
        """
        key = f"{target_environment}:{probe_type}:{endpoint_path}"
        is_timeout = response_time_ms > (timeout_seconds * 1000.0)
        is_status_ok = 200 <= status_code < 400
        is_healthy = is_status_ok and not is_timeout

        error_message = None
        if is_timeout:
            error_message = f"Probe timed out after {response_time_ms:.1f}ms (limit: {timeout_seconds * 1000:.1f}ms)"
        elif not is_status_ok:
            error_message = f"Unhealthy HTTP status code: {status_code}"

        if not is_healthy:
            self.consecutive_failures[key] = self.consecutive_failures.get(key, 0) + 1
        else:
            self.consecutive_failures[key] = 0

        result = ProbeExecutionResult(
            probe_type=probe_type,
            target_environment=target_environment,
            endpoint_path=endpoint_path,
            is_healthy=is_healthy,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
        )
        self.history.append(result)
        return result

    def is_probe_failing_threshold(
        self,
        target_environment: str,
        probe_type: str,
        endpoint_path: str,
    ) -> bool:
        """
        Checks whether consecutive failures reached or exceeded the failure threshold.
        """
        key = f"{target_environment}:{probe_type}:{endpoint_path}"
        return self.consecutive_failures.get(key, 0) >= self.failure_threshold

    def evaluate_slo_compliance(self, snapshot: SLOMetricSnapshot) -> SLOEvaluationResult:
        """
        Evaluates real-time performance telemetry against defined SLO contracts.
        """
        violations: List[str] = []
        latency_p95_ok = snapshot.latency_p95_ms <= self.slo_latency_p95_max_ms
        if not latency_p95_ok:
            violations.append(
                f"p95 latency {snapshot.latency_p95_ms:.1f}ms exceeds threshold {self.slo_latency_p95_max_ms:.1f}ms"
            )

        latency_p99_ok = snapshot.latency_p99_ms <= self.slo_latency_p99_max_ms
        if not latency_p99_ok:
            violations.append(
                f"p99 latency {snapshot.latency_p99_ms:.1f}ms exceeds threshold {self.slo_latency_p99_max_ms:.1f}ms"
            )

        error_rate_ok = snapshot.error_rate <= self.slo_error_rate_threshold
        if not error_rate_ok:
            violations.append(
                f"Error rate {snapshot.error_rate * 100:.2f}% exceeds threshold {self.slo_error_rate_threshold * 100:.2f}%"
            )

        saturation_ok = snapshot.saturation_percentage <= self.slo_saturation_max
        if not saturation_ok:
            violations.append(
                f"Saturation {snapshot.saturation_percentage:.1f}% exceeds max {self.slo_saturation_max:.1f}%"
            )

        # Calculate composite health score (0.0 - 1.0)
        penalty = 0.0
        if not latency_p95_ok:
            penalty += 0.25
        if not latency_p99_ok:
            penalty += 0.25
        if not error_rate_ok:
            penalty += 0.35
        if not saturation_ok:
            penalty += 0.15

        score = max(0.0, 1.0 - penalty)
        is_compliant = len(violations) == 0

        return SLOEvaluationResult(
            environment=snapshot.environment,
            is_compliant=is_compliant,
            violations=violations,
            latency_p95_ok=latency_p95_ok,
            latency_p99_ok=latency_p99_ok,
            error_rate_ok=error_rate_ok,
            saturation_ok=saturation_ok,
            score=round(score, 3),
        )

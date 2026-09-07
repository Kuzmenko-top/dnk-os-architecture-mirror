# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_auto_rollback_engine"
# purpose: "Automated Zero-Downtime Rollback Engine for Deployment SLO Violations (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from apps.api.services.blue_green_deployment_manager import BlueGreenDeploymentManager
from apps.api.services.health_probe_evaluator import (
    HealthProbeEvaluator,
    SLOMetricSnapshot,
    SLOEvaluationResult,
)
from apps.api.services.canary_analysis_engine import (
    CanaryAnalysisEngine,
    CanaryAnalysisInput,
    CanaryAnalysisResult,
)


class AutoRollbackDecision(BaseModel):
    triggered: bool
    deployment_id: str
    target_environment: str
    rollback_status: Optional[str] = None
    reason: Optional[str] = None
    violations: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = Field(default_factory=dict)


class AutoRollbackEngine:
    """
    Automated watchdog service responsible for monitoring telemetry during
    Blue/Green and Canary rollouts, triggering zero-downtime rollbacks when
    health probes, SLO thresholds, or statistical canary analyses fail.
    """

    def __init__(
        self,
        probe_evaluator: Optional[HealthProbeEvaluator] = None,
        canary_engine: Optional[CanaryAnalysisEngine] = None,
        auto_rollback_enabled: bool = True,
    ):
        self.probe_evaluator = probe_evaluator or HealthProbeEvaluator()
        self.canary_engine = canary_engine or CanaryAnalysisEngine()
        self.auto_rollback_enabled = auto_rollback_enabled
        self.rollback_history: List[AutoRollbackDecision] = []

    def evaluate_and_enforce(
        self,
        manager: BlueGreenDeploymentManager,
        candidate_slo_snapshot: Optional[SLOMetricSnapshot] = None,
        canary_analysis_result: Optional[CanaryAnalysisResult] = None,
        probe_failures_detected: bool = False,
    ) -> AutoRollbackDecision:
        """
        Evaluates candidate telemetry and triggers immediate zero-downtime rollback if needed.
        """
        candidate = manager.get_candidate_environment()
        violations: List[str] = []

        # 1. Health Probe Failure Streak
        if probe_failures_detected:
            violations.append("Consecutive health probe failure threshold reached on candidate instance")

        # 2. SLO Threshold Breach
        if candidate_slo_snapshot:
            slo_res = self.probe_evaluator.evaluate_slo_compliance(candidate_slo_snapshot)
            if not slo_res.is_compliant:
                violations.extend([f"SLO violation: {v}" for v in slo_res.violations])

        # 3. Statistical Canary Degradation
        if canary_analysis_result and canary_analysis_result.recommendation == "rollback":
            violations.append(f"Canary analysis trigger: {canary_analysis_result.analysis_notes}")

        # Check if rollback needed
        should_rollback = len(violations) > 0

        if not should_rollback:
            return AutoRollbackDecision(
                triggered=False,
                deployment_id=manager.config_id,
                target_environment=candidate,
                reason="All SLO and health probe checks compliant",
            )

        if not self.auto_rollback_enabled or not manager.auto_rollback_enabled:
            return AutoRollbackDecision(
                triggered=False,
                deployment_id=manager.config_id,
                target_environment=candidate,
                reason="Violations detected but auto-rollback is disabled in config",
                violations=violations,
            )

        # Trigger Zero-Downtime Rollback on Manager
        primary_reason = violations[0] if violations else "Unspecified degradation"
        rollback_res = manager.rollback(
            reason=primary_reason,
            triggered_by="auto_rollback_engine",
        )

        decision = AutoRollbackDecision(
            triggered=True,
            deployment_id=manager.config_id,
            target_environment=candidate,
            rollback_status=rollback_res.get("status"),
            reason=primary_reason,
            violations=violations,
            details=rollback_res,
        )
        self.rollback_history.append(decision)
        return decision

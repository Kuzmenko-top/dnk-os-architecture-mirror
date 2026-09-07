# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_blue_green_deployment_manager"
# purpose: "Lifecycle Orchestration for Zero-Downtime Blue/Green & Canary Deployments (DNK-PLATFORM-SCALE-004)"
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
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from apps.api.services.canary_traffic_splitter import CanaryTrafficSplitter, TrafficRoutingDecision


class EnvironmentState(BaseModel):
    environment_name: str  # 'blue', 'green'
    service_name: str
    image_tag: str
    status: str  # 'active', 'inactive', 'deploying', 'rolling_back'
    traffic_percentage: int
    deployed_at: Optional[datetime] = None


class DeploymentStateSnapshot(BaseModel):
    config_id: str
    deployment_name: str
    strategy: str
    active_environment: str
    canary_enabled: bool
    canary_traffic_percentage: int
    canary_steps: List[int]
    current_step_index: int
    auto_rollback_enabled: bool
    environments: Dict[str, EnvironmentState]
    last_updated: datetime


class BlueGreenDeploymentManager:
    """
    Stateful orchestrator for Blue/Green environments, progressive canary traffic shifting,
    safe candidate promotion, and instant rollbacks.
    """

    DEFAULT_CANARY_STEPS = [1, 5, 25, 50, 100]

    def __init__(
        self,
        config_id: str,
        deployment_name: str,
        blue_service_name: str,
        green_service_name: str,
        initial_image_tag: str = "v1.0.0",
        strategy: str = "canary",
        canary_steps: Optional[List[int]] = None,
        auto_rollback_enabled: bool = True,
    ) -> None:
        self.config_id = config_id
        self.deployment_name = deployment_name
        self.blue_service_name = blue_service_name
        self.green_service_name = green_service_name
        self.strategy = strategy
        self.canary_steps = canary_steps or self.DEFAULT_CANARY_STEPS
        self.auto_rollback_enabled = auto_rollback_enabled

        self.active_environment = "blue"
        self.canary_enabled = False
        self.canary_percentage = 0
        self.current_step_index = 0
        self.history_events: List[Dict[str, Any]] = []

        now = datetime.now(timezone.utc)
        self.environments: Dict[str, EnvironmentState] = {
            "blue": EnvironmentState(
                environment_name="blue",
                service_name=blue_service_name,
                image_tag=initial_image_tag,
                status="active",
                traffic_percentage=100,
                deployed_at=now,
            ),
            "green": EnvironmentState(
                environment_name="green",
                service_name=green_service_name,
                image_tag=initial_image_tag,
                status="inactive",
                traffic_percentage=0,
                deployed_at=None,
            ),
        }

        self._record_event(
            event_type="deployment_initialized",
            details={
                "initial_active": "blue",
                "image_tag": initial_image_tag,
                "strategy": strategy,
            },
            triggered_by="system",
        )

    def _record_event(self, event_type: str, details: Dict[str, Any], triggered_by: str = "system") -> None:
        event = {
            "event_type": event_type,
            "details": details,
            "triggered_by": triggered_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.history_events.append(event)

    def get_candidate_environment(self) -> str:
        return "green" if self.active_environment == "blue" else "blue"

    def get_splitter(self) -> CanaryTrafficSplitter:
        return CanaryTrafficSplitter(
            blue_service_name=self.blue_service_name,
            green_service_name=self.green_service_name,
            canary_percentage=self.canary_percentage,
            active_environment=self.active_environment,
            canary_enabled=self.canary_enabled,
        )

    def trigger_deploy(self, image_tag: str, triggered_by: str = "user") -> Dict[str, Any]:
        """
        Deploys a new image tag to the inactive candidate environment.
        """
        candidate = self.get_candidate_environment()
        now = datetime.now(timezone.utc)

        self.environments[candidate].image_tag = image_tag
        self.environments[candidate].status = "deploying"
        self.environments[candidate].deployed_at = now
        self.environments[candidate].traffic_percentage = 0

        self.canary_enabled = False
        self.canary_percentage = 0
        self.current_step_index = 0

        self._record_event(
            event_type="deployment_started",
            details={
                "candidate_environment": candidate,
                "image_tag": image_tag,
            },
            triggered_by=triggered_by,
        )

        return {
            "status": "deployed_to_candidate",
            "candidate_environment": candidate,
            "image_tag": image_tag,
            "active_environment": self.active_environment,
        }

    def start_canary(self, triggered_by: str = "user") -> Dict[str, Any]:
        """
        Starts canary rollout at the first step (e.g. 1% traffic).
        """
        candidate = self.get_candidate_environment()
        self.canary_enabled = True
        self.current_step_index = 0
        first_step = self.canary_steps[0] if self.canary_steps else 1
        self.canary_percentage = first_step

        self.environments[candidate].status = "active"
        self.environments[candidate].traffic_percentage = self.canary_percentage
        self.environments[self.active_environment].traffic_percentage = 100 - self.canary_percentage

        self._record_event(
            event_type="canary_started",
            details={
                "candidate_environment": candidate,
                "traffic_percentage": self.canary_percentage,
                "step_index": self.current_step_index,
            },
            triggered_by=triggered_by,
        )

        return {
            "status": "canary_in_progress",
            "canary_percentage": self.canary_percentage,
            "step_index": self.current_step_index,
            "candidate_environment": candidate,
        }

    def advance_canary_step(self, triggered_by: str = "user") -> Dict[str, Any]:
        """
        Advances traffic to the next step in the configured canary steps sequence.
        """
        if not self.canary_enabled:
            raise ValueError("Canary deployment is not active. Call start_canary first.")

        candidate = self.get_candidate_environment()
        if self.current_step_index + 1 < len(self.canary_steps):
            self.current_step_index += 1
            self.canary_percentage = self.canary_steps[self.current_step_index]
            self.environments[candidate].traffic_percentage = self.canary_percentage
            self.environments[self.active_environment].traffic_percentage = 100 - self.canary_percentage

            self._record_event(
                event_type="canary_step_completed",
                details={
                    "candidate_environment": candidate,
                    "traffic_percentage": self.canary_percentage,
                    "step_index": self.current_step_index,
                },
                triggered_by=triggered_by,
            )

            return {
                "status": "step_advanced",
                "canary_percentage": self.canary_percentage,
                "step_index": self.current_step_index,
                "is_last_step": self.current_step_index == len(self.canary_steps) - 1,
            }
        else:
            # Reached last step (100%), auto-promote
            return self.promote(triggered_by=triggered_by)

    def promote(self, triggered_by: str = "user") -> Dict[str, Any]:
        """
        Promotes candidate to full active baseline (100% traffic) with zero downtime.
        Old active becomes inactive baseline.
        """
        old_active = self.active_environment
        new_active = self.get_candidate_environment()

        self.active_environment = new_active
        self.canary_enabled = False
        self.canary_percentage = 0
        self.current_step_index = 0

        self.environments[new_active].status = "active"
        self.environments[new_active].traffic_percentage = 100

        self.environments[old_active].status = "inactive"
        self.environments[old_active].traffic_percentage = 0

        self._record_event(
            event_type="promotion_completed",
            details={
                "previous_active": old_active,
                "new_active": new_active,
                "image_tag": self.environments[new_active].image_tag,
            },
            triggered_by=triggered_by,
        )

        return {
            "status": "promotion_successful",
            "active_environment": new_active,
            "previous_environment": old_active,
            "image_tag": self.environments[new_active].image_tag,
        }

    def rollback(self, reason: str = "manual_rollback", triggered_by: str = "user") -> Dict[str, Any]:
        """
        Instantly diverts 100% of traffic back to the stable active baseline and marks candidate as rolling_back.
        """
        candidate = self.get_candidate_environment()
        prior_percentage = self.canary_percentage

        self.canary_enabled = False
        self.canary_percentage = 0
        self.current_step_index = 0

        self.environments[self.active_environment].status = "active"
        self.environments[self.active_environment].traffic_percentage = 100

        self.environments[candidate].status = "rolling_back"
        self.environments[candidate].traffic_percentage = 0

        self._record_event(
            event_type="auto_rollback_triggered" if "auto" in triggered_by.lower() else "manual_rollback_triggered",
            details={
                "restored_active": self.active_environment,
                "reverted_candidate": candidate,
                "prior_traffic_percentage": prior_percentage,
                "reason": reason,
            },
            triggered_by=triggered_by,
        )

        return {
            "status": "rollback_completed",
            "active_environment": self.active_environment,
            "reverted_candidate": candidate,
            "reason": reason,
            "traffic_percentage": 100,
        }

    def get_snapshot(self) -> DeploymentStateSnapshot:
        return DeploymentStateSnapshot(
            config_id=self.config_id,
            deployment_name=self.deployment_name,
            strategy=self.strategy,
            active_environment=self.active_environment,
            canary_enabled=self.canary_enabled,
            canary_traffic_percentage=self.canary_percentage,
            canary_steps=self.canary_steps,
            current_step_index=self.current_step_index,
            auto_rollback_enabled=self.auto_rollback_enabled,
            environments=self.environments,
            last_updated=datetime.now(timezone.utc),
        )

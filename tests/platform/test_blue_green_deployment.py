# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_blue_green_deployment"
# purpose: "Unit & Lifecycle Integration Tests for Blue/Green & Canary Manager (DNK-PLATFORM-SCALE-004)"
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
from apps.api.services.blue_green_deployment_manager import BlueGreenDeploymentManager


def test_blue_green_manager_initialization():
    manager = BlueGreenDeploymentManager(
        config_id="cfg-001",
        deployment_name="dnk-core-api",
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        initial_image_tag="v1.0.0",
    )
    snapshot = manager.get_snapshot()
    assert snapshot.active_environment == "blue"
    assert snapshot.canary_enabled is False
    assert snapshot.environments["blue"].status == "active"
    assert snapshot.environments["blue"].traffic_percentage == 100
    assert snapshot.environments["green"].status == "inactive"
    assert snapshot.environments["green"].traffic_percentage == 0


def test_blue_green_deploy_lifecycle():
    manager = BlueGreenDeploymentManager(
        config_id="cfg-001",
        deployment_name="dnk-core-api",
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        initial_image_tag="v1.0.0",
    )

    # 1. Trigger deploy to green
    deploy_res = manager.trigger_deploy(image_tag="v1.1.0", triggered_by="ci_pipeline")
    assert deploy_res["status"] == "deployed_to_candidate"
    assert deploy_res["candidate_environment"] == "green"
    assert manager.environments["green"].status == "deploying"
    assert manager.environments["green"].image_tag == "v1.1.0"

    # 2. Start Canary (Step 0 -> 1%)
    canary_start = manager.start_canary(triggered_by="operator")
    assert canary_start["status"] == "canary_in_progress"
    assert canary_start["canary_percentage"] == 1
    assert manager.environments["green"].traffic_percentage == 1
    assert manager.environments["blue"].traffic_percentage == 99

    # 3. Advance Steps: 5% -> 25% -> 50%
    step1 = manager.advance_canary_step()
    assert step1["canary_percentage"] == 5
    assert manager.environments["green"].traffic_percentage == 5

    step2 = manager.advance_canary_step()
    assert step2["canary_percentage"] == 25

    step3 = manager.advance_canary_step()
    assert step3["canary_percentage"] == 50

    # 4. Advance Step: 100%
    step4 = manager.advance_canary_step()
    assert step4["status"] == "step_advanced"
    assert step4["canary_percentage"] == 100
    assert step4["is_last_step"] is True

    # 5. Advance Step beyond 100% (Auto-Promote)
    step5 = manager.advance_canary_step()
    assert step5["status"] == "promotion_successful"
    assert step5["active_environment"] == "green"
    assert manager.active_environment == "green"
    assert manager.environments["green"].status == "active"
    assert manager.environments["green"].traffic_percentage == 100
    assert manager.environments["blue"].status == "inactive"
    assert manager.environments["blue"].traffic_percentage == 0


def test_blue_green_rollback():
    manager = BlueGreenDeploymentManager(
        config_id="cfg-001",
        deployment_name="dnk-core-api",
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        initial_image_tag="v1.0.0",
    )

    manager.trigger_deploy(image_tag="v1.2.0-broken")
    manager.start_canary()
    manager.advance_canary_step()  # 5%

    assert manager.environments["green"].traffic_percentage == 5

    # Trigger Rollback
    rollback_res = manager.rollback(reason="slo_error_rate_spike", triggered_by="auto_rollback")
    assert rollback_res["status"] == "rollback_completed"
    assert rollback_res["active_environment"] == "blue"
    assert manager.environments["blue"].status == "active"
    assert manager.environments["blue"].traffic_percentage == 100
    assert manager.environments["green"].status == "rolling_back"
    assert manager.environments["green"].traffic_percentage == 0
    assert manager.canary_enabled is False


def test_blue_green_direct_promotion():
    manager = BlueGreenDeploymentManager(
        config_id="cfg-001",
        deployment_name="dnk-core-api",
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        initial_image_tag="v1.0.0",
    )

    manager.trigger_deploy(image_tag="v2.0.0")
    promo_res = manager.promote(triggered_by="release_lead")
    assert promo_res["status"] == "promotion_successful"
    assert promo_res["active_environment"] == "green"
    assert promo_res["previous_environment"] == "blue"
    assert manager.active_environment == "green"

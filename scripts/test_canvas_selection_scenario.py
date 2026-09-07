# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/test_canvas_selection_scenario.py"
# purpose: "Standalone verification script for Canvas selection scenario and runtime event publishing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import sys
from typing import Any

from core.canvas_runtime_bridge import CanvasRuntimeBridge
from core.runtime_events import RuntimeEventBus


class MockRedisPubSub:
    """Mock Redis client capturing published channel messages for verification."""

    def __init__(self) -> None:
        self.published_messages: list[tuple[str, str]] = []

    def publish(self, channel: str, message: str) -> int:
        self.published_messages.append((channel, message))
        return 1

    def ping(self) -> bool:
        return True


def run_scenario() -> dict[str, Any]:
    print("=" * 70)
    print("🚀 [START] Canvas Selection Runtime Bridge Verification Scenario")
    print("=" * 70)

    event_bus = RuntimeEventBus()
    redis_mock = MockRedisPubSub()
    bridge = CanvasRuntimeBridge(
        event_bus=event_bus,
        redis_client=redis_mock,
        default_tenant_id="ws-alpha-001",
        default_workspace_id="ws-alpha-001",
        default_canvas_id="canvas_flow_01",
    )

    # 1. Single Node Lifecycle Test (Node Created & Node Executed)
    print("\n--- 1. Testing Standalone Node Lifecycle ---")
    ev_created = bridge.publish_node_created(
        node_id="node_user_query",
        name="UserInstructionCard",
        node_type="canvas_input",
        thread_id="th_scenario_demo",
    )
    print(
        f"✓ [EventBus/Redis] Node Created: id={ev_created.node_id}, "
        f"type={ev_created.event_type}, seq={ev_created.sequence_number}"
    )

    ev_executed = bridge.publish_node_executed(
        node_id="node_user_query",
        status="completed",
        thread_id="th_scenario_demo",
        execution_result={"prompt": "Build landing page hero section", "token_count": 42},
    )
    print(
        f"✓ [EventBus/Redis] Node Executed: id={ev_executed.node_id}, "
        f"type={ev_executed.event_type}, seq={ev_executed.sequence_number}"
    )

    # 2. Canvas Selection Scenario Test
    print("\n--- 2. Testing Canvas Selection Scenario Execution ---")
    selection_id = "sel_region_8849"
    selected_nodes = [
        {
            "id": "card_input_hero",
            "name": "HeroDesignSpec",
            "type": "design_spec",
            "bounds": {"x": 120.0, "y": 200.0, "width": 250.0, "height": 180.0},
        },
        {
            "id": "card_agent_coder",
            "name": "BuilderAgent",
            "type": "agent_worker",
            "bounds": {"x": 420.0, "y": 200.0, "width": 250.0, "height": 180.0},
        },
    ]
    selection_bounds = {"x": 100.0, "y": 180.0, "width": 600.0, "height": 240.0}

    scenario_result = bridge.execute_selection_scenario(
        selection_id=selection_id,
        selected_nodes=selected_nodes,
        selection_bounds=selection_bounds,
    )

    print(f"✓ Selection ID: {scenario_result['selection_id']}")
    print(f"✓ Execution ID: {scenario_result['execution_id']}")
    print(f"✓ Total Events Published: {scenario_result['events_count']}")
    print(f"✓ Total Redis Publishes: {len(redis_mock.published_messages)}")
    print(f"✓ Node States: {scenario_result['node_states']}")
    print(f"✓ Snapshot Status: {scenario_result['snapshot']['status']}")

    # Validation assertions
    assert scenario_result["status"] == "success", "Scenario must succeed"
    assert scenario_result["events_count"] == 6, "Expected 6 events for selection pipeline"
    assert len(redis_mock.published_messages) == 8, "Expected 8 total messages published to Redis (2 direct + 6 selection)"

    # Verify event types in Redis messages
    redis_event_types = [json.loads(msg[1])["event_type"] for msg in redis_mock.published_messages]
    assert "node.created" in redis_event_types, "Redis must have received node.created events"
    assert "node.executed" in redis_event_types, "Redis must have received node.executed events"

    print("\n" + "=" * 70)
    print("🎉 [SUCCESS] All Canvas Runtime Bridge Invariants 100% VERIFIED!")
    print("=" * 70)
    return scenario_result


if __name__ == "__main__":
    try:
        run_scenario()
        sys.exit(0)
    except Exception as err:
        print(f"❌ Verification failed: {err}", file=sys.stderr)
        sys.exit(1)

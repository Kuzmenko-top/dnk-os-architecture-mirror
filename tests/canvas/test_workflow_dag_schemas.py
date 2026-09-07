# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_workflow_dag_schemas"
# purpose: "Comprehensive Unit and Integration Tests for Visual Canvas Workflow DAG Schemas (DNK-CANVAS-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.schemas.workflow_dag_schemas import (
    WorkflowNodeType,
    NodeExecutionStatus,
    NodePosition,
    A2AAgentNodeConfig,
    EventTriggerNodeConfig,
    BatchTaskNodeConfig,
    ShopifyActionNodeConfig,
    HardwareActionNodeConfig,
    WorkflowNode,
    WorkflowEdge,
    WorkflowDAG,
    WorkflowExecuteRequest,
    WorkflowExecutionSummary
)


def test_a2a_agent_node_schema_validation():
    node = WorkflowNode(
        id="node_a2a_1",
        type=WorkflowNodeType.A2A_AGENT,
        label="Agent Builder",
        position=NodePosition(x=100.0, y=150.0),
        config={
            "agent_id": "gerych_builder",
            "role": "code_architect",
            "task_prompt": "Build Next.js component",
            "capabilities": ["code_generation", "ast_parse"],
            "consensus_threshold": 0.8,
            "timeout_sec": 45
        }
    )
    typed = node.get_typed_config()
    assert isinstance(typed, A2AAgentNodeConfig)
    assert typed.agent_id == "gerych_builder"
    assert typed.consensus_threshold == 0.8


def test_event_trigger_node_schema_validation():
    node = WorkflowNode(
        id="node_event_1",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Order Webhook Trigger",
        config={
            "stream_topic": "orders.created",
            "event_type": "webhook",
            "debounce_ms": 250,
            "auto_ack": True
        }
    )
    typed = node.get_typed_config()
    assert isinstance(typed, EventTriggerNodeConfig)
    assert typed.stream_topic == "orders.created"
    assert typed.debounce_ms == 250


def test_batch_task_node_schema_validation():
    node = WorkflowNode(
        id="node_batch_1",
        type=WorkflowNodeType.BATCH_TASK,
        label="Batch Data Enrichment",
        config={
            "batch_job_type": "vector_embedding_indexing",
            "payload_template": {"batch_size": 100},
            "max_retries": 3,
            "backoff_factor": 2.0,
            "priority": 5
        }
    )
    typed = node.get_typed_config()
    assert isinstance(typed, BatchTaskNodeConfig)
    assert typed.batch_job_type == "vector_embedding_indexing"
    assert typed.priority == 5


def test_shopify_action_node_schema_validation():
    node = WorkflowNode(
        id="node_shopify_1",
        type=WorkflowNodeType.SHOPIFY_ACTION,
        label="Create Fulfillment",
        config={
            "action_type": "order_fulfillment_create",
            "shop_domain": "m-craft.myshopify.com",
            "mutation_params": {"tracking_company": "Nova Poshta"},
            "api_version": "2026-01"
        }
    )
    typed = node.get_typed_config()
    assert isinstance(typed, ShopifyActionNodeConfig)
    assert typed.shop_domain == "m-craft.myshopify.com"


def test_hardware_action_node_schema_validation():
    node = WorkflowNode(
        id="node_hw_1",
        type=WorkflowNodeType.HARDWARE_ACTION,
        label="ReBurn Laser Pin Trigger",
        config={
            "device_id": "reburn_laser_engraver_01",
            "action_type": "gpio_write",
            "pin": 18,
            "payload": {"state": "HIGH", "duration_ms": 500}
        }
    )
    typed = node.get_typed_config()
    assert isinstance(typed, HardwareActionNodeConfig)
    assert typed.device_id == "reburn_laser_engraver_01"
    assert typed.pin == 18


def test_workflow_dag_topological_sort_and_validation():
    # Linear pipeline: Trigger -> Batch -> A2A -> Shopify -> Hardware
    n1 = WorkflowNode(
        id="n_trig",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Trigger",
        config={"stream_topic": "reburn.events"}
    )
    n2 = WorkflowNode(
        id="n_batch",
        type=WorkflowNodeType.BATCH_TASK,
        label="Batch Prep",
        config={"batch_job_type": "prep_job"}
    )
    n3 = WorkflowNode(
        id="n_a2a",
        type=WorkflowNodeType.A2A_AGENT,
        label="A2A Synthesizer",
        config={"agent_id": "dnk_dev_fullstack", "task_prompt": "Synthesize design"}
    )
    n4 = WorkflowNode(
        id="n_shop",
        type=WorkflowNodeType.SHOPIFY_ACTION,
        label="Shopify Sync",
        config={"action_type": "inventory_sync", "shop_domain": "test.myshopify.com"}
    )
    n5 = WorkflowNode(
        id="n_hw",
        type=WorkflowNodeType.HARDWARE_ACTION,
        label="ReBurn Actuator",
        config={"device_id": "reburn_01", "action_type": "trigger_actuator"}
    )

    edges = [
        WorkflowEdge(id="e1", source="n_trig", target="n_batch"),
        WorkflowEdge(id="e2", source="n_batch", target="n_a2a"),
        WorkflowEdge(id="e3", source="n_a2a", target="n_shop"),
        WorkflowEdge(id="e4", source="n_shop", target="n_hw"),
    ]

    dag = WorkflowDAG(
        id="wf_complete_01",
        name="ReBurn E-Commerce Auto-Manufacturing",
        nodes=[n1, n2, n3, n4, n5],
        edges=edges
    )

    order = dag.get_topological_order()
    assert order == ["n_trig", "n_batch", "n_a2a", "n_shop", "n_hw"]


def test_workflow_dag_cycle_detection_rejection():
    n1 = WorkflowNode(
        id="node_a",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Node A",
        config={"stream_topic": "topic.a"}
    )
    n2 = WorkflowNode(
        id="node_b",
        type=WorkflowNodeType.BATCH_TASK,
        label="Node B",
        config={"batch_job_type": "job.b"}
    )
    n3 = WorkflowNode(
        id="node_c",
        type=WorkflowNodeType.A2A_AGENT,
        label="Node C",
        config={"agent_id": "agent_c", "task_prompt": "prompt"}
    )

    # Cycle: A -> B -> C -> A
    edges = [
        WorkflowEdge(id="e1", source="node_a", target="node_b"),
        WorkflowEdge(id="e2", source="node_b", target="node_c"),
        WorkflowEdge(id="e3", source="node_c", target="node_a"),
    ]

    with pytest.raises(ValueError, match="Cycle detected in Workflow graph"):
        WorkflowDAG(
            name="Cyclic Graph",
            nodes=[n1, n2, n3],
            edges=edges
        )


def test_workflow_dag_dangling_edge_rejection():
    n1 = WorkflowNode(
        id="node_a",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Node A",
        config={"stream_topic": "topic.a"}
    )
    edges = [
        WorkflowEdge(id="e1", source="node_a", target="node_non_existent"),
    ]

    with pytest.raises(ValueError, match="non-existent target node"):
        WorkflowDAG(
            name="Dangling Edge Graph",
            nodes=[n1],
            edges=edges
        )


def test_workflow_dag_react_flow_roundtrip():
    n1 = WorkflowNode(
        id="rf_n1",
        type=WorkflowNodeType.EVENT_TRIGGER,
        label="Start Event",
        position=NodePosition(x=10.0, y=20.0),
        config={"stream_topic": "rf.events"}
    )
    n2 = WorkflowNode(
        id="rf_n2",
        type=WorkflowNodeType.HARDWARE_ACTION,
        label="Hardware Ping",
        position=NodePosition(x=200.0, y=220.0),
        config={"device_id": "reburn_unit", "action_type": "gpio_write", "pin": 4}
    )
    edge = WorkflowEdge(
        id="rf_e1",
        source="rf_n1",
        target="rf_n2",
        source_handle="output",
        target_handle="input",
        condition="payload.count > 0",
        edge_type="smoothstep"
    )

    dag = WorkflowDAG(
        id="wf_rf_test",
        name="React Flow Roundtrip Test",
        nodes=[n1, n2],
        edges=[edge]
    )

    rf_dict = dag.to_react_flow()
    assert rf_dict["id"] == "wf_rf_test"
    assert len(rf_dict["nodes"]) == 2
    assert len(rf_dict["edges"]) == 1
    assert rf_dict["nodes"][0]["position"] == {"x": 10.0, "y": 20.0}

    # Deserialization from React Flow
    reconstructed_dag = WorkflowDAG.from_react_flow(rf_dict)
    assert reconstructed_dag.id == "wf_rf_test"
    assert len(reconstructed_dag.nodes) == 2
    assert reconstructed_dag.nodes[0].position.x == 10.0
    assert reconstructed_dag.edges[0].condition == "payload.count > 0"

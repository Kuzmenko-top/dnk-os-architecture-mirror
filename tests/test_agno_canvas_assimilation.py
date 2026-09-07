# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_agno_canvas_assimilation.py"
# purpose: "Unit and integration tests for Agno Canvas Adapter, Team orchestration, DAG execution and HITL checkpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TEST-AGNO-CANVAS-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.dnk_agno_canvas_adapter import (
    DnkAgnoCanvasAdapter,
    CanvasNodeConfig,
    CanvasNodeType,
    AgnoTeamMode,
    CanvasNodeStatus,
    CanvasEdge,
)


@pytest.fixture
def adapter():
    return DnkAgnoCanvasAdapter()


def test_validate_graph_valid(adapter):
    graph = {
        "nodes": [
            {"node_id": "n1", "node_type": "agent", "title": "Node 1"},
            {"node_id": "n2", "node_type": "team", "title": "Node 2"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"}
        ],
    }
    res = adapter.validate_graph(graph)
    assert res["valid"] is True
    assert res["node_count"] == 2
    assert res["edge_count"] == 1


def test_validate_graph_cycle_detection(adapter):
    graph = {
        "nodes": [
            {"node_id": "n1", "node_type": "agent"},
            {"node_id": "n2", "node_type": "agent"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
            {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n1"},
        ],
    }
    res = adapter.validate_graph(graph)
    assert res["valid"] is False
    assert "Circular dependency" in res["error"]


def test_topological_compilation(adapter):
    graph = {
        "nodes": [
            {"node_id": "n3", "title": "Third"},
            {"node_id": "n1", "title": "First"},
            {"node_id": "n2", "title": "Second"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
            {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n3"},
        ],
    }
    sorted_nodes = adapter.compile_topological_dag(graph)
    ordered_ids = [n.node_id for n in sorted_nodes]
    assert ordered_ids == ["n1", "n2", "n3"]


def test_agent_node_execution_with_tools_and_memory(adapter):
    graph = {
        "graph_id": "g-agent-01",
        "nodes": [
            {
                "node_id": "agent-01",
                "node_type": "agent",
                "title": "Keyword Extractor Agent",
                "agent_name": "extractor",
                "tools": ["extract_keywords"],
                "memory_workspace": "ws-alpha-001",
            }
        ],
        "edges": [],
        "initial_inputs": {"prompt": "Shopify Liquid template rendering and canvas AST transformation"},
    }
    results = adapter.execute_graph_stepwise(graph)
    assert "agent-01" in results
    res = results["agent-01"]
    assert res.status == CanvasNodeStatus.COMPLETED
    assert res.output_data is not None
    assert "extract_keywords" in res.output_data["tool_results"]
    assert "keywords" in res.output_data["tool_results"]["extract_keywords"]
    assert res.tokens_consumed > 0

    # Verify SCONES memory sync
    memories = adapter.get_workspace_memories("ws-alpha-001")
    assert len(memories) >= 1
    assert memories[-1]["node_id"] == "agent-01"


def test_team_node_execution_all_modes(adapter):
    # 1. Route Mode
    graph_route = {
        "nodes": [
            {
                "node_id": "team-route",
                "node_type": "team",
                "title": "Route Swarm",
                "team_mode": "route",
                "member_agents": ["shopify_specialist", "backend_specialist"],
            }
        ],
        "edges": [],
        "initial_inputs": {"prompt": "Build product page"},
    }
    res_route = adapter.execute_graph_stepwise(graph_route)["team-route"]
    assert res_route.status == CanvasNodeStatus.COMPLETED
    assert "shopify_specialist" in res_route.output_data["member_outputs"]

    # 2. Broadcast Mode
    graph_broadcast = {
        "nodes": [
            {
                "node_id": "team-broadcast",
                "node_type": "team",
                "title": "Broadcast Swarm",
                "team_mode": "broadcast",
                "member_agents": ["worker_a", "worker_b"],
            }
        ],
        "edges": [],
        "initial_inputs": {"prompt": "Audit codebase"},
    }
    res_b = adapter.execute_graph_stepwise(graph_broadcast)["team-broadcast"]
    assert "worker_a" in res_b.output_data["member_outputs"]
    assert "worker_b" in res_b.output_data["member_outputs"]

    # 3. Consensus Mode
    graph_consensus = {
        "nodes": [
            {
                "node_id": "team-consensus",
                "node_type": "team",
                "title": "Debate Team",
                "team_mode": "consensus",
                "member_agents": ["auditor_1", "auditor_2"],
            }
        ],
        "edges": [],
        "initial_inputs": {"prompt": "Approve pull request"},
    }
    res_c = adapter.execute_graph_stepwise(graph_consensus)["team-consensus"]
    assert "synthesis" in res_c.output_data["member_outputs"]


def test_hitl_checkpoint_and_resumption(adapter):
    # Trigger dangerous tool
    graph_hitl = {
        "graph_id": "g-deploy",
        "nodes": [
            {
                "node_id": "deploy-agent",
                "node_type": "agent",
                "title": "Deployment Agent",
                "tools": ["deploy_shopify_theme"],
            },
            {
                "node_id": "verify-step",
                "node_type": "workflow_step",
                "title": "Verify Deployment",
            }
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "deploy-agent", "target_node_id": "verify-step"}
        ],
        "initial_inputs": {"theme_id": "theme_9988"},
    }

    results = adapter.execute_graph_stepwise(graph_hitl)
    deploy_res = results["deploy-agent"]
    assert deploy_res.status == CanvasNodeStatus.PAUSED_HITL
    assert deploy_res.checkpoint_id is not None
    assert "verify-step" not in results  # Execution suspended before reaching step 2

    chk_id = deploy_res.checkpoint_id

    # Test rejection
    rejection_res = adapter.resume_hitl_checkpoint(
        checkpoint_id=chk_id,
        decision="reject",
        user_comment="Rollback requested by Maxim",
    )
    assert rejection_res.status == CanvasNodeStatus.FAILED
    assert "rejected by user" in rejection_res.error_message

    # Test re-creating and approving checkpoint
    new_chk = adapter.create_hitl_checkpoint(
        graph_id="g-deploy",
        node_id="deploy-agent",
        reason="Approved after review",
        pending_action="deploy_shopify_theme",
        parameters={"theme_id": "theme_9988_prod"},
    )
    approval_res = adapter.resume_hitl_checkpoint(
        checkpoint_id=new_chk.checkpoint_id,
        decision="approve",
        user_comment="Verified and approved",
    )
    assert approval_res.status == CanvasNodeStatus.COMPLETED
    assert approval_res.output_data["result"]["approved"] is True

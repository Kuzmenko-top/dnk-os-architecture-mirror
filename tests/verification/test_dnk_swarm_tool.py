# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_dnk_swarm_tool.py"
# purpose: "Verify DNK Swarm tools discovery, registration, toolsets, and multi-agent dispatch via SwarmCoordinator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import sys
from pathlib import Path
import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

hermes_path = str(HUB_ROOT / "core" / "hermes_agent")
if hermes_path not in sys.path:
    sys.path.append(hermes_path)

from tools.registry import registry, discover_builtin_tools
from toolsets import TOOLSETS, _HERMES_CORE_TOOLS


def test_dnk_tools_discovery_and_registration():
    """Verify that all DNK tools are discovered and registered in Hermes ToolRegistry."""
    discover_builtin_tools()
    registered_tools = registry._tools
    
    expected_dnk_tools = [
        "dnk_swarm_dispatch",
        "dnk_swarm_pipeline",
        "dnk_swarm_parallel",
        "dnk_swarm_status",
        "dnk_decompose_task_dna",
        "scones_get_memories",
        "scones_add_memory",
        "dnk_query_error_solutions",
        "dnk_record_error_solution",
        "dnk_run_adversarial_review",
        "dnk_run_research_flow",
        "dnk_shopify_validate_liquid",
        "dnk_video_generate_composition",
        "dnk_vault_get_secret",
        "dnk_vault_set_secret",
        "dnk_visual_context_query",
        "dnk_workspace_occ_merge",
        "dnk_one_click_product_launch",
        "dnk_get_workspace_spending",
        "dnk_assimilate_repo",
    ]
    
    for tool_name in expected_dnk_tools:
        assert tool_name in registered_tools, f"Tool '{tool_name}' was not discovered in registry!"


def test_dnk_toolsets_definition():
    """Verify that dnk_swarm toolset is defined and contains all expected tools."""
    assert "dnk_swarm" in TOOLSETS, "dnk_swarm toolset not found in TOOLSETS!"
    dnk_ts = TOOLSETS["dnk_swarm"]
    assert "dnk_swarm_dispatch" in dnk_ts["tools"]
    assert "dnk_decompose_task_dna" in dnk_ts["tools"]
    assert "scones_get_memories" in dnk_ts["tools"]
    assert "dnk_swarm_dispatch" in _HERMES_CORE_TOOLS


def test_dnk_swarm_dispatch_live():
    """Verify dnk_swarm_dispatch execution routes to SwarmCoordinator."""
    from tools.dnk_swarm_tool import dnk_swarm_dispatch
    
    raw_res = dnk_swarm_dispatch(
        agent="gerych_builder",
        task_description="Implement unit test for checkout banner",
        workspace_id="ws-test-001"
    )
    res = json.loads(raw_res)
    assert res.get("status") == "success"
    assert res.get("agent") == "gerych_builder"
    assert "outcome" in res


def test_dnk_decompose_task_dna_with_dict_and_non_string():
    """Verify dnk_decompose_task_dna handles dict and non-string goals without unhashable type errors."""
    from tools.dnk_taskdna_tool import dnk_decompose_task_dna
    
    # 1. Test with dict input
    dict_goal = {"goal": "Build Spatial Canvas Studio", "priority": "high", "workspace": "ws-001"}
    res_raw = dnk_decompose_task_dna(goal=dict_goal)
    res = json.loads(res_raw)
    assert res.get("status") == "success"
    assert "task_id" in res
    assert len(res.get("dag_tree", [])) == 3
    assert res.get("total_subtasks") == 3
    
    # 2. Test with list input
    list_goal = ["Goal 1", "Goal 2"]
    res_raw2 = dnk_decompose_task_dna(goal=list_goal)
    res2 = json.loads(res_raw2)
    assert res2.get("status") == "success"
    assert "task_id" in res2
    assert len(res2.get("dag_tree", [])) == 3


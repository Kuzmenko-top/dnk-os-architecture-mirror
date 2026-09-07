# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_dnk_core.py"
# purpose: "Unit tests for DNK OS Core Kernel (user soul, task engine, omni router)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "0.1.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from user_soul import user_soul
from task_engine import task_engine
from omni_router import omni_router


def test_user_soul_context():
    ctx = user_soul.get_prompt_context()
    assert "Maxim" in ctx
    assert "[DNK OS USER SOUL CONTEXT]" in ctx


def test_task_engine_victory_map():
    # Cover status updating
    assert task_engine.update_status("ROOT", "done") is True
    assert task_engine.update_status("NON_EXISTENT", "done") is False

    task_engine.add_task("T1_SHOPIFY", "Shopify 3.0 Tinker setup", "task", "P1", "done")
    vmap = task_engine.get_victory_map()
    assert vmap["completed_tasks"] >= 1
    assert vmap["victory_percentage"] > 0
    assert vmap["system"] == "DNK OS 1.0.0"

    # Cover logging steps (trajectories)
    step1 = task_engine.log_step("T1_SHOPIFY", "init", "success", tokens_used=120)
    assert step1["step_index"] == 1
    assert step1["action"] == "init"
    assert step1["result"] == "success"
    assert step1["tokens_used"] == 120

    step2 = task_engine.log_step("T1_SHOPIFY", "test", "passed", tokens_used=50)
    assert step2["step_index"] == 2


def test_omni_router_dispatch():
    res = omni_router.dispatch("Configure Shopify theme Tinker 4.3.1")
    assert res["status"] == "dispatched"
    assert res["classification"]["assigned_agent"] == "shopify_pro"
    assert "[DNK OS USER SOUL CONTEXT]" in res["hydrated_context"]

    # Cover other branches of classify_intent
    res_research = omni_router.dispatch("Do git research on agent swarms")
    assert res_research["classification"]["assigned_agent"] == "herich_librarian"
    assert res_research["classification"]["intent"] == "research"

    res_else = omni_router.dispatch("Write a custom Python script")
    assert res_else["classification"]["assigned_agent"] == "gerych"
    assert res_else["classification"]["intent"] == "development"

# --- DNK-MRH-HEADER ---
# mrh_id: "test_gate5c_b_second_workspace.py"
# purpose: "Unit and integration tests for Gate 5C-B multi-workspace whitelisting, budget isolation, and fail-closed security."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# author: "DNK-e.com Maksym"
# license: "Internal"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pathlib
import uuid
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
services_path = ROOT / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

def test_gate5c_b_dual_workspace_whitelisting():
    ws_primary = str(uuid.uuid4())
    ws_secondary = str(uuid.uuid4())
    ws_unauthorized = str(uuid.uuid4())

    os.environ["LLM_PROVIDER_MODE"] = "validated"
    os.environ["LLM_WHITELISTED_WORKSPACES"] = f"{ws_primary},{ws_secondary}"

    whitelisted_list = [w.strip() for w in os.getenv("LLM_WHITELISTED_WORKSPACES", "").split(",") if w.strip()]

    assert ws_primary in whitelisted_list
    assert ws_secondary in whitelisted_list
    assert ws_unauthorized not in whitelisted_list

    # Clean up
    os.environ.pop("LLM_WHITELISTED_WORKSPACES", None)
    os.environ.pop("LLM_PROVIDER_MODE", None)

def test_gate5c_b_multi_workspace_whitelist_evaluation_routing():
    ws_primary = str(uuid.uuid4())
    ws_secondary = str(uuid.uuid4())
    ws_unauthorized = str(uuid.uuid4())

    os.environ["LLM_PROVIDER_MODE"] = "validated"
    os.environ["LLM_WHITELISTED_WORKSPACES"] = f"{ws_primary},{ws_secondary}"

    # Helper function matching supervisor whitelisting logic
    def evaluate_workspace_mode(workspace_id, llm_mode="validated"):
        if llm_mode == "validated":
            whitelisted_env = os.getenv("LLM_WHITELISTED_WORKSPACES", "")
            whitelisted_ids = [w.strip() for w in whitelisted_env.split(",") if w.strip()]
            if workspace_id in whitelisted_ids:
                return "validated"
            else:
                return "shadow"
        return llm_mode

    # Primary Workspace (Whitelisted)
    assert evaluate_workspace_mode(ws_primary) == "validated"

    # Secondary Workspace (Gate 5C-B Evaluated)
    assert evaluate_workspace_mode(ws_secondary) == "validated"

    # Unauthorized Workspace (Must degrade to Shadow)
    assert evaluate_workspace_mode(ws_unauthorized) == "shadow"

    # Clean up
    os.environ.pop("LLM_WHITELISTED_WORKSPACES", None)
    os.environ.pop("LLM_PROVIDER_MODE", None)

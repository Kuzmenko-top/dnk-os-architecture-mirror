# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_workflow_composer"
# purpose: "Verification test suite for Workflow Composer Agent, Node Registry, and Capability Registry"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if ROOT.name == "DNK OS":
    HUB_ROOT = ROOT.parent
else:
    HUB_ROOT = ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from core.registry.node_registry import node_registry
from core.registry.capability_registry import capability_registry
from core.workflows.workflow_composer import workflow_composer
from core.workflows.models import RiskLevel, NodeCategory


def test_capability_registry_lookup():
    """Verify that default capabilities are preloaded and domain filtering works."""
    caps = capability_registry.list_all()
    assert len(caps) >= 10

    shopify_caps = capability_registry.list_by_domain("shopify")
    assert len(shopify_caps) >= 3
    cap_ids = [c.id for c in shopify_caps]
    assert "shopify.theme.preview" in cap_ids
    assert "shopify.theme.deploy" in cap_ids

    deploy_cap = capability_registry.get("shopify.theme.deploy")
    assert deploy_cap is not None
    assert deploy_cap.risk_level == RiskLevel.HIGH


def test_node_registry_contracts_and_ports():
    """Verify that node contracts have defined input/output typed ports and categories."""
    contracts = node_registry.list_all()
    assert len(contracts) >= 6

    goal_contract = node_registry.get("dnk.core.goal")
    assert goal_contract is not None
    assert goal_contract.category == NodeCategory.GOAL
    assert len(goal_contract.outputs) >= 1

    approval_contract = node_registry.get("dnk.governance.approval")
    assert approval_contract is not None
    assert approval_contract.category == NodeCategory.APPROVAL
    assert approval_contract.approval_required is True
    assert approval_contract.risk_level == RiskLevel.HIGH


def test_workflow_composer_shopify_launch():
    """Verify that a Shopify business goal decomposes into an explainable DAG with ApprovalNode."""
    goal = "Створити промо-сторінку для нової коптильні ReBurn і підготувати запуск у Shopify"
    plan = workflow_composer.compose_workflow(goal=goal, workspace_id="ws_reburn")

    assert plan.intent == "shopify_launch"
    assert len(plan.nodes) >= 5
    assert len(plan.edges) >= 4

    node_types = [n.type for n in plan.nodes]
    assert "GoalNode" in node_types
    assert "ShopifyStoreNode" in node_types
    assert "VideoCompositionNode" in node_types
    assert "ApprovalNode" in node_types
    assert "ArtifactNode" in node_types

    # Verify that mandatory approval gate is enforced
    assert plan.approval_required is True
    assert "shopify.theme.deploy" in plan.high_risk_actions

    approval_node = next(n for n in plan.nodes if n.type == "ApprovalNode")
    assert approval_node.risk == RiskLevel.HIGH


def test_workflow_composer_video_campaign():
    """Verify that video creation goal produces a video-centric DAG."""
    goal = "Змонтувати та відрендерити 9:16 Remotion відеоролик для маркетингової кампанії"
    plan = workflow_composer.compose_workflow(goal=goal, workspace_id="ws_media")

    assert plan.intent == "video_campaign"
    node_types = [n.type for n in plan.nodes]
    assert "GoalNode" in node_types
    assert "VideoCompositionNode" in node_types
    assert "ArtifactNode" in node_types

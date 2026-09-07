# --- DNK-MRH-HEADER ---
# mrh_id: "core_workflows_workflow_composer"
# purpose: "Workflow Composer Agent (dnk_workflow_composer) for decomposing goals into validated TaskDNA DAG plans"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

import time
import uuid
from typing import Dict, List, Any, Optional
from core.workflows.models import (
    WorkflowPlan,
    WorkflowNodeInstance,
    WorkflowEdgeInstance,
    RiskLevel,
    NodeCategory,
    PortType
)
from core.registry.node_registry import node_registry
from core.registry.capability_registry import capability_registry


class WorkflowComposerAgent:
    """
    dnk_workflow_composer: Translates high-level natural-language business goals
    into explainable, validated, and executable workflow DAGs on the Canvas.
    Enforces mandatory ApprovalNodes before high-risk operations.
    """

    def compose_workflow(
        self,
        goal: str,
        workspace_id: str = "default-workspace",
        constraints: Optional[Dict[str, Any]] = None
    ) -> WorkflowPlan:
        intent = self._classify_intent(goal)
        workflow_id = f"wf_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"

        nodes: List[WorkflowNodeInstance] = []
        edges: List[WorkflowEdgeInstance] = []
        high_risk_actions: List[str] = []

        # 1. Root Goal Node (Always present)
        goal_node = WorkflowNodeInstance(
            id="goal_01",
            type="GoalNode",
            title=f"Goal: {goal[:40]}..." if len(goal) > 40 else f"Goal: {goal}",
            category=NodeCategory.GOAL,
            assigned_agent="dnk_mentor",
            state="completed",
            config={"goal": goal, "workspace_id": workspace_id},
            position={"x": 380.0, "y": 40.0},
            risk=RiskLevel.LOW
        )
        nodes.append(goal_node)

        # 2. Intent-based DAG Composition
        if intent == "shopify_launch":
            nodes.extend([
                WorkflowNodeInstance(
                    id="research_01",
                    type="TaskNode",
                    title="Market Brief & Persona Synthesis",
                    category=NodeCategory.RESEARCH,
                    assigned_agent="gerych_researcher",
                    state="running",
                    config={"capability": "research.market_brief"},
                    position={"x": 180.0, "y": 180.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="shopify_theme_01",
                    type="ShopifyStoreNode",
                    title="Liquid AST Theme Compilation",
                    category=NodeCategory.ECOMMERCE,
                    assigned_agent="dnk_shopify",
                    state="idle",
                    config={"capability": "shopify.theme.preview", "template": "reburn_v2"},
                    position={"x": 580.0, "y": 180.0},
                    risk=RiskLevel.MEDIUM
                ),
                WorkflowNodeInstance(
                    id="video_01",
                    type="VideoCompositionNode",
                    title="Remotion Ad Campaign Video",
                    category=NodeCategory.MEDIA,
                    assigned_agent="dnk_video_ai_creator",
                    state="idle",
                    config={"capability": "video.compose", "format": "9:16"},
                    position={"x": 180.0, "y": 340.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="approval_01",
                    type="ApprovalNode",
                    title="Release & Deploy Authorization",
                    category=NodeCategory.APPROVAL,
                    assigned_agent="dnk_mentor",
                    state="waiting_approval",
                    config={"action": "shopify.theme.deploy", "target": "production_store"},
                    position={"x": 580.0, "y": 340.0},
                    risk=RiskLevel.HIGH,
                    required_before=["shopify.theme.deploy"]
                ),
                WorkflowNodeInstance(
                    id="artifact_01",
                    type="ArtifactNode",
                    title="Live Landing & Video Package",
                    category=NodeCategory.ARTIFACT,
                    assigned_agent="gerych_builder",
                    state="idle",
                    config={"output_type": "shopify_release_bundle"},
                    position={"x": 380.0, "y": 500.0},
                    risk=RiskLevel.LOW
                )
            ])

            edges.extend([
                WorkflowEdgeInstance(id="e1", source="goal_01", target="research_01", edge_type=PortType.CONTROL),
                WorkflowEdgeInstance(id="e2", source="goal_01", target="shopify_theme_01", edge_type=PortType.CONTROL),
                WorkflowEdgeInstance(id="e3", source="research_01", target="video_01", edge_type=PortType.DATA, label="Market Brief"),
                WorkflowEdgeInstance(id="e4", source="shopify_theme_01", target="approval_01", edge_type=PortType.APPROVAL, label="Deploy Plan"),
                WorkflowEdgeInstance(id="e5", source="video_01", target="artifact_01", edge_type=PortType.DATA, label="Video MP4"),
                WorkflowEdgeInstance(id="e6", source="approval_01", target="artifact_01", edge_type=PortType.CONTROL, label="Approved Gate")
            ])
            high_risk_actions.append("shopify.theme.deploy")

        elif intent == "video_campaign":
            nodes.extend([
                WorkflowNodeInstance(
                    id="script_01",
                    type="TaskNode",
                    title="Script & Storyboard AI",
                    category=NodeCategory.TASK,
                    assigned_agent="dnk_video_ai_creator",
                    state="running",
                    config={"capability": "video.compose"},
                    position={"x": 280.0, "y": 180.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="video_01",
                    type="VideoCompositionNode",
                    title="Remotion Multi-Track Rendering",
                    category=NodeCategory.MEDIA,
                    assigned_agent="dnk_video_ai_creator",
                    state="idle",
                    config={"fps": 30, "resolution": "1080x1920"},
                    position={"x": 480.0, "y": 320.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="artifact_01",
                    type="ArtifactNode",
                    title="4K MP4 Video Ad Asset",
                    category=NodeCategory.ARTIFACT,
                    assigned_agent="gerych_builder",
                    state="idle",
                    config={"storage": "scones_vault"},
                    position={"x": 380.0, "y": 480.0},
                    risk=RiskLevel.LOW
                )
            ])
            edges.extend([
                WorkflowEdgeInstance(id="e1", source="goal_01", target="script_01", edge_type=PortType.CONTROL),
                WorkflowEdgeInstance(id="e2", source="script_01", target="video_01", edge_type=PortType.DATA),
                WorkflowEdgeInstance(id="e3", source="video_01", target="artifact_01", edge_type=PortType.DATA)
            ])

        else:
            # General TaskDNA Evolutionary DAG
            nodes.extend([
                WorkflowNodeInstance(
                    id="task_01",
                    type="TaskNode",
                    title="TaskDNA Subtask Analysis",
                    category=NodeCategory.TASK,
                    assigned_agent="dnk_mentor",
                    state="running",
                    config={"capability": "taskdna.decompose_goal"},
                    position={"x": 280.0, "y": 180.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="agent_01",
                    type="AgentNode",
                    title="Fullstack Builder Execution",
                    category=NodeCategory.AGENT,
                    assigned_agent="dnk_dev_fullstack",
                    state="idle",
                    config={"capability": "code.generate"},
                    position={"x": 480.0, "y": 320.0},
                    risk=RiskLevel.LOW
                ),
                WorkflowNodeInstance(
                    id="artifact_01",
                    type="ArtifactNode",
                    title="Verified Code Pull Request",
                    category=NodeCategory.ARTIFACT,
                    assigned_agent="gerych_auditor",
                    state="idle",
                    config={"output_type": "git_pr"},
                    position={"x": 380.0, "y": 480.0},
                    risk=RiskLevel.LOW
                )
            ])
            edges.extend([
                WorkflowEdgeInstance(id="e1", source="goal_01", target="task_01", edge_type=PortType.CONTROL),
                WorkflowEdgeInstance(id="e2", source="task_01", target="agent_01", edge_type=PortType.CONTROL),
                WorkflowEdgeInstance(id="e3", source="agent_01", target="artifact_01", edge_type=PortType.DATA)
            ])

        return WorkflowPlan(
            workflow_id=workflow_id,
            title=f"Workflow: {intent.replace('_', ' ').title()}",
            intent=intent,
            confidence=0.94,
            user_goal=goal,
            nodes=nodes,
            edges=edges,
            approval_required=len(high_risk_actions) > 0,
            high_risk_actions=high_risk_actions,
            trace_id=trace_id,
            created_at=str(time.time())
        )

    def _classify_intent(self, goal: str) -> str:
        g = goal.lower()
        if any(term in g for term in ["shopify", "магазин", "товар", "лендінг", "reburn", "коптильн", "ecom", "store"]):
            return "shopify_launch"
        elif any(term in g for term in ["відео", "video", "remotion", "ролик", "монтаж", "autocut", "ad"]):
            return "video_campaign"
        elif any(term in g for term in ["код", "api", "рефактор", "тест", "feature", "router"]):
            return "code_feature"
        return "general_taskdna"


workflow_composer = WorkflowComposerAgent()

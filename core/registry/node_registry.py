# --- DNK-MRH-HEADER ---
# mrh_id: "core_registry_node_registry"
# purpose: "Node Registry managing contracts, typed ports, capabilities, and risk profiles for all canvas nodes"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional
from core.workflows.models import (
    NodeContract,
    NodeCategory,
    PortDefinition,
    PortType,
    RiskLevel
)


class NodeRegistry:
    """
    Single Source of Truth for Node Contracts in DNK OS.
    Enforces typed I/O ports, capabilities, risk levels, and permission boundaries.
    """

    def __init__(self):
        self._contracts: Dict[str, NodeContract] = {}
        self._register_default_contracts()

    def register(self, contract: NodeContract) -> None:
        self._contracts[contract.id] = contract

    def get(self, contract_id: str) -> Optional[NodeContract]:
        return self._contracts.get(contract_id)

    def list_all(self) -> List[NodeContract]:
        return list(self._contracts.values())

    def _register_default_contracts(self) -> None:
        contracts = [
            # 1. Goal Node
            NodeContract(
                id="dnk.core.goal",
                title="Goal Intake Node",
                category=NodeCategory.GOAL,
                icon="target",
                ui_component="GoalNode",
                executor="core.workflows.executors.goal_executor",
                inputs=[],
                outputs=[
                    PortDefinition(name="taskdna_dag", data_type="taskdna.dag", port_type=PortType.CONTROL, description="Decomposed subtask tree"),
                    PortDefinition(name="goal_context", data_type="core.context", port_type=PortType.DATA, description="Structured goal context"),
                ],
                capabilities=["taskdna.decompose_goal"],
                permissions=["workspace:read"],
                risk_level=RiskLevel.LOW,
                description="Receives high-level user goal, triggers TaskDNA decomposition, and initiates workflow."
            ),
            # 2. Task Node
            NodeContract(
                id="dnk.core.task",
                title="Executable Task",
                category=NodeCategory.TASK,
                icon="check-square",
                ui_component="TaskNode",
                executor="core.workflows.executors.task_executor",
                inputs=[
                    PortDefinition(name="input_data", data_type="any", port_type=PortType.DATA, description="Upstream data payload"),
                    PortDefinition(name="trigger", data_type="control.signal", port_type=PortType.CONTROL, description="Execution trigger"),
                ],
                outputs=[
                    PortDefinition(name="result", data_type="any", port_type=PortType.DATA, description="Task execution outcome"),
                    PortDefinition(name="status", data_type="task.status", port_type=PortType.CONTROL, description="State transition signal"),
                ],
                capabilities=["a2a.delegate_task", "research.market_brief"],
                permissions=["workspace:write"],
                risk_level=RiskLevel.LOW,
                description="Executes a discrete subtask assigned to a specialized swarm worker."
            ),
            # 3. Agent Node
            NodeContract(
                id="dnk.core.agent",
                title="Swarm Agent",
                category=NodeCategory.AGENT,
                icon="bot",
                ui_component="AgentNode",
                executor="core.workflows.executors.agent_executor",
                inputs=[
                    PortDefinition(name="task_spec", data_type="taskdna.task", port_type=PortType.DATA, description="Task specification"),
                ],
                outputs=[
                    PortDefinition(name="thought_stream", data_type="agent.stream", port_type=PortType.DATA, description="Real-time A2A logs"),
                    PortDefinition(name="artifact_out", data_type="artifact.ref", port_type=PortType.DATA, description="Produced artifact"),
                ],
                capabilities=["a2a.delegate_task"],
                permissions=["agent:execute"],
                risk_level=RiskLevel.LOW,
                description="Monitors live reasoning, leases, and telemetry of a Swarm domain agent."
            ),
            # 4. Approval Node (Governance Gate)
            NodeContract(
                id="dnk.governance.approval",
                title="Human Approval Gate",
                category=NodeCategory.APPROVAL,
                icon="shield-alert",
                ui_component="ApprovalNode",
                executor="core.workflows.executors.approval_executor",
                inputs=[
                    PortDefinition(name="plan_proposal", data_type="workflow.plan", port_type=PortType.APPROVAL, description="Plan or action requiring verification"),
                ],
                outputs=[
                    PortDefinition(name="approved_signal", data_type="control.signal", port_type=PortType.CONTROL, description="Authorized signal to continue execution"),
                ],
                capabilities=["governance.request_approval"],
                permissions=["governance:approve"],
                risk_level=RiskLevel.HIGH,
                approval_required=True,
                description="Enforces explicit human approval before allowing external deployments or destructive side-effects."
            ),
            # 5. Artifact Node
            NodeContract(
                id="dnk.core.artifact",
                title="Deliverable Artifact",
                category=NodeCategory.ARTIFACT,
                icon="file-text",
                ui_component="ArtifactNode",
                executor="core.workflows.executors.artifact_executor",
                inputs=[
                    PortDefinition(name="content", data_type="any", port_type=PortType.DATA, description="Generated deliverable content"),
                ],
                outputs=[
                    PortDefinition(name="artifact_uri", data_type="artifact.uri", port_type=PortType.REFERENCE, description="Immutable URI in SCONES vault"),
                ],
                capabilities=["memory.store_evidence"],
                permissions=["workspace:write"],
                risk_level=RiskLevel.LOW,
                description="Encapsulates output deliverables such as landing pages, videos, pull requests, and audit reports."
            ),
            # 6. Shopify Store / Theme Node
            NodeContract(
                id="dnk.shopify.theme",
                title="Shopify Theme & Store",
                category=NodeCategory.ECOMMERCE,
                icon="shopping-bag",
                ui_component="ShopifyStoreNode",
                executor="core.workflows.executors.shopify_executor",
                inputs=[
                    PortDefinition(name="store_ref", data_type="shopify.store_ref", port_type=PortType.DATA, description="Connected Shopify store reference"),
                    PortDefinition(name="market_brief", data_type="research.brief", port_type=PortType.DATA, required=False, description="Design parameters"),
                ],
                outputs=[
                    PortDefinition(name="liquid_ast", data_type="shopify.theme_ast", port_type=PortType.DATA, description="Compiled Liquid AST blocks"),
                    PortDefinition(name="preview_url", data_type="url.preview", port_type=PortType.REFERENCE, description="Sandbox preview URL"),
                ],
                capabilities=["shopify.theme.preview", "shopify.products.sync", "shopify.theme.deploy"],
                permissions=["shopify:read_themes", "shopify:write_themes"],
                risk_level=RiskLevel.MEDIUM,
                description="Manages Shopify store synchronization, Liquid AST compilation, and theme releases."
            ),
            # 7. Video Composition Node
            NodeContract(
                id="dnk.media.video",
                title="Remotion Video Studio",
                category=NodeCategory.MEDIA,
                icon="film",
                ui_component="VideoCompositionNode",
                executor="core.workflows.executors.video_executor",
                inputs=[
                    PortDefinition(name="ad_copy", data_type="text.copy", port_type=PortType.DATA, description="Marketing script and headlines"),
                    PortDefinition(name="footage_ref", data_type="media.footage", port_type=PortType.DATA, required=False, description="Video assets"),
                ],
                outputs=[
                    PortDefinition(name="remotion_ast", data_type="video.remotion_ast", port_type=PortType.DATA, description="Multi-track Remotion composition"),
                    PortDefinition(name="video_mp4", data_type="media.mp4", port_type=PortType.DATA, description="Rendered video file"),
                ],
                capabilities=["video.compose", "video.render"],
                permissions=["media:render"],
                risk_level=RiskLevel.LOW,
                description="Synthesizes dynamic multi-track kinetic video ads via Remotion engine and Gemini 3.5."
            ),
        ]
        for c in contracts:
            self.register(c)


node_registry = NodeRegistry()

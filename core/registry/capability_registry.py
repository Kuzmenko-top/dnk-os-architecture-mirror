# --- DNK-MRH-HEADER ---
# mrh_id: "core_registry_capability_registry"
# purpose: "SSOT Capability Registry declaring all atomic executable operations and risk levels in DNK OS"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional
from core.workflows.models import CapabilityDefinition, RiskLevel


class CapabilityRegistry:
    """
    Single Source of Truth for system capabilities available to the
    Workflow Composer Agent and Swarm Orchestrator.
    """

    def __init__(self):
        self._capabilities: Dict[str, CapabilityDefinition] = {}
        self._register_default_capabilities()

    def register(self, cap: CapabilityDefinition) -> None:
        self._capabilities[cap.id] = cap

    def get(self, cap_id: str) -> Optional[CapabilityDefinition]:
        return self._capabilities.get(cap_id)

    def list_all(self) -> List[CapabilityDefinition]:
        return list(self._capabilities.values())

    def list_by_domain(self, domain: str) -> List[CapabilityDefinition]:
        return [c for c in self._capabilities.values() if c.domain == domain]

    def _register_default_capabilities(self) -> None:
        defaults = [
            # Core & TaskDNA
            CapabilityDefinition(
                id="taskdna.decompose_goal",
                name="Decompose Goal to DAG",
                domain="core",
                node_type="GoalNode",
                assigned_agent="dnk_mentor",
                risk_level=RiskLevel.LOW,
                description="Analyzes high-level natural language goal and produces an evolutionary task DAG."
            ),
            CapabilityDefinition(
                id="a2a.delegate_task",
                name="Delegate Task via A2A Mesh",
                domain="core",
                node_type="TaskNode",
                assigned_agent="gerych_builder",
                risk_level=RiskLevel.LOW,
                description="Dispatches task execution to specialized domain agent."
            ),
            # SCONES Memory
            CapabilityDefinition(
                id="memory.search_hybrid",
                name="SCONES Hybrid Search",
                domain="memory",
                node_type="MemoryNode",
                assigned_agent="dnk_mentor",
                risk_level=RiskLevel.LOW,
                description="Queries vector and keyword indices for matching templates, skills, and past solutions."
            ),
            CapabilityDefinition(
                id="memory.store_evidence",
                name="Store Execution Evidence",
                domain="memory",
                node_type="ArtifactNode",
                assigned_agent="gerych_auditor",
                risk_level=RiskLevel.LOW,
                description="Persists cryptographic execution artifacts into SCONES Memory Vault."
            ),
            # Research & Market
            CapabilityDefinition(
                id="research.market_brief",
                name="Generate Market & Competitor Brief",
                domain="research",
                node_type="TaskNode",
                assigned_agent="gerych_researcher",
                risk_level=RiskLevel.LOW,
                description="Synthesizes competitor patterns and generates customer persona briefs."
            ),
            # Shopify E-Commerce
            CapabilityDefinition(
                id="shopify.theme.preview",
                name="Preview Shopify Theme / Liquid AST",
                domain="shopify",
                node_type="ShopifyThemeNode",
                assigned_agent="dnk_shopify",
                risk_level=RiskLevel.LOW,
                description="Assembles and previews Liquid AST sections with Open Design tokens."
            ),
            CapabilityDefinition(
                id="shopify.products.sync",
                name="Sync Product Catalog",
                domain="shopify",
                node_type="ShopifyStoreNode",
                assigned_agent="dnk_shopify",
                risk_level=RiskLevel.MEDIUM,
                description="Synchronizes store products, inventory, and variants."
            ),
            CapabilityDefinition(
                id="shopify.theme.deploy",
                name="Deploy Theme to Live Store",
                domain="shopify",
                node_type="DeploymentNode",
                assigned_agent="dnk_shopify",
                risk_level=RiskLevel.HIGH,
                description="Pushes compiled theme assets directly to live merchant Shopify store."
            ),
            # Video & Media
            CapabilityDefinition(
                id="video.compose",
                name="Synthesize Remotion Video Timeline",
                domain="video",
                node_type="VideoCompositionNode",
                assigned_agent="dnk_video_ai_creator",
                risk_level=RiskLevel.LOW,
                description="Generates multi-track Remotion composition AST for ad campaigns."
            ),
            CapabilityDefinition(
                id="video.render",
                name="Render MP4 Video Campaign",
                domain="video",
                node_type="VideoCompositionNode",
                assigned_agent="dnk_video_ai_creator",
                risk_level=RiskLevel.MEDIUM,
                description="Executes Remotion Chromium renderer to produce high-bitrate MP4."
            ),
            # Code & Governance
            CapabilityDefinition(
                id="code.generate",
                name="Generate Clean Code Artifact",
                domain="code",
                node_type="CodeArtifactNode",
                assigned_agent="dnk_dev_fullstack",
                risk_level=RiskLevel.LOW,
                description="Produces React components, FastAPI routers, or schemas."
            ),
            CapabilityDefinition(
                id="governance.request_approval",
                name="Request User Explicit Approval",
                domain="governance",
                node_type="ApprovalNode",
                assigned_agent="dnk_mentor",
                risk_level=RiskLevel.LOW,
                description="Halts automated pipeline before side-effect actions until human approves."
            ),
            # Patent Shield
            CapabilityDefinition(
                id="patent.assess_risk",
                name="Clean-Room IP & Patent Risk Audit",
                domain="patent",
                node_type="PatentRiskNode",
                assigned_agent="gerych_auditor",
                risk_level=RiskLevel.LOW,
                description="Evaluates codebase against patent collision and donor license obligations."
            ),
        ]
        for cap in defaults:
            self.register(cap)


capability_registry = CapabilityRegistry()

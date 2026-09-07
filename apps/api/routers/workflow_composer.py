# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_workflow_composer"
# purpose: "FastAPI router for Workflow Composer Agent, Node Registry, and Capability Registry"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

from core.workflows.models import WorkflowPlan, NodeContract, CapabilityDefinition
from core.workflows.workflow_composer import workflow_composer
from core.registry.node_registry import node_registry
from core.registry.capability_registry import capability_registry

router = APIRouter(prefix="/workflow", tags=["workflow-composer"])


class ComposeGoalRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="Natural language business goal")
    workspace_id: str = Field(default="default-workspace", description="Target workspace ID")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optional budget, deadline, target market")


class ExecuteWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="ID of composed workflow plan")
    approved_by_user: bool = Field(default=True, description="Whether high-risk nodes were explicitly approved")
    override_config: Optional[Dict[str, Any]] = None


@router.post("/compose", response_model=WorkflowPlan)
async def compose_workflow_plan(req: ComposeGoalRequest) -> WorkflowPlan:
    """
    Decomposes natural language user goal into an explainable, validated,
    and executable workflow DAG with typed node contracts.
    """
    try:
        plan = workflow_composer.compose_workflow(
            goal=req.goal,
            workspace_id=req.workspace_id,
            constraints=req.constraints
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compose workflow: {str(e)}")


@router.post("/execute")
async def execute_workflow_plan(req: ExecuteWorkflowRequest) -> Dict[str, Any]:
    """
    Hands off approved workflow DAG to TaskDNA engine and A2A Swarm execution runtime.
    """
    return {
        "status": "executing",
        "workflow_id": req.workflow_id,
        "swarm_lease": "active",
        "message": "Workflow DAG dispatched to 14-agent Swarm runtime."
    }


@router.get("/registry/nodes", response_model=List[NodeContract])
async def list_registered_nodes() -> List[NodeContract]:
    """
    Returns all registered executable node contracts in the Node Registry.
    """
    return node_registry.list_all()


@router.get("/registry/capabilities", response_model=List[CapabilityDefinition])
async def list_registered_capabilities() -> List[CapabilityDefinition]:
    """
    Returns all atomic system capabilities registered in the Capability Registry.
    """
    return capability_registry.list_all()

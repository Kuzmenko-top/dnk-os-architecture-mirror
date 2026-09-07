# --- DNK-MRH-HEADER ---
# mrh_id: "core_supervisor_shopify_api"
# purpose: "FastAPI REST Router for Shopify Supervisor Ingress, Decision, Approval Binding & Simulated Write Plan (DNK-SHOPIFY-PILOT-003)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.plugins.plugin_installer import PluginInstaller
from core.supervisor.shopify_sync_supervisor import (
    ShopifySyncSupervisor,
    InvalidShopifyProductPayloadError,
    ShopifyPilotPermissionDeniedError,
    ShopifyPilotWriteForbiddenError,
    UntrustedPluginError,
    CustomerDataForbiddenError,
    DryRunMutationDetectedError,
    PluginQuarantinedError,
    InvalidApprovalPayloadError,
    ApprovalPermissionDeniedError,
    ApprovalAlreadyConsumedError,
    ApprovalArgumentsMismatchError,
    DuplicateApprovalRequestError,
    InvalidDiffBindingError,
    SimulatedPlanMutationAttemptError,
)

router = APIRouter(prefix="/shopify", tags=["shopify-supervisor"])

# Module-level supervisor instance factory
_global_installer = PluginInstaller()
_global_supervisor = ShopifySyncSupervisor(installer=_global_installer)


def get_shopify_supervisor(request: Request) -> ShopifySyncSupervisor:
    if hasattr(request.app.state, "supervisor") and request.app.state.supervisor is not None:
        return request.app.state.supervisor
    return _global_supervisor


class ProductDiffRequest(BaseModel):
    plugin_id: str = "dnk-shopify-sync"
    version: str = "0.1.0"
    payload: Dict[str, Any]
    existing_state: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class DecisionRequest(BaseModel):
    plugin_id: str = "dnk-shopify-sync"
    version: str = "0.1.0"
    payload: Dict[str, Any]
    existing_state: Optional[Dict[str, Any]] = None
    requested_permissions: Optional[List[str]] = Field(default_factory=lambda: ["products.read"])
    correlation_id: Optional[str] = None
    custom_idempotency_key: Optional[str] = None


class ApprovalPreviewRequest(BaseModel):
    plugin_id: str = "dnk-shopify-sync"
    version: str = "0.1.0"
    approval_payload: Dict[str, Any]
    payload: Optional[Dict[str, Any]] = None
    existing_state: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class SimulatedWritePlanRequest(BaseModel):
    approval_id: str
    plugin_id: str = "dnk-shopify-sync"
    version: str = "0.1.0"
    approval_payload: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


@router.post("/products/diff")
def post_product_diff(
    req: ProductDiffRequest,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    actor_id: str = Header(default="supervisor", alias="X-Actor-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    try:
        res = supervisor.reconcile_single_event(
            workspace_id=workspace_id,
            plugin_id=req.plugin_id,
            version=req.version,
            payload=req.payload,
            existing_state=req.existing_state,
            actor_id=actor_id,
            correlation_id=req.correlation_id,
        )
        return res
    except InvalidShopifyProductPayloadError as e:
        return JSONResponse(status_code=400, content={"error": e.error_type, "message": str(e)})
    except (ShopifyPilotPermissionDeniedError, UntrustedPluginError) as e:
        return JSONResponse(status_code=403, content={"error": e.error_type, "message": str(e)})
    except ShopifyPilotWriteForbiddenError as e:
        return JSONResponse(status_code=403, content={"error": "SHOPIFY_WRITE_FORBIDDEN", "message": str(e)})
    except (CustomerDataForbiddenError, DryRunMutationDetectedError) as e:
        return JSONResponse(status_code=422, content={"error": e.error_type, "message": str(e)})
    except PluginQuarantinedError as e:
        return JSONResponse(status_code=423, content={"error": e.error_type, "message": str(e)})


@router.post("/products/decision")
def post_supervisor_decision(
    req: DecisionRequest,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    actor_id: str = Header(default="supervisor", alias="X-Actor-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    try:
        res = supervisor.evaluate_supervisor_decision(
            workspace_id=workspace_id,
            plugin_id=req.plugin_id,
            version=req.version,
            payload=req.payload,
            existing_state=req.existing_state,
            requested_permissions=req.requested_permissions,
            actor_id=actor_id,
            correlation_id=req.correlation_id,
            custom_idempotency_key=req.custom_idempotency_key,
        )
        return res
    except InvalidShopifyProductPayloadError as e:
        return JSONResponse(status_code=400, content={"error": e.error_type, "message": str(e)})
    except (ApprovalPermissionDeniedError, ShopifyPilotPermissionDeniedError, UntrustedPluginError) as e:
        return JSONResponse(status_code=403, content={"error": e.error_type, "message": str(e)})
    except ShopifyPilotWriteForbiddenError as e:
        return JSONResponse(status_code=403, content={"error": "SHOPIFY_WRITE_FORBIDDEN", "message": str(e)})
    except CustomerDataForbiddenError as e:
        return JSONResponse(status_code=422, content={"error": e.error_type, "message": str(e)})
    except PluginQuarantinedError as e:
        return JSONResponse(status_code=423, content={"error": e.error_type, "message": str(e)})


@router.post("/products/approval-preview")
def post_approval_preview(
    req: ApprovalPreviewRequest,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    actor_id: str = Header(default="supervisor", alias="X-Actor-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    try:
        res = supervisor.create_approval_preview(
            workspace_id=workspace_id,
            plugin_id=req.plugin_id,
            version=req.version,
            approval_payload=req.approval_payload,
            payload=req.payload,
            existing_state=req.existing_state,
            actor_id=actor_id,
            correlation_id=req.correlation_id,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=res)
    except InvalidApprovalPayloadError as e:
        return JSONResponse(status_code=400, content={"error": e.error_type, "message": str(e)})
    except (ApprovalPermissionDeniedError, UntrustedPluginError) as e:
        return JSONResponse(status_code=403, content={"error": e.error_type, "message": str(e)})
    except ShopifyPilotWriteForbiddenError as e:
        return JSONResponse(status_code=403, content={"error": "SHOPIFY_WRITE_FORBIDDEN", "message": str(e)})
    except (DuplicateApprovalRequestError, ApprovalAlreadyConsumedError) as e:
        return JSONResponse(status_code=409, content={"error": e.error_type, "message": str(e)})
    except (CustomerDataForbiddenError, InvalidDiffBindingError) as e:
        return JSONResponse(status_code=422, content={"error": e.error_type, "message": str(e)})
    except PluginQuarantinedError as e:
        return JSONResponse(status_code=423, content={"error": e.error_type, "message": str(e)})


@router.post("/products/simulated-write-plan")
def post_simulated_write_plan(
    req: SimulatedWritePlanRequest,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    actor_id: str = Header(default="supervisor", alias="X-Actor-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    try:
        res = supervisor.generate_simulated_write_plan(
            approval_id=req.approval_id,
            workspace_id=workspace_id,
            plugin_id=req.plugin_id,
            version=req.version,
            approval_payload=req.approval_payload,
            actor_id=actor_id,
            correlation_id=req.correlation_id,
        )
        return res
    except InvalidApprovalPayloadError as e:
        return JSONResponse(status_code=400, content={"error": e.error_type, "message": str(e)})
    except (ApprovalAlreadyConsumedError, ApprovalArgumentsMismatchError) as e:
        return JSONResponse(status_code=409, content={"error": e.error_type, "message": str(e)})
    except (SimulatedPlanMutationAttemptError, InvalidDiffBindingError) as e:
        return JSONResponse(status_code=422, content={"error": e.error_type, "message": str(e)})


@router.get("/approvals/{approval_id}")
def get_approval(
    approval_id: str,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    try:
        appr = supervisor.get_approval_by_id(approval_id, workspace_id)
        return appr
    except InvalidApprovalPayloadError as e:
        return JSONResponse(status_code=404, content={"error": "APPROVAL_NOT_FOUND", "message": str(e)})
    except InvalidDiffBindingError as e:
        return JSONResponse(status_code=403, content={"error": "WORKSPACE_ACCESS_DENIED", "message": str(e)})


@router.get("/reconciliation/{correlation_id}")
def get_reconciliation(
    correlation_id: str,
    workspace_id: str = Header(default="sandbox", alias="X-Workspace-ID"),
    supervisor: ShopifySyncSupervisor = Depends(get_shopify_supervisor),
):
    matched_events = []
    for evt in supervisor.audit_logger.logs:
        if isinstance(evt, dict):
            ws = evt.get("workspace_id") or evt.get("tenant_id")
            details = evt.get("details", {})
            if ws == workspace_id and details.get("correlation_id") == correlation_id:
                matched_events.append(evt)
    return {
        "correlation_id": correlation_id,
        "workspace_id": workspace_id,
        "reconciled": len(matched_events) > 0,
        "matched_events": matched_events,
        "history": matched_events,
        "count": len(matched_events),
    }

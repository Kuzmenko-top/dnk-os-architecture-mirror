# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_artifact"
# purpose: "Artifact router endpoints for GET and PUT with Security Gate enforcement"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID, uuid4
from typing import Dict, Any, Optional

from apps.api.database import get_artifact, set_artifact
from core.decorators.security_gate import get_security_gate_service, SecurityGateDenied

router = APIRouter()

class ArtifactPayload(BaseModel):
    content: str
    run_id: Optional[str] = None

@router.get("/artifact/{canvas_id}")
async def fetch_artifact(canvas_id: str):
    art = get_artifact(canvas_id)
    if not art:
        # Return a default empty artifact instead of 404 so UI doesn't crash on clean canvases
        return {"canvas_id": canvas_id, "content": ""}
    return art

@router.put("/artifact/{canvas_id}")
async def update_artifact(canvas_id: str, payload: ArtifactPayload):
    content_str = payload.content
    run_id_str = payload.run_id or str(uuid4())
    
    # Risky Action: Update Artifact -> MUST EVALUATE THROUGH SECURITY GATE
    gate = get_security_gate_service()
    try:
        run_id_uuid = UUID(run_id_str)
    except ValueError:
        run_id_uuid = uuid4()

    decision = gate.evaluate_policy(
        run_id=run_id_uuid,
        action="artifact.update",
        arguments={"canvas_id": canvas_id, "content": content_str},
        context={}
    )
    
    if not decision.allowed:
        # Throw SecurityGateDenied so decorators/handlers pick it up as requested in spec
        raise SecurityGateDenied(f"Security Gate Denied: {decision.reason}")

    artifact = {
        "canvas_id": canvas_id,
        "content": content_str
    }
    set_artifact(canvas_id, artifact)
    return artifact

# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/artifacts.py"
# purpose: "FastAPI router for Artifact Server publishing, versioning, annotation, and MCP interaction"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any

from apps.api.schemas.artifacts import (
    ArtifactCreateRequest,
    ArtifactVersionCreateRequest,
    CommentCreateRequest,
    ArtifactResponse,
)
from core.adapters.dnk_artifact_server_adapter import DNKArtifactServerAdapter

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

_adapter = DNKArtifactServerAdapter()


def get_artifact_adapter() -> DNKArtifactServerAdapter:
    return _adapter


@router.post("", response_model=ArtifactResponse)
def create_artifact(request: ArtifactCreateRequest):
    try:
        created = _adapter.create_artifact(
            title=request.title,
            content=request.content,
            artifact_type=request.artifact_type,
            creator=request.creator,
            metadata=request.metadata,
        )
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[Dict[str, Any]])
def list_artifacts(
    artifact_type: Optional[str] = Query(None),
    creator: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    return _adapter.list_artifacts(
        artifact_type=artifact_type,
        creator=creator,
        limit=limit,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: str, version: Optional[int] = Query(None)):
    try:
        return _adapter.get_artifact(artifact_id=artifact_id, version=version)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{artifact_id}/versions", response_model=Dict[str, Any])
def create_artifact_version(artifact_id: str, request: ArtifactVersionCreateRequest):
    try:
        return _adapter.create_version(
            artifact_id=artifact_id,
            content=request.content,
            author=request.author,
            change_summary=request.change_summary,
            metadata=request.metadata,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{artifact_id}/comments", response_model=Dict[str, Any])
def add_artifact_comment(artifact_id: str, request: CommentCreateRequest):
    try:
        return _adapter.add_comment(
            artifact_id=artifact_id,
            version=request.version,
            author=request.author,
            content=request.content,
            line_number=request.line_number,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/status")
def artifacts_health():
    return {
        "status": "healthy",
        "service": "dnk_artifact_server",
        "version": "1.0.0",
        "mode": "clean_room_mit",
    }

# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/schemas/artifacts.py"
# purpose: "Pydantic v2 validation contracts for Artifact Publishing, Versioning, and Review"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ArtifactCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the artifact")
    content: str = Field(..., min_length=1, description="Raw content of the artifact")
    artifact_type: str = Field("markdown", description="Type: markdown, html, svg, json, code, diagram, video")
    creator: str = Field("gerych_prime", description="Identifier of the creating agent or user")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata tags")


class ArtifactVersionCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Updated content for the new revision")
    author: str = Field("gerych_prime", description="Author of this revision")
    change_summary: str = Field("Revision update", description="Summary of changes in this revision")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Version metadata")


class CommentCreateRequest(BaseModel):
    version: int = Field(..., ge=1, description="Target version number")
    author: str = Field(..., min_length=1, description="Comment author")
    content: str = Field(..., min_length=1, description="Comment text")
    line_number: Optional[int] = Field(None, ge=1, description="Optional target line number")


class ArtifactResponse(BaseModel):
    artifact_id: str
    title: str
    artifact_type: str
    creator: str
    created_at: str
    updated_at: str
    current_version: int
    requested_version: Optional[int] = None
    content: Optional[str] = None
    change_summary: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None
    comments: Optional[List[Dict[str, Any]]] = None
    total_versions: Optional[int] = None

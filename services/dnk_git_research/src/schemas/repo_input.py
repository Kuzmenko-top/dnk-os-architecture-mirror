# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_git_research/src/schemas/repo_input.py"
# purpose: "Pydantic validator and models for dnk_git_research input repository metadata."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-07-12"
# --- END DNK-MRH-HEADER ---

"""
repo_input.py — Repo Input Schema Validation
Language Policy: Technical file in English, logging in English.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any

class RepoInput(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: str = ""
    language: str = ""
    topics: List[str] = Field(default_factory=list)
    readme_text: str = ""
    deep_context: Dict[str, Any] = Field(default_factory=dict)
    loc_metrics: Dict[str, Any] = Field(default_factory=dict)
    configs: Dict[str, Any] = Field(default_factory=dict)
    entrypoints: List[Any] = Field(default_factory=list)
    tree_text: str = ""

    @model_validator(mode="before")
    @classmethod
    def require_identifier_and_validate_full_name(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")
        
        name = data.get("name")
        full_name = data.get("full_name")
        
        if not name and not full_name:
            raise ValueError("Either 'name' or 'full_name' must be provided and cannot be empty")
            
        if full_name is not None:
            if not isinstance(full_name, str):
                raise ValueError("full_name must be a string")
            if full_name.count("/") != 1:
                raise ValueError("full_name must be in 'owner/name' format with exactly one '/'")
                
        return data

def validate_repo_input(repo: dict) -> dict:
    """Validates the input dictionary using the RepoInput Pydantic model and returns serialized dictionary."""
    model = RepoInput(**repo)
    return model.model_dump()

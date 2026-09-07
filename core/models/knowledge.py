# --- DNK-MRH-HEADER ---
# mrh_id: "core_models_knowledge"
# purpose: "Domain models for knowledge base and vector documents (KnowledgeDocument, KnowledgeQueryResult)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Dict, Any, List

class KnowledgeDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: int
    updated_at: int

class KnowledgeQueryResult(BaseModel):
    doc_id: UUID
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- DNK-MRH-HEADER ---
# mrh_id: "core_stores_knowledge_store"
# purpose: "Abstract interface (Port) defining all operations on vector knowledge store"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import List, Optional, Union
from uuid import UUID

from core.models.knowledge import KnowledgeDocument, KnowledgeQueryResult

class KnowledgeStore(ABC):
    @abstractmethod
    def upsert_document(self, doc: KnowledgeDocument) -> None:
        pass

    @abstractmethod
    def search_similar(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> List[KnowledgeQueryResult]:
        pass

    @abstractmethod
    def delete_document(self, doc_id: UUID) -> None:
        pass

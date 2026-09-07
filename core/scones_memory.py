# --- DNK-MRH-HEADER ---
# mrh_id: "core/scones_memory.py"
# purpose: "SCONES long-term cognitive memory with pgvector HNSW dual-write, semantic search, error solution distillation, and context compaction"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional

try:
    from core.model_proxy.self_healing_router import SelfHealingModelRouter
except ImportError:
    try:
        from core.model_proxy.self_healing_router import SelfHealingModelRouter
    except ImportError:
        class SelfHealingModelRouter:  # type: ignore
            def resolve_model_with_fallback(self, model: str, error_code: int = 0):
                if error_code != 0:
                    return {
                        "status": "healed",
                        "active_model": "mistralai/codestral-22b-instruct",
                        "active_provider": "nvidia_nim",
                        "reason": f"Auto-healed from error {error_code}"
                    }
                return {"status": "ok", "active_model": model, "active_provider": "vertex"}

try:
    from core.playbooks.scripts.sanitize_context_bloat import sanitize_text
except ImportError:
    try:
        from core.playbooks.scripts.sanitize_context_bloat import sanitize_text
    except ImportError:
        def sanitize_text(text: str, max_lines: int = 50) -> str:
            lines = text.splitlines()
            if len(lines) <= max_lines:
                return text
            half = max_lines // 2
            return "\n".join(lines[:half] + ["\n[... TRUNCATED DUE TO CONTEXT BLOAT ...]\n"] + lines[-half:])

# pgvector store import with graceful fallback
try:
    from core.memory.pgvector_store import (
        PgVectorStore,
        generate_embedding,
        cosine_similarity,
        VECTOR_DIMENSION
    )
except ImportError:
    try:
        from core.memory.pgvector_store import (
            PgVectorStore,
            generate_embedding,
            cosine_similarity,
            VECTOR_DIMENSION
        )
    except ImportError:
        PgVectorStore = None  # type: ignore
        def generate_embedding(text: str, dim: int = 768) -> List[float]:
            return [0.0] * dim
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            return 0.0
        VECTOR_DIMENSION = 768

logger = logging.getLogger("SCONESMemoryEngine")


class SCONESMemoryEngine:
    """
    SCONES (Shared Cognitive Outcomes & Networked Extraction Storage) Memory Engine v2.0.
    
    Features:
    - Dual-Write: PostgreSQL + pgvector (HNSW) with instant local JSON fallback
    - Semantic Search: High-speed cosine similarity with 500ms timeout guard
    - Error Solution Distillation: Storage & vector search for fast self-healing
    - Metadata Isolation: Multi-tenant and workspace boundaries
    - Multi-model routing fallbacks & log compaction
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_pgvector: bool = True,
        pgvector_store: Optional[Any] = None,
        enable_expectation_hook: bool = True,
        strict_expectation: Optional[bool] = None,
        expectation_validator: Optional[Any] = None,
    ):
        if storage_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.storage_path = os.path.join(base_dir, "tests", "scones_storage.json")
        else:
            self.storage_path = storage_path

        self.error_solutions_path = self.storage_path.replace(".json", "_error_solutions.json")
        self.memories: List[Dict[str, Any]] = []
        self.error_solutions: List[Dict[str, Any]] = []
        self.model_router = SelfHealingModelRouter()

        # Zero-Click Middleware: SCONES Expectation Hook
        self.enable_expectation_hook = enable_expectation_hook
        self.strict_expectation = (
            strict_expectation
            if strict_expectation is not None
            else os.environ.get("SCONES_STRICT_EXPECTATION", "0") == "1"
        )
        if expectation_validator is not None:
            self.expectation_validator = expectation_validator
        elif self.enable_expectation_hook:
            try:
                from core.auditor.scones_expect import SconesExpectationValidator
                self.expectation_validator = SconesExpectationValidator.create_scones_memory_validator()
            except ImportError:
                self.expectation_validator = None
        else:
            self.expectation_validator = None

        # Initialize pgvector store if requested and available
        self.enable_pgvector = enable_pgvector
        if pgvector_store is not None:
            self.pgvector = pgvector_store
        elif enable_pgvector and PgVectorStore is not None:
            self.pgvector = PgVectorStore()
        else:
            self.pgvector = None

        self.load_memories()
        self.load_error_solutions()

    def load_memories(self) -> None:
        """Loads long-term memories from JSON storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception:
                self.memories = []
        else:
            self.memories = []

    def save_memories(self) -> None:
        """Saves memories back to JSON storage."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("SCONES Error: Failed to save memories: %s", e)

    def load_error_solutions(self) -> None:
        """Loads distilled error solutions from JSON storage."""
        if os.path.exists(self.error_solutions_path):
            try:
                with open(self.error_solutions_path, "r", encoding="utf-8") as f:
                    self.error_solutions = json.load(f)
            except Exception:
                self.error_solutions = []
        else:
            self.error_solutions = []

    def save_error_solutions(self) -> None:
        """Saves distilled error solutions back to JSON storage."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.error_solutions_path)), exist_ok=True)
            with open(self.error_solutions_path, "w", encoding="utf-8") as f:
                json.dump(self.error_solutions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("SCONES Error: Failed to save error solutions: %s", e)

    def add_memory(
        self,
        topic: str,
        content: str,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Adds a new cognitive outcome into long-term storage with dual-write to pgvector.
        """
        mem_id = f"SCONES-MEM-{int(time.time() * 1000)}"
        meta = metadata or {}
        embedding = generate_embedding(f"{topic} {content}")

        memory_entry = {
            "id": mem_id,
            "timestamp": time.time(),
            "topic": topic,
            "content": content,
            "importance": importance,
            "metadata": meta,
            "embedding": embedding
        }

        # Zero-Click Middleware: SCONES Expectation Hook
        if self.enable_expectation_hook and self.expectation_validator is not None:
            val_res = self.expectation_validator.validate_record(memory_entry)
            if not val_res.is_valid:
                violation_msgs = [v.message for v in val_res.violations]
                logger.warning(
                    "SCONES Expectation Hook caught %d violation(s) for topic '%s': %s",
                    len(violation_msgs),
                    topic,
                    violation_msgs,
                )
                meta["_expectation_violations"] = violation_msgs
                if self.strict_expectation:
                    raise ValueError(
                        f"SCONES memory validation failed ({len(violation_msgs)} violations): "
                        + "; ".join(violation_msgs)
                    )

        # 1. Write to local JSON store (guaranteed baseline)
        self.memories.append(memory_entry)
        self.save_memories()

        # 2. Dual-write to PostgreSQL pgvector if healthy
        if self.pgvector and self.pgvector.is_healthy():
            try:
                self.pgvector.upsert_memory(
                    id=mem_id,
                    topic=topic,
                    content=content,
                    importance=importance,
                    metadata=meta,
                    embedding=embedding,
                    created_at=memory_entry["timestamp"]
                )
            except Exception as e:
                logger.warning("PgVector dual-write failed, recorded in JSON fallback: %s", e)

        return memory_entry

    def validate_memory_entry(self, entry: Dict[str, Any]) -> Any:
        """
        Validates a candidate memory entry using SconesExpectationValidator.
        Returns an ExpectationResult object or None if validator is inactive.
        """
        if not self.expectation_validator:
            return None
        return self.expectation_validator.validate_record(entry)

    def get_memories(
        self,
        topic: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves stored memories, filtered by topic and metadata (tenant/workspace isolation)."""
        mems = self.memories
        if topic is not None:
            mems = [m for m in mems if m.get("topic", "").lower() == topic.lower()]
        if tenant_id is not None:
            mems = [m for m in mems if m.get("metadata", {}).get("tenant_id") == tenant_id]
        if workspace_id is not None:
            mems = [m for m in mems if m.get("metadata", {}).get("workspace_id") == workspace_id]
        return mems

    def search_semantic(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.3,
        topic: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        High-performance semantic search over cognitive memories using pgvector or local cosine similarity.
        """
        query_vec = generate_embedding(query)

        # 1. Try pgvector query first if healthy
        if self.pgvector and self.pgvector.is_healthy():
            try:
                results = self.pgvector.search_memories(
                    query_vector=query_vec,
                    limit=limit,
                    min_similarity=min_similarity,
                    topic=topic,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id
                )
                if results:
                    return results
            except Exception as e:
                logger.warning("PgVector semantic search failed (%s), falling back to in-memory cosine.", e)

        # 2. Fallback: Local in-memory cosine similarity
        candidates = self.get_memories(topic=topic, tenant_id=tenant_id, workspace_id=workspace_id)
        scored = []
        for m in candidates:
            m_vec = m.get("embedding")
            if not m_vec:
                m_vec = generate_embedding(f"{m.get('topic', '')} {m.get('content', '')}")
            sim = cosine_similarity(query_vec, m_vec)
            if sim >= min_similarity:
                scored.append({
                    "id": m.get("id"),
                    "topic": m.get("topic"),
                    "content": m.get("content"),
                    "importance": m.get("importance", 1.0),
                    "metadata": m.get("metadata", {}),
                    "similarity": round(float(sim), 4),
                    "created_at": m.get("timestamp")
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    # -------------------------------------------------------------------------
    # Error Solutions Distillation (Self-Healing Loop)
    # -------------------------------------------------------------------------

    def record_error_solution(
        self,
        error_text: str,
        solution_text: str,
        error_signature: Optional[str] = None,
        root_cause: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records an error and its verified solution with dual-write to pgvector.
        """
        sig = error_signature or hashlib.sha256(error_text.strip().encode("utf-8")).hexdigest()[:16]
        sol_id = f"SCONES-ERR-{sig}"
        meta = metadata or {}
        embedding = generate_embedding(f"{error_text} {solution_text} {root_cause or ''}")

        entry = {
            "id": sol_id,
            "error_signature": sig,
            "error_text": error_text,
            "solution_text": solution_text,
            "root_cause": root_cause,
            "metadata": meta,
            "embedding": embedding,
            "created_at": time.time(),
            "success_rate": 1.0
        }

        # Deduplicate / update in local store
        self.error_solutions = [e for e in self.error_solutions if e.get("id") != sol_id]
        self.error_solutions.append(entry)
        self.save_error_solutions()

        # Dual-write to pgvector
        if self.pgvector and self.pgvector.is_healthy():
            try:
                self.pgvector.upsert_error_solution(
                    id=sol_id,
                    error_text=error_text,
                    solution_text=solution_text,
                    error_signature=sig,
                    root_cause=root_cause,
                    metadata=meta,
                    embedding=embedding,
                    created_at=entry["created_at"]
                )
            except Exception as e:
                logger.warning("PgVector error solution dual-write failed, recorded in JSON fallback: %s", e)

        return entry

    def search_error_solution(
        self,
        query_or_trace: str,
        limit: int = 5,
        min_similarity: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Finds previously distilled solutions for an error using vector cosine similarity.
        """
        query_vec = generate_embedding(query_or_trace)

        # 1. Try pgvector first if healthy
        if self.pgvector and self.pgvector.is_healthy():
            try:
                results = self.pgvector.search_error_solutions(
                    query_vector=query_vec,
                    limit=limit,
                    min_similarity=min_similarity
                )
                if results:
                    return results
            except Exception as e:
                logger.warning("PgVector error search failed (%s), using local fallback.", e)

        # 2. Local in-memory fallback
        scored = []
        for entry in self.error_solutions:
            e_vec = entry.get("embedding")
            if not e_vec:
                e_vec = generate_embedding(f"{entry.get('error_text', '')} {entry.get('solution_text', '')}")
            sim = cosine_similarity(query_vec, e_vec)
            if sim >= min_similarity:
                scored.append({
                    "id": entry.get("id"),
                    "error_signature": entry.get("error_signature"),
                    "error_text": entry.get("error_text"),
                    "solution_text": entry.get("solution_text"),
                    "root_cause": entry.get("root_cause"),
                    "metadata": entry.get("metadata", {}),
                    "similarity": round(float(sim), 4),
                    "success_rate": entry.get("success_rate", 1.0)
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    def compact_log_context(self, raw_logs: str, max_lines: int = 50) -> str:
        """Compacts heavy log strings to prevent context bloat using our playbook utility."""
        return sanitize_text(raw_logs, max_lines=max_lines)

    def route_model(self, requested_model: str, error_code: int = 0) -> Dict[str, Any]:
        """Routes LLM request using our self-healing proxy fallbacks."""
        return self.model_router.resolve_model_with_fallback(requested_model, error_code)

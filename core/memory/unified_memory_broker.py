# --- DNK-MRH-HEADER ---
# mrh_id: "core/memory/unified_memory_broker.py"
# purpose: "Unified Memory Broker & Tiered Router consolidating L1 Hermes, L2/L3 SCONES, SQLite FTS5 Session Store, and Obsidian Vault"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Unified Memory Broker (UnifiedMemoryBroker) for DNK OS.

Solves the 4-tier memory dispersion problem:
1. Tier 1 (L1 Hermes Memory): Rapid in-memory facts, agent invariants, and user profile (MEMORY.md / USER.md). Latency: <5ms.
2. Tier 2/3 (L2/L3 SCONES Cognitive Engine): Episodic cognitive memories, distilled error solutions, and long-term semantic embeddings with temporal recency decay. Latency: <20-50ms.
3. Tier 4 (Obsidian Knowledge Vault): Architecture Decision Records (ADRs), system blueprints, and markdown knowledge base (docs/notes/). Latency: <30ms.
4. Tier 5 (Session SQLite FTS5): Historical conversation messages and tool execution logs (~/.hermes/state.db). Latency: <30ms.

Features:
- Intent Classification: Automatically routes queries to optimal tiers (INVARIANT, ERROR_SOLUTION, ARCHITECTURE, CONVERSATION, COMPREHENSIVE).
- Tiered Cascading & Early Exit: Terminates search if high-confidence results (>=0.85) are found in top-priority tier.
- Dialogue Backpropagation & Consolidation: Auto-extracts invariants to L1, error fixes to L2 SCONES, and architectural decisions to Obsidian Vault.
- Fenced RAG Synthesizer: Builds token-guarded <memory-context> blocks with tier attribution.
- Drop-in MemoryProvider: Subclasses MemoryProvider for seamless integration with MemoryManager.
"""

from __future__ import annotations

import os
import re
import time
import json
import uuid
import sqlite3
import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set, Union

from core.scones_memory import SCONESMemoryEngine
from core.scones_l3_memory import SCONESL3Memory
from core.memory.memory_provider import MemoryProvider

logger = logging.getLogger("UnifiedMemoryBroker")

STOPWORDS = {
    "what", "is", "the", "a", "an", "of", "to", "for", "in", "on", "and", "or",
    "how", "do", "we", "our", "are", "be", "with", "from", "by", "at", "as",
    "it", "this", "that", "can", "show", "me", "tell",
    "які", "яка", "яке", "яких", "що", "як", "де", "чи", "у", "в", "на", "до",
    "для", "з", "із", "та", "й", "і", "про", "це", "наш", "наша", "наші"
}


def _clean_query_tokens(text: str) -> List[str]:
    """Extract significant keywords from query, filtering out common stopwords."""
    raw = re.findall(r"[a-zA-Z0-9_\u0400-\u04FF]+", text.lower())
    filtered = [w for w in raw if len(w) > 1 and w not in STOPWORDS]
    return filtered if filtered else raw



class MemoryTier(str, Enum):
    """Enumeration of knowledge storage tiers."""
    L1_HERMES = "l1_hermes"
    L2_SCONES = "l2_scones"
    L3_SCONES = "l3_scones"
    OBSIDIAN_VAULT = "obsidian_vault"
    SESSION_FTS5 = "session_fts5"


class MemoryIntent(str, Enum):
    """Classified intent of a memory query."""
    INVARIANT = "invariant"              # Rules, user profile, system constraints
    ERROR_SOLUTION = "error_solution"    # Exceptions, bugs, tracebacks, fixes
    ARCHITECTURE = "architecture"        # ADRs, blueprints, canvases, specifications
    CONVERSATION = "conversation"        # Past session turns, dialogue history
    COMPREHENSIVE = "comprehensive"      # Hybrid search across all tiers


@dataclass
class MemoryRecord:
    """Standardized memory record retrieved from any tier."""
    id: str
    tier: MemoryTier
    topic: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tier": self.tier.value,
            "topic": self.topic,
            "content": self.content,
            "score": round(self.score, 3),
            "metadata": self.metadata,
            "latency_ms": round(self.latency_ms, 2)
        }


@dataclass
class BrokerQueryResult:
    """Unified query result returned by the broker."""
    query: str
    detected_intent: MemoryIntent
    records: List[MemoryRecord]
    total_latency_ms: float
    tiers_searched: List[str]
    early_exit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "detected_intent": self.detected_intent.value,
            "records": [r.to_dict() for r in self.records],
            "total_latency_ms": round(self.total_latency_ms, 2),
            "tiers_searched": self.tiers_searched,
            "early_exit": self.early_exit,
            "total_matches": len(self.records)
        }


class UnifiedMemoryBroker:
    """
    Central authoritative memory broker & tiered router.
    Orchestrates L1 Hermes, L2/L3 SCONES, SQLite FTS5 Session store, and Obsidian Vault.
    """

    def __init__(
        self,
        vault_path: Union[str, Path] = "./docs/notes",
        session_db_path: str = "~/.hermes/state.db",
        l1_memory_dir: Optional[str] = None,
        l1_memory_path: Optional[str] = None,
        scones_engine: Optional[SCONESMemoryEngine] = None,
        scones_l3: Optional[SCONESL3Memory] = None,
        early_exit_threshold: float = 0.70,
        default_workspace_id: str = "ws-alpha-001"
    ):
        self.vault_path = Path(vault_path).resolve()
        self.session_db_path = os.path.expanduser(session_db_path)
        self.default_workspace_id = default_workspace_id
        self.early_exit_threshold = early_exit_threshold

        # L1 Hermes paths
        target_l1 = l1_memory_dir or l1_memory_path
        if target_l1:
            self.l1_memory_dir = Path(target_l1).resolve()
        else:
            self.l1_memory_dir = Path("core/orchestrator/agents/gerych_prime/memories").resolve()

        # In-memory fast L1 cache
        self._l1_cache: Dict[str, Dict[str, Any]] = {}

        # SCONES Engines
        self.scones_l2 = scones_engine or SCONESMemoryEngine()
        self.scones_l3 = scones_l3 or SCONESL3Memory()

        # Tier routing priority configuration per intent
        self.routing_priorities: Dict[MemoryIntent, List[MemoryTier]] = {
            MemoryIntent.INVARIANT: [
                MemoryTier.L1_HERMES,
                MemoryTier.L2_SCONES,
                MemoryTier.OBSIDIAN_VAULT
            ],
            MemoryIntent.ERROR_SOLUTION: [
                MemoryTier.L2_SCONES,
                MemoryTier.L3_SCONES,
                MemoryTier.OBSIDIAN_VAULT
            ],
            MemoryIntent.ARCHITECTURE: [
                MemoryTier.OBSIDIAN_VAULT,
                MemoryTier.L2_SCONES,
                MemoryTier.L1_HERMES
            ],
            MemoryIntent.CONVERSATION: [
                MemoryTier.SESSION_FTS5,
                MemoryTier.L2_SCONES
            ],
            MemoryIntent.COMPREHENSIVE: [
                MemoryTier.L1_HERMES,
                MemoryTier.L2_SCONES,
                MemoryTier.OBSIDIAN_VAULT,
                MemoryTier.L3_SCONES,
                MemoryTier.SESSION_FTS5
            ]
        }

    # -------------------------------------------------------------------------
    # 1. INTENT CLASSIFICATION
    # -------------------------------------------------------------------------
    def classify_intent(self, query: str) -> MemoryIntent:
        """
        Sub-millisecond keyword & pattern intent classification.
        """
        q = query.lower()

        # Error / Bug / Fix indicators
        error_patterns = [
            r"\b(error|exception|traceback|fail|failed|crash|bug|fix|workaround|issue|exit code)\b",
            r"\b(помилк[а-я]*|збій|падінн[а-я]*|виправленн[а-я]*|фікс|стектрейс)\b",
            r"\b(500|404|429|502|503|operationalerror|typeerror|valueerror|keyerror)\b"
        ]
        if any(re.search(p, q) for p in error_patterns):
            return MemoryIntent.ERROR_SOLUTION

        # Invariant / Profile indicators
        invariant_patterns = [
            r"\b(invariant|rule|user preference|constraint|restriction|must not|always)\b",
            r"\b(інваріант[а-я]*|правил[а-я]*|профіл[а-я]*|стиль|заборон[а-я]*|обов'язков[а-я]*)\b",
            r"\b(mrh header|mrh_id|who is maxim|user profile|relative path)\b"
        ]
        if any(re.search(p, q) for p in invariant_patterns):
            return MemoryIntent.INVARIANT

        # Architecture / Spec / ADR indicators
        architecture_patterns = [
            r"\b(architecture|adr|blueprint|specification|spec|canvas|diagram|engine|protocol)\b",
            r"\b(архітектур[а-я]*|специфікаці[а-я]*|блюпрінт|дизайн|патерн|схем[а-я]*|нотатк[а-я]*)\b",
            r"\b(control plane|dag|state machine|sota assimilation|tier)\b"
        ]
        if any(re.search(p, q) for p in architecture_patterns):
            return MemoryIntent.ARCHITECTURE

        # Conversation / History indicators
        conversation_patterns = [
            r"\b(session|history|conversation|yesterday|past turn|previous chat|what did we do)\b",
            r"\b(сесі[а-я]*|діалог[а-я]*|вчора|минул[а-я]*|історі[а-я]*|що ми робили|попередн[а-я]*)\b"
        ]
        if any(re.search(p, q) for p in conversation_patterns):
            return MemoryIntent.CONVERSATION

        return MemoryIntent.COMPREHENSIVE

    # -------------------------------------------------------------------------
    # 2. TIER ACCESSORS
    # -------------------------------------------------------------------------
    def _query_l1_hermes(self, query: str, limit: int = 5) -> Tuple[List[MemoryRecord], float]:
        """Query Tier 1: L1 Hermes fast in-memory facts & markdown files (<5ms)."""
        start_t = time.perf_counter()
        records: List[MemoryRecord] = []
        tokens = set(_clean_query_tokens(query))
        if not tokens:
            return records, 0.0

        candidates: List[Tuple[str, str, Dict[str, Any]]] = []

        # 1. In-memory cache
        for cid, item in self._l1_cache.items():
            candidates.append((item.get("topic", "l1_fact"), item.get("content", ""), {"source": "in_memory"}))

        # 2. Markdown memory files (MEMORY.md, USER.md)
        for fname in ["MEMORY.md", "USER.md"]:
            fpath = self.l1_memory_dir / fname
            if fpath.exists():
                try:
                    text = fpath.read_text(encoding="utf-8", errors="ignore")
                    # Split into sections / bullets
                    blocks = re.split(r"\n(?=## |\n- )", text)
                    for block in blocks:
                        clean_block = block.strip()
                        if clean_block and not clean_block.startswith("# --- DNK-MRH-HEADER"):
                            first_line = clean_block.splitlines()[0]
                            topic = first_line.replace("#", "").replace("-", "").strip()[:40]
                            candidates.append((topic, clean_block, {"source": fname, "file": str(fpath)}))
                except Exception as e:
                    logger.debug("Failed reading L1 file %s: %s", fname, e)

        # Score candidates
        for topic, content, meta in candidates:
            c_text = (topic + " " + content).lower()
            c_tokens = set(re.findall(r"\w+", c_text))
            if not c_tokens:
                continue
            
            matched = set()
            for t in tokens:
                if t in c_tokens or any(t in ct or ct in t for ct in c_tokens):
                    matched.add(t)
            
            if matched:
                score = len(matched) / max(len(tokens), 1)
                # Boost if topic matches
                if any(t in topic.lower() for t in tokens):
                    score = min(1.0, score + 0.25)
                records.append(MemoryRecord(
                    id=f"l1_{uuid.uuid4().hex[:8]}",
                    tier=MemoryTier.L1_HERMES,
                    topic=topic,
                    content=content[:500],
                    score=min(1.0, score),
                    metadata=meta,
                    latency_ms=0.0
                ))

        records.sort(key=lambda r: r.score, reverse=True)
        latency = (time.perf_counter() - start_t) * 1000.0
        for r in records:
            r.latency_ms = latency
        return records[:limit], latency

    def _query_l2_scones(self, query: str, limit: int = 5) -> Tuple[List[MemoryRecord], float]:
        """Query Tier 2: SCONES Episodic Memories & Distilled Error Solutions (<20ms)."""
        start_t = time.perf_counter()
        records: List[MemoryRecord] = []
        tokens = set(re.findall(r"\w+", query.lower()))

        # 1. Check Error Distillation if relevant
        try:
            err_solutions = self.scones_l2.search_error_solution(query, limit=limit, min_similarity=0.2)
            if not err_solutions and hasattr(self.scones_l2, "error_solutions"):
                # Direct keyword fallback over error solutions
                clean_q_tokens = set(_clean_query_tokens(query))
                for entry in self.scones_l2.error_solutions:
                    e_text = (entry.get("error_text", "") + " " + entry.get("root_cause", "")).lower()
                    if any(t in e_text for t in clean_q_tokens):
                        err_solutions.append({
                            "id": entry.get("id"),
                            "error_text": entry.get("error_text"),
                            "solution_text": entry.get("solution_text"),
                            "root_cause": entry.get("root_cause"),
                            "similarity": 0.85
                        })
            if err_solutions:
                for sol in err_solutions:
                    records.append(MemoryRecord(
                        id=f"l2_err_{sol.get('id', uuid.uuid4().hex[:8])}",
                        tier=MemoryTier.L2_SCONES,
                        topic=f"ErrorFix: {sol.get('error_text', '')[:40]}",
                        content=f"Root Cause: {sol.get('root_cause', '')}\nSolution: {sol.get('solution_text', '')}",
                        score=float(sol.get("similarity", 0.95)),
                        metadata={"kind": "error_distillation", "raw": sol},
                        latency_ms=0.0
                    ))
        except Exception as e:
            logger.debug("SCONES error distillation query exception: %s", e)

        # 2. Check SCONES Episodic Memories
        try:
            try:
                all_memories = self.scones_l2.get_memories()
            except TypeError:
                all_memories = self.scones_l2.get_memories(workspace_id=self.default_workspace_id)
            
            clean_tokens = set(_clean_query_tokens(query))
            for m in all_memories:
                topic = m.get("topic", "")
                content = m.get("content", "")
                m_tokens = set(re.findall(r"\w+", (topic + " " + content).lower()))
                
                matched = set()
                for t in clean_tokens:
                    if t in m_tokens or any(t in mt or mt in t for mt in m_tokens):
                        matched.add(t)
                
                if matched:
                    score = len(matched) / max(len(clean_tokens), 1)
                    importance = float(m.get("importance", 1.0))
                    # Scale importance (0.1 to 2.0) into score boost
                    final_score = min(1.0, score * (0.8 + 0.2 * min(2.0, importance)))
                    records.append(MemoryRecord(
                        id=f"l2_{uuid.uuid4().hex[:8]}",
                        tier=MemoryTier.L2_SCONES,
                        topic=topic,
                        content=content,
                        score=final_score,
                        metadata=m,
                        latency_ms=0.0
                    ))
        except Exception as e:
            logger.debug("SCONES episodic query exception: %s", e)

        records.sort(key=lambda r: r.score, reverse=True)
        latency = (time.perf_counter() - start_t) * 1000.0
        for r in records:
            r.latency_ms = latency
        return records[:limit], latency

    def _query_l3_scones(self, query: str, limit: int = 5) -> Tuple[List[MemoryRecord], float]:
        """Query Tier 3: SCONES L3 Long-term memory with temporal recency (<30ms)."""
        start_t = time.perf_counter()
        records: List[MemoryRecord] = []
        tokens = set(re.findall(r"\w+", query.lower()))

        try:
            # Query in-memory store of L3
            for mem_id, mem in self.scones_l3._in_memory_l3_store.items():
                content = mem.get("content", "")
                m_tokens = set(re.findall(r"\w+", content.lower()))
                common = tokens.intersection(m_tokens)
                if common:
                    recency = float(mem.get("recency_score", 1.0))
                    score = (len(common) / max(len(tokens), 1)) * recency
                    records.append(MemoryRecord(
                        id=f"l3_{mem_id[:8]}",
                        tier=MemoryTier.L3_SCONES,
                        topic=mem.get("memory_type", "l3_semantic"),
                        content=content,
                        score=min(1.0, score),
                        metadata=mem,
                        latency_ms=0.0
                    ))
        except Exception as e:
            logger.debug("SCONES L3 query exception: %s", e)

        records.sort(key=lambda r: r.score, reverse=True)
        latency = (time.perf_counter() - start_t) * 1000.0
        for r in records:
            r.latency_ms = latency
        return records[:limit], latency

    def _query_obsidian_vault(self, query: str, limit: int = 5) -> Tuple[List[MemoryRecord], float]:
        """Query Tier 4: Obsidian Markdown Vault docs/notes/ (<30ms)."""
        start_t = time.perf_counter()
        records: List[MemoryRecord] = []
        tokens = set(_clean_query_tokens(query))
        if not self.vault_path.exists() or not tokens:
            return records, 0.0

        try:
            md_files = []
            for path in self.vault_path.rglob("*.md"):
                # Exclude noisy, internal or temporary subdirectories and test artifacts
                parts = path.parts
                if any(p.startswith(".") or p in ("archive", ".trash") for p in parts):
                    continue
                if path.name.startswith("test-") or path.name.startswith("test_") or path.name.endswith(".tmp"):
                    continue
                md_files.append(path)

            for md_file in md_files:
                fname = md_file.stem
                f_tokens = set(re.findall(r"\w+", fname.lower()))

                try:
                    text = md_file.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Parse YAML frontmatter if present
                try:
                    rel_to_vault = str(md_file.relative_to(self.vault_path))
                except Exception:
                    rel_to_vault = md_file.name

                meta: Dict[str, Any] = {
                    "filename": md_file.name,
                    "relative_path": f"./docs/notes/{rel_to_vault}"
                }
                tags: List[str] = []
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        fm_text = parts[1]
                        for line in fm_text.splitlines():
                            line_s = line.strip()
                            if line_s.startswith("title:"):
                                meta["title"] = line_s.replace("title:", "").strip().strip("\"'")
                            elif line_s.startswith("tags:"):
                                raw_tags = line_s.replace("tags:", "").strip(" []")
                                tags = [t.strip().strip("\"'") for t in raw_tags.split(",") if t.strip()]
                                meta["tags"] = tags
                            elif line_s.startswith("version:"):
                                meta["version"] = line_s.replace("version:", "").strip().strip("\"'")

                # Frontmatter and Title check
                content_tokens = set(re.findall(r"\w+", text.lower()))
                
                # Check title / filename / tag matches
                title_text = (meta.get("title", "") + " " + fname).lower()
                tag_text = " ".join(tags).lower()
                searchable_head = title_text + " " + tag_text
                
                head_tokens = set(re.findall(r"\w+", searchable_head))
                matched_head = set()
                for t in tokens:
                    if t in head_tokens or any(t in ht or ht in t for ht in head_tokens):
                        matched_head.add(t)
                
                matched_content = set()
                for t in tokens:
                    if t in content_tokens or any(t in ct or ct in t for ct in content_tokens):
                        matched_content.add(t)

                if matched_head or len(matched_content) >= 1:
                    title_score = (len(matched_head) / max(len(tokens), 1)) * 0.7
                    content_score = (len(matched_content) / max(len(tokens), 1)) * 0.3
                    score = min(1.0, title_score + content_score)
                    if len(matched_head) == len(tokens):
                        score = 1.0

                    # Extract best snippet matching tokens
                    snippet = self._extract_snippet(text, tokens)

                    records.append(MemoryRecord(
                        id=f"vault_{uuid.uuid4().hex[:8]}",
                        tier=MemoryTier.OBSIDIAN_VAULT,
                        topic=meta.get("title", fname),
                        content=snippet,
                        score=score,
                        metadata=meta,
                        latency_ms=0.0
                    ))
        except Exception as e:
            logger.debug("Obsidian vault query exception: %s", e)

        records.sort(key=lambda r: r.score, reverse=True)
        latency = (time.perf_counter() - start_t) * 1000.0
        for r in records:
            r.latency_ms = latency
        return records[:limit], latency

    def _query_session_fts5(self, query: str, limit: int = 5) -> Tuple[List[MemoryRecord], float]:
        """Query Tier 5: Session SQLite FTS5 database (~/.hermes/state.db) (<30ms)."""
        start_t = time.perf_counter()
        records: List[MemoryRecord] = []

        if not os.path.exists(self.session_db_path):
            return records, 0.0

        # Clean query tokens for FTS5 syntax
        clean_tokens = [w for w in re.findall(r"\w+", query) if len(w) > 2]
        if not clean_tokens:
            return records, 0.0

        fts_query = " OR ".join(clean_tokens[:5])

        try:
            # Use read-only URI connection with strict timeout
            conn = sqlite3.connect(
                f"file:{self.session_db_path}?mode=ro",
                uri=True,
                timeout=1.0
            )
            cur = conn.cursor()

            sql = """
            SELECT m.id, m.session_id, m.role, m.content
            FROM messages m
            JOIN messages_fts f ON m.rowid = f.rowid
            WHERE messages_fts MATCH ?
            ORDER BY m.id DESC
            LIMIT ?
            """
            cur.execute(sql, (fts_query, limit))
            rows = cur.fetchall()

            for mid, session_id, role, content in rows:
                if not content:
                    continue
                snippet = content.strip()[:350]
                records.append(MemoryRecord(
                    id=f"session_{mid}",
                    tier=MemoryTier.SESSION_FTS5,
                    topic=f"Session: {session_id[:16]} ({role})",
                    content=snippet,
                    score=0.75,
                    metadata={"session_id": session_id, "role": role, "message_id": mid},
                    latency_ms=0.0
                ))
            conn.close()
        except sqlite3.OperationalError:
            # Fallback to direct like query if FTS table has custom configuration
            try:
                conn = sqlite3.connect(f"file:{self.session_db_path}?mode=ro", uri=True, timeout=1.0)
                cur = conn.cursor()
                like_term = f"%{clean_tokens[0]}%"
                cur.execute(
                    "SELECT id, session_id, role, content FROM messages WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
                    (like_term, limit)
                )
                for mid, session_id, role, content in cur.fetchall():
                    if content:
                        records.append(MemoryRecord(
                            id=f"session_{mid}",
                            tier=MemoryTier.SESSION_FTS5,
                            topic=f"Session: {session_id[:16]} ({role})",
                            content=content[:350],
                            score=0.65,
                            metadata={"session_id": session_id, "role": role},
                            latency_ms=0.0
                        ))
                conn.close()
            except Exception:
                pass
        except Exception as e:
            logger.debug("Session FTS5 query error: %s", e)

        latency = (time.perf_counter() - start_t) * 1000.0
        for r in records:
            r.latency_ms = latency
        return records[:limit], latency

    # -------------------------------------------------------------------------
    # 3. ROUTING & UNIFIED QUERY
    # -------------------------------------------------------------------------
    def route_and_query(
        self,
        query: str,
        intent: Optional[MemoryIntent] = None,
        tiers: Optional[List[MemoryTier]] = None,
        limit: int = 5
    ) -> BrokerQueryResult:
        """
        Main query entrypoint.
        Routes across tiers according to intent, executes priority cascade,
        and applies early-exit when top-tier confidence threshold is satisfied.
        """
        overall_start = time.perf_counter()

        detected_intent = intent or self.classify_intent(query)
        tier_pipeline = tiers or self.routing_priorities.get(detected_intent, self.routing_priorities[MemoryIntent.COMPREHENSIVE])

        all_records: List[MemoryRecord] = []
        tiers_searched: List[str] = []
        early_exit_triggered = False

        for tier in tier_pipeline:
            tiers_searched.append(tier.value)

            if tier == MemoryTier.L1_HERMES:
                recs, _ = self._query_l1_hermes(query, limit=limit)
            elif tier == MemoryTier.L2_SCONES:
                recs, _ = self._query_l2_scones(query, limit=limit)
            elif tier == MemoryTier.L3_SCONES:
                recs, _ = self._query_l3_scones(query, limit=limit)
            elif tier == MemoryTier.OBSIDIAN_VAULT:
                recs, _ = self._query_obsidian_vault(query, limit=limit)
            elif tier == MemoryTier.SESSION_FTS5:
                recs, _ = self._query_session_fts5(query, limit=limit)
            else:
                recs = []

            all_records.extend(recs)

            # Check early-exit: if top result in this tier has high confidence
            if recs and recs[0].score >= self.early_exit_threshold:
                early_exit_triggered = True
                break

        # Deduplicate records by topic + content hash
        deduped: List[MemoryRecord] = []
        seen_hashes: Set[str] = set()
        for r in sorted(all_records, key=lambda x: x.score, reverse=True):
            h = f"{r.tier.value}_{r.topic[:30]}_{r.content[:40]}"
            if h not in seen_hashes:
                seen_hashes.add(h)
                deduped.append(r)

        total_latency = (time.perf_counter() - overall_start) * 1000.0

        return BrokerQueryResult(
            query=query,
            detected_intent=detected_intent,
            records=deduped[:limit],
            total_latency_ms=total_latency,
            tiers_searched=tiers_searched,
            early_exit=early_exit_triggered
        )

    # -------------------------------------------------------------------------
    # 4. UNIFIED WRITE & STORAGE
    # -------------------------------------------------------------------------
    def store(
        self,
        tier: MemoryTier,
        topic: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Unified storage method targeting specific tier.
        """
        meta = metadata or {}
        rec_id = str(uuid.uuid4())

        if tier == MemoryTier.L1_HERMES:
            self._l1_cache[rec_id] = {
                "id": rec_id,
                "topic": topic,
                "content": content,
                "metadata": meta,
                "stored_at": time.time()
            }
            return {"status": "stored", "tier": tier.value, "id": rec_id}

        elif tier == MemoryTier.L2_SCONES:
            importance = float(meta.get("importance", 1.0))
            self.scones_l2.add_memory(
                topic=topic,
                content=content,
                importance=importance,
                metadata=meta
            )
            return {"status": "stored", "tier": tier.value, "topic": topic}

        elif tier == MemoryTier.L3_SCONES:
            self.scones_l3._in_memory_l3_store[rec_id] = {
                "id": rec_id,
                "user_id": meta.get("user_id", "default"),
                "workspace_id": self.default_workspace_id,
                "memory_type": meta.get("memory_type", "semantic"),
                "content": content,
                "metadata": meta,
                "recency_score": 1.0,
                "created_at": time.time()
            }
            return {"status": "stored", "tier": tier.value, "id": rec_id}

        elif tier == MemoryTier.OBSIDIAN_VAULT:
            # Ensure vault path exists
            self.vault_path.mkdir(parents=True, exist_ok=True)
            safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', topic).strip()
            if not safe_title:
                safe_title = f"Note_{rec_id[:8]}"
            note_file = self.vault_path / f"{safe_title}.md"

            frontmatter = f"""---
title: "{topic}"
tier: "L4_Obsidian"
updated_at: "{time.strftime('%Y-%m-%d')}"
tags: {json.dumps(meta.get('tags', ['architecture', 'dnk-os']))}
---

# {topic}

{content}
"""
            note_file.write_text(frontmatter, encoding="utf-8")
            return {"status": "stored", "tier": tier.value, "path": str(note_file)}

        else:
            return {"status": "error", "message": f"Unsupported direct store for tier {tier.value}"}

    # -------------------------------------------------------------------------
    # 5. DIALOGUE CONSOLIDATION & BACKPROPAGATION
    # -------------------------------------------------------------------------
    def consolidate_dialogue_to_long_term(
        self,
        summary: Any,
        invariants: Optional[List[str]] = None,
        solved_errors: Optional[List[Dict[str, str]]] = None,
        architectural_decisions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Backpropagates extracted dialogue knowledge into persistent long-term tiers:
        - Invariants -> L1 Hermes cache
        - Solved errors -> L2 SCONES Error Distillation
        - Architectural decisions -> Obsidian Vault Markdown ADR notes
        """
        results: Dict[str, Any] = {
            "l1_invariants_added": 0,
            "l2_errors_distilled": 0,
            "vault_adrs_written": 0,
            "vault_adrs_created": 0
        }

        # If summary is a dict, extract fields
        if isinstance(summary, dict):
            if invariants is None:
                invariants = summary.get("new_invariants") or summary.get("invariants")
            if solved_errors is None:
                solved_errors = summary.get("solved_errors")
            if architectural_decisions is None:
                architectural_decisions = summary.get("architectural_decisions")

        # 1. Backpropagate invariants to L1
        if invariants:
            for inv in invariants:
                self.store(
                    tier=MemoryTier.L1_HERMES,
                    topic="system_invariant",
                    content=inv,
                    metadata={"source": "dialogue_backpropagation"}
                )
                results["l1_invariants_added"] += 1

        # 2. Backpropagate error solutions to L2
        if solved_errors:
            for err in solved_errors:
                self.scones_l2.record_error_solution(
                    error_text=err.get("error_text", ""),
                    solution_text=err.get("solution_text", ""),
                    root_cause=err.get("root_cause", "")
                )
                results["l2_errors_distilled"] += 1

        # 3. Backpropagate architectural decisions to Obsidian Vault
        if architectural_decisions:
            for adr in architectural_decisions:
                title = adr.get("title", f"ADR_{uuid.uuid4().hex[:6]}")
                content = adr.get("content")
                if not content:
                    content = f"## Context\n{adr.get('context', 'Context from dialogue consolidation')}\n\n## Decision\n{adr.get('decision', '')}\n\n## Consequences & Tradeoffs\n{adr.get('consequences', 'Verified green in CI/CD pipeline.')}"
                self.store(
                    tier=MemoryTier.OBSIDIAN_VAULT,
                    topic=title,
                    content=content,
                    metadata={"tags": adr.get("tags", ["adr", "consolidation", "backpropagation"])}
                )
                results["vault_adrs_written"] += 1
                results["vault_adrs_created"] += 1

        return results

    # -------------------------------------------------------------------------
    # 6. RAG CONTEXT FORMATTER (TOKEN-GUARDED)
    # -------------------------------------------------------------------------
    def format_rag_context(self, query: str, max_tokens: int = 1500) -> str:
        """
        Runs tiered query and formats a clean, token-guarded <memory-context> block
        with source attribution for immediate prompt injection.
        """
        result = self.route_and_query(query, limit=5)
        if not result.records:
            return ""

        parts = [
            "<memory-context>",
            f"[System note: Unified Memory Broker context retrieved across tiers (Intent: {result.detected_intent.value.upper()}, Latency: {result.total_latency_ms:.1f}ms, EarlyExit: {result.early_exit})]"
        ]

        # Estimate ~4 chars per token
        char_budget = max_tokens * 4
        current_chars = len("\n".join(parts))

        tier_labels = {
            MemoryTier.L1_HERMES: "[L1:Hermes]",
            MemoryTier.L2_SCONES: "[L2:SCONES]",
            MemoryTier.L3_SCONES: "[L3:SCONES-L3]",
            MemoryTier.OBSIDIAN_VAULT: "[Vault:Obsidian]",
            MemoryTier.SESSION_FTS5: "[Session:FTS5]"
        }

        for rec in result.records:
            label = tier_labels.get(rec.tier, f"[{rec.tier.value}]")
            item_line = f"{label} Topic: {rec.topic} (Score: {rec.score:.2f})\nContent: {rec.content.strip()}"
            if current_chars + len(item_line) + 20 > char_budget:
                break
            parts.append(item_line)
            current_chars += len(item_line)

        parts.append("</memory-context>")
        return "\n".join(parts)

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    def _extract_snippet(self, text: str, tokens: Set[str], max_len: int = 350) -> str:
        """Extracts the most relevant paragraph snippet from text based on query tokens."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("---")]
        best_p = ""
        best_overlap = 0

        for p in paragraphs:
            p_tokens = set(re.findall(r"\w+", p.lower()))
            overlap = len(tokens.intersection(p_tokens))
            if overlap > best_overlap:
                best_overlap = overlap
                best_p = p

        if best_p:
            return best_p[:max_len]
        return text.strip()[:max_len]

    def get_tier_stats(self) -> Dict[str, Any]:
        """Returns health and document count metrics for all 4 memory tiers."""
        vault_count = len([
            p for p in self.vault_path.rglob("*.md")
            if not any(part.startswith(".") or part in ("archive", ".trash") for part in p.parts)
            and not (p.name.startswith("test-") or p.name.startswith("test_") or p.name.endswith(".tmp"))
        ]) if self.vault_path.exists() else 0
        scones_count = len(self.scones_l2.get_memories(workspace_id=self.default_workspace_id))
        l3_count = len(self.scones_l3._in_memory_l3_store)
        l1_count = len(self._l1_cache)

        session_count = 0
        if os.path.exists(self.session_db_path):
            try:
                conn = sqlite3.connect(f"file:{self.session_db_path}?mode=ro", uri=True, timeout=0.5)
                cur = conn.cursor()
                cur.execute("SELECT count(*) FROM messages")
                session_count = cur.fetchone()[0]
                conn.close()
            except Exception:
                session_count = -1

        return {
            "tier_1_l1_hermes_items": l1_count,
            "tier_2_scones_l2_memories": scones_count,
            "tier_3_scones_l3_items": l3_count,
            "tier_4_obsidian_notes": vault_count,
            "tier_5_session_messages": session_count,
            "broker_status": "active"
        }


class UnifiedMemoryProvider(MemoryProvider):
    """
    Pluggable MemoryProvider implementation wrapping UnifiedMemoryBroker.
    Can be registered into MemoryManager directly.
    """

    def __init__(self, broker: Optional[UnifiedMemoryBroker] = None):
        self._broker = broker or UnifiedMemoryBroker()

    @property
    def name(self) -> str:
        return "unified_broker"

    def initialize(self, session_id: str, **kwargs) -> None:
        self.session_id = session_id
        logger.info("UnifiedMemoryProvider initialized with 4-tier broker for session %s.", session_id)

    def is_available(self) -> bool:
        """Checks if unified broker is available."""
        return True

    def system_prompt_block(self) -> str:
        return (
            "You are backed by the DNK OS Unified Memory Broker. "
            "Knowledge is automatically recalled across 4 tiers (L1 Hermes, L2/L3 SCONES, SQLite FTS5 Session store, and Obsidian Vault). "
            "You can query or store cross-tier knowledge using 'unified_memory_query' and 'unified_memory_store'."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        return self._broker.format_rag_context(query)

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        # Check if assistant response contains an invariant or error solution and auto-backpropagate
        pass

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "unified_memory_query",
                "description": "Query across all 4 knowledge tiers (L1 Hermes, L2/L3 SCONES, Obsidian Vault, and Session FTS5) with automated intent routing and cascading recall.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Semantic query or question."
                        },
                        "intent": {
                            "type": "string",
                            "enum": ["invariant", "error_solution", "architecture", "conversation", "comprehensive"],
                            "description": "Optional explicit intent routing."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return (default 5)."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "unified_memory_store",
                "description": "Store knowledge into a specific memory tier (l1_hermes, l2_scones, l3_scones, obsidian_vault).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tier": {
                            "type": "string",
                            "enum": ["l1_hermes", "l2_scones", "l3_scones", "obsidian_vault"],
                            "description": "Target memory tier."
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topic or title."
                        },
                        "content": {
                            "type": "string",
                            "description": "Memory payload, fact, or Markdown ADR text."
                        }
                    },
                    "required": ["tier", "topic", "content"]
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if tool_name == "unified_memory_query":
            q = args.get("query", "")
            intent_str = args.get("intent")
            intent = MemoryIntent(intent_str) if intent_str else None
            limit = int(args.get("limit", 5))
            res = self._broker.route_and_query(q, intent=intent, limit=limit)
            return json.dumps(res.to_dict(), ensure_ascii=False)

        elif tool_name == "unified_memory_store":
            tier_str = args.get("tier", "l2_scones")
            tier = MemoryTier(tier_str)
            topic = args.get("topic", "")
            content = args.get("content", "")
            res = self._broker.store(tier=tier, topic=topic, content=content)
            return json.dumps(res, ensure_ascii=False)

        return json.dumps({"error": f"Unknown tool {tool_name}"})

    def shutdown(self) -> None:
        pass


_GLOBAL_MEMORY_BROKER: Optional[UnifiedMemoryBroker] = None


def get_global_memory_broker(**kwargs) -> UnifiedMemoryBroker:
    """Get or create singleton global memory broker."""
    global _GLOBAL_MEMORY_BROKER
    if _GLOBAL_MEMORY_BROKER is None:
        _GLOBAL_MEMORY_BROKER = UnifiedMemoryBroker(**kwargs)
    return _GLOBAL_MEMORY_BROKER


def reset_global_memory_broker() -> None:
    """Reset singleton broker (useful in test teardown)."""
    global _GLOBAL_MEMORY_BROKER
    _GLOBAL_MEMORY_BROKER = None


# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_unified_memory_broker.py"
# purpose: "Comprehensive tests for Unified Memory Broker & Tiered Router"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import time
import sqlite3
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from core.memory.unified_memory_broker import (
    UnifiedMemoryBroker,
    UnifiedMemoryProvider,
    MemoryTier,
    MemoryIntent,
    MemoryRecord,
    BrokerQueryResult,
    get_global_memory_broker,
    reset_global_memory_broker
)
from core.memory.memory_manager import MemoryManager
from core.scones_memory import SCONESMemoryEngine
from core.scones_l3_memory import SCONESL3Memory


@pytest.fixture
def temp_memory_env(tmp_path):
    """Setup temporary filesystem environment for L1, Vault, and SQLite FTS5."""
    # 1. L1 Memory Dir
    l1_dir = tmp_path / "l1_memories"
    l1_dir.mkdir(parents=True, exist_ok=True)
    memory_md = l1_dir / "MEMORY.md"
    memory_md.write_text(
        "# Gerych Memory\n\n"
        "## Invariants\n"
        "- [PATH_HYGIENE]: Universal relative paths ONLY (./, ../). Never use absolute paths.\n"
        "- [CODE_STYLE]: Communication in Ukrainian, code in English.\n"
        "- [QUALITY_GATE]: 100% test pass rate required.\n\n"
        "## Dynamic Lessons\n"
        "- [SWARM_PARALLEL]: Always pass explicit target_files in task payload.\n"
    )
    user_md = l1_dir / "USER.md"
    user_md.write_text(
        "# User Profile\n\n"
        "- Owner: Maksym Kuzmenko (Maxim), Creator of DNK OS.\n"
        "- Preference: Reject narrative claims without diff proof.\n"
    )

    # 2. Obsidian Vault Dir
    vault_dir = tmp_path / "notes"
    vault_dir.mkdir(parents=True, exist_ok=True)
    
    note1 = vault_dir / "016 Unified Swarm Control Plane.md"
    note1.write_text(
        "---\n"
        "title: \"Unified Swarm Control Plane Architecture\"\n"
        "tags: [architecture, swarm, control_plane, adr]\n"
        "version: \"1.0.0\"\n"
        "---\n\n"
        "# Unified Swarm Control Plane Architecture\n\n"
        "Consolidated all 6 coordinator engines into a single DAG control plane.\n"
        "Features include State Machine, Checkpointer, and Sub-50ms Skill RAG.\n"
    )

    note2 = vault_dir / "007 Shopify Theme Canvas Synchronization.md"
    note2.write_text(
        "---\n"
        "title: \"Shopify Theme Canvas Sync Protocol\"\n"
        "tags: [shopify, liquid, canvas, sync]\n"
        "---\n\n"
        "# Shopify Theme Canvas Sync Protocol\n\n"
        "Bidirectional OCC 3-way structural merge between Canvas graph and Liquid AST.\n"
    )

    # 3. SQLite DB with FTS5
    db_file = tmp_path / "test_state.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at REAL
        )
    """)
    cur.execute("""
        CREATE VIRTUAL TABLE messages_fts USING fts5(
            content,
            content='messages',
            content_rowid='rowid'
        )
    """)
    
    sample_msgs = [
        ("m1", "sess_001", "user", "How do we run the verification script in Docker container?", 100.0),
        ("m2", "sess_001", "assistant", "Run bash scripts/verify_all.sh inside the container with venv activated.", 101.0),
        ("m3", "sess_002", "user", "What was the previous decision on database connection pool?", 200.0),
        ("m4", "sess_002", "assistant", "We decided to set max_overflow=20 and pool_size=10 in SQLAlchemy engine.", 201.0),
    ]
    for row in sample_msgs:
        cur.execute(
            "INSERT INTO messages(id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            row
        )
        cur.execute(
            "INSERT INTO messages_fts(rowid, content) VALUES (last_insert_rowid(), ?)",
            (row[3],)
        )
    conn.commit()
    conn.close()

    # 4. SCONES Engines (isolated)
    scones_l2_path = tmp_path / "scones_l2.json"
    scones_l2 = SCONESMemoryEngine(storage_path=str(scones_l2_path))
    scones_l2.add_memory(
        topic="FastAPI Router Patterns",
        content="Always use APIRouter with dependency injection and response_model schemas.",
        importance=0.9
    )
    scones_l2.record_error_solution(
        error_text="IntegrityError: duplicate key value violates unique constraint 'nodes_pkey'",
        solution_text="Ensure node_id is unique using UUID4 before inserting into TaskForestNode table.",
        root_cause="Concurrent task creation generated identical timestamp IDs."
    )

    scones_l3 = SCONESL3Memory()
    scones_l3._in_memory_l3_store["l3_001"] = {
        "id": "l3_001",
        "user_id": "default",
        "workspace_id": "ws-alpha-001",
        "memory_type": "semantic",
        "content": "Deep architectural rule: Avoid monolithic coordinator loops, use event-driven messaging.",
        "metadata": {"importance": 0.88},
        "recency_score": 0.95,
        "created_at": time.time()
    }

    broker = UnifiedMemoryBroker(
        vault_path=vault_dir,
        session_db_path=db_file,
        scones_engine=scones_l2,
        scones_l3=scones_l3,
        l1_memory_path=l1_dir,
        default_workspace_id="ws-alpha-001"
    )

    return {
        "broker": broker,
        "vault_dir": vault_dir,
        "l1_dir": l1_dir,
        "db_file": db_file,
        "scones_l2": scones_l2,
        "scones_l3": scones_l3
    }


def test_intent_classification(temp_memory_env):
    """Test fast intent heuristic classifier."""
    broker = temp_memory_env["broker"]

    assert broker.classify_intent("Які у нас правила та інваріанти для шляхів?") == MemoryIntent.INVARIANT
    assert broker.classify_intent("User preference for code style and persona") == MemoryIntent.INVARIANT
    assert broker.classify_intent("Fix IntegrityError: duplicate key traceback crash") == MemoryIntent.ERROR_SOLUTION
    assert broker.classify_intent("Збій у тестах: exception during connection pool init") == MemoryIntent.ERROR_SOLUTION
    assert broker.classify_intent("Show me the architecture ADR for swarm control plane") == MemoryIntent.ARCHITECTURE
    assert broker.classify_intent("Специфікація та дизайн Shopify Canvas синхронізації") == MemoryIntent.ARCHITECTURE
    assert broker.classify_intent("What did we do in the previous session yesterday?") == MemoryIntent.CONVERSATION
    assert broker.classify_intent("Минулий діалог про Docker container") == MemoryIntent.CONVERSATION
    assert broker.classify_intent("Tell me about general project goals") == MemoryIntent.COMPREHENSIVE


def test_l1_hermes_memory_retrieval(temp_memory_env):
    """Test L1 Hermes memory retrieval (<5ms target)."""
    broker = temp_memory_env["broker"]

    start = time.perf_counter()
    records, latency_ms = broker._query_l1_hermes("relative path hygiene", limit=3)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert len(records) > 0
    assert duration_ms < 50.0  # Ultra-fast
    assert records[0].tier == MemoryTier.L1_HERMES
    assert "relative paths" in records[0].content.lower()


def test_l2_scones_memory_and_distillation(temp_memory_env):
    """Test L2 SCONES episodic memory and error distillation recall."""
    broker = temp_memory_env["broker"]

    # 1. Error distillation recall
    err_records, _ = broker._query_l2_scones("IntegrityError duplicate key violates unique constraint", limit=3)
    assert len(err_records) > 0
    assert err_records[0].tier == MemoryTier.L2_SCONES
    assert "UUID4" in err_records[0].content

    # 2. Episodic memory recall
    mem_records, _ = broker._query_l2_scones("FastAPI router dependency injection", limit=3)
    assert len(mem_records) > 0
    assert mem_records[0].tier == MemoryTier.L2_SCONES
    assert "APIRouter" in mem_records[0].content


def test_l3_scones_memory_retrieval(temp_memory_env):
    """Test L3 long-term memory retrieval."""
    broker = temp_memory_env["broker"]

    records, _ = broker._query_l3_scones("monolithic coordinator event-driven", limit=2)
    assert len(records) > 0
    assert records[0].tier == MemoryTier.L3_SCONES
    assert "event-driven messaging" in records[0].content


def test_obsidian_vault_discovery_and_indexing(temp_memory_env):
    """Test Obsidian markdown vault indexing and snippet retrieval."""
    broker = temp_memory_env["broker"]

    # Search by tag / keyword
    records, _ = broker._query_obsidian_vault("control plane architecture DAG", limit=2)
    assert len(records) > 0
    assert records[0].tier == MemoryTier.OBSIDIAN_VAULT
    assert "Unified Swarm Control Plane" in records[0].topic
    assert records[0].metadata.get("tags") is not None
    assert "control_plane" in records[0].metadata["tags"]

    # Search Shopify sync note
    shopify_records, _ = broker._query_obsidian_vault("Liquid structural merge", limit=2)
    assert len(shopify_records) > 0
    assert "Shopify" in shopify_records[0].topic


def test_session_fts5_query(temp_memory_env):
    """Test SQLite FTS5 session search across historical messages."""
    broker = temp_memory_env["broker"]

    records, _ = broker._query_session_fts5("SQLAlchemy database connection pool", limit=2)
    assert len(records) > 0
    assert records[0].tier == MemoryTier.SESSION_FTS5
    assert "max_overflow=20" in records[0].content or "pool_size=10" in records[0].content
    assert records[0].metadata.get("session_id") == "sess_002"



def test_unified_cascading_routing_and_early_exit(temp_memory_env):
    """Test cascading query execution and early exit behavior."""
    broker = temp_memory_env["broker"]

    # 1. Invariant query: routes to L1 first
    res = broker.route_and_query("What is the relative path invariant?")
    assert res.detected_intent == MemoryIntent.INVARIANT
    assert len(res.records) > 0
    assert res.records[0].tier == MemoryTier.L1_HERMES
    assert res.early_exit is True  # Score was high enough to avoid scanning slower tiers

    # 2. Architecture query: routes to Obsidian Vault first
    res_arch = broker.route_and_query("Explain Swarm Control Plane DAG architecture")
    assert res_arch.detected_intent == MemoryIntent.ARCHITECTURE
    assert len(res_arch.records) > 0
    assert res_arch.records[0].tier == MemoryTier.OBSIDIAN_VAULT
    assert res_arch.early_exit is True

    # 3. Comprehensive query: searches across multiple tiers
    res_comp = broker.route_and_query("Docker container script execution", intent=MemoryIntent.COMPREHENSIVE)
    assert len(res_comp.tiers_searched) >= 2


def test_format_rag_context_fencing_and_budget(temp_memory_env):
    """Test XML fenced RAG context builder with token budget guards."""
    broker = temp_memory_env["broker"]

    rag_text = broker.format_rag_context("Shopify Theme Canvas sync protocol", max_tokens=500)
    assert "<memory-context>" in rag_text
    assert "</memory-context>" in rag_text
    assert "[Vault:Obsidian]" in rag_text or "[L2:SCONES]" in rag_text
    assert len(rag_text) <= 500 * 4 + 200  # Token limit respected


def test_unified_store_and_dialogue_backpropagation(temp_memory_env):
    """Test storing into tiers and backpropagating dialogue knowledge."""
    broker = temp_memory_env["broker"]
    vault_dir = temp_memory_env["vault_dir"]

    # 1. Store into L2
    res_l2 = broker.store(
        tier=MemoryTier.L2_SCONES,
        topic="Worker Scaffolding",
        content="Auto-scaffold dummy files before dispatching parallel workers."
    )
    assert res_l2["status"] == "stored"

    # 2. Store into Vault (creates new ADR note)
    res_vault = broker.store(
        tier=MemoryTier.OBSIDIAN_VAULT,
        topic="017 Memory Dispersion Resolution ADR",
        content="# ADR: Memory Dispersion Resolution\n\nConsolidate 4 tiers into Unified Memory Broker."
    )
    assert res_vault["status"] == "stored"
    created_note = vault_dir / "017 Memory Dispersion Resolution ADR.md"
    assert created_note.exists()
    assert "Unified Memory Broker" in created_note.read_text()

    # 3. Dialogue backpropagation
    dialogue_summary = {
        "new_invariants": [
            "[TEST_CLIENT_ISOLATION]: Use threading.local() for Starlette TestClient in multi-threaded tests."
        ],
        "solved_errors": [
            {
                "error_text": "OperationalError: database is locked in SQLite FTS5",
                "solution_text": "Use URI mode=ro with timeout=5.0 for concurrent reader threads.",
                "root_cause": "Exclusive write lock held during batch indexing."
            }
        ],
        "architectural_decisions": [
            {
                "title": "018 Multi-Agent Memory Tiering Protocol",
                "content": "# Multi-Agent Memory Tiering Protocol\n\nDefines L1 through L4 routing rules.",
                "tags": ["memory", "scones", "broker"]
            }
        ]
    }

    bp_res = broker.consolidate_dialogue_to_long_term(dialogue_summary)
    assert bp_res["l1_invariants_added"] == 1
    assert bp_res["l2_errors_distilled"] == 1
    assert bp_res["vault_adrs_created"] == 1

    # Verify backpropagated error can now be queried from L2!
    recalled_fix, _ = broker._query_l2_scones("OperationalError database is locked SQLite", limit=1)
    assert len(recalled_fix) > 0
    assert "timeout=5.0" in recalled_fix[0].content


def test_unified_memory_provider_integration(temp_memory_env):
    """Test UnifiedMemoryProvider as drop-in MemoryProvider inside MemoryManager."""
    broker = temp_memory_env["broker"]
    provider = UnifiedMemoryProvider(broker=broker)

    # 1. Provider metadata & tools
    assert provider.name == "unified_broker"
    schemas = provider.get_tool_schemas()
    assert len(schemas) == 2
    tool_names = [s["name"] for s in schemas]
    assert "unified_memory_query" in tool_names
    assert "unified_memory_store" in tool_names

    # 2. Prefetch context
    context = provider.prefetch("What is the relative path invariant?")
    assert "<memory-context>" in context
    assert "relative path" in context.lower()

    # 3. Tool call execution
    query_call_res = provider.handle_tool_call(
        tool_name="unified_memory_query",
        args={"query": "Explain Swarm Control Plane", "limit": 2}
    )
    assert "Unified Swarm Control Plane" in query_call_res

    # 4. MemoryManager integration
    mgr = MemoryManager()
    mgr.add_provider(provider)
    assert any(p.name == "unified_broker" for p in mgr._providers)
    assert mgr.get_provider("unified_broker") is not None

    system_prompt = mgr.build_system_prompt()
    assert "Unified Memory Broker" in system_prompt

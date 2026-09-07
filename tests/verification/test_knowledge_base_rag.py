# --- DNK-MRH-HEADER ---
# mrh_id: "test_knowledge_base_rag"
# purpose: "Verification tests for pgvector KnowledgeStore, RagService, and Timeline integration with audit trails"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
from datetime import datetime
import os
import sys
from pathlib import Path
import pytest
import asyncpg
from uuid import uuid4, UUID

# Setup paths relative to test file to resolve core modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.models.knowledge import KnowledgeDocument, KnowledgeQueryResult
from core.adapters.postgres_knowledge_store import PostgresKnowledgeStore
from core.services.rag_service import DNKRagService
from core.services.timeline_knowledge_service import TimelineKnowledgeService
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository
from core.config.timeline_config import DATABASE_URL
from core.models.timeline import Agent, Run, Event, Task as TimelineTask

# Set pytestmark to anyio for async tests
pytestmark = pytest.mark.anyio

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def db_pool():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, setup=setup_test_conn, timeout=2.0)
    except Exception as e:
        pytest.skip(f"PostgreSQL integration unavailable: {e}")
    
    async with pool.acquire() as conn:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS timeline;")
        await conn.execute("SET search_path TO timeline, public;")
        
    # Run migrations to ensure schema is ready in timeline
    migrations_dir = BASE_DIR / "db" / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    async with pool.acquire() as conn:
        for m_file in migration_files:
            sql = m_file.read_text(encoding="utf-8")
            try:
                await conn.execute(sql)
            except Exception as e:
                await pool.close()
                pytest.skip(f"PostgreSQL migration failed (e.g. missing pgvector): {e}")
            
    yield pool
    
    # Tear down test schema after testing
    async with pool.acquire() as conn:
        await conn.execute("DROP SCHEMA IF EXISTS timeline CASCADE;")
        
    await pool.close()

@pytest.fixture(autouse=True)
async def clean_tables(db_pool):
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE timeline.events, timeline.tasks, timeline.runs, timeline.agents CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS timeline.knowledge_documents CASCADE;")
    yield

@pytest.fixture
def knowledge_store(db_pool):
    # Pass raw string DATABASE_URL to avoid connection-pool loop mismatch across threads
    store = PostgresKnowledgeStore(DATABASE_URL)
    yield store
    store.close()

@pytest.fixture
def rag_service(knowledge_store):
    return DNKRagService(knowledge_store)

async def test_upsert_document(knowledge_store):
    """1. test_upsert_document — збереження документа."""
    doc_id = uuid4()
    embedding = [0.1] * 768
    
    doc = KnowledgeDocument(
        id=doc_id,
        content="SOTA Hexagonal Architecture implementation details",
        embedding=embedding,
        metadata={"source": "test"},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    
    knowledge_store.upsert_document(doc)
    
    # Search similar should find it
    results = knowledge_store.search_similar(embedding, limit=1)
    assert len(results) == 1
    assert results[0].doc_id == doc_id
    assert results[0].content == "SOTA Hexagonal Architecture implementation details"

async def test_search_similar(knowledge_store):
    """2. test_search_similar — пошук за запитом."""
    doc1 = KnowledgeDocument(
        id=uuid4(),
        content="FastAPI is a modern web framework",
        embedding=[0.5] * 768,
        metadata={"category": "web"},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    
    doc2 = KnowledgeDocument(
        id=uuid4(),
        content="FreeCAD uses Python API for CAD modeling",
        embedding=[-0.2] * 768,
        metadata={"category": "cad"},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    
    knowledge_store.upsert_document(doc1)
    knowledge_store.upsert_document(doc2)
    
    # Searching with [0.5]*768 should match FastAPI first due to higher similarity
    results = knowledge_store.search_similar([0.5] * 768, limit=1)
    assert len(results) == 1
    assert "FastAPI" in results[0].content

async def test_search_with_filters(knowledge_store):
    """3. test_search_with_filters — пошук з фільтрами."""
    run_id_1 = str(uuid4())
    run_id_2 = str(uuid4())
    
    doc1 = KnowledgeDocument(
        id=uuid4(),
        content="Knowledge from run A",
        embedding=[0.1] * 768,
        metadata={"run_id": run_id_1},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    
    doc2 = KnowledgeDocument(
        id=uuid4(),
        content="Knowledge from run B",
        embedding=[0.1] * 768,
        metadata={"run_id": run_id_2},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    
    knowledge_store.upsert_document(doc1)
    knowledge_store.upsert_document(doc2)
    
    # Search with filters restricting to run_id_2
    results = knowledge_store.search_similar([0.1] * 768, limit=10, filters={"run_id": run_id_2})
    assert len(results) == 1
    assert results[0].content == "Knowledge from run B"

async def test_retrieve_context(rag_service, knowledge_store):
    """4. test_retrieve_context — RAG retrieval."""
    doc_id = uuid4()
    content = "Shopify theme engineering uses Liquid templates"
    
    doc = KnowledgeDocument(
        id=doc_id,
        content=content,
        embedding=rag_service._get_embedding(content),
        metadata={"source": "manual"},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    knowledge_store.upsert_document(doc)
    
    # In mock/testing, query exact string to guarantee exact hash vector match & similarity score >= 0.7
    results = rag_service.retrieve_context(content)
    assert len(results) >= 1
    assert "Shopify" in results[0].content
    assert results[0].score >= 0.7

async def test_augment_prompt(rag_service, knowledge_store):
    """5. test_augment_prompt — додавання контексту до промпту."""
    content = "Pytest is used to verify the code"
    doc = KnowledgeDocument(
        id=uuid4(),
        content=content,
        embedding=rag_service._get_embedding(content),
        metadata={"source": "manual"},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    knowledge_store.upsert_document(doc)
    
    base_prompt = "Write a test suite."
    # Query exact content for mock hash vectors compatibility
    augmented = rag_service.augment_prompt(base_prompt, content)
    
    assert base_prompt in augmented
    assert "Context:" in augmented
    assert "Pytest is used to verify the code" in augmented

async def test_timeline_integration(db_pool, knowledge_store, rag_service):
    """6. test_timeline_integration — аналіз минулих виконань, генерація знань."""
    repo = PostgresTimelineRepository(db_pool)
    analyzer = TimelineKnowledgeService(repo, knowledge_store, rag_service)
    
    agent_id = uuid4()
    await repo.create_agent(Agent(id=agent_id, name="Research Agent"))
    
    run_id = uuid4()
    await repo.create_run(Run(
        id=run_id, 
        agent_id=agent_id, 
        run_type="research", 
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    ))
    
    task_id = uuid4()
    await repo.create_task(TimelineTask(
        id=task_id,
        run_id=run_id,
        task_type="research",
        status="completed",
        payload={"query": "pgvector hnsw"},
        result={"output": "HNSW index established successfully"},
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    ))
    
    generated = await analyzer.analyze_and_generate_knowledge(agent_id)
    assert len(generated) == 1
    assert "HNSW index established successfully" in generated[0].content
    assert generated[0].metadata["source"] == "timeline"
    assert generated[0].metadata["run_id"] == str(run_id)

async def test_audit_trail(db_pool):
    """7. test_audit_trail — всі операції записуються в Timeline DB."""
    repo = PostgresTimelineRepository(db_pool)
    
    # Pass real timeline repo to knowledge store constructor
    knowledge_store = PostgresKnowledgeStore(DATABASE_URL, timeline_repo=repo)
    
    agent_id = uuid4()
    await repo.create_agent(Agent(id=agent_id, name="Test Agent"))
    
    run_id = uuid4()
    await repo.create_run(Run(id=run_id, agent_id=agent_id, run_type="knowledge_sync", status="running"))
    
    doc_id = uuid4()
    doc = KnowledgeDocument(
        id=doc_id,
        content="Vector memory allows agents to persist experience across runs.",
        embedding=[0.2] * 768,
        metadata={"source": "audit_trail", "run_id": str(run_id)},
        created_at=int(datetime.utcnow().timestamp()),
        updated_at=int(datetime.utcnow().timestamp())
    )
    knowledge_store.upsert_document(doc)
    
    knowledge_store.search_similar([0.2] * 768, filters={"run_id": str(run_id)})
    
    await asyncio.sleep(0.5)
    
    events = await repo.get_events_by_run(run_id)
    assert len(events) >= 2
    
    event_types = [e.event_type for e in events]
    assert "knowledge_upserted" in event_types
    assert "knowledge_searched" in event_types
    
    knowledge_store.close()

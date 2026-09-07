-- --- DNK-MRH-HEADER ---
-- mrh_id: "apps/api/sql/003_scones_l3_schema.sql"
-- purpose: "PostgreSQL schema for SCONES L3 Long-Term Personalized Memory Engine (pgvector + tsvector + RLS + Temporal Decay)"
-- canonical_source: true
-- alters_files: []
-- triggers_tasks: ["DNK-SCONES-L3-001"]
-- status: "Active"
-- version: "1.0.0"
-- updated_at: "2026-08-28"
-- author: "DNK-e.com Maksym"
-- --- END DNK-MRH-HEADER ---

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Таблиця для L3 long-term memories
CREATE TABLE IF NOT EXISTS scones_longterm_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workspace_id UUID NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'system',
    memory_type TEXT NOT NULL DEFAULT 'semantic',  -- "episodic", "semantic", "procedural"
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,  -- emotions, timestamps, context, entities
    embedding vector(768) NOT NULL,
    search_vector tsvector NOT NULL,
    recency_score FLOAT NOT NULL DEFAULT 1.0,  -- Temporal decay score
    retention_policy TEXT NOT NULL DEFAULT 'forever',  -- "forever", "project_scoped", "ephemeral"
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    consolidated_from TEXT DEFAULT NULL  -- "L2" або NULL (якщо пряме збереження)
);

-- GIN індекс для full-text search
CREATE INDEX IF NOT EXISTS scones_l3_search_vector_idx
ON scones_longterm_memories USING GIN (search_vector);

-- HNSW індекс для vector search
CREATE INDEX IF NOT EXISTS scones_l3_embedding_idx
ON scones_longterm_memories
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Індекс для швидкого temporal decay та фільтрації по користувачу/воркспейсу
CREATE INDEX IF NOT EXISTS scones_l3_user_ws_idx
ON scones_longterm_memories (workspace_id, user_id, created_at DESC);

-- Тригер для авто-оновлення tsvector
CREATE OR REPLACE FUNCTION scones_l3_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.memory_type, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.metadata::text, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS scones_l3_search_vector_trigger ON scones_longterm_memories;
CREATE TRIGGER scones_l3_search_vector_trigger
BEFORE INSERT OR UPDATE ON scones_longterm_memories
FOR EACH ROW EXECUTE FUNCTION scones_l3_search_vector_update();

-- Row Level Security (RLS)
ALTER TABLE scones_longterm_memories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS scones_l3_isolation_policy ON scones_longterm_memories;
CREATE POLICY scones_l3_isolation_policy ON scones_longterm_memories
FOR ALL
USING (
    workspace_id = current_setting('app.current_workspace_id', true)::uuid
    AND user_id = current_setting('app.current_user_id', true)::uuid
);

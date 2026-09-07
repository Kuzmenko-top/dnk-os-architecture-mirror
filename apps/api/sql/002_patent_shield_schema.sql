-- --- DNK-MRH-HEADER ---
-- mrh_id: "apps/api/sql/002_patent_shield_schema.sql"
-- purpose: "PostgreSQL schema for Patent Shield corpus with pgvector and tsvector hybrid search"
-- canonical_source: true
-- alters_files: []
-- triggers_tasks: ["DNK-PATENT-001"]
-- status: "Active"
-- version: "1.0.0"
-- updated_at: "2026-08-28"
-- author: "DNK-e.com Maksym"
-- --- END DNK-MRH-HEADER ---

-- Enable pgvector and uuid extensions if not enabled
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Таблиця для патентного корпусу
CREATE TABLE IF NOT EXISTS patent_corpus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patent_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    claims TEXT[] NOT NULL DEFAULT '{}',
    classifications TEXT[] DEFAULT '{}',
    filing_date DATE,
    grant_date DATE,
    assignee TEXT,
    jurisdiction TEXT DEFAULT 'US',
    embedding vector(768),
    search_vector tsvector,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- GIN індекс для повнотекстового пошуку
CREATE INDEX IF NOT EXISTS patent_corpus_search_vector_idx
ON patent_corpus USING GIN (search_vector);

-- HNSW індекс для семантичного векторного пошуку
CREATE INDEX IF NOT EXISTS patent_corpus_embedding_idx
ON patent_corpus
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Тригер для автоматичного оновлення search_vector при додаванні/оновленні
CREATE OR REPLACE FUNCTION patent_corpus_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.abstract, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.claims, ' '), '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS patent_corpus_search_vector_trigger ON patent_corpus;
CREATE TRIGGER patent_corpus_search_vector_trigger
BEFORE INSERT OR UPDATE ON patent_corpus
FOR EACH ROW EXECUTE FUNCTION patent_corpus_search_vector_update();

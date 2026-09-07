-- --- DNK-MRH-HEADER ---
-- mrh_id: "apps/api/sql/001_enable_fulltext_search.sql"
-- purpose: "Enable full-text tsvector search column, GIN indexes, and auto-update triggers for scones_error_solutions and scones_memories"
-- canonical_source: true
-- alters_files: []
-- triggers_tasks: ["DNK-HYBRID-SEARCH-001"]
-- status: "Active"
-- version: "1.0.0"
-- updated_at: "2026-08-28"
-- author: "DNK-e.com Maksym"
-- --- END DNK-MRH-HEADER ---

-- 1. scones_error_solutions tsvector schema extension
ALTER TABLE scones_error_solutions
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_search_vector
ON scones_error_solutions USING GIN (search_vector);

CREATE OR REPLACE FUNCTION scones_error_solutions_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.error_signature, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.error_text, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.root_cause, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.solution_text, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS scones_error_solutions_search_vector_trigger ON scones_error_solutions;
CREATE TRIGGER scones_error_solutions_search_vector_trigger
BEFORE INSERT OR UPDATE ON scones_error_solutions
FOR EACH ROW EXECUTE FUNCTION scones_error_solutions_search_vector_update();

-- 2. scones_memories tsvector schema extension
ALTER TABLE scones_memories
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_scones_memories_search_vector
ON scones_memories USING GIN (search_vector);

CREATE OR REPLACE FUNCTION scones_memories_search_vector_update()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.topic, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS scones_memories_search_vector_trigger ON scones_memories;
CREATE TRIGGER scones_memories_search_vector_trigger
BEFORE INSERT OR UPDATE ON scones_memories
FOR EACH ROW EXECUTE FUNCTION scones_memories_search_vector_update();

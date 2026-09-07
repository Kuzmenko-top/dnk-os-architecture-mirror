# PostgreSQL tsvector Auto-Update Triggers & UNION ALL RRF CTE Pattern

## 1. Weighted tsvector Field Auto-Update Trigger

To maintain full-text search vectors in PostgreSQL without manual application code updates, use `BEFORE INSERT OR UPDATE` triggers with `setweight`:

```sql
-- 1. Add tsvector column and GIN index
ALTER TABLE scones_error_solutions ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_search_vector 
    ON scones_error_solutions USING gin (search_vector);

-- 2. Create PL/pgSQL auto-update trigger function
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

-- 3. Attach trigger
DROP TRIGGER IF EXISTS scones_error_solutions_search_vector_trigger ON scones_error_solutions;
CREATE TRIGGER scones_error_solutions_search_vector_trigger
BEFORE INSERT OR UPDATE ON scones_error_solutions
FOR EACH ROW EXECUTE FUNCTION scones_error_solutions_search_vector_update();
```

## 2. UNION ALL RRF SQL CTE Pattern

A robust Reciprocal Rank Fusion (RRF) query using `UNION ALL` handles cases gracefully where either full-text or semantic search returns zero or few candidates:

```sql
WITH
fulltext AS (
  SELECT id, ROW_NUMBER() OVER (
    ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', %s)) DESC
  ) AS r
  FROM scones_error_solutions
  WHERE search_vector @@ plainto_tsquery('english', %s)
    AND (%s::text IS NULL OR metadata->>'tenant_id' = %s)
    AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
  LIMIT %s
),
semantic AS (
  SELECT id, ROW_NUMBER() OVER (
    ORDER BY embedding <=> %s::vector ASC
  ) AS r
  FROM scones_error_solutions
  WHERE (%s::text IS NULL OR metadata->>'tenant_id' = %s)
    AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
  LIMIT %s
),
rrf AS (
  SELECT id, 1.0 / (%s + r) AS s FROM fulltext
  UNION ALL
  SELECT id, 1.0 / (%s + r) AS s FROM semantic
)
SELECT
  m.id,
  SUM(s) AS rrf_score,
  m.error_signature,
  m.error_text,
  m.solution_text,
  m.root_cause,
  m.metadata,
  m.created_at,
  m.success_rate
FROM rrf
JOIN scones_error_solutions AS m USING (id)
GROUP BY m.id, m.error_signature, m.error_text, m.solution_text, m.root_cause, m.metadata, m.created_at, m.success_rate
ORDER BY rrf_score DESC
LIMIT %s;
```

### Key Advantages of UNION ALL RRF CTE:
- **Zero-candidate Resilience**: If fulltext search matches 0 documents (e.g. specialized code tokens/hashes with no dictionary words), semantic search results still pass through and get ranked cleanly.
- **Score Fusion**: Document IDs appearing in both fulltext and semantic result sets receive summed reciprocal ranks, giving higher overall `rrf_score`.
- **Pure SQL Execution**: Entire hybrid retrieval and reranking happens inside PostgreSQL in a single database roundtrip.

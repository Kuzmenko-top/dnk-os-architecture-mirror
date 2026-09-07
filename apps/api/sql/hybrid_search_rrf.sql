-- --- DNK-MRH-HEADER ---
-- mrh_id: "apps/api/sql/hybrid_search_rrf.sql"
-- purpose: "Reciprocal Rank Fusion (RRF) SQL CTE query merging tsvector BM25 lexical rank with pgvector cosine distance rank"
-- canonical_source: true
-- alters_files: []
-- triggers_tasks: ["DNK-HYBRID-SEARCH-001"]
-- status: "Active"
-- version: "1.0.0"
-- updated_at: "2026-08-28"
-- author: "DNK-e.com Maksym"
-- --- END DNK-MRH-HEADER ---

WITH
fulltext AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(search_vector, query) DESC) AS r
  FROM scones_error_solutions, plainto_tsquery('english', :keyword_query) AS query
  WHERE search_vector @@ query
    AND (:tenant_id IS NULL OR metadata->>'tenant_id' = :tenant_id)
    AND (:workspace_id IS NULL OR metadata->>'workspace_id' = :workspace_id)
  LIMIT :candidate_limit
),
semantic AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> :query_vector) AS r
  FROM scones_error_solutions
  WHERE (:tenant_id IS NULL OR metadata->>'tenant_id' = :tenant_id)
    AND (:workspace_id IS NULL OR metadata->>'workspace_id' = :workspace_id)
  LIMIT :candidate_limit
),
rrf AS (
  SELECT id, 1.0 / (:rrf_k + r) AS s FROM fulltext
  UNION ALL
  SELECT id, 1.0 / (:rrf_k + r) AS s FROM semantic
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
LIMIT :top_k;

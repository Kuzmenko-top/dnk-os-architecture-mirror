// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/lib/api/vector_client.ts"
// purpose: "Client API SDK and hooks for PostgreSQL Hybrid Vector Search, Ingestion & Cross-Encoder Reranking"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-VECTOR-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

export interface VectorSearchResult {
  id: string;
  tenant_id: string;
  workspace_id: string;
  memory_type: string;
  content: string;
  metadata?: Record<string, any>;
  score?: number;
  rrf_score?: number;
  dense_rank?: number;
  sparse_rank?: number;
  rerank_score?: number;
  rerank_model?: string;
}

export interface HybridSearchResponse {
  query: string;
  tenant_id: string;
  workspace_id: string;
  results: VectorSearchResult[];
  total_count: number;
  reranked: boolean;
  metrics: {
    dense_latency_ms: number;
    sparse_latency_ms: number;
    fusion_latency_ms: number;
    rerank_latency_ms: number;
    total_latency_ms: number;
    dense_candidates_count: number;
    sparse_candidates_count: number;
  };
}

export interface HybridSearchPayload {
  query: string;
  dense_vector?: number[];
  tenant_id?: string;
  workspace_id?: string;
  top_k?: number;
  rrf_k?: number;
  dense_weight?: number;
  sparse_weight?: number;
  rerank?: boolean;
  rerank_top_k?: number;
  memory_type?: string;
  filter_metadata?: Record<string, any>;
}

export const vectorClient = {
  async hybridSearch(payload: HybridSearchPayload): Promise<HybridSearchResponse> {
    const res = await fetch("/api/v1/vector/hybrid-search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(`Hybrid search failed with status ${res.status}`);
    }
    return res.json();
  },

  async denseSearch(tenant_id: string, workspace_id: string, top_k = 10): Promise<{ results: VectorSearchResult[] }> {
    const params = new URLSearchParams({ tenant_id, workspace_id, top_k: String(top_k) });
    const res = await fetch(`/api/v1/vector/search/dense?${params.toString()}`);
    if (!res.ok) throw new Error(`Dense search failed: ${res.status}`);
    return res.json();
  },

  async sparseSearch(q: string, tenant_id: string, workspace_id: string, top_k = 10): Promise<{ results: VectorSearchResult[] }> {
    const params = new URLSearchParams({ q, tenant_id, workspace_id, top_k: String(top_k) });
    const res = await fetch(`/api/v1/vector/search/sparse?${params.toString()}`);
    if (!res.ok) throw new Error(`Sparse search failed: ${res.status}`);
    return res.json();
  },

  async rerank(query: string, documents: VectorSearchResult[], top_k = 5): Promise<{ results: VectorSearchResult[] }> {
    const res = await fetch("/api/v1/vector/rerank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, documents, top_k }),
    });
    if (!res.ok) throw new Error(`Rerank failed: ${res.status}`);
    return res.json();
  },

  async getCollectionStats(workspace_id: string): Promise<any> {
    const res = await fetch(`/api/v1/vector/collections/${encodeURIComponent(workspace_id)}/stats`);
    if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`);
    return res.json();
  },
};

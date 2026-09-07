// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/vector/HybridSearchInterface.tsx"
// purpose: "React Interactive Interface for Hybrid PostgreSQL pgvector + tsvector Search with RRF and Cross-Encoder tuning"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-VECTOR-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import { vectorClient, HybridSearchResponse, VectorSearchResult } from "../../lib/api/vector_client";
import { SearchResultsList } from "./SearchResultsList";
import { RerankedResultsCard } from "./RerankedResultsCard";

interface HybridSearchInterfaceProps {
  tenantId?: string;
  workspaceId?: string;
}

export const HybridSearchInterface: React.FC<HybridSearchInterfaceProps> = ({
  tenantId = "default_tenant",
  workspaceId = "default_workspace",
}) => {
  const [query, setQuery] = useState("");
  const [denseWeight, setDenseWeight] = useState(1.0);
  const [sparseWeight, setSparseWeight] = useState(1.0);
  const [enableRerank, setEnableRerank] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<HybridSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await vectorClient.hybridSearch({
        query: query.trim(),
        tenant_id: tenantId,
        workspace_id: workspaceId,
        dense_weight: denseWeight,
        sparse_weight: sparseWeight,
        rerank: enableRerank,
        top_k: 10,
        rerank_top_k: 5,
      });
      setResponse(data);
    } catch (err: any) {
      setError(err.message || "Failed to execute search");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <span>⚡</span> PostgreSQL Hybrid Search (pgvector + tsvector)
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Zero-Dual-Write multi-channel retrieval with Reciprocal Rank Fusion & Cross-Encoder reranking
        </p>
      </div>

      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents, conversation memories, or code snippets..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition"
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-300">
          <div>
            <label className="block mb-1 font-medium text-slate-400">Dense Weight (pgvector): {denseWeight}</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={denseWeight}
              onChange={(e) => setDenseWeight(parseFloat(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>
          <div>
            <label className="block mb-1 font-medium text-slate-400">Sparse Weight (tsvector): {sparseWeight}</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={sparseWeight}
              onChange={(e) => setSparseWeight(parseFloat(e.target.value))}
              className="w-full accent-amber-500"
            />
          </div>
          <div className="flex items-center gap-2 pt-3">
            <input
              type="checkbox"
              id="rerank-toggle"
              checked={enableRerank}
              onChange={(e) => setEnableRerank(e.target.checked)}
              className="rounded accent-indigo-600"
            />
            <label htmlFor="rerank-toggle" className="cursor-pointer font-medium text-slate-200">
              Cross-Encoder Reranker
            </label>
          </div>
        </div>
      </form>

      {error && (
        <div className="p-3 bg-rose-950/50 border border-rose-800 rounded-lg text-rose-300 text-xs">
          {error}
        </div>
      )}

      {response && response.metrics && (
        <div className="flex flex-wrap gap-4 text-xs font-mono bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-slate-400">
          <div>Total: <span className="text-indigo-400">{response.metrics.total_latency_ms}ms</span></div>
          <div>Dense ({response.metrics.dense_candidates_count}): <span className="text-blue-400">{response.metrics.dense_latency_ms}ms</span></div>
          <div>Sparse ({response.metrics.sparse_candidates_count}): <span className="text-amber-400">{response.metrics.sparse_latency_ms}ms</span></div>
          <div>Fusion: <span className="text-emerald-400">{response.metrics.fusion_latency_ms}ms</span></div>
          {response.reranked && (
            <div>Rerank: <span className="text-purple-400">{response.metrics.rerank_latency_ms}ms</span></div>
          )}
        </div>
      )}

      {response && (
        <div className="space-y-4">
          {response.reranked ? (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-300">Reranked Matches</h3>
              {response.results.map((item: VectorSearchResult, idx: number) => (
                <RerankedResultsCard key={item.id || idx} item={item} rank={idx + 1} />
              ))}
            </div>
          ) : (
            <SearchResultsList results={response.results} isLoading={isLoading} />
          )}
        </div>
      )}
    </div>
  );
};

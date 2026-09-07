// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/vector/SearchResultsList.tsx"
// purpose: "React Component for displaying Hybrid pgvector + tsvector Search results with RRF score tags"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-VECTOR-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { VectorSearchResult } from "../../lib/api/vector_client";

interface SearchResultsListProps {
  results: VectorSearchResult[];
  isLoading?: boolean;
}

export const SearchResultsList: React.FC<SearchResultsListProps> = ({ results, isLoading }) => {
  if (isLoading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[1, 2, 3].map((n) => (
          <div key={n} className="h-24 bg-slate-800 rounded-lg border border-slate-700" />
        ))}
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 bg-slate-900/50 rounded-lg border border-slate-800">
        No search results found. Try adjusting your query or filters.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {results.map((item, index) => (
        <div
          key={item.id || index}
          className="p-4 bg-slate-900/80 rounded-lg border border-slate-800 hover:border-indigo-500/50 transition-colors"
        >
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
              {item.memory_type}
            </span>
            <div className="flex items-center gap-2 text-xs font-mono">
              {item.rrf_score !== undefined && (
                <span className="text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                  RRF: {item.rrf_score}
                </span>
              )}
              {item.dense_rank && (
                <span className="text-blue-400 bg-blue-950/40 px-1.5 py-0.5 rounded">
                  D#{item.dense_rank}
                </span>
              )}
              {item.sparse_rank && (
                <span className="text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded">
                  S#{item.sparse_rank}
                </span>
              )}
            </div>
          </div>
          <p className="text-sm text-slate-200 line-clamp-3 leading-relaxed">{item.content}</p>
          {item.metadata && Object.keys(item.metadata).length > 0 && (
            <div className="mt-2 pt-2 border-t border-slate-800/80 text-xs text-slate-400 flex flex-wrap gap-2">
              {Object.entries(item.metadata).map(([k, v]) => (
                <span key={k} className="bg-slate-800/60 px-1.5 py-0.5 rounded">
                  {k}: {String(v)}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

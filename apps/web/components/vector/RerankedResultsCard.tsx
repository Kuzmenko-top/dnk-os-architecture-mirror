// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/vector/RerankedResultsCard.tsx"
// purpose: "React Component for presenting Cross-Encoder reranked items with semantic confidence metrics"
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

interface RerankedResultsCardProps {
  item: VectorSearchResult;
  rank: number;
}

export const RerankedResultsCard: React.FC<RerankedResultsCardProps> = ({ item, rank }) => {
  const scorePercent = item.rerank_score ? Math.round(item.rerank_score * 100) : 0;

  return (
    <div className="p-4 bg-slate-900 border border-indigo-900/40 rounded-xl relative overflow-hidden shadow-lg shadow-indigo-950/20">
      <div className="absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 to-purple-600" />
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs">
            #{rank}
          </span>
          <span className="text-xs font-medium text-slate-300">
            {item.memory_type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <span className="text-xs font-mono font-bold text-indigo-400">
              {scorePercent}% match
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {item.rerank_model || "cross-encoder"}
          </span>
        </div>
      </div>
      <p className="text-sm text-slate-100 line-clamp-4 leading-relaxed font-sans">{item.content}</p>
    </div>
  );
};

// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/memory-l3/SCONESL3Dashboard.tsx"
// purpose: "Generative UI Dashboard Component for SCONES L3 Long-Term Memory (Temporal Decay, Sleep Consolidation & Hybrid Search)"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-SCONES-L3-001", "DNK-SCONES-L3-002"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useSCONESL3Memory } from '../../ui/hooks/useSCONESL3Memory';

export const SCONESL3Dashboard: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const { memories, stats, loading, consolidating, error, fetchMemories, consolidate } =
    useSCONESL3Memory();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchMemories(searchQuery);
  };

  return (
    <div className="p-6 bg-slate-950 text-slate-100 min-h-screen font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-2xl">🧠</span>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              SCONES L3 Long-Term Memory Hub
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
              Native PostgreSQL SOTA
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous Sleep Consolidation, Hybrid RRF Search & Temporal Decay Tracking
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => consolidate(7)}
            disabled={consolidating}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-medium text-sm rounded-lg shadow-md transition duration-150 disabled:opacity-50 flex items-center gap-2"
          >
            {consolidating ? (
              <>
                <span className="animate-spin text-sm">🔄</span> Consolidating...
              </>
            ) : (
              <>
                <span>🌙</span> Run Sleep Consolidation
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-rose-950/70 border border-rose-800 text-rose-300 rounded-lg text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Total L3 Memories</div>
          <div className="text-2xl font-bold text-white mt-1">{stats.total}</div>
          <div className="text-xs text-emerald-400 mt-1">Persistent & Deduplicated</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Memory Clusters/Types</div>
          <div className="text-2xl font-bold text-teal-300 mt-1">{stats.types || 1}</div>
          <div className="text-xs text-slate-400 mt-1">Semantic, Episodic, Procedural</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400 uppercase tracking-wider">Avg Recency Weight</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {(stats.avg_recency * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 mt-1">Temporal Decay (Half-life ~7d)</div>
        </div>
      </div>

      {/* Search & Query Bar */}
      <form onSubmit={handleSearch} className="mt-6 flex gap-3">
        <input
          type="text"
          placeholder="Hybrid Search long-term memories (e.g. dark mode, UI preferences, docker port)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 bg-slate-900 border border-slate-700 text-slate-100 px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition"
        >
          🔍 Search
        </button>
      </form>

      {/* Memory Table */}
      <div className="mt-6 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-800 font-medium text-sm text-slate-300 flex justify-between items-center">
          <span>Persisted L3 Memories</span>
          <span className="text-xs text-slate-500">{memories.length} results</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Loading memories...</div>
        ) : memories.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No long-term memories found. Run consolidation or add memories.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {memories.map((mem) => (
              <div key={mem.id} className="p-4 hover:bg-slate-800/40 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 text-xs font-mono uppercase bg-emerald-950 text-emerald-400 border border-emerald-800 rounded">
                        {mem.memory_type}
                      </span>
                      {mem.metadata?.consolidated_from && (
                        <span className="px-2 py-0.5 text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 rounded">
                          🌙 Consolidated from {mem.metadata.consolidated_from}
                        </span>
                      )}
                      <span className="text-xs text-slate-500 font-mono">
                        {new Date(mem.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-200 leading-relaxed font-medium">
                      {mem.content}
                    </p>
                  </div>

                  {/* Scoring Column */}
                  <div className="text-right flex flex-col items-end gap-1">
                    <span className="text-xs font-mono text-emerald-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                      Score: {(mem.final_score ?? mem.recency_score ?? 1.0).toFixed(3)}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Recency: {((mem.recency_score ?? 1.0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_patent_shield_dashboard"
// purpose: "Patent Shield & Clean-Room IP Guard Visual Dashboard"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-PATENT-001"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { usePatentShield } from '../../ui/hooks/usePatentShield';

export const PatentShieldDashboard: React.FC = () => {
  const { loading, error, assessment, patents, searchPatents, assessRisk } = usePatentShield();
  const [query, setQuery] = useState('declarative video animation engine');
  const [spec, setSpec] = useState('DNK-CLEANROOM-001-video-engine with GPU keyframe shaders');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      searchPatents(query);
    }
  };

  const handleAssess = (e: React.FormEvent) => {
    e.preventDefault();
    if (spec.trim() && query.trim()) {
      assessRisk(spec, query);
    }
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'critical':
        return 'bg-red-900/40 text-red-400 border-red-700';
      case 'high':
        return 'bg-orange-900/40 text-orange-400 border-orange-700';
      case 'medium':
        return 'bg-yellow-900/40 text-yellow-400 border-yellow-700';
      case 'low':
      default:
        return 'bg-emerald-900/40 text-emerald-400 border-emerald-700';
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6 bg-slate-950 text-slate-100 rounded-xl border border-slate-800">
      <div className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            🛡️ Patent Shield & Clean-Room IP Guard
          </h1>
          <p className="text-sm text-slate-400">
            Real-time multi-factor patent infringement risk scoring, hybrid search, and claims overlap auditor.
          </p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-cyan-950/60 border border-cyan-800 text-cyan-400 text-xs rounded-full font-mono">
            Hybrid Search (RRF)
          </span>
          <span className="px-3 py-1 bg-purple-950/60 border border-purple-800 text-purple-400 text-xs rounded-full font-mono">
            PostgreSQL SSOT
          </span>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/50 border border-red-800 text-red-300 rounded-lg text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Input Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <form onSubmit={handleSearch} className="space-y-2 p-4 bg-slate-900/60 rounded-lg border border-slate-800">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Patent Query (Google Patents / USPTO)
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-md text-sm text-white focus:outline-none focus:border-cyan-500"
              placeholder="e.g. declarative video animation engine"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md text-sm font-medium transition disabled:opacity-50"
            >
              Search
            </button>
          </div>
        </form>

        <form onSubmit={handleAssess} className="space-y-2 p-4 bg-slate-900/60 rounded-lg border border-slate-800">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Clean-Room Specification
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={spec}
              onChange={(e) => setSpec(e.target.value)}
              className="flex-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-md text-sm text-white focus:outline-none focus:border-purple-500"
              placeholder="e.g. DNK-CLEANROOM-001..."
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-md text-sm font-medium transition disabled:opacity-50"
            >
              Assess Risk
            </button>
          </div>
        </form>
      </div>

      {/* Risk Assessment Results Card */}
      {assessment && (
        <div className="p-5 bg-slate-900/80 rounded-lg border border-slate-800 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white">Risk Assessment Summary</h2>
            <div className={`px-4 py-1.5 rounded-full border text-sm font-bold uppercase tracking-wider ${getRiskColor(assessment.overall_risk)}`}>
              Overall Risk: {assessment.overall_risk}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="text-xs text-slate-400">Max Similarity Score</span>
              <p className="text-xl font-bold text-cyan-400">{(assessment.max_similarity * 100).toFixed(1)}%</p>
            </div>
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="text-xs text-slate-400">Detected Risk Factors</span>
              <p className="text-xl font-bold text-yellow-400">{assessment.risk_factors.length}</p>
            </div>
            <div className="p-3 bg-slate-950 rounded border border-slate-800">
              <span className="text-xs text-slate-400">Compliance Action Items</span>
              <p className="text-xl font-bold text-purple-400">{assessment.recommendations.length}</p>
            </div>
          </div>

          {/* Recommendations List */}
          {assessment.recommendations.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300">Actionable Recommendations:</h3>
              <ul className="space-y-1">
                {assessment.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-slate-300 bg-slate-950/60 p-2.5 rounded border border-slate-800/80 flex items-start gap-2">
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Patent Results Table */}
      {patents.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-white">Matched Patent Corpus ({patents.length})</h2>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-3">Patent ID</th>
                  <th className="p-3">Title</th>
                  <th className="p-3">Abstract</th>
                  <th className="p-3">RRF Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                {patents.map((p, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40 transition">
                    <td className="p-3 font-mono font-medium text-cyan-400">{p.patent_id}</td>
                    <td className="p-3 font-medium text-white">{p.title}</td>
                    <td className="p-3 text-xs text-slate-400 line-clamp-2">{p.abstract}</td>
                    <td className="p-3 font-mono text-xs text-purple-400">
                      {p.rrf_score !== undefined ? (p.rrf_score * 100).toFixed(1) + '%' : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

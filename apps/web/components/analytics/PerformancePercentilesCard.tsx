// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_performance_percentiles_card"
// purpose: "Performance percentiles visualization card showing p50, p95, p99, avg and counts per endpoint"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface Percentiles {
  p50: number;
  p95: number;
  p99: number;
  avg: number;
  count: number;
}

interface PerformancePercentilesCardProps {
  performance: Record<string, Percentiles>;
}

export function PerformancePercentilesCard({ performance = {} }: PerformancePercentilesCardProps) {
  const entries = Object.entries(performance);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Performance Percentiles</h3>
        <span className="text-xs text-slate-400 font-mono">{entries.length} endpoints</span>
      </div>

      {entries.length === 0 ? (
        <div className="py-12 flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
          No latency performance data available
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto pr-1">
          {entries.map(([endpoint, metrics]) => (
            <div
              key={endpoint}
              className="bg-slate-950/40 border border-slate-800/80 rounded-lg p-3 hover:border-slate-700/80 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs text-cyan-300 font-semibold truncate max-w-xs" title={endpoint}>
                  {endpoint}
                </span>
                <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                  {metrics.count} calls
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="bg-slate-900/80 p-2 rounded border border-slate-800/50">
                  <p className="text-slate-400 text-[10px] uppercase">p50</p>
                  <p className="font-bold text-emerald-400 font-mono mt-0.5">{(metrics.p50 ?? 0).toFixed(1)} ms</p>
                </div>
                <div className="bg-slate-900/80 p-2 rounded border border-slate-800/50">
                  <p className="text-slate-400 text-[10px] uppercase">p95</p>
                  <p className="font-bold text-yellow-400 font-mono mt-0.5">{(metrics.p95 ?? 0).toFixed(1)} ms</p>
                </div>
                <div className="bg-slate-900/80 p-2 rounded border border-slate-800/50">
                  <p className="text-slate-400 text-[10px] uppercase">p99</p>
                  <p className="font-bold text-rose-400 font-mono mt-0.5">{(metrics.p99 ?? 0).toFixed(1)} ms</p>
                </div>
                <div className="bg-slate-900/80 p-2 rounded border border-slate-800/50">
                  <p className="text-slate-400 text-[10px] uppercase">avg</p>
                  <p className="font-bold text-indigo-300 font-mono mt-0.5">{(metrics.avg ?? 0).toFixed(1)} ms</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PerformancePercentilesCard;

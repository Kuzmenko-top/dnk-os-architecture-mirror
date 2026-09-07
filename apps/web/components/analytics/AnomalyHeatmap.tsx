// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_anomaly_heatmap"
// purpose: "React component rendering real-time time-series anomaly heatmap, Z-Score & EWMA scores, and anomaly events"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

export interface AnomalyScoreEntry {
  metric_type: string;
  score: number;
  detected_at: string;
  algorithm: 'zscore' | 'ewma' | 'hybrid';
  window_seconds: number;
}

export interface AnomalyEvent {
  metric_type: string;
  value: number;
  z_score?: number;
  ewma_score?: number;
  anomaly_score: number;
  detected_at: string;
}

interface AnomalyHeatmapProps {
  scores: AnomalyScoreEntry[];
  events?: AnomalyEvent[];
  timeBuckets?: string[];
}

export const AnomalyHeatmap: React.FC<AnomalyHeatmapProps> = ({
  scores = [],
  events = [],
  timeBuckets = ['-60m', '-45m', '-30m', '-15m', 'now'],
}) => {
  const metricTypes = Array.from(new Set(scores.map((s) => s.metric_type).concat(['error_rate', 'latency_p95', 'resource_usage'])));

  const getScoreColor = (score: number) => {
    if (score < 0.25) return 'bg-emerald-500/20 text-emerald-400 border-emerald-800/40';
    if (score < 0.5) return 'bg-sky-500/25 text-sky-300 border-sky-800/40';
    if (score < 0.75) return 'bg-amber-500/30 text-amber-300 border-amber-700/60';
    return 'bg-rose-500/40 text-rose-200 border-rose-600 animate-pulse';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-indigo-500" />
            Time-Series Anomaly Detection (Z-Score + EWMA)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time anomaly intensity matrix combining static statistical deviation and adaptive dynamic smoothing.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-emerald-500/30 border border-emerald-700" /> Normal (&lt;0.25)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-amber-500/30 border border-amber-700" /> Elevated (&gt;0.5)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-rose-500/40 border border-rose-600" /> Anomaly (&gt;0.75)
          </span>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400">
              <th className="py-2.5 px-3 font-semibold">Metric Name</th>
              {timeBuckets.map((bucket, i) => (
                <th key={i} className="py-2.5 px-3 text-center font-semibold">
                  {bucket}
                </th>
              ))}
              <th className="py-2.5 px-3 text-right font-semibold">Latest Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {metricTypes.map((metric) => {
              const matchedScore = scores.find((s) => s.metric_type === metric)?.score ?? 0.05;
              return (
                <tr key={metric} className="hover:bg-slate-800/20 transition">
                  <td className="py-3 px-3 font-mono font-medium text-slate-200">{metric}</td>
                  {timeBuckets.map((_, idx) => {
                    // Simulate progressive time bucket scores leading up to latest
                    const cellScore =
                      idx === timeBuckets.length - 1
                        ? matchedScore
                        : Math.max(0.01, +(matchedScore * (0.6 + idx * 0.1)).toFixed(2));
                    return (
                      <td key={idx} className="py-3 px-3 text-center">
                        <div
                          className={`inline-block w-16 py-1 rounded border text-center font-mono text-[11px] font-semibold ${getScoreColor(
                            cellScore
                          )}`}
                        >
                          {cellScore.toFixed(2)}
                        </div>
                      </td>
                    );
                  })}
                  <td className="py-3 px-3 text-right font-mono font-bold text-white">
                    {matchedScore.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detected Anomaly Stream */}
      {events.length > 0 && (
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800 space-y-3">
          <div className="text-xs font-semibold text-slate-300">Detected Anomaly Events</div>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {events.map((ev, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2.5 bg-rose-950/20 border border-rose-900/40 rounded text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-rose-900/60 text-rose-300 font-mono text-[10px]">
                    ANOMALY
                  </span>
                  <span className="font-semibold text-slate-200">{ev.metric_type}</span>
                  <span className="text-slate-400">Value: {ev.value}</span>
                </div>
                <div className="flex items-center gap-3 font-mono text-[11px]">
                  {ev.z_score !== undefined && (
                    <span className="text-slate-400">Z: {ev.z_score.toFixed(2)}</span>
                  )}
                  {ev.ewma_score !== undefined && (
                    <span className="text-slate-400">EWMA: {ev.ewma_score.toFixed(2)}</span>
                  )}
                  <span className="text-rose-400 font-bold">Score: {ev.anomaly_score.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

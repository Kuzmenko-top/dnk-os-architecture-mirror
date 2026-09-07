// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_live_metrics_pulse_card"
// purpose: "Real-time Live Metrics Pulse Card displaying live activity, latency, and error counter via WebSocket"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { useWorkspaceLiveMetrics } from '../../lib/api/analytics_client';

interface LiveMetricsPulseCardProps {
  workspaceId: string;
}

export function LiveMetricsPulseCard({ workspaceId }: LiveMetricsPulseCardProps) {
  const { liveMetrics, connected } = useWorkspaceLiveMetrics(workspaceId);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">⚡</span>
          <h3 className="text-lg font-semibold text-white">Live Metrics Stream</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">
            {connected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
          <div
            className={`w-3 h-3 rounded-full transition-all duration-300 ${
              connected ? 'bg-emerald-500 shadow-lg shadow-emerald-500/50 animate-pulse' : 'bg-rose-500 shadow-lg shadow-rose-500/50'
            }`}
          />
        </div>
      </div>

      {liveMetrics ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Activity (5m window)</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-3xl font-extrabold text-cyan-400">{liveMetrics.activity_count}</p>
              <span className="text-xs text-slate-500">events</span>
            </div>
          </div>
          <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Avg Latency</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-3xl font-extrabold text-indigo-400">
                {liveMetrics.performance?.avg_latency !== undefined ? liveMetrics.performance.avg_latency.toFixed(2) : '0.00'}
              </p>
              <span className="text-xs text-slate-500">ms</span>
            </div>
          </div>
          <div className="bg-slate-950/50 border border-slate-800/80 rounded-lg p-4">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Errors (5m window)</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className={`text-3xl font-extrabold ${liveMetrics.performance?.error_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {liveMetrics.performance?.error_count ?? 0}
              </p>
              <span className="text-xs text-slate-500">errors</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center py-6 text-slate-500 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-slate-500 animate-ping" />
            <span>Waiting for live metrics updates from WebSocket...</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default LiveMetricsPulseCard;

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_worker_QueueDepthChart"
// purpose: "React Component for Real-time Queue Depth & Latency Visualization (DNK-PLATFORM-SCALE-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { useQueueMetrics } from '../../lib/api/worker_client';

export interface QueueDepthChartProps {
  queueId: string;
}

export const QueueDepthChart: React.FC<QueueDepthChartProps> = ({ queueId }) => {
  const { metrics, loading } = useQueueMetrics(queueId);

  if (loading && !metrics) return <div className="p-4 text-slate-400 text-sm">Loading queue metrics...</div>;

  const queueDepth = metrics?.queue_depth || 0;
  const p95Latency = metrics?.latency_p95_ms || 0;
  const saturation = metrics?.saturation_pct || 0;
  const throughput = metrics?.throughput_tps || 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
        <span>Queue Telemetry: {queueId}</span>
        <span className="text-xs font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
          Live Stream
        </span>
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <div className="text-xs text-slate-400">Queue Depth</div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{queueDepth}</div>
        </div>
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <div className="text-xs text-slate-400">Latency p95</div>
          <div className="text-2xl font-bold text-amber-400 font-mono">{p95Latency} ms</div>
        </div>
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <div className="text-xs text-slate-400">Saturation</div>
          <div className="text-2xl font-bold text-cyan-400 font-mono">{saturation}%</div>
        </div>
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <div className="text-xs text-slate-400">Throughput</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">{throughput} tps</div>
        </div>
      </div>

      <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
        <div
          className="bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 h-full transition-all duration-500"
          style={{ width: `${Math.min(100, saturation)}%` }}
        />
      </div>
    </div>
  );
};

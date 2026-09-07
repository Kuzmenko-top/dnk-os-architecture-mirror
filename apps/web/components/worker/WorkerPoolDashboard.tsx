// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_worker_WorkerPoolDashboard"
// purpose: "React Component for Worker Pool Dashboard (DNK-PLATFORM-SCALE-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { useWorkerPools } from '../../lib/api/worker_client';

export interface WorkerPoolDashboardProps {
  workspaceId: string;
}

export const WorkerPoolDashboard: React.FC<WorkerPoolDashboardProps> = ({ workspaceId }) => {
  const { pools, loading, error, scalePool, refetch } = useWorkerPools(workspaceId);

  if (loading) return <div className="p-4 text-slate-400">Loading worker pools...</div>;
  if (error) return <div className="p-4 text-red-400">Error: {error}</div>;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Worker Pool Orchestrator</h2>
          <p className="text-sm text-slate-400">Manage auto-scaling worker pools and target queue depths</p>
        </div>
        <button
          onClick={refetch}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-medium rounded-lg transition"
        >
          Refresh Pools
        </button>
      </div>

      {pools.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-sm">No active worker pools configured for this workspace.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pools.map((pool) => (
            <div key={pool.id} className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-slate-200">{pool.name}</h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-mono">
                    {pool.min_workers} - {pool.max_workers} Workers
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 my-3 text-xs text-slate-400 font-mono">
                  <div>Target Depth: <span className="text-slate-200">{pool.target_queue_depth}</span></div>
                  <div>Scale-Up Threshold: <span className="text-amber-400">{pool.scale_up_threshold}</span></div>
                  <div>Idle Timeout: <span className="text-slate-200">{pool.scale_down_idle_seconds}s</span></div>
                  <div>Active Workers: <span className="text-emerald-400">{pool.active_workers || pool.min_workers}</span></div>
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-3 border-t border-slate-800/60">
                <button
                  onClick={() => scalePool(pool.id, (pool.active_workers || pool.min_workers) + 1)}
                  className="flex-1 py-1 px-2 bg-emerald-900/40 hover:bg-emerald-800/60 text-emerald-300 text-xs rounded font-medium transition"
                >
                  Scale Up +1
                </button>
                <button
                  onClick={() => scalePool(pool.id, Math.max(pool.min_workers, (pool.active_workers || pool.min_workers) - 1))}
                  className="flex-1 py-1 px-2 bg-amber-900/40 hover:bg-amber-800/60 text-amber-300 text-xs rounded font-medium transition"
                >
                  Scale Down -1
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

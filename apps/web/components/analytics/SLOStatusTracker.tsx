// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_slo_status_tracker"
// purpose: "React component displaying SLA/SLO uptime, error budget consumption, burn rate, and latency p95 tracker"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

export interface SLOSnapshot {
  id: string;
  workspace_id: string;
  snapshot_time: string;
  uptime_percentage: number;
  error_budget_remaining: number;
  latency_p95_ms: number;
  latency_slo_target_ms: number;
  slo_status: 'meeting' | 'at_risk' | 'breached';
  burn_rate: number;
}

export interface BurnRateChartPoint {
  timestamp: string;
  burn_rate: number;
  error_budget_remaining: number;
  threshold: number;
}

interface SLOStatusTrackerProps {
  currentStatus: SLOSnapshot | null;
  burnRateChart?: BurnRateChartPoint[];
}

export const SLOStatusTracker: React.FC<SLOStatusTrackerProps> = ({
  currentStatus,
  burnRateChart = [],
}) => {
  if (!currentStatus) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-400 text-sm animate-pulse">
        Loading SLA/SLO Monitoring data...
      </div>
    );
  }

  const {
    uptime_percentage,
    error_budget_remaining,
    latency_p95_ms,
    latency_slo_target_ms,
    slo_status,
    burn_rate,
  } = currentStatus;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'meeting':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Meeting SLO
          </span>
        );
      case 'at_risk':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-950 text-amber-400 border border-amber-800 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            At Risk
          </span>
        );
      case 'breached':
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-400" />
            Breached
          </span>
        );
    }
  };

  const budgetPct = Math.max(0, Math.min(100, Math.round(error_budget_remaining * 100)));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-emerald-500" />
            SLA / SLO Live Monitor (Rolling 24h)
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Tracking Uptime %, Error Budget, Burn Rate, and Latency against target Service Level Objectives.
          </p>
        </div>
        <div>{getStatusBadge(slo_status)}</div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Uptime */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
          <div className="text-xs text-slate-400 font-medium">Uptime Target &gt;= 99.90%</div>
          <div className="text-2xl font-bold text-white mt-1">
            {uptime_percentage.toFixed(2)}%
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3">
            <div
              className={`h-1.5 rounded-full ${
                uptime_percentage >= 99.90 ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, uptime_percentage)}%` }}
            />
          </div>
        </div>

        {/* Error Budget Remaining */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
          <div className="text-xs text-slate-400 font-medium">Error Budget Remaining</div>
          <div className="text-2xl font-bold text-white mt-1">{budgetPct}%</div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3">
            <div
              className={`h-1.5 rounded-full ${
                budgetPct > 30 ? 'bg-indigo-500' : budgetPct > 10 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${budgetPct}%` }}
            />
          </div>
        </div>

        {/* Burn Rate */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
          <div className="text-xs text-slate-400 font-medium">Burn Rate (Threshold &lt;= 1.0)</div>
          <div
            className={`text-2xl font-bold mt-1 ${
              burn_rate <= 1.0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {burn_rate.toFixed(2)}x
          </div>
          <div className="text-[11px] text-slate-400 mt-2">
            {burn_rate <= 1.0 ? 'Sustainable consumption' : 'Fast budget depletion'}
          </div>
        </div>

        {/* Latency p95 */}
        <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
          <div className="text-xs text-slate-400 font-medium">
            Latency p95 (SLO &lt; {latency_slo_target_ms}ms)
          </div>
          <div
            className={`text-2xl font-bold mt-1 ${
              latency_p95_ms <= latency_slo_target_ms ? 'text-white' : 'text-rose-400'
            }`}
          >
            {latency_p95_ms}ms
          </div>
          <div className="text-[11px] text-slate-400 mt-2">
            Margin: {latency_slo_target_ms - latency_p95_ms}ms
          </div>
        </div>
      </div>

      {/* Burn Rate Timeline Preview */}
      {burnRateChart.length > 0 && (
        <div className="bg-slate-950/40 p-4 rounded-lg border border-slate-800">
          <div className="text-xs font-semibold text-slate-300 mb-3 flex items-center justify-between">
            <span>Burn Rate History</span>
            <span className="text-[11px] text-slate-500">1.0x Baseline Limit</span>
          </div>
          <div className="h-20 flex items-end gap-1 pt-2">
            {burnRateChart.map((point, idx) => {
              const heightPct = Math.min(100, Math.max(10, Math.round((point.burn_rate / 2.0) * 100)));
              const isOver = point.burn_rate > 1.0;
              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center group relative cursor-pointer"
                >
                  <div
                    className={`w-full rounded-t transition-all ${
                      isOver ? 'bg-rose-500 group-hover:bg-rose-400' : 'bg-indigo-500 group-hover:bg-indigo-400'
                    }`}
                    style={{ height: `${heightPct}%` }}
                  />
                  {/* Tooltip */}
                  <div className="absolute bottom-full mb-1 hidden group-hover:block bg-slate-800 text-[10px] text-white px-2 py-1 rounded shadow z-10 whitespace-nowrap">
                    Burn: {point.burn_rate}x | Budget: {Math.round(point.error_budget_remaining * 100)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

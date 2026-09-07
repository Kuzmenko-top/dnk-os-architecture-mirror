// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_app_analytics_page"
// purpose: "Workspace Analytics Dashboard page connecting real-time metrics, timeline, percentiles, team activity and error logs"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useWorkspaceAnalytics } from '../../lib/api/analytics_client';
import { LiveMetricsPulseCard } from '../../components/analytics/LiveMetricsPulseCard';
import { ActivityTimelineChart } from '../../components/analytics/ActivityTimelineChart';
import { PerformancePercentilesCard } from '../../components/analytics/PerformancePercentilesCard';
import { WorkspaceUsersActivityTable } from '../../components/analytics/WorkspaceUsersActivityTable';
import { WorkspaceErrorsLog } from '../../components/analytics/WorkspaceErrorsLog';

export default function AnalyticsDashboardPage() {
  const [workspaceId, setWorkspaceId] = useState<string>('ws_alpha');
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');

  const timeRangeHours =
    timeRange === '1h' ? 1 : timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720;

  const { metrics, loading, error } = useWorkspaceAnalytics(workspaceId, timeRangeHours);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col p-6 gap-6 selection:bg-blue-600/30">
      {/* Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/40 border border-slate-800/60 p-5 rounded-2xl backdrop-blur-md shadow-2xl">
        <div className="flex items-center gap-3">
          <span className="text-4xl filter drop-shadow">📊</span>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide">Workspace Analytics</h1>
            <p className="text-xs text-slate-400 font-medium">
              Real-time monitoring, latency percentiles & team metrics
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Workspace Selector */}
          <div className="flex items-center gap-2 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800/80">
            <span className="text-xs text-slate-400 font-mono">Workspace:</span>
            <input
              type="text"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              className="bg-transparent text-xs text-cyan-300 font-mono focus:outline-none w-24 border-b border-cyan-500/30 pb-0.5"
              placeholder="ws_id"
            />
          </div>

          {/* Time Range Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950/60 p-1.5 rounded-xl border border-slate-800/80">
            {(['1h', '24h', '7d', '30d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  timeRange === range
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Grid */}
      {loading && !metrics ? (
        <div className="flex flex-1 items-center justify-center py-24 text-slate-400">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500" />
            <span className="text-sm">Loading workspace metrics...</span>
          </div>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-950/30 border border-rose-800/60 rounded-xl text-rose-300 text-sm">
          <p className="font-bold">Error loading analytics:</p>
          <p className="font-mono mt-1 text-xs">{error}</p>
        </div>
      ) : metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Live Metrics Pulse */}
          <div className="lg:col-span-3">
            <LiveMetricsPulseCard workspaceId={workspaceId} />
          </div>

          {/* Activity Timeline */}
          <div className="lg:col-span-2">
            <ActivityTimelineChart activity={metrics.activity} timeRange={timeRange} />
          </div>

          {/* Performance Percentiles */}
          <div>
            <PerformancePercentilesCard performance={metrics.performance} />
          </div>

          {/* Users Activity */}
          <div className="lg:col-span-2">
            <WorkspaceUsersActivityTable users={metrics.users} />
          </div>

          {/* Errors Log */}
          <div>
            <WorkspaceErrorsLog errors={metrics.errors} />
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-slate-500 text-sm">
          No metrics available for workspace {workspaceId}
        </div>
      )}
    </div>
  );
}

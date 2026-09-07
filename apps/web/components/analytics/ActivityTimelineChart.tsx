// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_activity_timeline_chart"
// purpose: "Activity timeline bar chart visualization with time range selector"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface ActivityItem {
  timestamp: string;
  count: number;
  event_type?: string;
}

interface ActivityTimelineChartProps {
  activity: ActivityItem[];
  timeRange: '1h' | '24h' | '7d' | '30d';
}

export function ActivityTimelineChart({ activity = [], timeRange }: ActivityTimelineChartProps) {
  const maxCount = Math.max(...activity.map((item) => item.count || 0), 1);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Activity Timeline ({timeRange})</h3>
        <span className="text-xs text-slate-400">Total data points: {activity.length}</span>
      </div>

      {activity.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
          No activity recorded for this period
        </div>
      ) : (
        <div className="h-64 flex items-end space-x-1.5 p-2 bg-slate-950/40 border border-slate-800/60 rounded-lg overflow-x-auto">
          {activity.map((item, index) => {
            const heightPercent = Math.max(8, Math.min(100, ((item.count || 0) / maxCount) * 100));
            return (
              <div
                key={index}
                className="group relative flex-1 min-w-[12px] flex flex-col items-center justify-end h-full"
              >
                <div
                  className="w-full bg-gradient-to-t from-blue-600 to-cyan-400 rounded-t transition-all duration-300 group-hover:from-blue-500 group-hover:to-cyan-300 group-hover:brightness-125"
                  style={{ height: `${heightPercent}%` }}
                />
                <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center z-20 pointer-events-none">
                  <div className="bg-slate-900 border border-slate-700 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap">
                    <p className="font-bold">{item.count} events</p>
                    <p className="text-[10px] text-slate-400">{item.timestamp}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ActivityTimelineChart;

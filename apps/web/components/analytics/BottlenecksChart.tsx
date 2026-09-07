// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_bottlenecks_chart"
// purpose: "Render high-fidelity bottlenecks bar chart using responsive pure SVG and Tailwind CSS"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-12"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface Bottleneck {
  task_type: string;
  avg_duration_seconds: number;
  failure_rate: number;
  count: number;
}

interface BottlenecksChartProps {
  data: Bottleneck[];
}

export default function BottlenecksChart({ data }: BottlenecksChartProps) {
  // Find maximum duration to scale the bars
  const maxDuration = Math.max(...data.map(item => item.avg_duration_seconds), 1);

  return (
    <div className="bg-slate-900/30 border border-slate-800/60 p-5 rounded-2xl shadow-2xl backdrop-blur-md flex flex-col gap-4">
      <div>
        <h3 className="text-base font-bold text-white tracking-wide">⏳ Вузькі Місця (Bottlenecks)</h3>
        <p className="text-xs text-slate-500 font-medium">Аналіз тривалості та відсотку помилок за типом задач</p>
      </div>

      <div className="flex flex-col gap-4 pt-2">
        {data.map((item, idx) => {
          const widthPercent = (item.avg_duration_seconds / maxDuration) * 100;
          return (
            <div key={idx} className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-extrabold text-white capitalize">{item.task_type}</span>
                <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
                  <span>Всього: <b className="text-slate-200">{item.count}</b></span>
                  <span>Помилки: <b className="text-rose-400">{(item.failure_rate * 100).toFixed(0)}%</b></span>
                  <span>Час: <b className="text-amber-400">{item.avg_duration_seconds.toFixed(1)} с</b></span>
                </div>
              </div>
              <div className="w-full bg-slate-800/50 rounded-lg h-5 overflow-hidden border border-slate-700/20 relative flex items-center px-2">
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-amber-500/20 via-amber-500/40 to-amber-400/50 rounded-r-md transition-all duration-500" 
                  style={{ width: `${widthPercent}%` }}
                />
                <span className="relative z-10 text-[10px] font-black text-amber-200 font-mono">
                  {item.avg_duration_seconds.toFixed(1)}s
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

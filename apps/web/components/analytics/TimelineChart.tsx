// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_timeline_chart"
// purpose: "Render premium interactive timeline SVG area/line chart with gradients and grid lines"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-12"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface TimelineData {
  timestamp: string;
  runs_count: number;
  success_count: number;
  error_count: number;
}

interface TimelineChartProps {
  data: TimelineData[];
}

export default function TimelineChart({ data }: TimelineChartProps) {
  const width = 600;
  const height = 180;
  const padding = 20;

  // Find max value to scale chart
  const maxVal = Math.max(...data.map(d => Math.max(d.runs_count, d.success_count, d.error_count)), 5);

  const getPoints = (key: 'runs_count' | 'success_count' | 'error_count') => {
    if (data.length <= 1) return '';
    return data.map((d, i) => {
      const x = padding + (i / (data.length - 1)) * (width - padding * 2);
      const val = d[key];
      const y = height - padding - (val / maxVal) * (height - padding * 2);
      return `${x},${y}`;
    }).join(' ');
  };

  const runsPoints = getPoints('runs_count');
  const successPoints = getPoints('success_count');
  const errorPoints = getPoints('error_count');

  // Format date to local Ukrainian label
  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="bg-slate-900/30 border border-slate-800/60 p-5 rounded-2xl shadow-2xl backdrop-blur-md flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-base font-bold text-white tracking-wide">📈 Таймлайн Виконань</h3>
          <p className="text-xs text-slate-500 font-medium">Динаміка запусків, успіхів та помилок</p>
        </div>
        <div className="flex gap-4 text-xs font-semibold">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
            <span className="text-slate-400">Всього</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-400">Успішно</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span className="text-slate-400">Помилки</span>
          </div>
        </div>
      </div>

      <div className="w-full h-auto min-h-[200px] bg-slate-900/10 border border-slate-800/20 p-2 rounded-xl flex items-center justify-center relative">
        {data.length <= 1 ? (
          <span className="text-xs text-slate-500 font-medium">Недостатньо даних для побудови графіку</span>
        ) : (
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full select-none overflow-visible">
            <defs>
              <linearGradient id="runsGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25"/>
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0"/>
              </linearGradient>
              <linearGradient id="successGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.25"/>
                <stop offset="100%" stopColor="#10b981" stopOpacity="0"/>
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((p, idx) => {
              const y = padding + p * (height - padding * 2);
              return (
                <line 
                  key={idx} 
                  x1={padding} 
                  y1={y} 
                  x2={width - padding} 
                  y2={y} 
                  stroke="#334155" 
                  strokeWidth="0.5" 
                  strokeDasharray="4 4" 
                />
              );
            })}

            {/* Area gradients */}
            {runsPoints && (
              <polygon
                points={`${padding},${height - padding} ${runsPoints} ${width - padding},${height - padding}`}
                fill="url(#runsGrad)"
              />
            )}
            {successPoints && (
              <polygon
                points={`${padding},${height - padding} ${successPoints} ${width - padding},${height - padding}`}
                fill="url(#successGrad)"
              />
            )}

            {/* Line Paths */}
            {runsPoints && (
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={runsPoints}
              />
            )}
            {successPoints && (
              <polyline
                fill="none"
                stroke="#10b981"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={successPoints}
              />
            )}
            {errorPoints && (
              <polyline
                fill="none"
                stroke="#f43f5e"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="3 3"
                points={errorPoints}
              />
            )}

            {/* Axis Labels */}
            {data.map((d, i) => {
              if (i % Math.max(1, Math.floor(data.length / 5)) !== 0) return null;
              const x = padding + (i / (data.length - 1)) * (width - padding * 2);
              return (
                <text
                  key={i}
                  x={x}
                  y={height - 2}
                  fill="#64748b"
                  fontSize="9"
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="middle"
                >
                  {formatDate(d.timestamp)}
                </text>
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
}

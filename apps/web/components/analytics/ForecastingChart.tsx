// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_forecasting_chart"
// purpose: "Interactive Time-Series Forecasting Chart with shaded p10/p50/p90 confidence bands and model selector"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { ForecastSnapshot } from '../../lib/api/analytics_forecast_client';

interface ForecastingChartProps {
  snapshots: ForecastSnapshot[];
  metricType?: string;
  onMetricChange?: (metric: string) => void;
  isLoading?: boolean;
}

export default function ForecastingChart({
  snapshots,
  metricType = 'queue_depth',
  onMetricChange,
  isLoading = false,
}: ForecastingChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<ForecastSnapshot | null>(null);

  const filteredSnapshots = snapshots
    .filter((s) => s.metric_type === metricType)
    .sort((a, b) => a.forecast_horizon_minutes - b.forecast_horizon_minutes);

  // SVG Dimensions & Scales
  const svgWidth = 700;
  const svgHeight = 260;
  const padding = { top: 30, right: 40, bottom: 40, left: 50 };
  const chartWidth = svgWidth - padding.left - padding.right;
  const chartHeight = svgHeight - padding.top - padding.bottom;

  const maxVal = Math.max(
    ...filteredSnapshots.map((s) => s.confidence_p90),
    ...filteredSnapshots.map((s) => s.predicted_value),
    10
  ) * 1.15;
  const minVal = 0;

  const getX = (index: number) => {
    if (filteredSnapshots.length <= 1) return padding.left + chartWidth / 2;
    return padding.left + (index / (filteredSnapshots.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    const clamped = Math.max(minVal, Math.min(val, maxVal));
    return padding.top + chartHeight - ((clamped - minVal) / (maxVal - minVal)) * chartHeight;
  };

  // Generate Confidence Band Area Path (p90 forward, p10 backward)
  const generateBandPath = () => {
    if (filteredSnapshots.length < 2) return '';
    let topPath = '';
    let bottomPath = '';

    filteredSnapshots.forEach((s, idx) => {
      const x = getX(idx);
      const yTop = getY(s.confidence_p90);
      const yBottom = getY(s.confidence_p10);
      if (idx === 0) {
        topPath += `M ${x} ${yTop}`;
        bottomPath = `L ${x} ${yBottom}`;
      } else {
        topPath += ` L ${x} ${yTop}`;
        bottomPath = ` L ${x} ${yBottom}` + bottomPath;
      }
    });

    return `${topPath} ${bottomPath} Z`;
  };

  // Generate p50 line path
  const generateP50Line = () => {
    if (filteredSnapshots.length < 2) return '';
    return filteredSnapshots
      .map((s, idx) => `${idx === 0 ? 'M' : 'L'} ${getX(idx)} ${getY(s.predicted_value)}`)
      .join(' ');
  };

  const metrics = [
    { id: 'queue_depth', label: 'Черга (Queue Depth)', color: 'text-indigo-400' },
    { id: 'latency_p95', label: 'Latency p95 (ms)', color: 'text-amber-400' },
    { id: 'worker_count', label: 'Воркери (Workers)', color: 'text-emerald-400' },
    { id: 'error_rate', label: 'Помилки (Error Rate %)', color: 'text-rose-400' },
  ];

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-3xl shadow-2xl backdrop-blur-xl flex flex-col gap-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-xl">🔮</span>
            <h3 className="text-lg font-black text-white tracking-wide">
              Предиктивний ML Прогноз (Forecasting Engine)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
              p10 / p50 / p90 Bands
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Triple Exponential Smoothing & Ensemble моделювання часових рядів навантаження
          </p>
        </div>

        {/* Metric Selector Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-950/60 p-1.5 rounded-2xl border border-slate-800/60">
          {metrics.map((m) => (
            <button
              key={m.id}
              onClick={() => onMetricChange && onMetricChange(m.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                metricType === m.id
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Chart Area */}
      <div className="relative w-full overflow-x-auto">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
            Обчислення ML прогнозу та довірчих інтервалів...
          </div>
        ) : filteredSnapshots.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
            Немає даних для прогнозу за метрикою {metricType}
          </div>
        ) : (
          <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto select-none">
            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((ratio, i) => {
              const y = padding.top + chartHeight * ratio;
              const val = maxVal - (maxVal - minVal) * ratio;
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={svgWidth - padding.right}
                    y2={y}
                    stroke="#334155"
                    strokeDasharray="4 4"
                    strokeOpacity="0.4"
                  />
                  <text
                    x={padding.left - 10}
                    y={y + 4}
                    fill="#64748b"
                    fontSize="10"
                    fontFamily="monospace"
                    textAnchor="end"
                  >
                    {val.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* Shaded p10 - p90 Confidence Band */}
            <path
              d={generateBandPath()}
              fill="url(#confidenceGradient)"
              opacity="0.35"
              className="transition-all duration-300"
            />

            {/* p50 Expected Trajectory Line */}
            <path
              d={generateP50Line()}
              fill="none"
              stroke="#6366f1"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="drop-shadow-lg"
            />

            {/* Target Data Nodes */}
            {filteredSnapshots.map((s, idx) => {
              const x = getX(idx);
              const y = getY(s.predicted_value);
              const isHovered = hoveredPoint?.id === s.id;
              return (
                <g
                  key={s.id}
                  className="cursor-pointer transition-transform duration-200"
                  onMouseEnter={() => setHoveredPoint(s)}
                  onMouseLeave={() => setHoveredPoint(null)}
                >
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? 7 : 4}
                    fill={isHovered ? '#818cf8' : '#4f46e5'}
                    stroke="#ffffff"
                    strokeWidth={isHovered ? 2.5 : 1.5}
                  />
                  <text
                    x={x}
                    y={svgHeight - padding.bottom + 18}
                    fill="#94a3b8"
                    fontSize="10"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    +{s.forecast_horizon_minutes}хв
                  </text>
                </g>
              );
            })}

            {/* Gradients */}
            <defs>
              <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#818cf8" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.05" />
              </linearGradient>
            </defs>
          </svg>
        )}

        {/* Hover Tooltip Overlay */}
        {hoveredPoint && (
          <div className="absolute top-2 right-4 bg-slate-950/90 border border-indigo-500/40 p-3 rounded-2xl shadow-xl backdrop-blur-md text-xs font-mono flex flex-col gap-1 z-20">
            <div className="font-bold text-indigo-300">
              Горизонт: +{hoveredPoint.forecast_horizon_minutes} хв ({hoveredPoint.model_used.toUpperCase()})
            </div>
            <div className="text-white">
              Очікуване (p50): <b className="text-indigo-400">{hoveredPoint.predicted_value.toFixed(2)}</b>
            </div>
            <div className="text-slate-400 text-[11px]">
              Інтервал: [p10: {hoveredPoint.confidence_p10.toFixed(2)} – p90: {hoveredPoint.confidence_p90.toFixed(2)}]
            </div>
            <div className="text-emerald-400 text-[10px]">
              Confidence Score: {(hoveredPoint.confidence_score * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>

      {/* Legend & Confidence Summary */}
      <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/40 text-xs text-slate-400">
        <div className="flex items-center gap-4 font-mono">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-indigo-500" />
            <span>p50 (Очікуваний тренд)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-indigo-500/30 border border-indigo-400/50" />
            <span>p10 - p90 (Довірчий коридор 80%)</span>
          </div>
        </div>

        <div className="font-mono text-[11px] text-slate-300">
          Моделі: <span className="text-indigo-300">Holt-Winters • Poly • ARIMA • Linear Ensemble</span>
        </div>
      </div>
    </div>
  );
}

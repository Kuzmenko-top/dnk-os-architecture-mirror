// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_predictive_capacity_planner"
// purpose: "Interactive Predictive Capacity Planning UI Component (Proactive pre-scaling, workload surge mitigation)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { WorkloadPrediction, RecommendedCapacity } from '../../lib/api/analytics_forecast_client';

interface PredictiveCapacityPlannerProps {
  predictions: WorkloadPrediction[];
  capacity: RecommendedCapacity | null;
  onTriggerScaling?: () => void;
  isLoading?: boolean;
}

export default function PredictiveCapacityPlanner({
  predictions,
  capacity,
  onTriggerScaling,
  isLoading = false,
}: PredictiveCapacityPlannerProps) {
  if (isLoading) {
    return (
      <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-3xl backdrop-blur-xl text-center text-slate-500">
        Завантаження плану предиктивної потужності...
      </div>
    );
  }

  const currentWorkers = capacity?.current_worker_count ?? 4;
  const recommendedWorkers = capacity?.recommended_worker_count ?? 6;
  const workerDelta = recommendedWorkers - currentWorkers;
  const isScaleUpRecommended = capacity?.proactive_scale_recommended ?? workerDelta > 0;

  return (
    <div className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-3xl shadow-2xl backdrop-blur-xl flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="text-xl">⚡</span>
            <h3 className="text-lg font-black text-white tracking-wide">
              Предиктивне Планування Потужності (Workload Predictor)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              Proactive Pre-Scale
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Проактивне виділення інстансів воркерів на основі прогнозу черги завдань
          </p>
        </div>

        {isScaleUpRecommended && (
          <button
            onClick={onTriggerScaling}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-xs rounded-2xl shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 self-start md:self-auto"
          >
            <span>🚀</span>
            <span>Застосувати Пре-Скейлінг (+{workerDelta} воркерів)</span>
          </button>
        )}
      </div>

      {/* Proactive Scale Recommendation Banner */}
      <div
        className={`p-4 rounded-2xl border flex items-center justify-between gap-4 transition-all ${
          isScaleUpRecommended
            ? 'bg-amber-950/20 border-amber-500/40 text-amber-200'
            : 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200'
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{isScaleUpRecommended ? '⚠️' : '✅'}</span>
          <div>
            <div className="text-xs font-black uppercase tracking-wider">
              {isScaleUpRecommended ? 'Виявлено ризик перевантаження черги' : 'Оптимальний баланс ресурсів'}
            </div>
            <div className="text-xs text-slate-300 font-mono mt-0.5">
              {isScaleUpRecommended
                ? `Прогноз пікового навантаження черги (p90: ${capacity?.peak_predicted_queue_p90.toFixed(0)} задач). Рекомендовано завчасно розширити пул до ${recommendedWorkers} воркерів.`
                : `Поточна кількість воркерів (${currentWorkers}) покриває прогнозований потік з буфером безпеки ${capacity?.headroom_buffer_percent || 20}%.`}
            </div>
          </div>
        </div>

        <div className="hidden sm:flex flex-col items-end font-mono text-xs">
          <span className="text-slate-400 text-[10px]">Горизонт прогнозу</span>
          <span className="font-bold text-white">+{capacity?.horizon_minutes || 60} хв</span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-950/50 border border-slate-800/80 p-4 rounded-2xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400">Поточні Воркери</span>
          <span className="text-2xl font-black text-white font-mono">{currentWorkers}</span>
          <span className="text-[10px] text-slate-500">Активний пул</span>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/80 p-4 rounded-2xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400">Рекомендовано ML</span>
          <span
            className={`text-2xl font-black font-mono ${
              isScaleUpRecommended ? 'text-amber-400' : 'text-emerald-400'
            }`}
          >
            {recommendedWorkers}
          </span>
          <span className="text-[10px] text-slate-500">
            {workerDelta > 0 ? `+${workerDelta} інстансів завчасно` : 'Без змін'}
          </span>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/80 p-4 rounded-2xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400">Пік Черги (p50 / p90)</span>
          <span className="text-2xl font-black text-indigo-300 font-mono">
            {capacity?.peak_predicted_queue_p50.toFixed(0) || '0'} /{' '}
            {capacity?.peak_predicted_queue_p90.toFixed(0) || '0'}
          </span>
          <span className="text-[10px] text-slate-500">Очікуваний наплив</span>
        </div>

        <div className="bg-slate-950/50 border border-slate-800/80 p-4 rounded-2xl flex flex-col gap-1">
          <span className="text-[11px] font-semibold text-slate-400">Headroom Buffer</span>
          <span className="text-2xl font-black text-emerald-400 font-mono">
            {capacity?.headroom_buffer_percent || 20}%
          </span>
          <span className="text-[10px] text-slate-500">Резерв на сплески</span>
        </div>
      </div>

      {/* Horizon Prediction Timeline */}
      <div className="flex flex-col gap-3">
        <h4 className="text-xs font-black text-slate-300 uppercase tracking-wider">
          Траєкторія Навантаження за Горизонтами
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {predictions.map((p, idx) => (
            <div
              key={p.id || idx}
              className="bg-slate-950/40 border border-slate-800/60 p-3.5 rounded-2xl flex flex-col gap-2 hover:border-indigo-500/30 transition-all"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300">Горизонт</span>
                <span className="font-mono text-indigo-400 font-bold">
                  {new Date(p.target_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-slate-400 text-xs">Очікувана черга:</span>
                <span className="font-mono font-bold text-white text-sm">
                  {p.predicted_queue_depth} задач
                </span>
              </div>
              <div className="flex justify-between items-baseline text-[11px]">
                <span className="text-slate-400">Потрібно воркерів:</span>
                <span className="font-mono font-bold text-emerald-400">
                  {p.recommended_worker_count}
                </span>
              </div>
              <div className="w-full bg-slate-800/40 rounded-full h-1.5 overflow-hidden mt-1">
                <div
                  className="bg-indigo-500 h-full rounded-full"
                  style={{ width: `${Math.min(100, (p.predicted_queue_depth / 50) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

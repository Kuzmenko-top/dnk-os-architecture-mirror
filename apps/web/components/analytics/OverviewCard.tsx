// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_overview_card"
// purpose: "Render total metrics cards for runs, success rates, duration, and errors with dark premium theme"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-12"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface OverviewCardProps {
  totalRuns: number;
  successRate: number;
  avgDuration: number;
  totalErrors: number;
}

export default function OverviewCard({ totalRuns, successRate, avgDuration, totalErrors }: OverviewCardProps) {
  const cards = [
    {
      title: 'Всього Запусків',
      value: totalRuns,
      icon: '🚀',
      color: 'from-blue-600/20 to-cyan-600/5 border-blue-500/20',
      textStyle: 'text-blue-400'
    },
    {
      title: 'Успішність',
      value: `${(successRate * 100).toFixed(0)}%`,
      icon: '🏆',
      color: 'from-emerald-600/20 to-teal-600/5 border-emerald-500/20',
      textStyle: 'text-emerald-400'
    },
    {
      title: 'Середня Тривалість',
      value: `${avgDuration.toFixed(1)} с`,
      icon: '⏱️',
      color: 'from-amber-600/20 to-orange-600/5 border-amber-500/20',
      textStyle: 'text-amber-400'
    },
    {
      title: 'Всього Помилок',
      value: totalErrors,
      icon: '⚠️',
      color: 'from-rose-600/20 to-red-600/5 border-rose-500/20',
      textStyle: 'text-rose-400'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className={`bg-gradient-to-br ${card.color} border p-5 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-md transition-all hover:scale-[1.02] duration-300`}
        >
          <div className="flex flex-col gap-1">
            <span className="text-slate-400 text-sm font-semibold tracking-wide">{card.title}</span>
            <span className={`text-3xl font-black ${card.textStyle}`}>{card.value}</span>
          </div>
          <span className="text-3xl filter drop-shadow">{card.icon}</span>
        </div>
      ))}
    </div>
  );
}

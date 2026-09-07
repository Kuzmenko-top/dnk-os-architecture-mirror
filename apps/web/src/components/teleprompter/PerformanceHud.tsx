/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/PerformanceHud.tsx"
// purpose: "Real-Time Teleprompter Performance HUD (WPM, Pace, Elapsed, Estimated Time, Adherence)."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React from 'react';

interface PerformanceHudProps {
  currentWpm: number;
  targetWpm: number;
  elapsedSeconds: number;
  estimatedRemainingSeconds: number;
  completedTokensCount: number;
  totalTokensCount: number;
  adherenceScore: number;
  currentSceneRole?: string;
  isRecording: boolean;
}

function formatDuration(seconds: number): string {
  const m = Math.floor(Math.max(0, seconds) / 60);
  const s = Math.floor(Math.max(0, seconds) % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

export const PerformanceHud: React.FC<PerformanceHudProps> = ({
  currentWpm,
  targetWpm,
  elapsedSeconds,
  estimatedRemainingSeconds,
  completedTokensCount,
  totalTokensCount,
  adherenceScore,
  currentSceneRole,
  isRecording,
}) => {
  const progressPercent = totalTokensCount > 0 ? Math.round((completedTokensCount / totalTokensCount) * 100) : 0;
  const wpmDiff = currentWpm - targetWpm;

  return (
    <header
      data-testid="performance-hud"
      className="fixed top-0 left-0 right-0 z-40 px-4 py-3 bg-slate-950/85 backdrop-blur-md border-b border-slate-800 shadow-2xl safe-area-top"
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-3 text-xs md:text-sm">
        {/* Left: Recording state & Live Time */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                isRecording ? 'bg-rose-500 animate-ping' : 'bg-slate-600'
              }`}
            />
            <span className="font-mono font-bold text-slate-200">
              {formatDuration(elapsedSeconds)}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1 text-slate-400 font-mono">
            <span>/</span>
            <span>est. -{formatDuration(estimatedRemainingSeconds)}</span>
          </div>

          {currentSceneRole && (
            <span className="hidden md:inline-block px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-700/50 text-indigo-300 text-[11px] font-mono">
              🎬 {currentSceneRole}
            </span>
          )}
        </div>

        {/* Center: WPM Speed Gauge */}
        <div className="flex items-center gap-4 bg-slate-900/80 border border-slate-800 px-3 py-1 rounded-xl">
          <div className="flex flex-col items-center">
            <span className="text-[10px] uppercase text-slate-400 font-mono">Speed (WPM)</span>
            <div className="flex items-baseline gap-1">
              <span className="font-mono font-black text-sm md:text-base text-emerald-400">
                {Math.round(currentWpm)}
              </span>
              <span className="text-[10px] text-slate-500">/ {targetWpm}</span>
            </div>
          </div>

          <div className="hidden sm:flex flex-col items-start">
            <span className="text-[10px] uppercase text-slate-400 font-mono">Pace Status</span>
            <span
              className={`font-mono text-xs font-semibold ${
                Math.abs(wpmDiff) <= 15
                  ? 'text-emerald-400'
                  : wpmDiff > 15
                  ? 'text-amber-400'
                  : 'text-sky-400'
              }`}
            >
              {Math.abs(wpmDiff) <= 15
                ? '🎯 ON PACE'
                : wpmDiff > 15
                ? `⚡ +${Math.round(wpmDiff)} (Fast)`
                : `🐢 ${Math.round(wpmDiff)} (Slow)`}
            </span>
          </div>
        </div>

        {/* Right: Adherence & Progress */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase text-slate-400 font-mono">Adherence</span>
              <span className="font-mono font-bold text-emerald-400">
                {Math.round(adherenceScore * 100)}%
              </span>
            </div>
            <div className="w-20 md:w-28 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          <div className="hidden lg:flex flex-col items-end font-mono text-[11px] text-slate-400">
            <span>
              {completedTokensCount} / {totalTokensCount} words
            </span>
            <span className="text-slate-500">{progressPercent}% done</span>
          </div>
        </div>
      </div>
    </header>
  );
};

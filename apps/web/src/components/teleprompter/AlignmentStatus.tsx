/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/AlignmentStatus.tsx"
// purpose: "Visual ASR Alignment Status, Confidence Gauge, and Recovery Indicators."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React from 'react';
import type { ASRHypothesis } from '@dnk/teleprompter-core';

interface AlignmentStatusProps {
  lastHypothesis: ASRHypothesis | null;
  recoveryMode?: 'none' | 'local' | 'forward_jump' | 'manual_required';
  asrProviderName: string;
  isListening: boolean;
}

export const AlignmentStatus: React.FC<AlignmentStatusProps> = ({
  lastHypothesis,
  recoveryMode = 'none',
  asrProviderName,
  isListening,
}) => {
  const confidence = lastHypothesis?.confidence ?? 0;
  const isFinal = lastHypothesis?.isFinal ?? false;
  const seq = lastHypothesis?.sequence ?? 0;

  return (
    <div
      data-testid="alignment-status"
      className="fixed bottom-24 left-4 right-4 md:left-12 md:right-auto md:w-96 z-30 p-3 rounded-xl bg-slate-950/90 backdrop-blur-md border border-slate-800/80 shadow-2xl text-xs"
    >
      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isListening ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
            }`}
          />
          <span className="font-mono text-slate-300 font-semibold uppercase tracking-wider text-[10px]">
            ASR: {asrProviderName}
          </span>
        </div>

        <div className="flex items-center gap-1.5 font-mono text-[10px]">
          {recoveryMode !== 'none' && (
            <span
              className={`px-1.5 py-0.5 rounded font-bold uppercase ${
                recoveryMode === 'manual_required'
                  ? 'bg-rose-950 text-rose-300 border border-rose-600/50'
                  : 'bg-amber-950 text-amber-300 border border-amber-600/50'
              }`}
            >
              ⚠️ {recoveryMode.replace('_', ' ')}
            </span>
          )}
          <span className="text-slate-500">#{seq}</span>
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="text-slate-400">Confidence</span>
          <span
            className={`font-semibold ${
              confidence >= 0.8
                ? 'text-emerald-400'
                : confidence >= 0.5
                ? 'text-amber-400'
                : 'text-rose-400'
            }`}
          >
            {Math.round(confidence * 100)}% ({isFinal ? 'Final' : 'Interim'})
          </span>
        </div>

        {/* Live speech preview */}
        <div className="p-2 rounded bg-slate-900/90 border border-slate-800 font-mono text-[11px] text-slate-200 truncate">
          {lastHypothesis?.text ? (
            <span>🗣️ &ldquo;{lastHypothesis.text}&rdquo;</span>
          ) : (
            <span className="text-slate-500 italic">Listening for speech...</span>
          )}
        </div>
      </div>
    </div>
  );
};

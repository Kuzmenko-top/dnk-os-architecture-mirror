/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/ProsodyToken.tsx"
// purpose: "Interactive Visual Token with Prosody Cues, State Indicators, and Jump Target."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React from 'react';
import type { RuntimeToken } from '@dnk/teleprompter-core';

interface ProsodyTokenProps {
  token: RuntimeToken;
  isCurrent: boolean;
  onTokenClick?: (token: RuntimeToken) => void;
}

export const ProsodyToken: React.FC<ProsodyTokenProps> = ({
  token,
  isCurrent,
  onTokenClick,
}) => {
  const { status, prosody, word } = token;

  // Status-based styling
  let statusClasses = 'text-white/90 bg-transparent';
  if (isCurrent) {
    statusClasses = 'text-emerald-300 font-extrabold scale-110 bg-emerald-950/80 ring-2 ring-emerald-400 rounded-md px-1.5 py-0.5 shadow-lg shadow-emerald-500/20';
  } else {
    switch (status) {
      case 'speculative':
        statusClasses = 'text-amber-300 font-bold bg-amber-950/50 ring-1 ring-amber-400/50 rounded px-1 py-0.5 animate-pulse';
        break;
      case 'confirmed':
        statusClasses = 'text-emerald-400 font-semibold bg-emerald-950/30 rounded px-1';
        break;
      case 'completed':
        statusClasses = 'text-slate-500 line-through opacity-60';
        break;
      case 'skipped':
        statusClasses = 'text-rose-400/70 line-through decoration-rose-500/50 opacity-40';
        break;
      case 'upcoming':
      default:
        statusClasses = 'text-white/90 hover:text-white';
        break;
    }
  }

  // Prosody emphasis styling
  let prosodyEmphasisClasses = '';
  if (prosody?.emphasis === 'punch') {
    prosodyEmphasisClasses = 'underline decoration-2 decoration-orange-500 uppercase font-black tracking-wide text-orange-200';
  } else if (prosody?.emphasis === 'whisper') {
    prosodyEmphasisClasses = 'italic text-indigo-300/90 font-light';
  } else if (prosody?.emphasis === 'stretched') {
    prosodyEmphasisClasses = 'tracking-widest font-medium text-cyan-200';
  }

  return (
    <span
      data-testid={`token-${token.index}`}
      data-token-status={status}
      data-is-current={isCurrent ? 'true' : 'false'}
      onClick={() => onTokenClick && onTokenClick(token)}
      className={`inline-flex flex-col items-center mx-1 my-1 cursor-pointer transition-all duration-150 select-none ${statusClasses} ${prosodyEmphasisClasses}`}
      title={`Token #${token.index} (${status})${prosody?.pauseAfterMs ? ` [Pause ${prosody.pauseAfterMs}ms]` : ''}`}
    >
      <span className="flex items-center gap-1">
        <span>{word}</span>
        {prosody?.pauseAfterMs && (
          <span className="inline-flex items-center px-1 text-[10px] font-mono font-normal tracking-tight text-amber-400 bg-amber-950/80 border border-amber-500/40 rounded-full">
            ⏸ {(prosody.pauseAfterMs / 1000).toFixed(1)}s
          </span>
        )}
      </span>

      {prosody?.gesture && (
        <span className="text-[9px] font-mono tracking-tighter text-purple-300 bg-purple-950/80 border border-purple-500/30 rounded px-1 mt-0.5 whitespace-nowrap">
          👉 {prosody.gesture}
        </span>
      )}
    </span>
  );
};

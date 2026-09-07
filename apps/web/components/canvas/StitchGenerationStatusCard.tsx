// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchGenerationStatusCard"
// purpose: "Google Stitch Top-Left Generation Status Card with AI prompt bubble and status state"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Copy, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, RotateCw } from 'lucide-react';

interface StitchGenerationStatusCardProps {
  promptText?: string;
  userPrompt?: string;
  statusType?: 'error' | 'generating' | 'success' | 'idle';
  statusMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
}

export const StitchGenerationStatusCard: React.FC<StitchGenerationStatusCardProps> = ({
  promptText,
  userPrompt,
  statusType = 'error',
  statusMessage,
  errorMessage,
  onRetry,
}) => {
  const effectivePrompt = promptText || userPrompt || 'прибери останній компонент навігації';
  const effectiveMessage = statusMessage || errorMessage || "Something unexpected happened, and Stitch couldn't complete your generation. Please try again in a moment.";
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(effectivePrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="absolute top-20 left-6 z-30 w-[330px] rounded-2xl bg-[#1c1d22]/95 backdrop-blur-xl border border-white/10 shadow-2xl p-3.5 flex flex-col gap-3 transition-all duration-300">
      {/* Top AI Logo Icon */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Stitch Pill AI Icon with two eyes */}
          <div className="h-6 w-11 rounded-full bg-neutral-800 border border-white/10 flex items-center justify-center gap-1.5 px-2">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse delay-100" />
          </div>
          <span className="text-xs font-semibold text-white/90">Stitch AI</span>
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 text-white/50 hover:text-white/90 transition-colors rounded-lg hover:bg-white/5"
          title={isCollapsed ? "Розгорнути" : "Згорнути"}
        >
          {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>
      </div>

      {!isCollapsed && (
        <>
          {/* User Prompt Bubble */}
          <div className="rounded-xl bg-[#282a30]/80 border border-white/5 p-2.5 flex items-start gap-2.5">
            {/* User Avatar */}
            <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0 shadow">
              s
            </div>

            {/* Prompt Text with Ukrainian query */}
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white/90 truncate font-medium">
                {promptText}
              </p>
            </div>

            {/* Actions: Copy & Details */}
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={handleCopy}
                className="p-1 text-white/50 hover:text-white transition-colors rounded hover:bg-white/5"
                title="Копіювати промпт"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
              {copied && <span className="text-[10px] text-emerald-400 font-mono">✓</span>}
            </div>
          </div>

          {/* Status Message */}
          <div className="flex items-start gap-2 pt-1 text-xs text-neutral-300">
            {statusType === 'error' && (
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            )}
            {statusType === 'generating' && (
              <RotateCw className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5 animate-spin" />
            )}
            {statusType === 'success' && (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            )}
            <div className="flex-1 text-[11px] leading-relaxed text-neutral-300">
              {statusMessage}
              {statusType === 'error' && onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-2 block text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  Спробувати знову (Retry)
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default StitchGenerationStatusCard;

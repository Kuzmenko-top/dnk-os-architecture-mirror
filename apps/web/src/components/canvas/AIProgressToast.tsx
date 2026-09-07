// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/AIProgressToast.tsx"
// purpose: "Real-time AI Processing Progress Toast and Status Indicator for Canvas Studio."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import React, { useEffect, useState } from 'react';

export interface AIProgressToastProps {
  isVisible?: boolean;
  actionType?: 'cutout' | 'relight' | 'generate' | string | null;
  message?: string | null;
  progress?: number | null; // 0 to 100
  error?: string | null;
  onDismiss?: () => void;
  autoHideDurationMs?: number;
}

export const AIProgressToast: React.FC<AIProgressToastProps> = ({
  isVisible = false,
  actionType = null,
  message = null,
  progress = null,
  error = null,
  onDismiss,
  autoHideDurationMs = 5000,
}) => {
  const [internalVisible, setInternalVisible] = useState(isVisible);

  useEffect(() => {
    setInternalVisible(isVisible || Boolean(error));
  }, [isVisible, error]);

  useEffect(() => {
    if (!isVisible && !error && internalVisible) {
      const timer = setTimeout(() => {
        setInternalVisible(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, error, internalVisible]);

  useEffect(() => {
    if (error && autoHideDurationMs > 0) {
      const timer = setTimeout(() => {
        if (onDismiss) {
          onDismiss();
        } else {
          setInternalVisible(false);
        }
      }, autoHideDurationMs);
      return () => clearTimeout(timer);
    }
  }, [error, autoHideDurationMs, onDismiss]);

  if (!internalVisible) return null;

  const getActionDetails = () => {
    switch (actionType) {
      case 'cutout':
        return {
          title: 'BiRefNet Background Removal',
          icon: '✂️',
          badgeBg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          accentColor: 'from-emerald-500 to-teal-400',
        };
      case 'relight':
        return {
          title: 'IC-Light Illumination Harmonization',
          icon: '💡',
          badgeBg: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          accentColor: 'from-amber-500 to-orange-400',
        };
      case 'generate':
      case 'generate-layer':
        return {
          title: 'FLUX.1 + LayerDiffuse Synthesis',
          icon: '✨',
          badgeBg: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
          accentColor: 'from-indigo-500 to-purple-400',
        };
      default:
        return {
          title: 'AI Canvas Processing',
          icon: '⚡',
          badgeBg: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
          accentColor: 'from-blue-500 to-indigo-500',
        };
    }
  };

  const details = getActionDetails();
  const displayProgress = progress !== null && progress !== undefined ? Math.max(0, Math.min(100, progress)) : null;

  return (
    <div
      className="fixed bottom-6 right-6 z-50 max-w-md w-full animate-slide-up"
      role="status"
      aria-live="polite"
    >
      <div
        className={`p-4 rounded-2xl shadow-2xl border backdrop-blur-md transition-all ${
          error
            ? 'bg-red-950/90 border-red-800 text-red-100 shadow-red-900/20'
            : 'bg-slate-900/95 border-slate-700/80 text-white shadow-black/40'
        }`}
      >
        <div className="flex items-start justify-between space-x-3">
          {/* Action Icon / Spinner */}
          <div className="flex-shrink-0 mt-0.5">
            {error ? (
              <div className="w-8 h-8 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 text-base">
                ⚠️
              </div>
            ) : isVisible ? (
              <div className="relative w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
                <span className="text-base">{details.icon}</span>
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500" />
                </span>
              </div>
            ) : (
              <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 text-base">
                ✓
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${details.badgeBg}`}>
                {details.title}
              </span>
              {displayProgress !== null && (
                <span className="text-xs font-mono text-slate-400">
                  {Math.round(displayProgress)}%
                </span>
              )}
            </div>

            <p className="mt-1 text-sm font-medium text-slate-200 truncate">
              {error || message || (isVisible ? 'Processing AI model request...' : 'Task completed')}
            </p>

            {/* Progress Bar */}
            {isVisible && !error && (
              <div className="mt-2.5 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden border border-slate-700/60">
                {displayProgress !== null ? (
                  <div
                    className={`h-full bg-gradient-to-r ${details.accentColor} transition-all duration-300 ease-out`}
                    style={{ width: `${displayProgress}%` }}
                  />
                ) : (
                  <div className={`h-full bg-gradient-to-r ${details.accentColor} animate-indeterminate-bar w-1/3`} />
                )}
              </div>
            )}
          </div>

          {/* Dismiss Button */}
          {onDismiss && (
            <button
              onClick={onDismiss}
              aria-label="Dismiss notification"
              className="flex-shrink-0 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

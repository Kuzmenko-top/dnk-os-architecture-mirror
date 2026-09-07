// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_workspace_errors_log"
// purpose: "Workspace Errors Log component displaying recorded error events with severity badges and details"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

interface ErrorItem {
  error_type?: string;
  error_message?: string;
  endpoint?: string;
  timestamp?: string;
  count?: number;
  stack_trace?: string;
}

interface WorkspaceErrorsLogProps {
  errors: ErrorItem[];
}

export function WorkspaceErrorsLog({ errors = [] }: WorkspaceErrorsLogProps) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">⚠️</span>
          <h3 className="text-lg font-semibold text-white">Workspace Errors Log</h3>
        </div>
        <span className={`text-xs px-2.5 py-1 rounded font-mono font-bold ${
          errors.length > 0 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
        }`}>
          {errors.length} {errors.length === 1 ? 'Incident' : 'Incidents'}
        </span>
      </div>

      {errors.length === 0 ? (
        <div className="py-8 flex items-center justify-center text-emerald-400/80 text-sm border border-dashed border-emerald-900/40 rounded-lg bg-emerald-950/10">
          ✓ All systems clear. No errors reported for this period.
        </div>
      ) : (
        <div className="space-y-3 max-h-80 overflow-y-auto pr-1 font-mono text-xs">
          {errors.map((err, idx) => (
            <div
              key={idx}
              className="bg-slate-950/60 border border-rose-900/40 rounded-lg p-3 hover:border-rose-700/60 transition-colors"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <span className="text-rose-400 font-bold">
                  {err.error_type || 'WorkspaceError'}
                </span>
                <span className="text-[10px] text-slate-500">
                  {err.timestamp || 'Recent'}
                </span>
              </div>
              <p className="text-slate-300 font-sans text-xs mb-1">
                {err.error_message || 'Unknown error occurred in workspace operation'}
              </p>
              {err.endpoint && (
                <div className="text-[11px] text-slate-400 flex items-center gap-1">
                  <span className="text-slate-600">Endpoint:</span>
                  <span className="text-cyan-400">{err.endpoint}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default WorkspaceErrorsLog;

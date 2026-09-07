/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/PermissionState.tsx"
// purpose: "Browser Capabilities and Permissions Diagnostic Banner."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React from 'react';
import type { WebCapabilities } from '../../adapters/teleprompter/ports';

interface PermissionStateProps {
  capabilities: WebCapabilities | null;
  onRequestPermissions: () => void;
  isPermissionGranted: boolean;
}

export const PermissionState: React.FC<PermissionStateProps> = ({
  capabilities,
  onRequestPermissions,
  isPermissionGranted,
}) => {
  if (!capabilities) return null;

  const isFullySupported =
    capabilities.secureContext &&
    capabilities.indexedDb &&
    (capabilities.microphone || isPermissionGranted);

  if (isFullySupported && isPermissionGranted) {
    return null;
  }

  return (
    <div
      data-testid="permission-state-banner"
      className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs shadow-xl space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-base">🛡️</span>
          <h3 className="font-semibold text-slate-200">Device & Browser Capabilities</h3>
        </div>
        {!isPermissionGranted && (
          <button
            type="button"
            onClick={onRequestPermissions}
            data-testid="grant-permissions-btn"
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-semibold text-xs transition-all"
          >
            Enable Camera & Mic
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[11px] font-mono">
        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.secureContext
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-rose-950/40 border-rose-600/30 text-rose-300'
          }`}
        >
          <span>HTTPS Context</span>
          <span className="font-bold">{capabilities.secureContext ? '✅ YES' : '❌ NO'}</span>
        </div>

        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.microphone || isPermissionGranted
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-amber-950/40 border-amber-600/30 text-amber-300'
          }`}
        >
          <span>Microphone</span>
          <span className="font-bold">
            {capabilities.microphone || isPermissionGranted ? '✅ Ready' : '⚠️ Needed'}
          </span>
        </div>

        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.camera || isPermissionGranted
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-slate-800/40 border-slate-700/30 text-slate-400'
          }`}
        >
          <span>Camera</span>
          <span className="font-bold">
            {capabilities.camera || isPermissionGranted ? '✅ Ready' : 'Optional'}
          </span>
        </div>

        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.mediaRecorder
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-amber-950/40 border-amber-600/30 text-amber-300'
          }`}
        >
          <span>MediaRecorder</span>
          <span className="font-bold">{capabilities.mediaRecorder ? '✅ Ready' : '⚠️ Fallback'}</span>
        </div>

        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.speechRecognition
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-sky-950/40 border-sky-600/30 text-sky-300'
          }`}
        >
          <span>Web Speech</span>
          <span className="font-bold">{capabilities.speechRecognition ? '✅ Native' : '🤖 Mock ASR'}</span>
        </div>

        <div
          className={`p-2 rounded-lg border flex flex-col items-center justify-center text-center ${
            capabilities.indexedDb
              ? 'bg-emerald-950/40 border-emerald-600/30 text-emerald-300'
              : 'bg-rose-950/40 border-rose-600/30 text-rose-300'
          }`}
        >
          <span>IndexedDB</span>
          <span className="font-bold">{capabilities.indexedDb ? '✅ Ready' : '❌ Disabled'}</span>
        </div>
      </div>

      {!capabilities.secureContext && (
        <div className="p-2.5 rounded-lg bg-rose-950/50 border border-rose-600/40 text-rose-200 text-xs">
          ⚠️ <strong>Insecure Origin:</strong> Web Speech API and MediaStream require a Secure Context (HTTPS or localhost).
        </div>
      )}
    </div>
  );
};

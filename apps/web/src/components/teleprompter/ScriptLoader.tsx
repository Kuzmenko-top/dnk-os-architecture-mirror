/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/ScriptLoader.tsx"
// purpose: "Script and Prosody Loader with ReBurn Reference Fixture Quick-Select & JSON Import."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React, { useState } from 'react';
import type { ScriptDocument, ProsodyDocument } from '@dnk/video-audit-core';
import { reburnReferenceFixture } from '@dnk/video-audit-core';

interface ScriptLoaderProps {
  onLoadScript: (script: ScriptDocument, prosody?: ProsodyDocument) => void;
  currentScriptTitle?: string;
  totalTokensCount: number;
}

export const ScriptLoader: React.FC<ScriptLoaderProps> = ({
  onLoadScript,
  currentScriptTitle,
  totalTokensCount,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);

  const handleLoadReburnFixture = () => {
    onLoadScript(
      reburnReferenceFixture.script,
      reburnReferenceFixture.prosody
    );
    setIsOpen(false);
    setParseError(null);
  };

  const handleCustomJsonImport = () => {
    try {
      setParseError(null);
      const parsed = JSON.parse(jsonInput);
      if (!parsed.scriptDocument) {
        throw new Error('JSON must contain a "scriptDocument" field.');
      }
      onLoadScript(parsed.scriptDocument, parsed.prosodyDocument);
      setIsOpen(false);
      setJsonInput('');
    } catch (err: unknown) {
      setParseError((err as Error).message || 'Invalid JSON format');
    }
  };

  return (
    <div data-testid="script-loader" className="relative z-30">
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 backdrop-blur-md shadow-lg text-xs">
        <div className="flex items-center gap-2 truncate">
          <span className="text-base">📜</span>
          <div className="truncate">
            <span className="text-slate-400 font-mono">Script: </span>
            <span className="font-bold text-slate-200">
              {currentScriptTitle || 'No script loaded'}
            </span>
            {totalTokensCount > 0 && (
              <span className="ml-2 text-slate-400 font-mono">
                ({totalTokensCount} words ~ {Math.round((totalTokensCount / 130) * 60)}s)
              </span>
            )}
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          data-testid="toggle-script-loader-btn"
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs transition-colors"
        >
          {isOpen ? 'Close' : 'Change Script ▾'}
        </button>
      </div>

      {isOpen && (
        <div
          data-testid="script-loader-modal"
          className="mt-2 p-4 rounded-2xl bg-slate-950 border border-slate-800 shadow-2xl space-y-4 animate-in fade-in slide-in-from-top-2"
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="font-semibold text-slate-200 text-sm">Select or Paste Script</h4>
            <span className="text-[11px] font-mono text-slate-500">Contract-First v1.0.0</span>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={handleLoadReburnFixture}
              data-testid="load-reburn-fixture-btn"
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-950 to-teal-950 border border-emerald-600/40 hover:border-emerald-500 text-left transition-all group"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-emerald-300 group-hover:text-emerald-200">
                  🔥 ReBurn Commercial Reference Fixture
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300">
                  Verified Contract
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                4 Scenes • Ukrainian Prosody Annotations (punch, whisper, stretched) • 130 Target WPM
              </p>
            </button>
          </div>

          <div className="pt-2 border-t border-slate-800 space-y-2">
            <label className="block text-xs font-mono text-slate-400">
              Or paste custom Script & Prosody JSON:
            </label>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder='{ "scriptDocument": { ... }, "prosodyDocument": { ... } }'
              rows={4}
              data-testid="custom-script-json-input"
              className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />

            {parseError && (
              <p className="text-xs text-rose-400 font-mono">⚠️ {parseError}</p>
            )}

            <button
              type="button"
              onClick={handleCustomJsonImport}
              disabled={!jsonInput.trim()}
              data-testid="import-custom-script-btn"
              className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 font-medium text-xs transition-colors"
            >
              Import Custom JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

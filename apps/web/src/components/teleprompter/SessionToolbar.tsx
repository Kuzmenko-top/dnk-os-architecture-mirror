/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/SessionToolbar.tsx"
// purpose: "Touch-Optimized Bottom Session Control Toolbar with Mobile Safe-Area Support."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React from 'react';
import type { FontSizeOption } from './PrompterViewport';

interface SessionToolbarProps {
  sessionStatus: 'idle' | 'recording' | 'paused' | 'completed';
  isCameraEnabled: boolean;
  isMirrorMode: boolean;
  fontSize: FontSizeOption;
  asrProviderType: 'web-speech' | 'mock-stream';
  onStartRecording: () => void;
  onPauseRecording: () => void;
  onResumeRecording: () => void;
  onFinishRecording: () => void;
  onResetSession: () => void;
  onToggleCamera: () => void;
  onToggleMirror: () => void;
  onChangeFontSize: (size: FontSizeOption) => void;
  onChangeAsrProvider: (provider: 'web-speech' | 'mock-stream') => void;
}

export const SessionToolbar: React.FC<SessionToolbarProps> = ({
  sessionStatus,
  isCameraEnabled,
  isMirrorMode,
  fontSize,
  asrProviderType,
  onStartRecording,
  onPauseRecording,
  onResumeRecording,
  onFinishRecording,
  onResetSession,
  onToggleCamera,
  onToggleMirror,
  onChangeFontSize,
  onChangeAsrProvider,
}) => {
  const fontSizes: FontSizeOption[] = ['sm', 'md', 'lg', 'xl', '2xl'];

  const cycleFontSize = () => {
    const currentIndex = fontSizes.indexOf(fontSize);
    const nextIndex = (currentIndex + 1) % fontSizes.length;
    onChangeFontSize(fontSizes[nextIndex]);
  };

  return (
    <nav
      data-testid="session-toolbar"
      className="fixed bottom-0 left-0 right-0 z-40 px-4 py-3 bg-slate-950/90 backdrop-blur-lg border-t border-slate-800 shadow-2xl safe-area-bottom"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-2">
        {/* Secondary controls */}
        <div className="flex items-center gap-1.5 md:gap-2">
          {/* Camera toggle */}
          <button
            type="button"
            onClick={onToggleCamera}
            data-testid="toggle-camera-btn"
            title="Toggle Camera Background"
            className={`px-3 py-2 rounded-xl text-xs font-mono font-medium border transition-colors flex items-center gap-1.5 ${
              isCameraEnabled
                ? 'bg-emerald-950/80 border-emerald-600/50 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            📹 <span className="hidden sm:inline">Cam</span>
          </button>

          {/* Mirror toggle */}
          <button
            type="button"
            onClick={onToggleMirror}
            data-testid="toggle-mirror-btn"
            title="Toggle Mirror Mode"
            className={`px-3 py-2 rounded-xl text-xs font-mono font-medium border transition-colors flex items-center gap-1.5 ${
              isMirrorMode
                ? 'bg-cyan-950/80 border-cyan-600/50 text-cyan-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            🪞 <span className="hidden sm:inline">Mirror</span>
          </button>

          {/* Font size adjuster */}
          <button
            type="button"
            onClick={cycleFontSize}
            data-testid="cycle-font-size-btn"
            title="Cycle Font Size"
            className="px-3 py-2 rounded-xl text-xs font-mono font-medium bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 transition-colors"
          >
            🔤 {fontSize.toUpperCase()}
          </button>
        </div>

        {/* Primary action buttons */}
        <div className="flex items-center gap-2">
          {sessionStatus === 'idle' && (
            <button
              type="button"
              onClick={onStartRecording}
              data-testid="start-recording-btn"
              className="px-6 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 active:scale-95 text-white font-bold text-sm tracking-wide shadow-lg shadow-rose-600/30 transition-all flex items-center gap-2"
            >
              <span className="w-3 h-3 rounded-full bg-white animate-ping" />
              START REC
            </button>
          )}

          {sessionStatus === 'recording' && (
            <>
              <button
                type="button"
                onClick={onPauseRecording}
                data-testid="pause-recording-btn"
                className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 active:scale-95 text-white font-semibold text-xs tracking-wide shadow-md transition-all flex items-center gap-1.5"
              >
                ⏸ PAUSE
              </button>
              <button
                type="button"
                onClick={onFinishRecording}
                data-testid="finish-recording-btn"
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-semibold text-xs tracking-wide shadow-md transition-all flex items-center gap-1.5"
              >
                ⏹ FINISH
              </button>
            </>
          )}

          {sessionStatus === 'paused' && (
            <>
              <button
                type="button"
                onClick={onResumeRecording}
                data-testid="resume-recording-btn"
                className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-semibold text-xs tracking-wide shadow-md transition-all flex items-center gap-1.5"
              >
                ▶ RESUME
              </button>
              <button
                type="button"
                onClick={onFinishRecording}
                data-testid="finish-paused-recording-btn"
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-white font-semibold text-xs tracking-wide shadow-md transition-all flex items-center gap-1.5"
              >
                ⏹ FINISH
              </button>
            </>
          )}

          {sessionStatus === 'completed' && (
            <button
              type="button"
              onClick={onResetSession}
              data-testid="reset-session-btn"
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-semibold text-xs tracking-wide shadow-md transition-all flex items-center gap-1.5"
            >
              🔄 NEW TAKE
            </button>
          )}
        </div>

        {/* Right: ASR Source Switcher */}
        <div className="hidden sm:flex items-center gap-1">
          <select
            value={asrProviderType}
            onChange={(e) =>
              onChangeAsrProvider(e.target.value as 'web-speech' | 'mock-stream')
            }
            data-testid="asr-provider-select"
            className="px-2.5 py-1.5 rounded-xl text-[11px] font-mono bg-slate-900 border border-slate-800 text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="web-speech">🎙️ Web Speech API</option>
            <option value="mock-stream">🤖 Mock ASR (Offline)</option>
          </select>
        </div>
      </div>
    </nav>
  );
};

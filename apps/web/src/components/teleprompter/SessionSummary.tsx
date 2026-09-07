/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/teleprompter/SessionSummary.tsx"
// purpose: "Post-Take Session Summary, Video Playback, Adherence Metrics, and JSON Export."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

'use client';

import React, { useState, useEffect } from 'react';
import type { TeleprompterSession, SessionAnalytics } from '@dnk/teleprompter-core';

interface SessionSummaryProps {
  session: TeleprompterSession;
  analytics?: SessionAnalytics | null;
  totalTokensCount: number;
  targetWpm?: number;
  recordedVideoBlob?: Blob | null;
  onNewTake: () => void;
}

export const SessionSummary: React.FC<SessionSummaryProps> = ({
  session,
  analytics,
  totalTokensCount,
  targetWpm = 130,
  recordedVideoBlob,
  onNewTake,
}) => {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    if (recordedVideoBlob) {
      const url = URL.createObjectURL(recordedVideoBlob);
      setVideoUrl(url);
      return () => {
        URL.revokeObjectURL(url);
      };
    }
    setVideoUrl(null);
  }, [recordedVideoBlob]);

  const adherencePercent = analytics?.adherenceScore
    ? Math.round(analytics.adherenceScore * 100)
    : 100;

  const durationSec = analytics?.totalDurationMs
    ? Math.round(analytics.totalDurationMs / 1000)
    : session.completedAtMs && session.startedAtMs
    ? Math.round((session.completedAtMs - session.startedAtMs) / 1000)
    : 0;

  const handleExportJson = () => {
    const exportPayload = {
      _header: {
        exportedAt: new Date().toISOString(),
        system: 'DNK Content Intelligence Teleprompter PWA',
        version: '1.0.0',
      },
      session,
      analytics,
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `teleprompter-session-${session.sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadVideo = () => {
    if (!videoUrl || !recordedVideoBlob) return;
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = `take-${session.sessionId}.${recordedVideoBlob.type.includes('mp4') ? 'mp4' : 'webm'}`;
    a.click();
  };

  return (
    <div
      data-testid="session-summary-container"
      className="max-w-3xl mx-auto p-6 md:p-8 rounded-3xl bg-slate-950/90 border border-slate-800 shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-200"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-widest text-emerald-400">
            Take Complete
          </span>
          <h2 className="text-2xl md:text-3xl font-black text-white mt-1">
            Session Performance Summary
          </h2>
        </div>
        <button
          type="button"
          onClick={onNewTake}
          data-testid="summary-new-take-btn"
          className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs tracking-wide shadow-lg shadow-emerald-600/30 transition-all"
        >
          🔄 New Take
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Adherence Score</span>
          <span className="text-2xl md:text-3xl font-black text-emerald-400 mt-1">
            {adherencePercent}%
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-1">
            {analytics?.adherenceNote || 'Script Matching'}
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Average WPM</span>
          <span className="text-2xl md:text-3xl font-black text-slate-200 mt-1">
            {Math.round(analytics?.actualWpm ?? targetWpm)}
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-1">
            Target: {targetWpm} WPM
          </span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Duration</span>
          <span className="text-2xl md:text-3xl font-black text-slate-200 mt-1">
            {durationSec}s
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-1">Total Recording Time</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 flex flex-col">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Tokens</span>
          <span className="text-2xl md:text-3xl font-black text-indigo-400 mt-1">
            {totalTokensCount}
          </span>
          <span className="text-[10px] text-slate-500 font-mono mt-1">
            Skipped: {analytics?.skippedTokenCount ?? 0}
          </span>
        </div>
      </div>

      {/* Video Playback if recorded */}
      {videoUrl && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-200">Take Video Recording</h3>
          <div className="rounded-2xl overflow-hidden bg-black border border-slate-800 aspect-video max-h-80 mx-auto flex items-center justify-center">
            <video
              src={videoUrl}
              controls
              playsInline
              data-testid="summary-recorded-video"
              className="w-full h-full object-contain"
            />
          </div>
          <button
            type="button"
            onClick={handleDownloadVideo}
            data-testid="download-video-btn"
            className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs transition-colors flex items-center justify-center gap-2"
          >
            💾 Download Recorded Video
          </button>
        </div>
      )}

      {/* Export session actions */}
      <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="font-mono text-slate-500 text-[11px]">
          Session ID: {session.sessionId} • Version: {session.scriptVersion}
        </div>

        <button
          type="button"
          onClick={handleExportJson}
          data-testid="export-session-json-btn"
          className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-mono text-xs transition-colors flex items-center gap-1.5"
        >
          📄 Export Session JSON (Verification)
        </button>
      </div>
    </div>
  );
};

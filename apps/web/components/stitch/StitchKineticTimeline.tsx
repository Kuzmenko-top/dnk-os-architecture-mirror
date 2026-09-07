// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/stitch/StitchKineticTimeline.tsx"
// purpose: "CapCut AI-Design Multi-Track Kinetic Timeline for Video, Frame Sequencing & Animation Transitions in DNK Canvas."
// canonical_source: true
// status: "Active"
// version: "2.1.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect, useRef } from 'react';

export interface TimelineTrack {
  id: string;
  name: string;
  type: 'ui_frame' | 'video' | 'kinetic_text' | 'audio';
  color: string;
  keyframes: number[]; // timestamps in ms
  durationMs: number;
}

export interface KineticTimelineProps {
  activeScreenId?: string;
  onSeek?: (timestampMs: number) => void;
  onNotification?: (msg: { text: string; type: 'success' | 'info' | 'warning' | 'error' }) => void;
}

export default function StitchKineticTimeline({
  activeScreenId,
  onSeek,
  onNotification
}: KineticTimelineProps) {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(0);
  const [totalDurationMs] = useState<number>(15000);
  const [fps, setFps] = useState<number>(60);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  const [tracks, setTracks] = useState<TimelineTrack[]>([
    {
      id: 'trk-01',
      name: 'Track 1: UI Screens / Frame Transitions',
      type: 'ui_frame',
      color: '#38bdf8', // sky-400
      keyframes: [0, 2500, 7000, 12000],
      durationMs: 15000
    },
    {
      id: 'trk-02',
      name: 'Track 2: Hero Video Asset (Remotion / FFmpeg)',
      type: 'video',
      color: '#a855f7', // purple-500
      keyframes: [0, 5000, 10000],
      durationMs: 15000
    },
    {
      id: 'trk-03',
      name: 'Track 3: Kinetic Text & Spring Physics (GSAP)',
      type: 'kinetic_text',
      color: '#10b981', // emerald-500
      keyframes: [1000, 3500, 8500],
      durationMs: 15000
    }
  ]);

  const animationRef = useRef<number | null>(null);
  const lastTickRef = useRef<number>(Date.now());

  useEffect(() => {
    if (isPlaying) {
      lastTickRef.current = Date.now();
      const tick = () => {
        const now = Date.now();
        const delta = now - lastTickRef.current;
        lastTickRef.current = now;

        setCurrentTimeMs((prev) => {
          const next = prev + delta;
          if (next >= totalDurationMs) {
            setIsPlaying(false);
            return 0;
          }
          if (onSeek) onSeek(next);
          return next;
        });
        animationRef.current = requestAnimationFrame(tick);
      };
      animationRef.current = requestAnimationFrame(tick);
    } else if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying, totalDurationMs, onSeek]);

  const handleTogglePlay = () => {
    setIsPlaying(!isPlaying);
    if (onNotification) {
      onNotification({
        text: !isPlaying ? 'Playback started (CapCut Kinetic Sequencer).' : 'Playback paused.',
        type: 'info'
      });
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setCurrentTimeMs(val);
    if (onSeek) onSeek(val);
  };

  const handleAddKeyframe = () => {
    setTracks((prev) =>
      prev.map((t) => ({
        ...t,
        keyframes: Array.from(new Set([...t.keyframes, currentTimeMs])).sort((a, b) => a - b)
      }))
    );
    if (onNotification) {
      onNotification({
        text: `Keyframe inserted at ${formatTime(currentTimeMs)} across all active tracks.`,
        type: 'success'
      });
    }
  };

  const formatTime = (ms: number) => {
    const totalSecs = ms / 1000;
    const mins = Math.floor(totalSecs / 60);
    const secs = Math.floor(totalSecs % 60);
    const millis = Math.floor((ms % 1000) / 10);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(2, '0')}`;
  };

  if (isCollapsed) {
    return (
      <div className="absolute bottom-4 right-4 z-40">
        <button
          onClick={() => setIsCollapsed(false)}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-xs font-medium text-slate-200 border border-slate-700 rounded-lg shadow-xl backdrop-blur-md transition-all"
        >
          <span>🎬 Open CapCut Timeline</span>
        </button>
      </div>
    );
  }

  return (
    <div className="absolute bottom-0 left-0 right-0 z-40 bg-slate-950/95 border-t border-slate-800/80 backdrop-blur-xl shadow-2xl flex flex-col transition-all">
      {/* Top Controller Bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/60 bg-slate-900/40">
        {/* Left: Transport Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleTogglePlay}
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm transition-all ${
              isPlaying
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md'
            }`}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          <button
            onClick={() => {
              setCurrentTimeMs(0);
              setIsPlaying(false);
            }}
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-xs text-slate-300 rounded border border-slate-700"
          >
            ⏮ Reset
          </button>

          <div className="font-mono text-xs font-semibold text-slate-200 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
            <span className="text-indigo-400">{formatTime(currentTimeMs)}</span> / {formatTime(totalDurationMs)}
          </div>

          <button
            onClick={handleAddKeyframe}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-medium rounded transition-all"
          >
            <span>🔷 + Keyframe</span>
          </button>
        </div>

        {/* Center: Active Screen Indicator */}
        <div className="text-xs text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></span>
          <span>
            Target Scene: <strong className="text-slate-200">{activeScreenId || 'All Active Canvas Nodes'}</strong>
          </span>
        </div>

        {/* Right: FPS & Collapse */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-[11px] text-slate-400">
            <span>FPS:</span>
            <button
              onClick={() => setFps(fps === 60 ? 30 : 60)}
              className="text-slate-200 font-semibold hover:text-indigo-400"
            >
              {fps}fps
            </button>
          </div>

          <button
            onClick={() => setIsCollapsed(true)}
            className="text-slate-400 hover:text-white text-xs px-2 py-1"
            title="Minimize timeline"
          >
            ▼ Hide
          </button>
        </div>
      </div>

      {/* Scrubber Range Slider */}
      <div className="relative px-4 pt-2">
        <input
          type="range"
          min={0}
          max={totalDurationMs}
          value={currentTimeMs}
          onChange={handleSliderChange}
          className="w-full accent-indigo-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
        />
      </div>

      {/* Multi-Track Sequencer Rows */}
      <div className="px-4 py-2 space-y-1.5 max-h-36 overflow-y-auto font-mono text-xs">
        {tracks.map((track) => {
          const progressPct = (currentTimeMs / totalDurationMs) * 100;
          return (
            <div
              key={track.id}
              className="flex items-center gap-3 bg-slate-900/60 p-1.5 rounded-lg border border-slate-800/80 hover:border-slate-700 transition-all"
            >
              <div className="w-64 truncate text-[11px] font-semibold text-slate-300 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: track.color }} />
                <span>{track.name}</span>
              </div>

              {/* Track Bar with Keyframe Diamonds */}
              <div className="relative flex-1 h-6 bg-slate-950 rounded border border-slate-800/80 overflow-hidden">
                {/* Active playhead line inside track */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-indigo-400 z-20 shadow-[0_0_8px_rgba(99,102,241,0.8)]"
                  style={{ left: `${progressPct}%` }}
                />

                {/* Keyframe Markers */}
                {track.keyframes.map((kf, i) => {
                  const kfPct = (kf / totalDurationMs) * 100;
                  return (
                    <div
                      key={i}
                      className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-amber-400 rotate-45 z-10 border border-slate-950 shadow hover:scale-125 cursor-pointer transition-transform"
                      style={{ left: `calc(${kfPct}% - 6px)` }}
                      title={`Keyframe at ${formatTime(kf)}`}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

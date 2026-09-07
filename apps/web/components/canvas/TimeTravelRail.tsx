// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_TimeTravelRail"
// purpose: "Interactive Task Forest Time-Travel Timeline Rail with Scrubber Slider, State History Replay & Mutation Pulse"
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  History,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Radio,
  RotateCcw,
  Sparkles,
  ChevronUp,
  ChevronDown,
  Activity,
  Layers,
  Clock,
  ArrowRight
} from 'lucide-react';

export interface EvolutionHistoryItem {
  event_id: string;
  timestamp: string;
  node_id: string;
  node_title: string;
  plant_scale: string;
  mutation_type: string;
  previous_status?: string | null;
  new_status?: string | null;
  previous_progress?: number | null;
  new_progress?: number | null;
  overall_field_progress: number;
  description: string;
}

export interface TimeTravelRailProps {
  onSelectEvent?: (event: EvolutionHistoryItem | null, eventIndex: number) => void;
  onReturnToLiveHead?: () => void;
  activeNodeId?: string | null;
  className?: string;
}

const SCALE_ICONS: Record<string, string> = {
  field: '🌾',
  sector: '🏞️',
  tree: '🌳',
  bush: '🌿',
  flower: '🌸'
};

export default function TimeTravelRail({
  onSelectEvent,
  onReturnToLiveHead,
  activeNodeId,
  className = ''
}: TimeTravelRailProps) {
  const [events, setEvents] = useState<EvolutionHistoryItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(-1); // -1 = Live Head
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const playTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v3/task_forest/evolution_history?limit=100');
      if (res.ok) {
        const data = await res.json();
        const historyEvents: EvolutionHistoryItem[] = data.events || [];
        setEvents(historyEvents);
      }
    } catch (error: unknown) {
      console.error('Failed to load evolution history for Time-Travel Rail', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const isLive = currentIndex === -1 || currentIndex === events.length - 1;
  const currentEvent: EvolutionHistoryItem | null =
    currentIndex >= 0 && currentIndex < events.length ? events[currentIndex] : null;

  // Handle Scrubbing
  const handleScrub = (idx: number) => {
    if (idx >= events.length - 1) {
      setCurrentIndex(-1);
      if (onReturnToLiveHead) onReturnToLiveHead();
      if (onSelectEvent) onSelectEvent(null, -1);
    } else {
      setCurrentIndex(idx);
      const ev = events[idx];
      if (onSelectEvent) onSelectEvent(ev, idx);
    }
  };

  // Return to Live Head
  const handleReturnToLive = () => {
    setCurrentIndex(-1);
    setIsPlaying(false);
    if (onReturnToLiveHead) onReturnToLiveHead();
    if (onSelectEvent) onSelectEvent(null, -1);
  };

  // Step Forward / Backward
  const handleStepPrev = () => {
    if (events.length === 0) return;
    const nextIdx = currentIndex === -1 ? events.length - 2 : Math.max(0, currentIndex - 1);
    handleScrub(nextIdx);
  };

  const handleStepNext = () => {
    if (events.length === 0 || currentIndex === -1) return;
    const nextIdx = currentIndex + 1;
    handleScrub(nextIdx);
  };

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          const next = prev === -1 ? 0 : prev + 1;
          if (next >= events.length) {
            setIsPlaying(false);
            if (onReturnToLiveHead) onReturnToLiveHead();
            return -1;
          }
          const ev = events[next];
          if (onSelectEvent) onSelectEvent(ev, next);
          return next;
        });
      }, 1200);
    } else if (playTimerRef.current) {
      clearInterval(playTimerRef.current);
      playTimerRef.current = null;
    }

    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, events, onSelectEvent, onReturnToLiveHead]);

  const formatTime = (isoString?: string) => {
    if (!isoString) return '--:--:--';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString.slice(11, 19);
    }
  };

  if (events.length === 0 && !isLoading) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-40 transition-all duration-300 ${className}`}
    >
      <div className="relative rounded-2xl bg-slate-950/90 border border-slate-800/90 shadow-2xl backdrop-blur-xl p-3.5 w-[680px] max-w-[95vw] text-white select-none">
        {/* Glow indicator line */}
        <div
          className={`absolute top-0 left-4 right-4 h-0.5 rounded-full transition-all duration-500 ${
            !isLive ? 'bg-gradient-to-r from-amber-500 via-yellow-400 to-amber-500 animate-pulse' : 'bg-gradient-to-r from-cyan-500 to-emerald-500'
          }`}
        />

        {/* Header Bar */}
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
              <History className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold tracking-tight text-slate-100">
                  Task Forest Time-Travel Rail
                </span>
                {!isLive ? (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300">
                    <Clock className="w-2.5 h-2.5" />
                    T_{currentIndex + 1} / {events.length}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold bg-emerald-500/20 border border-emerald-500/40 text-emerald-400">
                    <Radio className="w-2.5 h-2.5 animate-pulse text-emerald-400" />
                    LIVE HEAD
                  </span>
                )}
              </div>
              <span className="text-[10px] text-slate-400 font-mono block">
                {events.length} historical mutation snapshots recorded
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!isLive && (
              <button
                onClick={handleReturnToLive}
                className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900 transition-all flex items-center gap-1 shadow-lg hover:shadow-emerald-500/20"
              >
                <RotateCcw className="w-3 h-3" />
                Return to Live Head
              </button>
            )}

            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors"
            >
              {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {!isMinimized && (
          <>
            {/* Timeline Scrubber Controls */}
            <div className="flex items-center gap-3 my-2.5">
              {/* Step Prev */}
              <button
                onClick={handleStepPrev}
                disabled={currentIndex === 0}
                className="p-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Previous snapshot"
              >
                <SkipBack className="w-3.5 h-3.5" />
              </button>

              {/* Play / Pause Replay */}
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`p-1.5 rounded-lg border transition-all ${
                  isPlaying
                    ? 'bg-amber-950 border-amber-500 text-amber-300'
                    : 'bg-cyan-950/80 border-cyan-800/80 text-cyan-300 hover:bg-cyan-900'
                }`}
                title={isPlaying ? 'Pause replay' : 'Play mutation replay'}
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              </button>

              {/* Step Next */}
              <button
                onClick={handleStepNext}
                disabled={isLive}
                className="p-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Next snapshot"
              >
                <SkipForward className="w-3.5 h-3.5" />
              </button>

              {/* Scrubber Range Slider */}
              <div className="relative flex-1 flex items-center">
                <input
                  type="range"
                  min={0}
                  max={Math.max(0, events.length - 1)}
                  value={currentIndex === -1 ? events.length - 1 : currentIndex}
                  onChange={(e) => handleScrub(parseInt(e.target.value, 10))}
                  className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
                />
              </div>

              {/* Timestamp Indicator */}
              <span className="text-xs font-mono text-slate-400 shrink-0">
                {currentEvent ? formatTime(currentEvent.timestamp) : 'Live Now'}
              </span>
            </div>

            {/* Snapshot Inspection Detail Card */}
            {currentEvent ? (
              <div className="mt-2.5 p-2.5 rounded-xl bg-slate-900/70 border border-amber-500/30 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2.5 truncate max-w-[480px]">
                  <span className="text-base leading-none">
                    {SCALE_ICONS[currentEvent.plant_scale] || '🌸'}
                  </span>
                  <div className="truncate">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-amber-400 uppercase font-bold">
                        {currentEvent.mutation_type}
                      </span>
                      <span className="text-slate-200 font-bold truncate">
                        {currentEvent.node_title}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 block truncate">
                      {currentEvent.description}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-right shrink-0">
                  <div className="text-right">
                    <span className="text-[9px] text-slate-500 block uppercase">Field Progress</span>
                    <span className="text-xs font-bold text-emerald-400">
                      {Math.round(currentEvent.overall_field_progress)}%
                    </span>
                  </div>
                  {currentEvent.new_status && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 border border-slate-700 text-slate-200">
                      {currentEvent.new_status}
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <div className="mt-2.5 p-2 rounded-xl bg-slate-900/40 border border-slate-800/60 flex items-center justify-between text-xs font-mono text-slate-400">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <Sparkles className="w-3.5 h-3.5" />
                  Viewing latest real-time task forest state
                </span>
                <span className="text-[11px] text-slate-500">
                  Drag scrubber to rewind mutations
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export { TimeTravelRail };

// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/NodeTaskMarketingVideoViewer.tsx"
// purpose: "Interactive 9:16 Marketing Video Storyboard & Remotion Preview for Node Tasks"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Loader2,
  Smartphone,
  Clock,
  Layers,
  FileCode,
  Volume2,
  Film,
  Flame,
  CheckCircle2,
  Mic,
  Download,
  CheckCircle,
} from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { MarketingVideoScene, MarketingVideoPayload } from '@/types/nodeTasks';

interface NodeTaskMarketingVideoViewerProps {
  nodeId: string;
}

export function NodeTaskMarketingVideoViewer({ nodeId }: NodeTaskMarketingVideoViewerProps) {
  const node = useNodeTasksStore((s) => s.nodesMap[nodeId]);
  const video = useNodeTasksStore((s) => s.marketingVideos[nodeId]);
  const isGeneratingVideo = useNodeTasksStore((s) => s.isGeneratingVideo);
  const fetchMarketingVideo = useNodeTasksStore((s) => s.fetchMarketingVideo);
  const generateMarketingVideo = useNodeTasksStore((s) => s.generateMarketingVideo);

  // Slice 2: Voice AI & Video Exporter
  const audioUrl = useNodeTasksStore((s) => s.audioUrls[nodeId]);
  const isSynthesizingVoice = useNodeTasksStore((s) => !!s.isSynthesizingVoice[nodeId]);
  const isExportingVideo = useNodeTasksStore((s) => !!s.isExportingVideo[nodeId]);
  const videoExportStatus = useNodeTasksStore((s) => s.videoExportStatuses[nodeId]);
  const synthesizeVoiceover = useNodeTasksStore((s) => s.synthesizeVoiceover);
  const exportVideoMp4 = useNodeTasksStore((s) => s.exportVideoMp4);
  const fetchVideoExportStatus = useNodeTasksStore((s) => s.fetchVideoExportStatus);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [copiedVoiceover, setCopiedVoiceover] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const animationFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Fetch video on mount if not loaded
  useEffect(() => {
    if (nodeId) {
      fetchMarketingVideo(nodeId);
    }
  }, [nodeId, fetchMarketingVideo]);

  const fps = video?.fps || 30;
  const totalFrames = video?.duration_in_frames || 480;

  // Scene timeline boundaries calculation
  const sceneOffsets = useMemo(() => {
    if (!video || !video.scenes || video.scenes.length === 0) return [];
    let acc = 0;
    return video.scenes.map((scene) => {
      const start = acc;
      const duration = scene.duration_frames || 120;
      acc += duration;
      return {
        ...scene,
        startFrame: start,
        endFrame: acc,
        duration,
      };
    });
  }, [video]);

  // Determine current scene from playback frame
  const activeSceneIndex = useMemo(() => {
    if (sceneOffsets.length === 0) return 0;
    const foundIdx = sceneOffsets.findIndex(
      (s) => currentFrame >= s.startFrame && currentFrame < s.endFrame
    );
    return foundIdx !== -1 ? foundIdx : sceneOffsets.length - 1;
  }, [sceneOffsets, currentFrame]);

  const activeScene: (MarketingVideoScene & { startFrame?: number; endFrame?: number }) | undefined =
    sceneOffsets[activeSceneIndex] || video?.scenes?.[0];

  // Playback loop
  useEffect(() => {
    if (!isPlaying) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      lastTimeRef.current = null;
      return;
    }

    const frameDurationMs = 1000 / fps;

    const tick = (now: number) => {
      if (!lastTimeRef.current) {
        lastTimeRef.current = now;
      }
      const delta = now - lastTimeRef.current;

      if (delta >= frameDurationMs) {
        const framesElapsed = Math.floor(delta / frameDurationMs);
        lastTimeRef.current = now - (delta % frameDurationMs);

        setCurrentFrame((prev) => {
          const next = prev + framesElapsed;
          if (next >= totalFrames) {
            setIsPlaying(false);
            return 0;
          }
          return next;
        });
      }

      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [isPlaying, fps, totalFrames]);

  // Synchronize HTML5 audio element with video playback & scrubbing (Slice 2)
  useEffect(() => {
    if (!audioRef.current || !audioUrl) return;
    if (isPlaying) {
      const targetTime = currentFrame / fps;
      if (Math.abs(audioRef.current.currentTime - targetTime) > 0.3) {
        audioRef.current.currentTime = targetTime;
      }
      audioRef.current.play().catch(() => {});
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying, currentFrame, fps, audioUrl]);

  const handleTogglePlay = () => {
    setIsPlaying((prev) => !prev);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentFrame(0);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.pause();
    }
  };

  const handleSelectScene = (index: number) => {
    if (sceneOffsets[index]) {
      const targetFrame = sceneOffsets[index].startFrame;
      setCurrentFrame(targetFrame);
      if (audioRef.current) {
        audioRef.current.currentTime = targetFrame / fps;
      }
    }
  };

  const handleSynthesizeVoice = async () => {
    setActionFeedback('🎙️ Синтез аудіо через Voice AI...');
    const res = await synthesizeVoiceover(nodeId);
    if (res.success) {
      setActionFeedback('✅ Voice AI озвучення успішно згенеровано!');
      setTimeout(() => setActionFeedback(null), 3000);
    } else {
      setActionFeedback(`Помилка синтезу: ${res.error || 'Не вдалося озвучити'}`);
      setTimeout(() => setActionFeedback(null), 4000);
    }
  };

  const handleExportMp4 = async () => {
    setActionFeedback('🎬 Рендеринг MP4 відео через Remotion...');
    const res = await exportVideoMp4(nodeId);
    if (res.success) {
      setActionFeedback('✅ Відео MP4 успішно згенеровано!');
      setTimeout(() => setActionFeedback(null), 4000);
    } else {
      setActionFeedback(`Помилка експорту: ${res.error || 'Не вдалося експортувати MP4'}`);
      setTimeout(() => setActionFeedback(null), 4000);
    }
  };

  const handleCopyVoiceover = async () => {
    if (!video?.voiceover_script) return;
    try {
      await navigator.clipboard.writeText(video.voiceover_script);
      setCopiedVoiceover(true);
      setTimeout(() => setCopiedVoiceover(false), 2500);
    } catch {
      setActionFeedback('Не вдалося скопіювати текст у буфер.');
      setTimeout(() => setActionFeedback(null), 3000);
    }
  };

  const handleRegenerate = async () => {
    setIsPlaying(false);
    setCurrentFrame(0);
    const res = await generateMarketingVideo(nodeId);
    if (!res.success) {
      setActionFeedback(res.error || 'Помилка при генерації відео.');
      setTimeout(() => setActionFeedback(null), 4000);
    } else {
      setActionFeedback('Відео успішно згенеровано!');
      setTimeout(() => setActionFeedback(null), 3000);
    }
  };

  // 1. Loading & Generating State
  if (isGeneratingVideo) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center space-y-4 rounded-2xl bg-zinc-900/40 border border-zinc-800/60 backdrop-blur-md">
        <div className="relative">
          <div className="w-16 h-16 rounded-full bg-purple-600/20 border border-purple-500/30 flex items-center justify-center animate-pulse">
            <Film className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
          <Sparkles className="w-5 h-5 text-amber-400 absolute -top-1 -right-1 animate-bounce" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Синтез Remotion 9:16 Сценарію...</h3>
          <p className="text-xs text-zinc-400 mt-1 max-w-sm">
            Аналіз виконаних diff-артефактів, побудова 4-етапного маркетингового сторіборду (Hook, Problem, Solution, CTA) та войсоверу.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-purple-400 bg-purple-950/40 px-3 py-1.5 rounded-full border border-purple-800/50">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>Генерація композиції триває...</span>
        </div>
      </div>
    );
  }

  // 2. Empty State (no video generated yet)
  if (!video) {
    return (
      <div className="flex flex-col items-center justify-center p-10 text-center space-y-5 rounded-2xl bg-zinc-900/30 border border-zinc-800/80 backdrop-blur-md">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600/20 to-indigo-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-lg shadow-purple-950/50">
          <Film className="w-7 h-7" />
        </div>
        <div className="space-y-1.5 max-w-md">
          <h3 className="text-sm font-semibold text-zinc-100">Маркетингове 9:16 Відео ще не згенеровано</h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Створіть готовий для публікацій вертикальний відеоролик (TikTok, Reels, Shorts) на основі коду та артефактів цієї задачі.
          </p>
        </div>
        <button
          onClick={handleRegenerate}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-purple-900/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Sparkles className="w-4 h-4 text-amber-300" />
          <span>🎬 Згенерувати 9:16 Маркетингове Відео</span>
        </button>
        {actionFeedback && (
          <p className="text-xs text-amber-400 bg-amber-950/40 px-3 py-1 rounded border border-amber-900/50">
            {actionFeedback}
          </p>
        )}
      </div>
    );
  }

  const durationSeconds = (totalFrames / fps).toFixed(0);
  const currentTimeSeconds = (currentFrame / fps).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Top Control Bar with Badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-zinc-900/60 border border-zinc-800 rounded-xl backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-950/60 border border-purple-800/60 text-purple-300 font-medium">
            <Smartphone className="w-3.5 h-3.5 text-purple-400" />
            <span>9:16 Vertical</span>
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800/80 border border-zinc-700/60 text-zinc-300">
            <Clock className="w-3.5 h-3.5 text-zinc-400" />
            <span>{durationSeconds}s ({totalFrames} кадрів)</span>
          </span>
          <span className="px-2 py-1 rounded-md bg-zinc-800/50 border border-zinc-700/40 text-zinc-400 font-mono text-[11px]">
            {fps} FPS
          </span>
          <span className="hidden sm:inline-block px-2 py-1 rounded-md bg-zinc-800/50 border border-zinc-700/40 text-zinc-400 font-mono text-[11px]">
            ID: {video.composition_id}
          </span>
          {audioUrl && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 font-medium">
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>🔊 Аудіо озвучено</span>
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Voice AI Action */}
          <button
            onClick={handleSynthesizeVoice}
            disabled={isSynthesizingVoice}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-950/70 hover:bg-purple-900/80 disabled:opacity-50 text-purple-200 border border-purple-700/60 text-xs font-medium transition shadow-sm"
            title="Згенерувати живий аудіо-потік через Voice AI"
          >
            {isSynthesizingVoice ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                <span>Озвучення...</span>
              </>
            ) : (
              <>
                <Mic className="w-3.5 h-3.5 text-purple-400" />
                <span>{audioUrl ? '🎙️ Переозвучити Voice AI' : '🎙️ Озвучити через Voice AI'}</span>
              </>
            )}
          </button>

          {/* MP4 Export / Download Action */}
          {videoExportStatus?.status === 'completed' && videoExportStatus.download_url ? (
            <div className="flex items-center gap-1.5">
              <a
                href={videoExportStatus.download_url}
                download={`video_${nodeId}_vertical.mp4`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950 transition"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>✅ Скачати MP4</span>
              </a>
              <button
                onClick={handleExportMp4}
                disabled={isExportingVideo}
                className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 transition"
                title="Повторити рендеринг MP4"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isExportingVideo ? 'animate-spin' : ''}`} />
              </button>
            </div>
          ) : (
            <button
              onClick={handleExportMp4}
              disabled={isExportingVideo}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 text-white text-xs font-medium shadow-md shadow-purple-950 transition"
            >
              {isExportingVideo ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                  <span>Рендеринг MP4...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>⬇️ Експорт MP4 (9:16)</span>
                </>
              )}
            </button>
          )}

          <button
            onClick={handleRegenerate}
            disabled={isGeneratingVideo}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 hover:text-white text-xs font-medium border border-zinc-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-purple-400 ${isGeneratingVideo ? 'animate-spin' : ''}`} />
            <span>🎬 Регенерувати</span>
          </button>
        </div>
      </div>

      {actionFeedback && (
        <div className="p-2.5 rounded-lg bg-purple-950/50 border border-purple-800 text-xs text-purple-200 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-purple-400 shrink-0" />
          <span>{actionFeedback}</span>
        </div>
      )}

      {/* Main Studio Workspace: 9:16 Player + Storyboard Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: 9:16 Smartphone Mockup Frame */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="relative w-full max-w-[260px] aspect-[9/16] rounded-[36px] p-3.5 bg-zinc-950 border-[3px] border-zinc-700/70 shadow-2xl shadow-purple-950/30 flex flex-col justify-between overflow-hidden ring-1 ring-white/10 select-none">
            {/* Dynamic Animated Scene Background */}
            <div
              className="absolute inset-0 transition-all duration-700 ease-out"
              style={{
                background:
                  activeScene?.bg_gradient ||
                  'linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%)',
              }}
            />

            {/* Subtle Glassmorphic Overlay Texture */}
            <div className="absolute inset-0 bg-black/25 backdrop-blur-[1px] pointer-events-none" />

            {/* Smartphone Top Notch / Status Bar */}
            <div className="relative z-10 flex items-center justify-between text-[10px] text-white/70 px-2 pt-1 font-mono">
              <span>9:41</span>
              <div className="w-16 h-3.5 bg-black/80 rounded-full border border-white/10 mx-auto" />
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-[9px] uppercase font-bold text-white/90">DNK REELS</span>
              </div>
            </div>

            {/* Kinetic Typography Display (Active Scene Center) */}
            <div className="relative z-10 my-auto text-center px-3 space-y-3">
              {/* Scene Phase Tag */}
              <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-black/50 border border-white/20 text-[10px] font-semibold tracking-wider uppercase text-white shadow-sm backdrop-blur-md">
                <Flame className="w-3 h-3 text-amber-400" />
                <span>{activeScene?.id || `Scene ${activeSceneIndex + 1}`}</span>
              </div>

              {/* Animated Kinetic Scene Title */}
              <h2
                className="text-lg font-black leading-tight tracking-tight drop-shadow-lg transition-transform duration-300"
                style={{
                  color: activeScene?.accent_color || '#ffffff',
                  textShadow: '0 2px 10px rgba(0,0,0,0.8)',
                }}
              >
                {activeScene?.title || 'No Title'}
              </h2>

              {/* Kinetic Subtitle */}
              <p className="text-xs text-white/90 leading-snug drop-shadow-md font-medium px-1">
                {activeScene?.subtitle || ''}
              </p>
            </div>

            {/* Smartphone Bottom Bar: Audio Wave Simulation & Timecode */}
            <div className="relative z-10 p-2.5 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-md space-y-2">
              <div className="flex items-center justify-between text-[11px] text-white/80 font-mono">
                <div className="flex items-center gap-1.5">
                  <Volume2 className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-[10px] uppercase font-semibold text-purple-300">VOICEOVER SYNC</span>
                </div>
                <span>
                  {currentTimeSeconds}s / {durationSeconds}s
                </span>
              </div>

              {/* Mini Audio Visualizer Waves */}
              <div className="flex items-end justify-center gap-1 h-3 pt-0.5">
                {[40, 75, 55, 90, 65, 30, 85, 45, 100, 60, 80, 50, 70].map((h, i) => (
                  <div
                    key={i}
                    className="w-1 bg-purple-400/80 rounded-full transition-all duration-150"
                    style={{
                      height: isPlaying ? `${Math.max(20, (h * (currentFrame % 30)) / 30)}%` : '30%',
                      opacity: isPlaying ? 0.9 : 0.4,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Player Controls Bar */}
          <div className="w-full max-w-[260px] mt-4 space-y-2">
            <div className="flex items-center justify-between gap-2 p-2 bg-zinc-900 border border-zinc-800 rounded-xl">
              <button
                onClick={handleTogglePlay}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs transition shadow-md shadow-purple-950"
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-3.5 h-3.5" />
                    <span>Пауза</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Відтворити</span>
                  </>
                )}
              </button>

              <button
                onClick={handleReset}
                title="Перезапустити з початку"
                className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white border border-zinc-700 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Multi-Segment Scene Timeline Bar */}
            <div className="space-y-1">
              <div className="flex gap-1.5 h-2 w-full">
                {sceneOffsets.map((scene, idx) => {
                  const isCurrent = activeSceneIndex === idx;
                  const isPassed = currentFrame >= scene.endFrame;
                  let fillPct = 0;
                  if (isPassed) fillPct = 100;
                  else if (isCurrent) {
                    fillPct = Math.min(
                      100,
                      Math.max(0, ((currentFrame - scene.startFrame) / scene.duration) * 100)
                    );
                  }

                  return (
                    <button
                      key={scene.id}
                      onClick={() => handleSelectScene(idx)}
                      title={`${scene.id}: ${scene.title}`}
                      className="relative flex-1 h-full bg-zinc-800 rounded-full overflow-hidden hover:opacity-90 transition-opacity"
                    >
                      <div
                        className="h-full transition-all duration-75"
                        style={{
                          width: `${fillPct}%`,
                          backgroundColor: scene.accent_color || '#a855f7',
                        }}
                      />
                    </button>
                  );
                })}
              </div>
              <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono px-0.5">
                <span>{currentTimeSeconds}s</span>
                <div className="flex items-center gap-1.5">
                  <span className="text-purple-400 font-medium">
                    {activeScene?.id?.toUpperCase() || `SCENE ${activeSceneIndex + 1}`} ({activeSceneIndex + 1}/
                    {sceneOffsets.length})
                  </span>
                  {audioUrl && (
                    <span className="text-[9px] text-emerald-400 bg-emerald-950/70 border border-emerald-800/60 px-1.5 py-0.2 rounded font-sans">
                      🔊 Озвучено
                    </span>
                  )}
                </div>
                <span>{durationSeconds}.0s</span>
              </div>
            </div>

            {/* HTML5 Audio Stream element for Voice AI (Slice 2) */}
            {audioUrl && (
              <audio
                ref={audioRef}
                src={audioUrl}
                preload="auto"
                className="hidden"
                onEnded={() => {
                  if (isPlaying) setIsPlaying(false);
                }}
              />
            )}
          </div>
        </div>

        {/* Right Column: Scenes Breakdown, Voiceover, & Grounded Artifacts */}
        <div className="lg:col-span-7 space-y-5">
          {/* 1. Voiceover Script Block */}
          <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800 backdrop-blur-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Volume2 className="w-4 h-4 text-purple-400" />
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
                  Текст озвучення (Voiceover Script)
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleSynthesizeVoice}
                  disabled={isSynthesizingVoice}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-950/70 hover:bg-purple-900/80 disabled:opacity-50 text-purple-200 border border-purple-700/60 text-xs font-medium transition"
                  title="Озвучити текст через Voice AI"
                >
                  {isSynthesizingVoice ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                      <span>Генерація...</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-3.5 h-3.5 text-purple-400" />
                      <span>🎙️ Озвучити через Voice AI</span>
                    </>
                  )}
                </button>
                <button
                  onClick={handleCopyVoiceover}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 text-xs font-medium transition"
                >
                {copiedVoiceover ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Скопійовано!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>📋 Скопіювати текст озвучення</span>
                  </>
                )}
                </button>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800/80 text-xs text-zinc-300 leading-relaxed font-sans whitespace-pre-wrap select-text">
              {video.voiceover_script || 'Озвучення відсутнє.'}
            </div>
          </div>

          {/* 2. Interactive Scene Cards Breakdown */}
          <div className="space-y-2.5">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
                Сцени сторіборду (4 фази)
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {sceneOffsets.map((sc, idx) => {
                const isActive = activeSceneIndex === idx;
                return (
                  <div
                    key={sc.id}
                    onClick={() => handleSelectScene(idx)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      isActive
                        ? 'bg-purple-950/30 border-purple-500/80 ring-1 ring-purple-500/40 shadow-md shadow-purple-950/30'
                        : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/80'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                        style={{
                          backgroundColor: `${sc.accent_color}25`,
                          color: sc.accent_color,
                        }}
                      >
                        {sc.id}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        {(sc.duration / fps).toFixed(1)}s ({sc.duration}f)
                      </span>
                    </div>
                    <h5 className="font-semibold text-zinc-100 line-clamp-1">{sc.title}</h5>
                    <p className="text-[11px] text-zinc-400 line-clamp-2 mt-1 leading-normal">
                      {sc.subtitle}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 3. Grounded Code Artifacts Summary */}
          {video.grounded_diffs_summary && video.grounded_diffs_summary.length > 0 && (
            <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800 backdrop-blur-sm space-y-2.5">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-purple-400" />
                <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
                  Залучені артефакти коду (Grounded Artifacts)
                </h4>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {video.grounded_diffs_summary.map((item, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-950 border border-zinc-800 text-zinc-300 font-mono text-[11px]"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    <span>{item}</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

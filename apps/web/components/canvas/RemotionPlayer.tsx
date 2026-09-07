// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/canvas/RemotionPlayer.tsx"
// purpose: "In-canvas interactive Remotion player for live preview of 9:16 Shorts with playback timeline."
// author: "DNK-e.com Maksym"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState, useRef, useEffect } from 'react';

export interface RemotionPlayerProps {
  compositionId?: string;
  durationInFrames?: number;
  fps?: number;
  width?: number;
  height?: number;
  videoUrl?: string;
  title?: string;
  onTimeUpdate?: (frame: number) => void;
}

export const RemotionPlayer: React.FC<RemotionPlayerProps> = ({
  compositionId = 'shorts_comp_ugc',
  durationInFrames = 300, // 10 seconds at 30fps
  fps = 30,
  width = 1080,
  height = 1920,
  videoUrl,
  title = 'DNK Shorts Preview',
  onTimeUpdate,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const durationSeconds = durationInFrames / fps;

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentFrame((prev) => {
          const next = prev + 1;
          if (next >= durationInFrames) {
            setIsPlaying(false);
            return 0;
          }
          if (onTimeUpdate) {
            onTimeUpdate(next);
          }
          return next;
        });
      }, 1000 / fps);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isPlaying, durationInFrames, fps, onTimeUpdate]);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const frame = parseInt(e.target.value, 10);
    setCurrentFrame(frame);
    if (videoRef.current) {
      videoRef.current.currentTime = (frame / fps);
    }
    if (onTimeUpdate) {
      onTimeUpdate(frame);
    }
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
    if (videoRef.current) {
      if (!isPlaying) {
        videoRef.current.play().catch(() => {});
      } else {
        videoRef.current.pause();
      }
    }
  };

  const currentTimeSeconds = (currentFrame / fps).toFixed(1);

  return (
    <div className="flex flex-col bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl w-full max-w-sm text-white select-none">
      {/* Header Info */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-wide text-slate-300 uppercase truncate max-w-[180px]">
            {title}
          </span>
        </div>
        <span className="text-[10px] font-mono bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
          9:16 • {width}x{height}
        </span>
      </div>

      {/* 9:16 Video Canvas Preview Stage */}
      <div className="relative w-full aspect-[9/16] bg-black flex items-center justify-center overflow-hidden group">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-cover"
            muted={isMuted}
            loop
            playsInline
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-indigo-950 via-slate-900 to-purple-950 p-6 text-center">
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#6366f1_1px,transparent_1px)] [background-size:16px_16px]" />
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/30 border border-indigo-500/50 flex items-center justify-center mb-4 shadow-lg shadow-indigo-500/20">
              <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Remotion Live Preview</h4>
            <p className="text-xs text-slate-400 font-mono mb-4">Composition: {compositionId}</p>
            <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl px-4 py-2 text-xs font-mono text-emerald-400 backdrop-blur">
              Frame: {currentFrame} / {durationInFrames} ({currentTimeSeconds}s)
            </div>
          </div>
        )}

        {/* Overlay Play/Pause Button on Hover */}
        <button
          onClick={togglePlay}
          className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-md border border-white/40 flex items-center justify-center shadow-xl transform group-hover:scale-105 transition-transform">
            {isPlaying ? (
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-6 h-6 text-white translate-x-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </div>
        </button>
      </div>

      {/* Timeline Controls */}
      <div className="p-4 bg-slate-950 flex flex-col space-y-3">
        {/* Scrubber */}
        <div className="flex items-center space-x-3">
          <span className="text-[10px] font-mono text-slate-400 w-8">{currentTimeSeconds}s</span>
          <input
            type="range"
            min={0}
            max={durationInFrames - 1}
            value={currentFrame}
            onChange={handleSeek}
            className="flex-1 accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
          <span className="text-[10px] font-mono text-slate-400 w-8 text-right">{durationSeconds.toFixed(1)}s</span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-1">
          <button
            onClick={togglePlay}
            className="flex-1 mr-2 py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center space-x-2"
          >
            {isPlaying ? (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" /></svg>
                <span>Pause</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                <span>Play Preview</span>
              </>
            )}
          </button>

          <button
            onClick={() => setIsMuted(!isMuted)}
            className={`p-2 rounded-xl border text-xs font-semibold transition-all ${
              isMuted
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clipRule="evenodd" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

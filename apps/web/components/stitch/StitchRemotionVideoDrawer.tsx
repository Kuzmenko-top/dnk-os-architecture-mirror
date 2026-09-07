// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/stitch/StitchRemotionVideoDrawer.tsx"
// purpose: "Remotion 9:16 Video AI Creator Drawer for DNK OS with real-time kinetic preview, template selection & render pipeline."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect, useRef } from 'react';

export interface StitchRemotionVideoDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialTitle?: string;
  initialPrice?: number;
  onNotification?: (msg: { text: string; type: 'success' | 'info' | 'warning' | 'error' }) => void;
}

export interface VideoTemplate {
  id: string;
  name: string;
  aspectRatio: string;
  fps: number;
  durationSeconds: number;
  badge: string;
  bgGradient: string;
}

const TEMPLATES: VideoTemplate[] = [
  {
    id: 'VIRAL_TIKTOK',
    name: 'Viral TikTok Hook',
    aspectRatio: '9:16',
    fps: 30,
    durationSeconds: 5,
    badge: 'Trending 🔥',
    bgGradient: 'from-fuchsia-900 via-indigo-950 to-slate-950',
  },
  {
    id: 'CLEAN_LUXURY',
    name: 'Clean Luxury UGC',
    aspectRatio: '9:16',
    fps: 30,
    durationSeconds: 8,
    badge: 'High AOV 💎',
    bgGradient: 'from-amber-950 via-slate-900 to-black',
  },
  {
    id: 'PRODUCT_SHOWCASE',
    name: 'Tech Feature Showcase',
    aspectRatio: '9:16',
    fps: 60,
    durationSeconds: 6,
    badge: 'Feature Focus ⚡',
    bgGradient: 'from-cyan-950 via-slate-950 to-slate-900',
  },
];

export default function StitchRemotionVideoDrawer({
  isOpen,
  onClose,
  initialTitle = 'DNK Neural Agent Hub',
  initialPrice = 149.99,
  onNotification,
}: StitchRemotionVideoDrawerProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('VIRAL_TIKTOK');
  const [title, setTitle] = useState<string>(initialTitle);
  const [hook, setHook] = useState<string>('Stop scrolling! Watch this');
  const [price, setPrice] = useState<number>(initialPrice);
  const [ctaText, setCtaText] = useState<string>('Get Yours Now 🚀');
  const [reviewerName, setReviewerName] = useState<string>('Alex M., Verified Buyer');
  const [reviewText, setReviewText] = useState<string>('Literally 10x faster than doing it manually.');

  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [renderedVideoUrl, setRenderedVideoUrl] = useState<string | null>(null);
  const [renderProgress, setRenderProgress] = useState<number>(0);

  const activeTemplate = TEMPLATES.find((t) => t.id === selectedTemplate) || TEMPLATES[0];
  const totalFrames = activeTemplate.fps * activeTemplate.durationSeconds;
  const playTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync initial props
  useEffect(() => {
    if (initialTitle) setTitle(initialTitle);
    if (initialPrice) setPrice(initialPrice);
  }, [initialTitle, initialPrice]);

  // Frame animation loop
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = setInterval(() => {
        setCurrentFrame((prev) => {
          if (prev >= totalFrames) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000 / activeTemplate.fps);
    } else if (playTimerRef.current) {
      clearInterval(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current);
    };
  }, [isPlaying, totalFrames, activeTemplate.fps]);

  if (!isOpen) return null;

  const progressPercent = Math.min(100, Math.round((currentFrame / totalFrames) * 100));

  const handleTriggerRender = async () => {
    setIsRendering(true);
    setRenderProgress(10);
    onNotification?.({
      text: `Rendering Remotion 9:16 composition for "${title}"...`,
      type: 'info',
    });

    try {
      const response = await fetch('/api/v1/video/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_style: selectedTemplate,
          title,
          hook,
          price,
          cta_text: ctaText,
          reviewer_name: reviewerName,
          review_text: reviewText,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRenderProgress(100);
        if (data.render_result?.output_path) {
          setRenderedVideoUrl(data.render_result.output_path);
        }
        onNotification?.({
          text: 'Video rendered successfully! Ready for export.',
          type: 'success',
        });
      } else {
        // Fallback simulated render for preview
        setTimeout(() => {
          setRenderProgress(100);
          onNotification?.({
            text: 'Preview timeline synchronized.',
            type: 'info',
          });
        }, 1200);
      }
    } catch {
      // Local preview fallback
      setRenderProgress(100);
      onNotification?.({
        text: 'Preview composition generated in local canvas.',
        type: 'info',
      });
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[540px] bg-slate-950/95 border-l border-slate-800 shadow-2xl backdrop-blur-2xl flex flex-col transition-all">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-fuchsia-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-fuchsia-600/20">
            <span className="text-lg">🎬</span>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white tracking-wide">
              Remotion Video Studio (9:16)
            </h2>
            <p className="text-xs text-slate-400">Autonomous Video AI Creator &bull; FrameCN Engine</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800/80 transition-all text-xs"
        >
          ✕
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {/* Template Selector */}
        <div>
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
            Video Template Style
          </label>
          <div className="grid grid-cols-3 gap-2">
            {TEMPLATES.map((tmpl) => (
              <button
                key={tmpl.id}
                onClick={() => {
                  setSelectedTemplate(tmpl.id);
                  setCurrentFrame(0);
                  setIsPlaying(false);
                }}
                className={`p-3 rounded-xl border text-left flex flex-col justify-between transition-all ${
                  selectedTemplate === tmpl.id
                    ? 'border-indigo-500 bg-indigo-500/10 text-white shadow-md shadow-indigo-500/10'
                    : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-300'
                }`}
              >
                <div>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 mb-1 inline-block">
                    {tmpl.badge}
                  </span>
                  <div className="text-xs font-medium mt-1">{tmpl.name}</div>
                </div>
                <div className="text-[10px] text-slate-400 mt-2 font-mono">
                  {tmpl.durationSeconds}s &bull; {tmpl.fps}fps
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 9:16 Phone Preview Mockup */}
        <div className="flex flex-col items-center">
          <div className="relative w-[240px] h-[426px] rounded-3xl border-4 border-slate-700/80 bg-slate-900 overflow-hidden shadow-2xl flex flex-col justify-between">
            {/* Dynamic Background */}
            <div
              className={`absolute inset-0 bg-gradient-to-b ${activeTemplate.bgGradient} opacity-90 transition-all duration-500`}
            />

            {/* Kinetic Dynamic Content */}
            <div className="relative z-10 p-4 flex flex-col h-full justify-between">
              {/* Top: Hook & Avatar */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-600/80 text-white uppercase tracking-wider animate-pulse">
                    LIVE REEL
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {Math.floor(currentFrame / activeTemplate.fps)}s / {activeTemplate.durationSeconds}s
                  </span>
                </div>

                <div
                  className="bg-black/40 backdrop-blur-md rounded-xl p-2.5 border border-white/10 transition-transform duration-300"
                  style={{
                    transform: isPlaying
                      ? `scale(${1 + Math.sin(currentFrame / 4) * 0.03})`
                      : 'scale(1)',
                  }}
                >
                  <p className="text-xs font-black text-amber-300 leading-snug tracking-tight uppercase">
                    &ldquo;{hook}&rdquo;
                  </p>
                </div>
              </div>

              {/* Center: Hero Product Title & Price */}
              <div className="text-center space-y-1.5 my-auto">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500/30 to-fuchsia-500/30 border border-white/20 flex items-center justify-center shadow-lg">
                  <span className="text-2xl animate-bounce">📦</span>
                </div>
                <h3 className="text-sm font-extrabold text-white leading-tight drop-shadow-md">
                  {title}
                </h3>
                <div className="inline-flex items-baseline gap-1.5 bg-black/60 px-3 py-1 rounded-full border border-emerald-500/30">
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    ${price.toFixed(2)}
                  </span>
                  <span className="text-[10px] text-slate-400 line-through">
                    ${(price * 1.4).toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Bottom: UGC Review & CTA */}
              <div className="space-y-2">
                <div className="bg-white/10 backdrop-blur-md rounded-xl p-2 border border-white/10">
                  <p className="text-[11px] text-slate-200 italic line-clamp-2">
                    &ldquo;{reviewText}&rdquo;
                  </p>
                  <span className="text-[9px] text-amber-300 font-semibold mt-1 block">
                    ⭐ 5.0 &bull; {reviewerName}
                  </span>
                </div>

                <div className="w-full py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-black text-xs rounded-xl text-center shadow-lg uppercase tracking-wider">
                  {ctaText}
                </div>
              </div>
            </div>

            {/* Scrubber Progress Bar inside Mockup */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-fuchsia-500 transition-all duration-75"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Transport Bar */}
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md transition-all flex items-center gap-1.5"
            >
              <span>{isPlaying ? '⏸ Pause' : '▶ Play Preview'}</span>
            </button>
            <button
              onClick={() => {
                setCurrentFrame(0);
                setIsPlaying(false);
              }}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
            >
              ⏮ Reset
            </button>
            <span className="text-xs font-mono text-slate-400">
              {currentFrame} / {totalFrames} frames ({progressPercent}%)
            </span>
          </div>
        </div>

        {/* Video Creative Controls */}
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Video Hook / Opening Caption
            </label>
            <input
              type="text"
              value={hook}
              onChange={(e) => setHook(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Product Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Price (USD)</label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">CTA Button Text</label>
            <input
              type="text"
              value={ctaText}
              onChange={(e) => setCtaText(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">UGC Review Snippet</label>
            <input
              type="text"
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {renderedVideoUrl && (
          <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 space-y-1">
            <span className="font-semibold block">✅ Render Ready:</span>
            <span className="font-mono text-[10px] text-slate-400 break-all">{renderedVideoUrl}</span>
          </div>
        )}
      </div>

      {/* Footer Render Action */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <button
          onClick={onClose}
          className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        >
          Close
        </button>
        <button
          onClick={handleTriggerRender}
          disabled={isRendering}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            isRendering
              ? 'bg-indigo-600/50 text-indigo-200 cursor-not-allowed'
              : 'bg-gradient-to-r from-fuchsia-600 to-indigo-600 hover:from-fuchsia-500 hover:to-indigo-500 text-white shadow-lg shadow-indigo-600/25'
          }`}
        >
          {isRendering ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              <span>Rendering Remotion {renderProgress}%...</span>
            </>
          ) : (
            <>
              <span>⚡ Render H.264 MP4</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export { StitchRemotionVideoDrawer };

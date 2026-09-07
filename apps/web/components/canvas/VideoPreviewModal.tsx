// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_VideoPreviewModal"
// purpose: "Diffusion Studio SOTA Assimilation: Agentic Multi-Track Video Timeline IDE & 9:16 Canvas Simulator"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-29"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Film, 
  Sparkles, 
  X, 
  Sliders, 
  Download, 
  CheckCircle2, 
  Layers, 
  Volume2, 
  Smartphone,
  Cpu,
  Code2,
  Copy,
  Check,
  Music,
  Type,
  Video as VideoIcon,
  Tag
} from 'lucide-react';

interface VideoPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTitle?: string;
  initialPrice?: number;
}

export default function VideoPreviewModal({
  isOpen,
  onClose,
  initialTitle = 'DNK Ultra Clean Hoodie',
  initialPrice = 89.99
}: VideoPreviewModalProps) {
  const [activeTab, setActiveTab] = useState<'canvas' | 'timeline' | 'code'>('canvas');
  const [style, setStyle] = useState<'VIRAL_TIKTOK' | 'CLEAN_LUXURY' | 'ECOMMERCE_URGENCY'>('VIRAL_TIKTOK');
  const [title, setTitle] = useState(initialTitle);
  const [price, setPrice] = useState(initialPrice);
  const [ctaText, setCtaText] = useState('Order Now with 50% OFF');
  
  const [isPlaying, setIsPlaying] = useState(true);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isRendering, setIsRendering] = useState(false);
  const [renderResult, setRenderResult] = useState<any | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);
  const [timelineData, setTimelineData] = useState<any | null>(null);
  const [tsxCode, setTsxCode] = useState<string>('');

  const totalFrames = 150; // 5 seconds at 30 fps
  const fps = 30;

  // Load Multi-Track Timeline from backend
  const fetchTimeline = async () => {
    try {
      const res = await fetch('/api/v1/video/timeline/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          price,
          original_price: price * 1.5,
          hook: style === 'VIRAL_TIKTOK' ? 'Wait! Stop Scrolling! 🔥' : 'Redefine Your Style',
          cta_text: ctaText,
          template_style: style
        })
      });
      const data = await res.json();
      if (data.success) {
        setTimelineData(data.composition);
        setTsxCode(data.tsx_code);
      }
    } catch (e) {
      console.error('Failed to fetch timeline:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTimeline();
    }
  }, [isOpen, title, price, ctaText, style]);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentFrame((prev) => (prev >= totalFrames ? 0 : prev + 1));
      }, 1000 / fps);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  if (!isOpen) return null;

  const currentSeconds = (currentFrame / fps).toFixed(1);
  const progressPct = (currentFrame / totalFrames) * 100;

  // Kinetic scene calculation
  const isHookActive = currentFrame >= 0 && currentFrame < 45;
  const isProductActive = currentFrame >= 45 && currentFrame < 105;
  const isCtaActive = currentFrame >= 105;

  const handleRender = async () => {
    setIsRendering(true);
    setRenderResult(null);
    try {
      const res = await fetch('/api/v1/video/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_style: style,
          title: title,
          hook: style === 'VIRAL_TIKTOK' ? 'Wait! Stop Scrolling! 🔥' : 'Redefine Your Style',
          price: price,
          original_price: price * 1.5,
          cta_text: ctaText,
          captions: [
            'Stop scrolling!',
            `Meet the all-new ${title}`,
            'Engineered for maximum comfort & aesthetics'
          ]
        })
      });

      const data = await res.json();
      if (res.ok) {
        setRenderResult(data);
      } else {
        alert(data.detail || 'Rendering failed');
      }
    } catch (e: any) {
      alert(`Render error: ${e.message}`);
    } finally {
      setIsRendering(false);
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(tsxCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl w-full max-w-5xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-pink-400">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">dnk_video_ai_creator</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/30">
                  Diffusion Studio IDE
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Remotion & FFmpeg
                </span>
              </div>
              <p className="text-xs text-slate-400">Автономний Multi-Track Video IDE (9:16 Canvas ⇄ Multi-Track Timeline ⇄ TSX Code)</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Tab Switcher */}
            <div className="flex items-center p-1 bg-slate-950/80 border border-slate-800 rounded-xl">
              <button
                onClick={() => setActiveTab('canvas')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'canvas'
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>9:16 Смартфон</span>
              </button>

              <button
                onClick={() => setActiveTab('timeline')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'timeline'
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Таймлайн (4 Треки)</span>
              </button>

              <button
                onClick={() => setActiveTab('code')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  activeTab === 'code'
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>TSX Код</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800/60 hover:bg-slate-700/80 text-slate-400 hover:text-white transition-all cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-6 p-6 overflow-y-auto">
          {/* Main Visualizer Area */}
          <div className="md:col-span-8 flex flex-col items-center justify-center bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4">
            {/* TAB 1: 9:16 Smartphone Simulator */}
            {activeTab === 'canvas' && (
              <div className="flex flex-col items-center">
                <div className="relative w-[280px] h-[500px] bg-slate-900 border-[6px] border-slate-800 rounded-[42px] shadow-2xl overflow-hidden flex flex-col justify-between p-4 select-none">
                  {/* Top notch */}
                  <div className="absolute top-2 left-1/2 -translate-x-1/2 w-28 h-4 bg-slate-800 rounded-full z-20" />

                  {/* Dynamic Video Scene Background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-slate-950 to-purple-950 flex items-center justify-center overflow-hidden">
                    <div className="absolute w-48 h-48 rounded-full bg-pink-500/15 blur-3xl animate-pulse" />
                    <div className="absolute w-40 h-40 rounded-full bg-blue-500/15 blur-3xl -bottom-10 -right-10" />

                    {/* SCENE 1: Kinetic Hook */}
                    {isHookActive && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center animate-in zoom-in-90 duration-300">
                        <span className="text-4xl mb-2 animate-bounce">🔥</span>
                        <h3 className="text-2xl font-black text-white uppercase tracking-tight bg-gradient-to-r from-amber-300 via-pink-400 to-rose-400 bg-clip-text text-transparent drop-shadow-md">
                          Stop Scrolling!
                        </h3>
                        <p className="text-xs text-pink-200 mt-2 font-mono bg-black/40 px-3 py-1 rounded-full border border-pink-500/30">
                          Unbelievable Tech Drop
                        </p>
                      </div>
                    )}

                    {/* SCENE 2: Product Showcase */}
                    {isProductActive && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center animate-in slide-in-from-bottom-8 duration-300">
                        <div className="w-28 h-28 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-indigo-500/20 border border-indigo-400/40 flex items-center justify-center mb-4 shadow-xl">
                          <Sparkles className="w-12 h-12 text-cyan-300" />
                        </div>
                        <h4 className="text-lg font-bold text-white leading-snug">{title}</h4>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-2xl font-black text-emerald-400">${price.toFixed(2)}</span>
                          <span className="text-xs text-slate-500 line-through">${(price * 1.5).toFixed(2)}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                            -33%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* SCENE 3: Call to Action */}
                    {isCtaActive && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center animate-in zoom-in-95 duration-300">
                        <div className="p-3 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 mb-3 animate-pulse">
                          <CheckCircle2 className="w-8 h-8" />
                        </div>
                        <h4 className="text-xl font-black text-white uppercase tracking-wider">{ctaText}</h4>
                        <p className="text-[11px] text-slate-300 mt-1">Free 2-Day Delivery Included</p>
                        <div className="mt-4 px-6 py-2.5 rounded-xl bg-gradient-to-r from-pink-500 to-rose-500 text-white font-bold text-xs shadow-lg shadow-pink-500/30 animate-pulse">
                          Tap Link in Bio 🔗
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Bottom Overlays inside phone */}
                  <div className="relative z-10 flex items-center justify-between text-[10px] text-slate-400 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                    <span className="flex items-center gap-1 font-mono">
                      <Volume2 className="w-3 h-3 text-pink-400" /> 128 BPM Trending Track
                    </span>
                    <span className="font-mono text-cyan-300">{currentSeconds}s</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Multi-Track Timeline (Diffusion Studio ECS Model) */}
            {activeTab === 'timeline' && (
              <div className="w-full flex flex-col gap-3 py-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-purple-400" /> Multi-Track Layer Sequencer (150 Frames / 5.0s)
                  </div>
                  <span className="font-mono text-[11px] text-pink-400 bg-pink-500/10 px-2.5 py-0.5 rounded-full border border-pink-500/20">
                    Frame {currentFrame} / 150 ({currentSeconds}s)
                  </span>
                </div>

                {/* Track 1: Video */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex flex-col gap-1.5">
                  <div className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5">
                    <VideoIcon className="w-3.5 h-3.5 text-indigo-400" /> Track 1: Video & Background Scene
                  </div>
                  <div className="w-full h-8 bg-slate-900 rounded-lg relative overflow-hidden flex gap-1 p-0.5">
                    <div className="w-[30%] h-full bg-indigo-600/30 border border-indigo-500/50 rounded flex items-center px-2 text-[10px] text-indigo-300 truncate">
                      Hook Scene (0-45f)
                    </div>
                    <div className="w-[40%] h-full bg-blue-600/30 border border-blue-500/50 rounded flex items-center px-2 text-[10px] text-blue-300 truncate">
                      Product Showcase (45-105f)
                    </div>
                    <div className="w-[30%] h-full bg-purple-600/30 border border-purple-500/50 rounded flex items-center px-2 text-[10px] text-purple-300 truncate">
                      Outro CTA (105-150f)
                    </div>
                    {/* Live Playhead Indicator */}
                    <div 
                      className="absolute top-0 bottom-0 w-0.5 bg-rose-500 shadow-md z-10"
                      style={{ left: `${progressPct}%` }}
                    />
                  </div>
                </div>

                {/* Track 2: Text / Kinetic Typography */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex flex-col gap-1.5">
                  <div className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5">
                    <Type className="w-3.5 h-3.5 text-pink-400" /> Track 2: Kinetic Typography & Captions
                  </div>
                  <div className="w-full h-8 bg-slate-900 rounded-lg relative overflow-hidden flex gap-1 p-0.5">
                    <div className="w-[30%] h-full bg-pink-600/30 border border-pink-500/50 rounded flex items-center px-2 text-[10px] text-pink-300 truncate">
                      🔥 Stop Scrolling
                    </div>
                    <div className="w-[20%] h-full bg-amber-600/30 border border-amber-500/50 rounded flex items-center px-2 text-[10px] text-amber-300 truncate">
                      ✨ 100% Organic
                    </div>
                    <div className="w-[20%] h-full bg-cyan-600/30 border border-cyan-500/50 rounded flex items-center px-2 text-[10px] text-cyan-300 truncate">
                      ⚡ Cyber Fit
                    </div>
                    <div className="w-[30%] h-full bg-emerald-600/30 border border-emerald-500/50 rounded flex items-center px-2 text-[10px] text-emerald-300 truncate">
                      🛍️ Order Now
                    </div>
                    {/* Live Playhead */}
                    <div 
                      className="absolute top-0 bottom-0 w-0.5 bg-rose-500 shadow-md z-10"
                      style={{ left: `${progressPct}%` }}
                    />
                  </div>
                </div>

                {/* Track 3: Audio */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex flex-col gap-1.5">
                  <div className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5">
                    <Music className="w-3.5 h-3.5 text-cyan-400" /> Track 3: Audio & Trending EDM Beat (128 BPM)
                  </div>
                  <div className="w-full h-8 bg-slate-900 rounded-lg relative overflow-hidden p-0.5">
                    <div className="w-full h-full bg-cyan-600/20 border border-cyan-500/40 rounded flex items-center px-3 text-[10px] text-cyan-300 font-mono">
                      🎵 Phonk Bassline (128 BPM) • Audio Ducking: -6dB
                    </div>
                    {/* Live Playhead */}
                    <div 
                      className="absolute top-0 bottom-0 w-0.5 bg-rose-500 shadow-md z-10"
                      style={{ left: `${progressPct}%` }}
                    />
                  </div>
                </div>

                {/* Track 4: Stickers & Conversion Badges */}
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex flex-col gap-1.5">
                  <div className="text-[11px] font-bold text-slate-400 flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-emerald-400" /> Track 4: Conversion Badges & Rating
                  </div>
                  <div className="w-full h-8 bg-slate-900 rounded-lg relative overflow-hidden flex gap-1 p-0.5">
                    <div className="w-[30%] h-full" />
                    <div className="w-[70%] h-full bg-emerald-600/30 border border-emerald-500/50 rounded flex items-center px-2 text-[10px] text-emerald-300 truncate">
                      ⭐ 4.9 Rating • 50% OFF Badge (45-150f)
                    </div>
                    {/* Live Playhead */}
                    <div 
                      className="absolute top-0 bottom-0 w-0.5 bg-rose-500 shadow-md z-10"
                      style={{ left: `${progressPct}%` }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Synchronized Remotion TSX Code */}
            {activeTab === 'code' && (
              <div className="w-full flex flex-col gap-2 h-full">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Code2 className="w-4 h-4 text-cyan-400" /> Declarative Remotion TSX AST
                  </div>
                  <button
                    onClick={handleCopyCode}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition-all cursor-pointer font-mono"
                  >
                    {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedCode ? 'Скопійовано' : 'Копіювати TSX'}</span>
                  </button>
                </div>
                <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-slate-300 font-mono text-[11px] overflow-auto max-h-[440px] leading-relaxed">
                  {tsxCode || '// Generating Remotion TSX AST...'}
                </pre>
              </div>
            )}

            {/* Playback Controls & Scrubber */}
            <div className="w-full max-w-md mt-4 flex flex-col gap-2">
              <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>{currentSeconds}s / 5.0s</span>
                <span className="text-pink-400">Frame {currentFrame} / 150</span>
              </div>
              <div 
                className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden relative cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const clickX = e.clientX - rect.left;
                  const pct = clickX / rect.width;
                  setCurrentFrame(Math.floor(pct * totalFrames));
                }}
              >
                <div 
                  className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 transition-all duration-75"
                  style={{ width: `${progressPct}%` }}
                />
              </div>

              <div className="flex items-center justify-center gap-3 mt-1">
                <button
                  onClick={() => setCurrentFrame(0)}
                  className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all cursor-pointer"
                  title="Спочатку"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white shadow-lg transition-all cursor-pointer"
                  title={isPlaying ? 'Пауза' : 'Відтворити'}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Controls & FFmpeg Renderer */}
          <div className="md:col-span-4 flex flex-col gap-4">
            {/* Style Selector */}
            <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-2xl">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" /> Template Style
              </label>
              <div className="flex flex-col gap-2 mt-2">
                {[
                  { id: 'VIRAL_TIKTOK', label: 'Viral TikTok Hook', desc: '9:16 Fast-Paced' },
                  { id: 'CLEAN_LUXURY', label: 'Clean Luxury UGC', desc: 'Minimalist Premium' },
                  { id: 'ECOMMERCE_URGENCY', label: 'Flash Sale Urgency', desc: 'Countdown Drop' },
                ].map((tpl) => (
                  <button
                    key={tpl.id}
                    onClick={() => setStyle(tpl.id as any)}
                    className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                      style === tpl.id
                        ? 'bg-purple-600/20 border-purple-500/60 text-white shadow-md shadow-purple-500/10'
                        : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div className="text-xs font-bold">{tpl.label}</div>
                    <div className="text-[10px] text-slate-500">{tpl.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Creative Props */}
            <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col gap-3">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-cyan-400" /> Creative Props
              </label>
              
              <div>
                <label className="text-[11px] text-slate-400">Назва Продукту</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400">Ціна ($ USD)</label>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400">Call to Action (CTA)</label>
                <input
                  type="text"
                  value={ctaText}
                  onChange={(e) => setCtaText(e.target.value)}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 font-sans"
                />
              </div>
            </div>

            {/* FFmpeg Render Trigger */}
            <div className="p-4 bg-gradient-to-br from-slate-900/90 to-purple-950/40 border border-purple-500/30 rounded-2xl flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-pink-400" /> FFmpeg Renderer
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">Рендеринг MP4 відео</p>
                </div>
                <button
                  onClick={handleRender}
                  disabled={isRendering}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 active:scale-95 text-xs font-bold text-white shadow-lg shadow-purple-600/30 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isRendering ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Рендеринг...</span>
                    </>
                  ) : (
                    <>
                      <Film className="w-3.5 h-3.5" />
                      <span>Скомпілювати MP4</span>
                    </>
                  )}
                </button>
              </div>

              {renderResult && (
                <div className="mt-2 p-3 bg-emerald-950/60 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 animate-in fade-in duration-200 flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Успішно!
                    </span>
                    <span className="font-mono text-[10px] text-emerald-400">
                      {renderResult.render_time_ms}ms
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-300 font-mono">
                    Файл: <span className="text-cyan-300">{renderResult.output_path || renderResult.output_filename}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

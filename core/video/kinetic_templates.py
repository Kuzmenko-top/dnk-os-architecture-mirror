# --- DNK-MRH-HEADER ---
# mrh_id: "core/video/kinetic_templates.py"
# purpose: "High-converting kinetic video templates library for dnk_video_ai_creator (9:16 TikTok/Reels)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateStyle(str, Enum):
    CYBER_NEON = "CYBER_NEON"
    CLEAN_LUXURY = "CLEAN_LUXURY"
    VIRAL_TIKTOK = "VIRAL_TIKTOK"
    ECOMMERCE_URGENCY = "ECOMMERCE_URGENCY"


class KineticTemplateSpec(BaseModel):
    template_name: str
    style: TemplateStyle = TemplateStyle.VIRAL_TIKTOK
    title: str
    hook: str
    price: float
    original_price: Optional[float] = None
    discount_pct: Optional[int] = None
    rating: float = 4.9
    reviews_count: int = 1240
    cta_text: str = "Order Now with 50% OFF"
    captions: List[str] = Field(default_factory=list)


class KineticTemplatesLibrary:
    """
    SOTA Remotion Video Template Engine.
    Generates high-performance React Remotion TSX code for 9:16 vertical video ads.
    """

    def generate_viral_reel_tsx(self, spec: KineticTemplateSpec) -> str:
        captions_json = json.dumps(spec.captions or ["Stop scrolling!", f"Meet the all-new {spec.title}", "Limited drop available now"])
        orig_p = spec.original_price if spec.original_price is not None else round(spec.price * 1.5, 2)
        
        return f"""import React from 'react';
import {{
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
}} from 'remotion';

export interface ViralReelProps {{
  title?: string;
  price?: number;
  originalPrice?: number;
  ctaText?: string;
}}

export const ViralReelComposition: React.FC<ViralReelProps> = ({{
  title = "{spec.title}",
  price = {spec.price},
  originalPrice = {orig_p},
  ctaText = "{spec.cta_text}",
}}) => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();

  const scale = spring({{ frame, fps, config: {{ damping: 12, stiffness: 120 }} }});
  const hookOpacity = interpolate(frame, [0, 15, 45, 60], [0, 1, 1, 0]);
  const productSlide = interpolate(frame, [50, 75], [100, 0], {{ extrapolateRight: 'clamp' }});
  const ctaPulse = 1 + 0.05 * Math.sin(frame / 5);

  const captions = {captions_json};
  const activeCaptionIndex = Math.min(Math.floor(frame / 40), captions.length - 1);

  return (
    <AbsoluteFill className="bg-slate-950 text-white font-sans flex flex-col items-center justify-between p-12 select-none overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/40 via-slate-950 to-slate-950" />
      <div className="absolute top-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

      <div
        className="relative z-10 text-center mt-12 transition-opacity"
        style={{{{ opacity: hookOpacity, transform: `scale(${{scale}})` }}}}
      >
        <span className="px-4 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 text-sm font-bold uppercase tracking-widest">
          🔥 TRENDING DROP
        </span>
        <h1 className="text-4xl font-extrabold text-white mt-4 tracking-tight">
          "{spec.hook}"
        </h1>
      </div>

      <div
        className="relative z-10 w-full max-w-sm rounded-3xl bg-slate-900/80 border border-slate-800 p-8 backdrop-blur-2xl shadow-2xl flex flex-col items-center text-center"
        style={{{{ transform: `translateY(${{productSlide}}px)` }}}}
      >
        <div className="w-48 h-48 rounded-2xl bg-indigo-900/30 border border-indigo-500/20 flex items-center justify-center mb-6 shadow-inner">
          <span className="text-6xl">📦</span>
        </div>

        <h2 className="text-2xl font-bold text-white">{{title}}</h2>
        
        <div className="flex items-baseline gap-3 my-4">
          <span className="text-4xl font-black text-emerald-400">${{price}}</span>
          <span className="text-xl line-through text-slate-500">${{originalPrice}}</span>
          <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 text-xs font-bold">
            SAVE 33%
          </span>
        </div>

        <p className="text-sm font-medium text-slate-300 min-h-[40px] px-2">
          {{captions[activeCaptionIndex]}}
        </p>
      </div>

      <div
        className="relative z-10 w-full max-w-sm mb-8"
        style={{{{ transform: `scale(${{ctaPulse}})` }}}}
      >
        <button className="w-full py-4 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-lg shadow-xl shadow-indigo-600/40 tracking-wide transition-all">
          {{ctaText}} ➔
        </button>
      </div>
    </AbsoluteFill>
  );
}};
"""


kinetic_templates = KineticTemplatesLibrary()

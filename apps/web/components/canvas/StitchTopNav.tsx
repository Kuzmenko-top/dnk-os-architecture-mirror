// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchTopNav"
// purpose: "Top Navigation Bar for Google Stitch Spatial Canvas in DNK OS with Stitch aesthetics and brand highlights"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Menu, 
  Play, 
  Download, 
  Share2, 
  Check, 
  Sparkles,
  Layers,
  ArrowLeft,
  ShoppingBag
} from 'lucide-react';

interface StitchTopNavProps {
  projectName?: string;
  onPlayPreview?: () => void;
  onExport?: () => void;
  onShare?: () => void;
  onOpenMenu?: () => void;
  onToggleSwarm?: () => void;
  onToggleTimeline?: () => void;
  onToggleShopify?: () => void;
  onToggleBi?: () => void;
  onToggleForest?: () => void;
  activeDrawer?: string | null;
}

export default function StitchTopNav({
  projectName = 'ReBurn Smoker & E-Com Brand Identity',
  onPlayPreview,
  onExport,
  onShare,
  onOpenMenu,
  onToggleSwarm,
  onToggleTimeline,
  onToggleShopify,
  onToggleBi,
  onToggleForest,
  activeDrawer
}: StitchTopNavProps) {
  return (
    <header className="absolute top-4 left-4 right-4 h-12 bg-[#161921]/90 backdrop-blur-xl border border-white/10 rounded-2xl px-4 flex items-center justify-between shadow-2xl z-30 pointer-events-auto">
      {/* Left: Back to Hub + Menu + Project Name */}
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-xs font-medium transition-colors border border-white/5"
          title="Повернутися на Головний Хаб"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Хаб</span>
        </Link>

        <button 
          onClick={onOpenMenu}
          className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <div className="h-4 w-[1px] bg-white/10" />

        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-white text-[10px] font-bold shadow-md shadow-purple-500/20">
            S
          </div>
          <h1 className="text-xs font-semibold text-white tracking-tight font-sans">
            {projectName}
          </h1>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live Sync
          </span>
        </div>
      </div>

      {/* Center: Interactive Cockpit Drawer Launchers */}
      <div className="hidden md:flex items-center gap-1.5 bg-black/30 p-1 rounded-xl border border-white/5">
        <button
          onClick={onToggleSwarm}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeDrawer === 'swarm'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-500/20'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
          }`}
          title="Swarm Multi-Agent Command Center"
        >
          <span>🐝</span>
          <span>Рій Агентів</span>
        </button>

        <button
          onClick={onToggleTimeline}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeDrawer === 'timeline'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/20'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
          }`}
          title="Kinetic Event & Time-Travel Timeline"
        >
          <span>⚡</span>
          <span>Таймлайн</span>
        </button>

        <button
          onClick={onToggleShopify}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeDrawer === 'shopify'
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/20'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
          }`}
          title="Shopify OS 2.0 Liquid Section Live Preview"
        >
          <span>🛍️</span>
          <span>Shopify Liquid</span>
        </button>

        <button
          onClick={onToggleBi}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeDrawer === 'bi'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm shadow-indigo-500/20'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
          }`}
          title="DuckDB Lakehouse BI & NL2SQL Analyst"
        >
          <span>📊</span>
          <span>BI Аналітика</span>
        </button>

        <button
          onClick={onToggleForest}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
            activeDrawer === 'forest'
              ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm shadow-teal-500/20'
              : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
          }`}
          title="Task Forest 5-Level Evolutionary DAG"
        >
          <span>🌲</span>
          <span>Task Forest</span>
        </button>
      </div>

      {/* Right: Actions (Stitch exact layout: Play, Export, Share, S avatar) */}
      <div className="flex items-center gap-2.5">
        {/* Play Preview */}
        <button
          onClick={onPlayPreview}
          className="p-2 rounded-xl text-xs font-semibold bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 transition-all cursor-pointer"
          title="Play Preview"
        >
          <Play className="w-4 h-4 fill-current text-white/90" />
        </button>

        {/* Export - Outlined button */}
        <button
          onClick={onExport}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-transparent hover:bg-white/5 text-slate-200 border border-white/15 transition-all cursor-pointer"
        >
          <Download className="w-3.5 h-3.5 text-slate-300" />
          <span>Export</span>
        </button>

        {/* Share - Outlined button */}
        <button
          onClick={onShare}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-transparent hover:bg-white/5 text-slate-200 border border-white/15 transition-all cursor-pointer"
        >
          <Share2 className="w-3.5 h-3.5 text-slate-300" />
          <span>Share</span>
        </button>

        {/* User Profile Avatar - Solid purple circle with S */}
        <div className="w-8 h-8 rounded-full bg-[#8E44EC] text-white font-bold text-sm flex items-center justify-center shadow-md ml-1 select-none">
          S
        </div>
      </div>
    </header>
  );
}

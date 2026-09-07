// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_HubTopBar"
// purpose: "Top navigation bar and announcement header for DNK OS Main Hub based on CapCut /my-edit"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  Search, 
  Bell, 
  HelpCircle, 
  Sun, 
  Moon, 
  Sliders, 
  ArrowUpRight,
  ShieldCheck,
  ChevronDown,
  X
} from 'lucide-react';
import { useOpenDesignTheme } from '../../context/OpenDesignThemeContext';

interface HubTopBarProps {
  onOpenCommandBar?: () => void;
  onOpenCustomizer?: () => void;
}

export default function HubTopBar({ onOpenCommandBar, onOpenCustomizer }: HubTopBarProps) {
  const { currentPreset } = useOpenDesignTheme();
  const [showBanner, setShowBanner] = useState(true);

  return (
    <header className="flex flex-col border-b border-zinc-800/80 bg-[#0e1017] dark:bg-[#0e1017] shrink-0 select-none z-20 font-sans">
      
      {/* 1. Top Announcement Banner (Excalidraw Reference) */}
      {showBanner && (
        <div className="bg-[#141824] border-b border-zinc-800/60 px-4 py-1.5 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2 mx-auto">
            <span className="text-amber-400">🎁</span>
            <span>
              Credit discount on <strong className="text-white">Seedance 2.0 Fast and Mini</strong> for DNK OS Pro and Ultra users.{' '}
              <Link href="/os" className="text-[#00dc82] hover:underline font-semibold ml-1">
                Get it in Video Studio ›
              </Link>
            </span>
          </div>
          <button 
            onClick={() => setShowBanner(false)}
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 2. Main Top Bar Actions */}
      <div className="h-14 px-6 flex items-center justify-between">
        
        {/* Left: Search / Command Trigger */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenCommandBar}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-zinc-900/90 border border-zinc-800 hover:border-zinc-700 text-xs text-slate-400 transition-all w-64 justify-between group shadow-inner"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300" />
              <span>Search templates, files, agents...</span>
            </div>
            <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] font-mono text-slate-400">⌘K</kbd>
          </button>
        </div>

        {/* Right: Credits, Theme, Profile */}
        <div className="flex items-center gap-3">
          
          {/* Credits Counter Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium">
            <span className="text-[#00dc82] font-bold">✦ 1,311</span>
            <button className="text-[#00dc82] font-semibold hover:underline">
              Renew
            </button>
          </div>

          {/* Free Credits */}
          <button className="text-xs font-medium text-slate-400 hover:text-white px-2 py-1 transition-colors">
            🎁 Free credits
          </button>

          {/* Theme Presets Quick Toggle */}
          <button
            onClick={onOpenCustomizer}
            className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-slate-400 hover:text-[#00dc82] hover:border-[#00dc82]/40 transition-all text-xs flex items-center gap-1.5 font-medium"
            title="Design System & Theme Customizer"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Theme</span>
          </button>

          {/* User Profile Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-black font-bold text-xs shadow-md ring-2 ring-[#00dc82]/30">
            M
          </div>

        </div>

      </div>

    </header>
  );
}

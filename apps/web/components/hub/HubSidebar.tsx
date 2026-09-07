// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_HubSidebar"
// purpose: "Left navigation sidebar for DNK OS Main Hub based on CapCut /my-edit layout with DNK Emerald Green branding"
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
  Home, 
  Paintbrush, 
  Film, 
  Mic2, 
  LayoutGrid, 
  LayoutTemplate, 
  Share2, 
  Clock, 
  UserPlus, 
  Plus, 
  Sparkles,
  HelpCircle,
  ChevronDown,
  Layers,
  ShoppingBag,
  Network
} from 'lucide-react';

interface HubSidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenAllTools: () => void;
}

export default function HubSidebar({ activeTab, onSelectTab, onOpenAllTools }: HubSidebarProps) {
  const [selectedSpace, setSelectedSpace] = useState('ReBurn Store & E-Com');
  const [isSpaceMenuOpen, setIsSpaceMenuOpen] = useState(false);

  const spaces = [
    'ReBurn Store & E-Com',
    'Timoshka space (Default)',
    'DNK Agentic Studio'
  ];

  return (
    <aside className="w-64 bg-[#0e1017] dark:bg-[#0e1017] border-r border-zinc-800/80 text-slate-300 flex flex-col h-full select-none shrink-0 z-30 font-sans">
      
      {/* Brand Header */}
      <div className="p-4 flex items-center justify-between border-b border-zinc-800/60">
        <Link href="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
          <div className="w-7 h-7 rounded-lg bg-[#00dc82] flex items-center justify-center text-black font-black text-xs shadow-md shadow-emerald-500/20">
            🧬
          </div>
          <span className="font-extrabold text-base tracking-tight text-white font-sans">
            DNK <span className="text-[#00dc82]">OS</span>
          </span>
        </Link>
      </div>

      {/* Primary Action Button: + Create new (DNK Green) */}
      <div className="p-3.5 pb-2">
        <Link 
          href="/os"
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-[#00dc82] hover:bg-[#00c574] text-black font-bold text-xs tracking-wide shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99]"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Create new</span>
        </Link>
      </div>

      {/* Scrollable Navigation List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-5 text-xs">
        
        {/* Home */}
        <div>
          <button
            onClick={() => onSelectTab('home')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl font-medium transition-all ${
              activeTab === 'home'
                ? 'bg-zinc-800/90 text-white font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40'
            }`}
          >
            <Home className={`w-4 h-4 ${activeTab === 'home' ? 'text-[#00dc82]' : 'text-slate-400'}`} />
            <span>Home</span>
          </button>
        </div>

        {/* Section: Create with AI */}
        <div>
          <div className="px-3 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Create with AI
          </div>
          <div className="space-y-0.5">
            <Link
              href="/os"
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all"
            >
              <Paintbrush className="w-4 h-4 text-[#00dc82]" />
              <span>Design Studio</span>
            </Link>
            
            <Link
              href="/canvas/video-studio"
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all"
            >
              <Film className="w-4 h-4 text-emerald-400" />
              <span>Video Studio</span>
            </Link>

            <button
              onClick={() => onSelectTab('voice')}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all text-left"
            >
              <Mic2 className="w-4 h-4 text-emerald-400" />
              <span>Voice Studio</span>
            </button>

            <button
              onClick={onOpenAllTools}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all text-left"
            >
              <LayoutGrid className="w-4 h-4 text-[#00dc82]" />
              <span>All tools</span>
            </button>
          </div>
        </div>

        {/* Section: Templates & projects */}
        <div>
          <div className="px-3 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Templates & projects
          </div>
          <div className="space-y-0.5">
            <Link
              href="/tasks"
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all"
            >
              <Network className="w-4 h-4 text-cyan-400" />
              <span>Node Tasks & DAG</span>
            </Link>

            <button
              onClick={() => onSelectTab('templates')}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-left transition-all ${
                activeTab === 'templates' ? 'bg-zinc-800/90 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40'
              }`}
            >
              <LayoutTemplate className="w-4 h-4 text-slate-400" />
              <span>Templates</span>
            </button>

            <button
              onClick={() => onSelectTab('share')}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all text-left"
            >
              <Share2 className="w-4 h-4 text-slate-400" />
              <span>Share and schedule</span>
            </button>

            <button
              onClick={() => onSelectTab('recent')}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 transition-all text-left"
            >
              <Clock className="w-4 h-4 text-slate-400" />
              <span>Recent projects</span>
            </button>
          </div>
        </div>

        {/* Section: Spaces */}
        <div>
          <div className="px-3 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Spaces
          </div>
          
          <div className="space-y-1.5">
            {/* Active Space Item */}
            <div className="p-2.5 rounded-xl bg-zinc-900/90 border border-zinc-800/80">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-6 h-6 rounded-lg bg-[#00dc82]/20 border border-[#00dc82]/40 flex items-center justify-center text-[#00dc82] font-bold text-[10px]">
                  R
                </div>
                <div className="flex-1 truncate">
                  <div className="text-xs font-semibold text-slate-200 truncate">ReBurn Space</div>
                  <div className="text-[10px] text-slate-500">Shopify & Media</div>
                </div>
              </div>
              
              <button className="w-full flex items-center justify-center gap-1.5 py-1 px-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-slate-300 text-[11px] font-medium transition-colors">
                <UserPlus className="w-3 h-3 text-slate-400" />
                <span>Invite members</span>
              </button>
            </div>

            {/* Create new space button */}
            <button className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-zinc-800/40 text-left transition-all">
              <Plus className="w-4 h-4 text-slate-500" />
              <span>Create new space</span>
            </button>
          </div>
        </div>

      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-zinc-800/60 flex items-center justify-between text-xs text-slate-500">
        <button className="flex items-center gap-2 hover:text-slate-300 transition-colors">
          <Sparkles className="w-4 h-4 text-[#00dc82]" />
          <span>What&apos;s new</span>
        </button>
      </div>

    </aside>
  );
}

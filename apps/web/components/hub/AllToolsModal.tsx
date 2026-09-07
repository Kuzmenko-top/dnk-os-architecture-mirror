// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_hub_AllToolsModal"
// purpose: "All Tools Mega Popover & Creation Matrix matching Excalidraw 'Что можно створювати в данном додатку?'"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  X, 
  Film, 
  Image as ImageIcon, 
  Wand2, 
  Smartphone, 
  Monitor, 
  Square, 
  Instagram, 
  Facebook, 
  Sparkles, 
  Mic2, 
  Scissors, 
  MessageSquare, 
  ShoppingBag,
  ArrowUpRight
} from 'lucide-react';

interface AllToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AllToolsModal({ isOpen, onClose }: AllToolsModalProps) {
  const [activeCategory, setActiveCategory] = useState<'all' | 'video' | 'image' | 'audio' | 'business'>('all');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="bg-[#12141c] border border-zinc-800 rounded-3xl w-full max-w-4xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col font-sans text-slate-100">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#00dc82]/10 border border-[#00dc82]/30 flex items-center justify-center text-[#00dc82] font-bold text-sm">
              ✨
            </div>
            <div>
              <h3 className="text-base font-extrabold text-white">All tools & Creation Matrix</h3>
              <p className="text-xs text-slate-400">Everything you can create in DNK OS</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Category tabs */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-zinc-900 border border-zinc-800 text-xs">
              <button 
                onClick={() => setActiveCategory('all')} 
                className={`px-3 py-1 rounded-lg font-medium transition-all ${activeCategory === 'all' ? 'bg-[#00dc82] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                All
              </button>
              <button 
                onClick={() => setActiveCategory('video')} 
                className={`px-3 py-1 rounded-lg font-medium transition-all ${activeCategory === 'video' ? 'bg-[#00dc82] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                For videos
              </button>
              <button 
                onClick={() => setActiveCategory('image')} 
                className={`px-3 py-1 rounded-lg font-medium transition-all ${activeCategory === 'image' ? 'bg-[#00dc82] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                For images
              </button>
              <button 
                onClick={() => setActiveCategory('audio')} 
                className={`px-3 py-1 rounded-lg font-medium transition-all ${activeCategory === 'audio' ? 'bg-[#00dc82] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                For audio
              </button>
              <button 
                onClick={() => setActiveCategory('business')} 
                className={`px-3 py-1 rounded-lg font-medium transition-all ${activeCategory === 'business' ? 'bg-[#00dc82] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                For business
              </button>
            </div>

            <button 
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body: 3 Columns matching Excalidraw */}
        <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Column 1: Video */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <Film className="w-4 h-4 text-[#00dc82]" />
              <span>Video</span>
            </div>

            <div className="space-y-2">
              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <Square className="w-3.5 h-3.5" />
                    <span>Blank canvas</span>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-[#00dc82]" />
                </div>
                <p className="text-[11px] text-slate-400">Custom resolution video workspace</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <Monitor className="w-3.5 h-3.5" />
                    <span>16:9 Landscape</span>
                  </div>
                  <span className="text-[10px] text-slate-400">YouTube, TV</span>
                </div>
                <p className="text-[11px] text-slate-400">1920x1080 Full HD Video format</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <Smartphone className="w-3.5 h-3.5 text-[#00dc82]" />
                    <span>9:16 Vertical</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00dc82]/10 text-[#00dc82] font-bold">HOT</span>
                </div>
                <p className="text-[11px] text-slate-400">TikTok, Instagram Reels, Shorts</p>
              </Link>
            </div>
          </div>

          {/* Column 2: Image */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <ImageIcon className="w-4 h-4 text-[#00dc82]" />
              <span>Image & Design</span>
            </div>

            <div className="space-y-2">
              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="text-xs font-bold text-white group-hover:text-[#00dc82]">Custom size</div>
                <p className="text-[11px] text-slate-400">Input exact pixel dimensions</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82]">Instagram post</div>
                  <span className="text-[10px] text-slate-400">1080x1080</span>
                </div>
                <p className="text-[11px] text-slate-400">Square product & lifestyle graphics</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82]">Instagram story</div>
                  <span className="text-[10px] text-slate-400">1080x1920</span>
                </div>
                <p className="text-[11px] text-slate-400">Full-screen mobile product teasers</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82]">Shopify Product Card</div>
                  <span className="text-[10px] text-[#00dc82] font-semibold">Liquid AST</span>
                </div>
                <p className="text-[11px] text-slate-400">Interactive 3D theme component</p>
              </Link>
            </div>
          </div>

          {/* Column 3: Magic Tools */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <Wand2 className="w-4 h-4 text-[#00dc82]" />
              <span>Magic tools</span>
            </div>

            <div className="space-y-2">
              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5 text-[#00dc82]" />
                    <span>AI captions</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-[#00dc82] font-bold">New</span>
                </div>
                <p className="text-[11px] text-slate-400">Auto subtitle generator with stylish animations</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <Mic2 className="w-3.5 h-3.5 text-[#00dc82]" />
                    <span>Text to speech</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-[#00dc82] font-bold">New</span>
                </div>
                <p className="text-[11px] text-slate-400">100+ natural sounding AI voices</p>
              </Link>

              <Link 
                href="/os" 
                onClick={onClose}
                className="block p-3 rounded-2xl bg-zinc-900/90 border border-zinc-800 hover:border-[#00dc82]/50 hover:bg-zinc-800/80 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-bold text-white group-hover:text-[#00dc82] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[#00dc82]" />
                    <span>TaskDNA Swarm Orchestrator</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-[#00dc82] font-bold">14 Agents</span>
                </div>
                <p className="text-[11px] text-slate-400">Automate research, video, liquid theme & copy</p>
              </Link>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

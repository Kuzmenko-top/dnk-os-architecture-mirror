// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_LiveWebPreviewNode"
// purpose: "Interactive Live Web Preview Node for Google Stitch Canvas in DNK OS"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Laptop, 
  ExternalLink, 
  RefreshCw, 
  Sparkles, 
  ArrowUpRight,
  ShieldCheck,
  Cpu,
  Layers,
  Zap,
  Activity,
  Dna,
  Bot
} from 'lucide-react';

export default function LiveWebPreviewNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  const [activeTab, setActiveTab] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div 
      className={`group relative rounded-2xl transition-all duration-300 ${
        selected ? 'ring-2 ring-purple-500 shadow-2xl shadow-purple-500/20' : 'shadow-xl'
      }`}
      style={{ width: 680, minHeight: 880 }}
    >
      {/* Node Connection Handles */}
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-3 h-3 bg-purple-500 border-2 border-white dark:border-slate-900 rounded-full" 
      />
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-3 h-3 bg-purple-500 border-2 border-white dark:border-slate-900 rounded-full" 
      />
      <Handle 
        type="target" 
        position={Position.Left} 
        className="w-3 h-3 bg-purple-500 border-2 border-white dark:border-slate-900 rounded-full" 
      />
      <Handle 
        type="source" 
        position={Position.Right} 
        className="w-3 h-3 bg-purple-500 border-2 border-white dark:border-slate-900 rounded-full" 
      />

      {/* Top Browser Chrome Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900 border-t border-x border-slate-800 rounded-t-2xl text-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 mr-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <Laptop className="w-3.5 h-3.5 text-purple-400" />
          <span className="text-slate-300 font-mono tracking-tight font-semibold">
            {String(nodeData.title || 'DNK OS Stripe-Inspired Desktop Landing')}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-800/80 rounded-md p-0.5 text-[10px] text-slate-400">
            <button 
              onClick={() => setActiveTab('desktop')}
              className={`px-2 py-0.5 rounded ${activeTab === 'desktop' ? 'bg-purple-600 text-white font-semibold' : 'hover:text-slate-200'}`}
            >
              Desktop
            </button>
            <button 
              onClick={() => setActiveTab('tablet')}
              className={`px-2 py-0.5 rounded ${activeTab === 'tablet' ? 'bg-purple-600 text-white font-semibold' : 'hover:text-slate-200'}`}
            >
              Tablet
            </button>
            <button 
              onClick={() => setActiveTab('mobile')}
              className={`px-2 py-0.5 rounded ${activeTab === 'mobile' ? 'bg-purple-600 text-white font-semibold' : 'hover:text-slate-200'}`}
            >
              Mobile
            </button>
          </div>
          <button className="text-slate-400 hover:text-white transition-colors" title="Reload iframe">
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Main Preview Container (Obsidian Aurora Theme) */}
      <div className="bg-[#030712] text-slate-100 rounded-b-2xl border border-slate-800/80 overflow-hidden font-sans relative">
        {/* Ambient Aurora Glow Background */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-gradient-to-tr from-purple-900/30 via-indigo-900/20 to-emerald-900/20 blur-[100px] pointer-events-none" />

        {/* Mock Landing Nav */}
        <header className="flex items-center justify-between px-6 py-3.5 border-b border-slate-800/50 backdrop-blur-md bg-slate-950/40 relative z-10">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
              <Dna className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-black text-sm tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-purple-300">
              DNK OS
            </span>
          </div>

          <nav className="flex items-center gap-4 text-[11px] text-slate-400 font-medium">
            <span className="hover:text-purple-400 cursor-pointer transition-colors">Resources</span>
            <span className="hover:text-purple-400 cursor-pointer transition-colors">Integrity</span>
            <span className="hover:text-purple-400 cursor-pointer transition-colors">Governance</span>
            <span className="hover:text-purple-400 cursor-pointer transition-colors">Methodology</span>
          </nav>

          <button className="px-3 py-1 text-[11px] rounded-full font-medium bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600 hover:text-white transition-all shadow-sm">
            Launch OS
          </button>
        </header>

        {/* Hero Section */}
        <section className="px-8 pt-10 pb-8 text-center relative z-10">
          {/* 3D Glowing Brand Typography Badge */}
          <div className="inline-flex items-center justify-center mb-6">
            <div className="px-6 py-3 rounded-2xl bg-gradient-to-b from-purple-900/40 via-slate-900/80 to-slate-950/90 border border-purple-500/40 shadow-2xl shadow-purple-500/30 backdrop-blur-xl">
              <div className="flex items-center gap-3">
                <Dna className="w-7 h-7 text-purple-400 animate-pulse" />
                <span className="text-3xl font-black tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-purple-300 via-pink-400 to-amber-300 drop-shadow-[0_0_25px_rgba(168,85,247,0.5)]">
                  DNKOS
                </span>
              </div>
            </div>
          </div>

          <h1 className="text-2xl font-black text-white tracking-tight sm:text-3xl mb-3">
            The World&apos;s First Agentic OS
          </h1>

          <p className="max-w-md mx-auto text-xs text-slate-400 leading-relaxed mb-6">
            Unified Multi-Agent Spatial Orchestration, Autonomous E-Commerce Workflows, 
            and Zero-Waste Execution Protocol in a single, next-gen digital canvas.
          </p>

          <div className="flex items-center justify-center gap-3 mb-10">
            <button className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 shadow-lg shadow-purple-600/30 transition-all">
              Initialize Core
            </button>
            <button className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-900/80 border border-slate-700/60 hover:bg-slate-800 hover:text-white transition-all">
              Agent Architecture Guide
            </button>
          </div>

          {/* Section: High-Performance Systems */}
          <div className="text-left mt-8 pt-6 border-t border-slate-800/60">
            <div className="text-center mb-6">
              <h2 className="text-sm font-bold text-white tracking-wide">High-Performance Systems</h2>
              <p className="text-[10px] text-slate-400">Precision bio-digital architectures built for agentic intelligence.</p>
            </div>

            {/* 3 Equipment Cards with Hover Microinteractions */}
            <div className="grid grid-cols-3 gap-3">
              {/* Card 1 */}
              <div className="group/card p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-purple-500/50 hover:bg-slate-900/90 transition-all duration-200">
                <div className="w-full h-24 rounded-lg bg-gradient-to-br from-purple-950/80 to-slate-950 flex items-center justify-center mb-2.5 overflow-hidden border border-purple-900/30 relative">
                  <div className="absolute inset-0 bg-purple-500/10 opacity-0 group-hover/card:opacity-100 transition-opacity" />
                  <Cpu className="w-8 h-8 text-purple-400 group-hover/card:scale-110 transition-transform duration-300" />
                </div>
                <h3 className="text-xs font-bold text-slate-200 group-hover/card:text-purple-300 transition-colors">
                  Synthetix DNA Sequencer
                </h3>
                <p className="text-[9px] text-slate-400 mt-1 leading-snug">
                  Ultra-rapid genomic sequence alignment for Cloud BioTech computing.
                </p>
                <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[8px] text-slate-500 font-mono">
                  <span>v3.4.0-PRO</span>
                  <span className="text-emerald-400">● Operational</span>
                </div>
              </div>

              {/* Card 2 */}
              <div className="group/card p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/50 hover:bg-slate-900/90 transition-all duration-200">
                <div className="w-full h-24 rounded-lg bg-gradient-to-br from-indigo-950/80 to-slate-950 flex items-center justify-center mb-2.5 overflow-hidden border border-indigo-900/30 relative">
                  <div className="absolute inset-0 bg-indigo-500/10 opacity-0 group-hover/card:opacity-100 transition-opacity" />
                  <Activity className="w-8 h-8 text-indigo-400 group-hover/card:scale-110 transition-transform duration-300" />
                </div>
                <h3 className="text-xs font-bold text-slate-200 group-hover/card:text-indigo-300 transition-colors">
                  Nano-Bio Reactor
                </h3>
                <p className="text-[9px] text-slate-400 mt-1 leading-snug">
                  Automated continuous peptide synthesis and screening unit.
                </p>
                <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[8px] text-slate-500 font-mono">
                  <span>v1.8.2-AIR</span>
                  <span className="text-emerald-400">● Active Stream</span>
                </div>
              </div>

              {/* Card 3 */}
              <div className="group/card p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-pink-500/50 hover:bg-slate-900/90 transition-all duration-200">
                <div className="w-full h-24 rounded-lg bg-gradient-to-br from-pink-950/80 to-slate-950 flex items-center justify-center mb-2.5 overflow-hidden border border-pink-900/30 relative">
                  <div className="absolute inset-0 bg-pink-500/10 opacity-0 group-hover/card:opacity-100 transition-opacity" />
                  <Zap className="w-8 h-8 text-pink-400 group-hover/card:scale-110 transition-transform duration-300" />
                </div>
                <h3 className="text-xs font-bold text-slate-200 group-hover/card:text-pink-300 transition-colors">
                  Neural Link Pro
                </h3>
                <p className="text-[9px] text-slate-400 mt-1 leading-snug">
                  Implantable computer interface for next-level A2A telemetry.
                </p>
                <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[8px] text-slate-500 font-mono">
                  <span>v2.0.1-LINK</span>
                  <span className="text-emerald-400">● 100% Sync</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Minimal Footer */}
        <footer className="px-6 py-4 bg-slate-950/80 border-t border-slate-900 text-[10px] text-slate-500 flex items-center justify-between">
          <span>© 2026 DNK OS. Autonomous Swarm Verified.</span>
          <div className="flex items-center gap-3">
            <span className="hover:text-slate-300 cursor-pointer">Terms</span>
            <span className="hover:text-slate-300 cursor-pointer">Security</span>
            <span className="hover:text-slate-300 cursor-pointer">API</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

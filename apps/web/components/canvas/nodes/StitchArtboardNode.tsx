// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_StitchArtboardNode"
// purpose: "Pixel-perfect Google Stitch Artboard Frame Node supporting Design System, Mobile Mockups, and Desktop Views"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Sparkles, 
  Terminal, 
  Smartphone, 
  Monitor, 
  CheckCircle2, 
  Activity, 
  ShieldCheck, 
  Zap, 
  Search, 
  Image as ImageIcon, 
  Film, 
  Layers, 
  Sliders, 
  Cpu,
  BarChart3
} from 'lucide-react';

export default function StitchArtboardNode({ id, data, selected }: NodeProps) {
  const artboardType = (data?.artboardType as string) || 'design-system';
  const title = (data?.title as string) || 'Artboard';
  const subtitle = (data?.subtitle as string) || '';

  const [toggles, setToggles] = useState({
    quiz: true,
    novaPoshta: true,
    stickyATC: true,
    freeShip: true,
  });

  return (
    <div className="relative group font-sans">
      {/* Artboard Title Tag Above Frame (Google Stitch Style) */}
      <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-400 px-1">
        <div className="flex items-center gap-1.5 truncate max-w-[400px]">
          <span className="font-semibold text-slate-200">{title}</span>
          {subtitle && <span className="text-slate-500 text-[11px]">· {subtitle}</span>}
        </div>
        <div className="flex items-center gap-1 text-[10px] text-slate-500 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Synced</span>
        </div>
      </div>

      {/* Subtle React Flow Connectors (No giant white bars) */}
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-2.5 h-2.5 bg-slate-400/40 border border-[#16181f] rounded-full opacity-0 group-hover:opacity-100 transition-opacity" 
      />
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-2.5 h-2.5 bg-slate-400/40 border border-[#16181f] rounded-full opacity-0 group-hover:opacity-100 transition-opacity" 
      />
      <Handle 
        type="target" 
        position={Position.Left} 
        id="left" 
        className="w-2.5 h-2.5 bg-slate-400/40 border border-[#16181f] rounded-full opacity-0 group-hover:opacity-100 transition-opacity" 
      />
      <Handle 
        type="source" 
        position={Position.Right} 
        id="right" 
        className="w-2.5 h-2.5 bg-slate-400/40 border border-[#16181f] rounded-full opacity-0 group-hover:opacity-100 transition-opacity" 
      />

      {/* Artboard Frame Body */}
      <div className={`transition-all duration-200 rounded-2xl shadow-2xl overflow-hidden ${
        selected ? 'ring-2 ring-emerald-400/80 shadow-[0_0_35px_rgba(51,238,117,0.2)]' : 'ring-1 ring-white/10'
      }`}>
        {/* Render By Artboard Type */}

        {/* 1. Design System Kit: Obsidian Flow */}
        {artboardType === 'design-system' && (
          <div className="w-[580px] bg-[#121317] p-6 text-slate-200 flex flex-col gap-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#33EE75]" />
                <h3 className="font-bold text-sm text-white tracking-wide">Obsidian Flow Design System</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#33EE75]/10 text-[#33EE75] border border-[#33EE75]/20">
                DNK-UI v2.4
              </span>
            </div>

            <div className="grid grid-cols-3 gap-5">
              {/* Palette */}
              <div className="flex flex-col gap-2.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Palette</span>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#33EE75] text-black font-bold text-xs shadow-md">
                    <span>Primary</span>
                    <span className="font-mono text-[10px]">#33EE75</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#1E293B] text-slate-200 text-xs border border-white/5">
                    <span>Secondary</span>
                    <span className="font-mono text-[10px] opacity-70">#1E293B</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#0F172A] text-slate-300 text-xs border border-white/5">
                    <span>Tertiary</span>
                    <span className="font-mono text-[10px] opacity-70">#0F172A</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-xl bg-[#05070A] text-slate-400 text-xs border border-white/5">
                    <span>Neutral</span>
                    <span className="font-mono text-[10px] opacity-60">#05070A</span>
                  </div>
                </div>
              </div>

              {/* Typography */}
              <div className="flex flex-col gap-2.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Typography</span>
                <div className="flex flex-col gap-3 p-3 rounded-xl bg-black/40 border border-white/5">
                  <div>
                    <span className="text-2xl font-black text-white">Aa</span>
                    <p className="text-[10px] text-slate-400 font-mono">Headline 32px Bold</p>
                  </div>
                  <div>
                    <span className="text-lg font-semibold text-slate-200">Aa</span>
                    <p className="text-[10px] text-slate-400 font-mono">Subhead 20px Medium</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-300">Aa</span>
                    <p className="text-[10px] text-slate-400 font-mono">Body 14px Regular</p>
                  </div>
                </div>
              </div>

              {/* Components */}
              <div className="flex flex-col gap-2.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Components</span>
                <div className="flex flex-col gap-2.5">
                  <button className="w-full py-2 px-3 rounded-full bg-[#33EE75] hover:bg-[#28d765] text-black font-bold text-xs shadow-lg shadow-[#33EE75]/20 transition-all">
                    Filled Button
                  </button>
                  <button className="w-full py-2 px-3 rounded-full border border-[#33EE75] text-[#33EE75] hover:bg-[#33EE75]/10 font-semibold text-xs transition-all">
                    Outlined Button
                  </button>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-400">
                    <Search className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-[11px]">Search input...</span>
                  </div>
                  <div className="flex items-center justify-between px-1 pt-1">
                    <span className="text-[11px] text-slate-300">Active Toggle</span>
                    <div className="w-8 h-4 rounded-full bg-[#33EE75] p-0.5 flex justify-end">
                      <div className="w-3 h-3 rounded-full bg-black shadow-sm" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 2. Mobile Mockup 1: Studio Intelligence */}
        {artboardType === 'mobile-home' && (
          <div className="w-[340px] h-[640px] bg-[#0c0d11] p-4 text-slate-200 flex flex-col justify-between overflow-hidden relative">
            {/* Dynamic Island / Notch */}
            <div className="w-24 h-4 rounded-full bg-black mx-auto mb-2 border border-white/5 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-[#33EE75]/80 animate-ping" />
            </div>

            <div className="flex flex-col gap-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#33EE75]" />
                  <span className="font-bold text-xs text-white">Studio Intelligence</span>
                </div>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                  Live
                </span>
              </div>

              {/* System Integrity */}
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-medium">System Integrity</span>
                  <span className="font-mono text-[#33EE75] font-bold">99.98%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="w-[99%] h-full bg-[#33EE75] rounded-full" />
                </div>
              </div>

              {/* Input Buffer */}
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-medium">Input Buffer (Tokens)</span>
                  <span className="font-mono text-slate-300">14.2k / 20k</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="w-[71%] h-full bg-indigo-500 rounded-full" />
                </div>
              </div>

              {/* Molecular Catalog Card */}
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-950/40 to-slate-900 border border-purple-500/30 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Molecular Catalog Upgrade</span>
                  <Zap className="w-3.5 h-3.5 text-[#33EE75]" />
                </div>
                <p className="text-[11px] text-slate-300 leading-relaxed">
                  Real-time Shopify OS 2.0 component synthesis & liquid generation ready.
                </p>
              </div>

              {/* Media Cards Grid */}
              <div className="grid grid-cols-2 gap-2.5">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col items-center gap-1.5 text-center">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-[#33EE75]">
                    <ImageIcon className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-semibold text-white">Image</span>
                  <span className="text-[10px] text-slate-400 font-mono">1024x1024 UHD</span>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col items-center gap-1.5 text-center">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                    <Film className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-semibold text-white">Video</span>
                  <span className="text-[10px] text-slate-400 font-mono">9:16 Kinetic</span>
                </div>
              </div>
            </div>

            {/* Bottom Nav Simulation */}
            <div className="pt-2 border-t border-white/10 flex items-center justify-around text-slate-500 text-xs">
              <span className="text-[#33EE75] font-semibold">Home</span>
              <span>Catalog</span>
              <span>Agents</span>
              <span>Settings</span>
            </div>
          </div>
        )}

        {/* 3. Mobile Mockup 2: Executive Monitor */}
        {artboardType === 'mobile-executive' && (
          <div className="w-[340px] h-[640px] bg-[#0c0d11] p-4 text-slate-200 flex flex-col justify-between overflow-hidden relative font-sans">
            {/* Dynamic Island / Notch */}
            <div className="w-24 h-4 rounded-full bg-black mx-auto mb-2 border border-white/5" />

            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between pb-2 border-b border-white/10">
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-[#33EE75]" />
                  <span className="font-bold text-xs text-white">Executive Stream</span>
                </div>
                <span className="font-mono text-[10px] text-slate-400">node-01:ready</span>
              </div>

              {/* Terminal Snippet */}
              <div className="p-2.5 rounded-xl bg-black/70 border border-white/5 font-mono text-[10px] text-[#33EE75] leading-relaxed">
                <div>&gt; SSH connected: dnk-gateway</div>
                <div className="text-slate-400">&gt; FastAPI health: 200 OK (12ms)</div>
                <div className="text-slate-400">&gt; Liquid AST: verified 4 blocks</div>
                <div>&gt; Ready for prompt dispatch_</div>
              </div>

              {/* Backend Health Cards */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1">
                  <span className="text-[10px] text-slate-400 uppercase font-mono">FastAPI</span>
                  <span className="text-xs font-bold text-[#33EE75]">99.99% Up</span>
                  <span className="text-[9px] text-slate-500">Port 8000</span>
                </div>
                <div className="p-2.5 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1">
                  <span className="text-[10px] text-slate-400 uppercase font-mono">Next.js WB</span>
                  <span className="text-xs font-bold text-indigo-400">Port 3000</span>
                  <span className="text-[9px] text-slate-500">SSR Live</span>
                </div>
              </div>

              {/* CRM Toggles */}
              <div className="flex flex-col gap-1.5 p-3 rounded-xl bg-white/5 border border-white/10 text-xs">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Ecom Modules
                </span>
                <div className="flex items-center justify-between py-1 border-b border-white/5">
                  <span className="text-slate-300">Quiz Engine</span>
                  <div className="w-7 h-3.5 rounded-full bg-[#33EE75] p-0.5 flex justify-end">
                    <div className="w-2.5 h-2.5 rounded-full bg-black shadow" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-white/5">
                  <span className="text-slate-300">Nova Poshta API</span>
                  <div className="w-7 h-3.5 rounded-full bg-[#33EE75] p-0.5 flex justify-end">
                    <div className="w-2.5 h-2.5 rounded-full bg-black shadow" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-white/5">
                  <span className="text-slate-300">Sticky ATC</span>
                  <div className="w-7 h-3.5 rounded-full bg-[#33EE75] p-0.5 flex justify-end">
                    <div className="w-2.5 h-2.5 rounded-full bg-black shadow" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-300">Free Ship Tier</span>
                  <div className="w-7 h-3.5 rounded-full bg-[#33EE75] p-0.5 flex justify-end">
                    <div className="w-2.5 h-2.5 rounded-full bg-black shadow" />
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Nav Simulation */}
            <div className="pt-2 border-t border-white/10 flex items-center justify-around text-slate-500 text-xs">
              <span className="text-[#33EE75] font-semibold">Create</span>
              <span>Projects</span>
              <span>Templates</span>
              <span>Settings</span>
            </div>
          </div>
        )}

        {/* 4. Desktop View: Executive Mentor Report */}
        {artboardType === 'desktop-report' && (
          <div className="w-[820px] h-[520px] bg-[#0e1014] p-5 text-slate-200 flex gap-4 overflow-hidden font-sans">
            {/* Sidebar */}
            <div className="w-48 bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col justify-between shrink-0">
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2.5 pb-3 border-b border-white/10">
                  <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow">
                    CA
                  </div>
                  <div>
                    <h4 className="font-bold text-xs text-white">Creative Agent</h4>
                    <p className="text-[10px] text-slate-400">Mentor Mode</p>
                  </div>
                </div>

                <div className="flex flex-col gap-1 text-xs">
                  <span className="px-2.5 py-1.5 rounded-lg bg-[#33EE75]/15 text-[#33EE75] font-semibold">
                    Personal Space
                  </span>
                  <span className="px-2.5 py-1.5 rounded-lg hover:bg-white/5 text-slate-400">Team Projects</span>
                  <span className="px-2.5 py-1.5 rounded-lg hover:bg-white/5 text-slate-400">Archived</span>
                  <span className="px-2.5 py-1.5 rounded-lg hover:bg-white/5 text-slate-400">Documentation</span>
                  <span className="px-2.5 py-1.5 rounded-lg hover:bg-white/5 text-slate-400">Support</span>
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-[10px] text-slate-400 font-mono">
                DNK Core v4.3.0
              </div>
            </div>

            {/* Main Window */}
            <div className="flex-1 flex flex-col gap-3.5 overflow-hidden">
              {/* Header with dots */}
              <div className="flex items-center justify-between pb-2 border-b border-white/10">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                  <span className="text-xs font-bold text-white ml-2">Executive Mentor Report</span>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono">
                  <span className="text-slate-400">Latency:</span>
                  <span className="text-[#33EE75] font-bold">14ms</span>
                  <span className="text-slate-500">|</span>
                  <span className="text-slate-400">Health:</span>
                  <span className="text-[#33EE75] font-bold">99.98%</span>
                </div>
              </div>

              {/* Monospace SSH & Execution Terminal */}
              <div className="p-3 rounded-xl bg-black/80 border border-white/5 font-mono text-xs text-[#33EE75] leading-relaxed">
                <div>&gt; Initializing DNK OS Swarm Protocol... OK</div>
                <div className="text-slate-400">&gt; Checking relative path enforcement... 100% compliant</div>
                <div>&gt; liquid_ast_check: 2 components ready for compilation</div>
              </div>

              {/* Liquid Component Progress Bars */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300">_image.liquid</span>
                    <span className="text-[#33EE75] font-bold font-mono">100%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="w-full h-full bg-[#33EE75] rounded-full" />
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300">_accordion-row.liquid</span>
                    <span className="text-indigo-400 font-bold font-mono">85%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                    <div className="w-[85%] h-full bg-indigo-500 rounded-full" />
                  </div>
                </div>
              </div>

              {/* Tech Stack Evolution Matrix */}
              <div className="flex-1 rounded-xl bg-white/5 border border-white/10 p-3 flex flex-col gap-2 overflow-hidden">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Tech Stack Evolution Matrix
                </span>
                <div className="grid grid-cols-4 gap-2 text-xs text-slate-300 pt-1 font-mono">
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-slate-400 text-[10px]">Framework</div>
                    <div className="font-bold text-white">Next.js 14</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-slate-400 text-[10px]">Backend</div>
                    <div className="font-bold text-[#33EE75]">FastAPI 0.111</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-slate-400 text-[10px]">Canvas</div>
                    <div className="font-bold text-indigo-400">XYFlow / ReactFlow</div>
                  </div>
                  <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                    <div className="text-slate-400 text-[10px]">Database</div>
                    <div className="font-bold text-white">PostgreSQL 16</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 5. Thumbnail 1: Metric Dashboard Preview */}
        {artboardType === 'thumb-metrics' && (
          <div className="w-[240px] h-[320px] bg-[#0f1116] p-3 text-slate-200 flex flex-col gap-2.5 overflow-hidden font-sans">
            <div className="flex items-center justify-between pb-1.5 border-b border-white/10">
              <span className="text-xs font-bold text-white truncate">System Metrics</span>
              <Activity className="w-3.5 h-3.5 text-[#33EE75]" />
            </div>
            <div className="p-2 rounded-lg bg-black/60 border border-white/5 font-mono text-[9px] text-[#33EE75] leading-tight">
              <div>&gt; latency: 12ms</div>
              <div className="text-slate-400">&gt; memory: 412MB</div>
              <div>&gt; status: 200 OK</div>
            </div>
            <div className="flex-1 p-2 rounded-lg bg-white/5 border border-white/10 flex flex-col justify-end gap-1">
              <div className="flex items-end gap-1.5 h-20 w-full pt-2">
                <div className="w-1/5 h-[40%] bg-[#33EE75]/40 rounded-t" />
                <div className="w-1/5 h-[65%] bg-[#33EE75]/60 rounded-t" />
                <div className="w-1/5 h-[50%] bg-[#33EE75]/50 rounded-t" />
                <div className="w-1/5 h-[85%] bg-[#33EE75]/80 rounded-t" />
                <div className="w-1/5 h-[100%] bg-[#33EE75] rounded-t" />
              </div>
              <span className="text-[9px] text-slate-400 font-mono text-center">Req / sec throughput</span>
            </div>
          </div>
        )}

        {/* 6. Thumbnail 2: Typo & Palette Preview */}
        {artboardType === 'thumb-typo' && (
          <div className="w-[240px] h-[320px] bg-[#0f1116] p-3 text-slate-200 flex flex-col gap-2.5 overflow-hidden font-sans">
            <div className="flex items-center justify-between pb-1.5 border-b border-white/10">
              <span className="text-xs font-bold text-white truncate">UI Scale Preview</span>
              <div className="w-2.5 h-2.5 rounded-full bg-[#33EE75]" />
            </div>
            <div className="flex items-center gap-1.5">
              <div className="flex-1 h-6 rounded bg-[#33EE75]" />
              <div className="flex-1 h-6 rounded bg-[#1E293B]" />
              <div className="flex-1 h-6 rounded bg-[#0F172A]" />
            </div>
            <div className="p-2 rounded-lg bg-black/40 border border-white/5 flex flex-col gap-1">
              <span className="text-xl font-black text-white">Aa</span>
              <span className="text-xs font-medium text-slate-300">Aa Scale Subhead</span>
              <span className="text-[10px] text-slate-400">Regular body font 14px</span>
            </div>
            <button className="w-full py-1.5 rounded-full bg-[#33EE75] text-black font-bold text-[10px]">
              Button Filled
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

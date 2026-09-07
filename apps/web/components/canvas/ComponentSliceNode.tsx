// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_ComponentSliceNode"
// purpose: "Isolated Component Slice Node for Google Stitch Canvas in DNK OS"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Cpu, 
  Activity, 
  Zap, 
  Sparkles, 
  Layers, 
  Code,
  Copy,
  ExternalLink
} from 'lucide-react';

export default function ComponentSliceNode({ data, selected }: NodeProps) {
  return (
    <div 
      className={`group relative rounded-2xl transition-all duration-300 ${
        selected ? 'ring-2 ring-purple-500 shadow-2xl shadow-purple-500/20' : 'shadow-xl'
      }`}
      style={{ width: 620 }}
    >
      {/* Connection Handles */}
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

      {/* Component Slice Container */}
      <div className="bg-[#030712] text-slate-100 rounded-2xl border border-slate-800/90 overflow-hidden font-sans p-5 relative">
        {/* Glow backdrop */}
        <div className="absolute top-0 right-0 w-64 h-32 bg-purple-600/10 blur-3xl pointer-events-none" />

        {/* Slice Header */}
        <div className="text-center mb-5">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-purple-950/60 border border-purple-800/40 text-[10px] text-purple-300 font-mono mb-2">
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Component Slice: Systems Grid</span>
          </div>
          <h2 className="text-sm font-bold text-white tracking-wide">High-Performance Systems</h2>
          <p className="text-[10px] text-slate-400 mt-0.5">Precision bio-digital architectures built for agentic intelligence.</p>
        </div>

        {/* 3 Equipment Cards */}
        <div className="grid grid-cols-3 gap-3">
          {/* Card 1 */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/50 transition-all group/item">
            <div className="w-full h-20 rounded-lg bg-gradient-to-br from-purple-950/80 to-slate-950 flex items-center justify-center mb-2 overflow-hidden border border-purple-900/30">
              <Cpu className="w-7 h-7 text-purple-400 group-hover/item:scale-110 transition-transform" />
            </div>
            <h4 className="text-[11px] font-bold text-slate-200 group-hover/item:text-purple-300 transition-colors">
              Synthetix DNA Sequencer
            </h4>
            <p className="text-[8.5px] text-slate-400 mt-1 leading-tight">
              Ultra-rapid genomic sequence alignment for Cloud BioTech.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 transition-all group/item">
            <div className="w-full h-20 rounded-lg bg-gradient-to-br from-indigo-950/80 to-slate-950 flex items-center justify-center mb-2 overflow-hidden border border-indigo-900/30">
              <Activity className="w-7 h-7 text-indigo-400 group-hover/item:scale-110 transition-transform" />
            </div>
            <h4 className="text-[11px] font-bold text-slate-200 group-hover/item:text-indigo-300 transition-colors">
              Nano-Bio Reactor
            </h4>
            <p className="text-[8.5px] text-slate-400 mt-1 leading-tight">
              Continuous peptide synthesis and bio-molecular screening.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-pink-500/50 transition-all group/item">
            <div className="w-full h-20 rounded-lg bg-gradient-to-br from-pink-950/80 to-slate-950 flex items-center justify-center mb-2 overflow-hidden border border-pink-900/30">
              <Zap className="w-7 h-7 text-pink-400 group-hover/item:scale-110 transition-transform" />
            </div>
            <h4 className="text-[11px] font-bold text-slate-200 group-hover/item:text-pink-300 transition-colors">
              Neural Link Pro
            </h4>
            <p className="text-[8.5px] text-slate-400 mt-1 leading-tight">
              Implantable computer interface for next-level A2A telemetry.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

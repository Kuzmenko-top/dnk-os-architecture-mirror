// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_DesignGalleryNode"
// purpose: "CapCut Design Assets Note Card (Card 5) with multi-image gallery grid, visual product renders, 9:16 mobile mockups, and UI components"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Image as ImageIcon, 
  MoreVertical, 
  Sparkles, 
  Layers 
} from 'lucide-react';
import { CopilotToolbar } from '../../../src/canvas/copilot/CopilotToolbar';

export default function DesignGalleryNode({ id, data, selected }: NodeProps) {
  const aiParams = data?.aiParams as Record<string, any> | undefined;
  const badge = data?.badge as string | undefined;
  const title = data?.title as string | undefined;

  return (
    <div className={`w-[320px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
      selected ? 'border-pink-500 ring-2 ring-pink-500/30 shadow-[0_0_30px_rgba(236,72,153,0.25)]' : ''
    }`}>
      {/* 4-Way Smooth Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-pink-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#f472b6]" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-pink-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#f472b6]" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-pink-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#f472b6]" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-pink-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#f472b6]" />

      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-[#232938]">
        <div className="flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-pink-400" />
          <span className="font-bold text-sm text-white">{title || 'Design Assets'}</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category Pill Badge */}
      <div className="mb-3 flex items-center justify-between">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#2e1724] text-pink-300 border border-pink-500/30">
          {badge || 'Image gallery'}
        </span>
      </div>

      {/* 2x2 Asset Grid */}
      <div className="grid grid-cols-2 gap-2">
        {/* Asset 1: 3D Holographic Ribbon */}
        <div className="h-24 rounded-xl bg-gradient-to-br from-indigo-950 via-purple-900 to-slate-900 border border-[#232938] flex flex-col items-center justify-center p-2 relative overflow-hidden group hover:border-pink-500 transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-pink-500 to-indigo-500 blur-sm absolute" />
          <span className="text-[10px] font-mono font-bold text-white z-10">Hero 3D</span>
          <span className="text-[8px] text-slate-400 font-mono z-10">Render 4K</span>
        </div>

        {/* Asset 2: UI Storefront Mockup */}
        <div className="h-24 rounded-xl bg-[#090b10] border border-[#232938] p-2 flex flex-col justify-between group hover:border-pink-500 transition-colors">
          <div className="h-2 w-12 bg-slate-700 rounded-sm mb-1" />
          <div className="h-8 bg-gradient-to-r from-emerald-950 to-slate-900 rounded border border-emerald-500/20" />
          <div className="h-2 w-full bg-slate-800 rounded-sm" />
        </div>

        {/* Asset 3: Emerald Wave */}
        <div className="h-24 rounded-xl bg-gradient-to-br from-emerald-950 via-teal-900 to-black border border-[#232938] flex flex-col items-center justify-center p-2 group hover:border-pink-500 transition-colors">
          <span className="text-[10px] font-mono font-bold text-emerald-300">Wave 9:16</span>
          <span className="text-[8px] text-slate-400 font-mono">Remotion</span>
        </div>

        {/* Asset 4: Dark Product Packaging */}
        <div className="h-24 rounded-xl bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 border border-[#232938] flex flex-col items-center justify-center p-2 group hover:border-pink-500 transition-colors">
          <span className="text-[10px] font-mono font-bold text-purple-300">Package UI</span>
          <span className="text-[8px] text-slate-400 font-mono">Cocktail Box</span>
        </div>
      </div>

      {aiParams?.prompt && (
        <div className="mt-3 p-2 bg-[#090b10] border border-pink-500/20 rounded-xl text-[10px] font-mono text-pink-300">
          <div className="font-semibold text-pink-400 mb-0.5">Prompt Co-Pilot:</div>
          <p className="line-clamp-2 text-slate-300 leading-relaxed">{aiParams.prompt}</p>
        </div>
      )}

      <CopilotToolbar
        nodeId={id}
        nodeType="DesignGalleryNode"
        defaultAgentId="dnk_video_ai_creator"
      />
    </div>
  );
}

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ConceptMindmapNode"
// purpose: "CapCut Concept Map & Mindmap Note Card (Card 3) with interactive central concept node, branching sub-nodes, and visual connector labels"
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
  Network, 
  MoreVertical, 
  Sparkles, 
  Layers 
} from 'lucide-react';

export default function ConceptMindmapNode({ data, selected }: NodeProps) {
  return (
    <div className={`w-[340px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
      selected ? 'border-purple-500 ring-2 ring-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.25)]' : ''
    }`}>
      {/* 4-Way Smooth Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-purple-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#c084fc]" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-purple-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#c084fc]" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-purple-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#c084fc]" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-purple-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#c084fc]" />

      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-[#232938]">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-purple-400" />
          <span className="font-bold text-sm text-white">Concept Map</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category Pill Badge */}
      <div className="mb-3">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#231a30] text-purple-300 border border-purple-500/30">
          Mindmap
        </span>
      </div>

      {/* Visual Mindmap Tree Graphic */}
      <div className="p-4 rounded-xl bg-[#090b10] border border-[#1a1f2c] relative flex flex-col items-center justify-center min-h-[160px] overflow-hidden">
        {/* Central Root Node */}
        <div className="px-4 py-2 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-xs shadow-lg shadow-purple-500/30 z-10 border border-purple-400/40">
          Mindmap
        </div>

        {/* SVG Curved Connectors */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-purple-500/40" strokeWidth="1.5" fill="none">
          <path d="M 170 80 C 130 50, 90 40, 60 40" />
          <path d="M 170 80 C 130 110, 90 120, 60 120" />
          <path d="M 170 80 C 210 50, 250 40, 280 40" />
          <path d="M 170 80 C 210 110, 250 120, 280 120" />
        </svg>

        {/* Top-Left Node */}
        <div className="absolute top-2 left-3 px-2.5 py-1 rounded-lg bg-[#161b26] border border-[#232938] text-[10px] font-medium text-slate-300 shadow-sm">
          Node 1
        </div>

        {/* Bottom-Left Node */}
        <div className="absolute bottom-2 left-3 px-2.5 py-1 rounded-lg bg-[#161b26] border border-[#232938] text-[10px] font-medium text-slate-300 shadow-sm">
          Label 2
        </div>

        {/* Top-Right Node */}
        <div className="absolute top-2 right-3 px-2.5 py-1 rounded-lg bg-[#161b26] border border-[#232938] text-[10px] font-medium text-slate-300 shadow-sm">
          Nodes 2
        </div>

        {/* Bottom-Right Node */}
        <div className="absolute bottom-2 right-3 px-2.5 py-1 rounded-lg bg-[#161b26] border border-[#232938] text-[10px] font-medium text-slate-300 shadow-sm">
          Connects
        </div>
      </div>
    </div>
  );
}

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MarketResearchNode"
// purpose: "CapCut Market Research Note Card (Card 2) with Image badge, live SVG bar chart, donut chart, and analytical research text metrics"
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
  BarChart3, 
  MoreVertical, 
  TrendingUp, 
  PieChart, 
  Image as ImageIcon 
} from 'lucide-react';

export default function MarketResearchNode({ data, selected }: NodeProps) {
  return (
    <div className={`w-[320px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
      selected ? 'border-cyan-500 ring-2 ring-cyan-500/30 shadow-[0_0_30px_rgba(6,182,212,0.25)]' : ''
    }`}>
      {/* 4-Way Smooth Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-cyan-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#22d3ee]" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-cyan-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#22d3ee]" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-cyan-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#22d3ee]" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-cyan-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#22d3ee]" />

      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-[#232938]">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          <span className="font-bold text-sm text-white">Market Research</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category Pill Badge */}
      <div className="mb-3">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#16252e] text-cyan-300 border border-cyan-500/30">
          Image
        </span>
      </div>

      {/* Live Visual Analytics Dashboard */}
      <div className="p-3 rounded-xl bg-[#090b10] border border-[#1a1f2c] mb-3">
        {/* Top Mini Metrics & Donut Chart */}
        <div className="flex items-center justify-between mb-3 border-b border-[#1a1f2c] pb-2">
          <div>
            <span className="text-[9px] text-slate-500 font-mono block">TAM GROWTH</span>
            <span className="text-sm font-bold text-white font-mono">$47.8M</span>
            <span className="text-[9px] text-emerald-400 font-mono">▲ +28.4%</span>
          </div>

          {/* Mini Donut Chart */}
          <div className="relative w-11 h-11 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-[#1a1f2c]"
                strokeWidth="4"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-cyan-400"
                strokeDasharray="70, 100"
                strokeWidth="4"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-pink-500"
                strokeDasharray="25, 100"
                strokeDashoffset="-70"
                strokeWidth="4"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-[8px] font-mono font-bold text-white">70%</span>
          </div>
        </div>

        {/* Mini Bar Chart */}
        <div className="mb-2">
          <div className="flex items-end justify-between h-14 gap-1.5 pt-2">
            {[35, 55, 40, 75, 60, 90, 85, 100].map((h, i) => (
              <div key={i} className="flex-1 bg-[#1a1f2c] rounded-t-sm h-full flex items-end overflow-hidden">
                <div
                  className="w-full bg-gradient-to-t from-cyan-600 to-cyan-400 rounded-t-sm transition-all hover:brightness-125"
                  style={{ height: `${h}%` }}
                />
              </div>
            ))}
          </div>
          <div className="flex justify-between text-[8px] text-slate-500 font-mono mt-1">
            <span>Q1</span>
            <span>Q2</span>
            <span>Q3</span>
            <span>Q4</span>
          </div>
        </div>
      </div>

      {/* Research Summary Text */}
      <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
        Target audience demonstrates strong demand for premium cocktail infusion bundles with $120+ average checkout valuation.
      </p>
    </div>
  );
}

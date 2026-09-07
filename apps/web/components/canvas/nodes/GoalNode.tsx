// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_GoalNode"
// purpose: "Goal Intake Node for DNK Canvas displaying TaskDNA status and natural language prompt"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Target, Sparkles, Dna, CheckCircle2 } from 'lucide-react';

export default function GoalNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  return (
    <div className={`w-[320px] rounded-2xl bg-gradient-to-b from-purple-950/90 via-slate-900/90 to-slate-950/90 backdrop-blur-xl border border-purple-500/50 p-4 text-white shadow-2xl transition-all ${selected ? 'ring-2 ring-purple-400 scale-[1.02]' : ''}`}>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-purple-500 border-2 border-white rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-purple-500/30 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-purple-600/30 border border-purple-500/40 text-purple-300">
            <Target className="w-4 h-4" />
          </div>
          <span className="font-bold text-xs uppercase tracking-wider text-purple-300 font-mono">
            Goal Intake Node
          </span>
        </div>
        <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-mono">
          <CheckCircle2 className="w-2.5 h-2.5" /> Ready
        </span>
      </div>

      {/* Title & Goal Content */}
      <h3 className="font-semibold text-sm text-slate-100 leading-snug mb-2">
        {String(nodeData.title || 'User Business Goal')}
      </h3>

      {nodeData.config?.goal && (
        <p className="text-[11px] text-slate-400 bg-slate-950/60 rounded-xl p-2.5 border border-purple-900/30 leading-relaxed font-sans mb-3">
          &ldquo;{String(nodeData.config.goal)}&rdquo;
        </p>
      )}

      {/* Footer Pill */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-purple-900/30">
        <div className="flex items-center gap-1 text-purple-300">
          <Dna className="w-3 h-3" />
          <span>TaskDNA v2.4</span>
        </div>
        <span className="font-mono text-slate-500">A2A Verified</span>
      </div>
    </div>
  );
}

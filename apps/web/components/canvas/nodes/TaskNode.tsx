// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_TaskNode"
// purpose: "Executable Subtask Node for DNK Canvas displaying assigned agent, state, and I/O ports"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { CheckSquare, Bot, Play, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

export default function TaskNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  const state = String(nodeData.state || 'idle');
  const assignedAgent = String(nodeData.assigned_agent || 'gerych_builder');

  const getStateBadge = () => {
    switch (state) {
      case 'running':
        return (
          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-500/40 font-mono animate-pulse">
            <Play className="w-2.5 h-2.5 fill-current" /> Running
          </span>
        );
      case 'completed':
        return (
          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 font-mono">
            <CheckCircle2 className="w-2.5 h-2.5" /> Done
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono">
            <Clock className="w-2.5 h-2.5" /> Queued
          </span>
        );
    }
  };

  return (
    <div className={`w-[280px] rounded-2xl bg-slate-900/90 backdrop-blur-xl border border-slate-700/80 p-3.5 text-white shadow-xl transition-all ${selected ? 'ring-2 ring-indigo-400 scale-[1.02]' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-indigo-400 border-2 border-white rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-indigo-400 border-2 border-white rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
        <div className="flex items-center gap-1.5">
          <div className="p-1 rounded-lg bg-indigo-500/20 text-indigo-400">
            <CheckSquare className="w-3.5 h-3.5" />
          </div>
          <span className="font-bold text-[11px] uppercase tracking-wider text-slate-300 font-mono">
            Task Node
          </span>
        </div>
        {getStateBadge()}
      </div>

      {/* Task Content */}
      <h4 className="font-bold text-sm text-slate-100 mb-1 leading-snug">
        {String(nodeData.title || 'Execute Subtask')}
      </h4>

      {/* Meta Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px]">
        <div className="flex items-center gap-1 text-slate-400">
          <Bot className="w-3 h-3 text-indigo-400" />
          <span className="font-mono text-indigo-300 font-semibold">{assignedAgent}</span>
        </div>
        <span className="font-mono text-slate-500">{String(nodeData.config?.task_id || 'dna_001')}</span>
      </div>
    </div>
  );
}

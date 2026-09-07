// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_AgentNode"
// purpose: "Swarm Agent Worker Node for DNK Canvas showing live A2A thought streams and lease status"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot, Terminal, Activity, Radio, Cpu } from 'lucide-react';

export default function AgentNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as Record<string, any>;
  const agentName = String(nodeData.assigned_agent || nodeData.config?.agent || 'dnk_dev_fullstack');

  return (
    <div className={`w-[300px] rounded-2xl bg-slate-900/95 backdrop-blur-xl border border-cyan-500/40 p-4 text-white shadow-2xl transition-all ${selected ? 'ring-2 ring-cyan-400 scale-[1.02]' : ''}`}>
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-cyan-400 border-2 border-white rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-cyan-400 border-2 border-white rounded-full" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-cyan-500/30 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-300">
            <Bot className="w-4 h-4" />
          </div>
          <span className="font-bold text-xs uppercase tracking-wider text-cyan-300 font-mono">
            Swarm Agent
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 text-[10px] font-mono border border-cyan-500/30">
          <Radio className="w-2.5 h-2.5 animate-pulse text-cyan-400" />
          <span>Leased</span>
        </div>
      </div>

      {/* Title / Agent Name */}
      <div className="mb-3">
        <h4 className="font-bold text-sm text-slate-100">{String(nodeData.title || 'Agent Worker')}</h4>
        <span className="text-[11px] font-mono text-cyan-400 font-semibold">{agentName}</span>
      </div>

      {/* Simulated Live Stream Console */}
      <div className="bg-slate-950/80 rounded-xl p-2.5 border border-slate-800 text-[10px] font-mono text-slate-300 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 text-slate-500 text-[9px] border-b border-slate-800/80 pb-1">
          <Terminal className="w-3 h-3 text-cyan-400" />
          <span>A2A Reasoning Stream</span>
        </div>
        <p className="text-emerald-400 leading-tight mt-1">› Synced SCONES template context</p>
        <p className="text-slate-400 leading-tight">› Compiling Liquid / React AST tokens...</p>
      </div>
    </div>
  );
}

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapAgentNode"
// purpose: "Mind Map Agent Node (Orange Robot card) with agent dispatcher, live status telemetry, and one-click Phase 1 Swarm trigger"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { NodeProps } from '@xyflow/react';
import { Bot, Play, Loader2, CheckCircle2, AlertTriangle, Cpu } from 'lucide-react';
import BaseMindMapNode from './BaseMindMapNode';
import { useCanvasStore } from '../../../store/canvasStore';

export interface MindMapAgentData {
  title?: string;
  description?: string;
  agent_type?: string;
  agentStatus?: 'idle' | 'thinking' | 'running' | 'completed' | 'error';
  agentTraceId?: string;
  last_result?: string;
  [key: string]: any;
}

const AVAILABLE_AGENTS = [
  { id: 'dnk_shopify', name: 'Shopify Expert' },
  { id: 'dnk_dev_fullstack', name: 'Fullstack Dev' },
  { id: 'gerych_prime', name: 'Gerych Prime' },
  { id: 'dnk_video_ai_creator', name: 'Video AI Creator' },
];

export default function MindMapAgentNode(props: NodeProps) {
  const { id, data } = props;
  const nodeData = (data || {}) as MindMapAgentData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);
  const triggerNodeAgent = useCanvasStore((state) => state.triggerNodeAgent);

  const agentType = nodeData.agent_type || 'dnk_shopify';
  const status = nodeData.agentStatus || 'idle';
  const traceId = nodeData.agentTraceId;

  const [prompt, setPrompt] = useState('');

  const isBusy = status === 'thinking' || status === 'running';

  const handleRunAgent = () => {
    if (triggerNodeAgent && !isBusy) {
      triggerNodeAgent(id, prompt || nodeData.description, agentType);
    }
  };

  const handleSelectAgent = (e: React.ChangeEvent<HTMLSelectElement>) => {
    updateNodeData(id, { agent_type: e.target.value });
  };

  return (
    <BaseMindMapNode
      {...props}
      themeColor="orange"
      icon={<Bot className="w-4 h-4" />}
      categoryLabel="Agent"
    >
      <div className="flex flex-col gap-2.5">
        {/* Agent Selector Dropdown */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-xs text-orange-300">
            <Cpu className="w-3.5 h-3.5" />
            <select
              value={agentType}
              onChange={handleSelectAgent}
              disabled={isBusy}
              className="bg-slate-900 border border-orange-500/30 rounded px-1.5 py-0.5 text-xs text-orange-200 focus:outline-none focus:border-orange-400 cursor-pointer"
            >
              {AVAILABLE_AGENTS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center gap-1 text-[10px] font-mono">
            {isBusy ? (
              <span className="inline-flex items-center gap-1 text-orange-400">
                <Loader2 className="w-3 h-3 animate-spin" />
                {status}
              </span>
            ) : status === 'completed' ? (
              <span className="inline-flex items-center gap-1 text-emerald-400">
                <CheckCircle2 className="w-3 h-3" />
                done
              </span>
            ) : status === 'error' ? (
              <span className="inline-flex items-center gap-1 text-red-400">
                <AlertTriangle className="w-3 h-3" />
                error
              </span>
            ) : (
              <span className="text-slate-500">idle</span>
            )}
          </div>
        </div>

        {/* Action Button & Trace ID */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-800/60">
          <span className="text-[9px] font-mono text-slate-500 truncate max-w-[150px]">
            {traceId ? `trace: ${traceId.slice(-8)}` : 'Swarm v1.0'}
          </span>

          <button
            onClick={handleRunAgent}
            disabled={isBusy}
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold shadow transition-all cursor-pointer ${
              isBusy
                ? 'bg-orange-950/60 text-orange-300/60 border border-orange-500/20 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white shadow-orange-500/20'
            }`}
          >
            {isBusy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 fill-white" />}
            <span>{isBusy ? 'Running...' : 'Run'}</span>
          </button>
        </div>
      </div>
    </BaseMindMapNode>
  );
}

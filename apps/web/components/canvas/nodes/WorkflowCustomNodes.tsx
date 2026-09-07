// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_workflow_custom_nodes"
// purpose: "React Flow Custom Node Components for Visual Canvas Designer (DNK-CANVAS-001 Phase 3)"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-29"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot, Zap, Cpu, ShoppingBag, Radio, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface BaseNodeData {
  label: string;
  node_type: string;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  config?: Record<string, any>;
  onConfigChange?: (newConfig: Record<string, any>) => void;
}

const StatusBadge = ({ status }: { status?: string }) => {
  if (status === 'running') {
    return (
      <span className="flex items-center gap-1 text-[10px] font-bold text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-500/40 animate-pulse">
        <Loader2 className="w-2.5 h-2.5 animate-spin" /> RUNNING
      </span>
    );
  }
  if (status === 'completed') {
    return (
      <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/40">
        <CheckCircle className="w-2.5 h-2.5" /> DONE
      </span>
    );
  }
  if (status === 'failed') {
    return (
      <span className="flex items-center gap-1 text-[10px] font-bold text-rose-400 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-500/40">
        <AlertCircle className="w-2.5 h-2.5" /> ERROR
      </span>
    );
  }
  return (
    <span className="text-[10px] font-medium text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700">
      IDLE
    </span>
  );
};

// 1. A2A Agent Node
export const A2AAgentNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as unknown as BaseNodeData;
  const config = nodeData.config || {};
  return (
    <div
      className={`min-w-[220px] rounded-xl border bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur transition-all ${
        selected ? 'border-cyan-400 shadow-cyan-500/20' : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-zinc-950" />
      <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-cyan-950/80 p-1.5 text-cyan-400 border border-cyan-500/30">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100">{nodeData.label || 'A2A Agent'}</div>
            <div className="text-[10px] text-zinc-400">Mesh Protocol: {config.protocol || 'DNK-A2A-004'}</div>
          </div>
        </div>
        <StatusBadge status={nodeData.status} />
      </div>

      <div className="space-y-1 text-[11px] text-zinc-300">
        <div className="flex justify-between text-zinc-400">
          <span>Agent ID:</span>
          <span className="font-mono text-zinc-200">{config.agent_id || 'unassigned'}</span>
        </div>
        <div className="flex justify-between text-zinc-400">
          <span>Consensus:</span>
          <span className="font-mono text-cyan-300">{(config.consensus_threshold || 0.8) * 100}%</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-zinc-950" />
    </div>
  );
});

// 2. Event Trigger Node
export const EventTriggerNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as unknown as BaseNodeData;
  const config = nodeData.config || {};
  return (
    <div
      className={`min-w-[220px] rounded-xl border bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur transition-all ${
        selected ? 'border-amber-400 shadow-amber-500/20' : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-amber-950/80 p-1.5 text-amber-400 border border-amber-500/30">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100">{nodeData.label || 'Event Trigger'}</div>
            <div className="text-[10px] text-zinc-400">Stream: {config.stream_name || 'default-stream'}</div>
          </div>
        </div>
        <StatusBadge status={nodeData.status} />
      </div>

      <div className="space-y-1 text-[11px] text-zinc-300">
        <div className="flex justify-between text-zinc-400">
          <span>Event Type:</span>
          <span className="font-mono text-amber-300">{config.event_type || '*'}</span>
        </div>
        <div className="flex justify-between text-zinc-400">
          <span>Debounce:</span>
          <span className="font-mono text-zinc-200">{config.debounce_ms || 0}ms</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-amber-500 !border-2 !border-zinc-950" />
    </div>
  );
});

// 3. Batch Task Node
export const BatchTaskNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as unknown as BaseNodeData;
  const config = nodeData.config || {};
  return (
    <div
      className={`min-w-[220px] rounded-xl border bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur transition-all ${
        selected ? 'border-indigo-400 shadow-indigo-500/20' : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-indigo-500 !border-2 !border-zinc-950" />
      <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-indigo-950/80 p-1.5 text-indigo-400 border border-indigo-500/30">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100">{nodeData.label || 'Batch Task'}</div>
            <div className="text-[10px] text-zinc-400">DNK-BATCH-001 Engine</div>
          </div>
        </div>
        <StatusBadge status={nodeData.status} />
      </div>

      <div className="space-y-1 text-[11px] text-zinc-300">
        <div className="flex justify-between text-zinc-400">
          <span>Task Type:</span>
          <span className="font-mono text-indigo-300">{config.task_type || 'standard_compute'}</span>
        </div>
        <div className="flex justify-between text-zinc-400">
          <span>Timeout:</span>
          <span className="font-mono text-zinc-200">{config.timeout_sec || 300}s</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-indigo-500 !border-2 !border-zinc-950" />
    </div>
  );
});

// 4. Shopify Action Node
export const ShopifyActionNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as unknown as BaseNodeData;
  const config = nodeData.config || {};
  return (
    <div
      className={`min-w-[220px] rounded-xl border bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur transition-all ${
        selected ? 'border-emerald-400 shadow-emerald-500/20' : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-zinc-950" />
      <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-emerald-950/80 p-1.5 text-emerald-400 border border-emerald-500/30">
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100">{nodeData.label || 'Shopify Action'}</div>
            <div className="text-[10px] text-zinc-400">GraphQL App Bridge 2.0</div>
          </div>
        </div>
        <StatusBadge status={nodeData.status} />
      </div>

      <div className="space-y-1 text-[11px] text-zinc-300">
        <div className="flex justify-between text-zinc-400">
          <span>Action:</span>
          <span className="font-mono text-emerald-300 font-semibold">{config.action_type || 'create_order'}</span>
        </div>
        <div className="flex justify-between text-zinc-400">
          <span>API:</span>
          <span className="font-mono text-zinc-200">{config.api_version || '2026-07'}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-zinc-950" />
    </div>
  );
});

// 5. Hardware Action Node
export const HardwareActionNode = memo(({ data, selected }: NodeProps) => {
  const nodeData = (data || {}) as unknown as BaseNodeData;
  const config = nodeData.config || {};
  return (
    <div
      className={`min-w-[220px] rounded-xl border bg-zinc-900/95 p-3.5 shadow-2xl backdrop-blur transition-all ${
        selected ? 'border-purple-400 shadow-purple-500/20' : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-purple-500 !border-2 !border-zinc-950" />
      <div className="flex items-center justify-between gap-2 border-b border-zinc-800 pb-2 mb-2.5">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-purple-950/80 p-1.5 text-purple-400 border border-purple-500/30">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-zinc-100">{nodeData.label || 'ReBurn Hardware'}</div>
            <div className="text-[10px] text-zinc-400">IoT Controller Bridge</div>
          </div>
        </div>
        <StatusBadge status={nodeData.status} />
      </div>

      <div className="space-y-1 text-[11px] text-zinc-300">
        <div className="flex justify-between text-zinc-400">
          <span>Device:</span>
          <span className="font-mono text-purple-300">{config.device_id || 'reburn-sensor-01'}</span>
        </div>
        <div className="flex justify-between text-zinc-400">
          <span>Action:</span>
          <span className="font-mono text-zinc-200">{config.action_type || 'read_sensor'}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-purple-500 !border-2 !border-zinc-950" />
    </div>
  );
});

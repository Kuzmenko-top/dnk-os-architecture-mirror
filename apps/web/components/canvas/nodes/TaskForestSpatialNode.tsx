// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_TaskForestSpatialNode"
// purpose: "Task Forest Spatial Node with 3-Level-of-Detail (LOD: 0.2x Macro Heatmap, 1.0x Meso Structural, 2.5x Micro Deep Execution & Git Diff)"
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps, useViewport } from '@xyflow/react';
import {
  Layers,
  GitBranch,
  GitCommit,
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  ShieldCheck,
  ShieldAlert,
  Code,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Bot,
  Activity,
  RotateCcw,
  CheckSquare
} from 'lucide-react';

export interface TaskForestNodeData {
  id?: string;
  title: string;
  plant_scale: 'field' | 'sector' | 'tree' | 'bush' | 'flower';
  status: 'todo' | 'pending' | 'in_progress' | 'completed' | 'cancelled' | 'ready';
  progress: number;
  parent_id?: string | null;
  assigned_agent?: string | null;
  author?: string;
  weight?: number;
  git_diff?: string | null;
  dto_contract?: Record<string, any> | null;
  verification_status?: 'verified' | 'pending' | 'failed' | string;
  updated_at?: string;
  children_count?: number;
  scale_counts?: Record<string, number>;
  is_time_travel_highlighted?: boolean;
  onMutate?: (nodeId: string, newStatus: string, newProgress: number) => void;
}

const PLANT_ICONS: Record<string, string> = {
  field: '🌾',
  sector: '🏞️',
  tree: '🌳',
  bush: '🌿',
  flower: '🌸'
};

const PLANT_LABELS: Record<string, string> = {
  field: 'Field (Root)',
  sector: 'Sector',
  tree: 'Tree (Epic)',
  bush: 'Bush (Submodule)',
  flower: 'Flower (Atomic Task)'
};

export default function TaskForestSpatialNode({ id, data, selected }: NodeProps) {
  const nodeData = (data || {}) as unknown as TaskForestNodeData;
  const { zoom } = useViewport();

  const [isDiffExpanded, setIsDiffExpanded] = useState<boolean>(false);
  const [isDtoExpanded, setIsDtoExpanded] = useState<boolean>(false);
  const [isMutating, setIsMutating] = useState<boolean>(false);

  const plantScale = nodeData.plant_scale || 'flower';
  const plantIcon = PLANT_ICONS[plantScale] || '🌸';
  const title = nodeData.title || 'Task Forest Node';
  const progress = typeof nodeData.progress === 'number' ? Math.round(nodeData.progress) : 0;
  const status = nodeData.status || 'todo';
  const assignedAgent = nodeData.assigned_agent || 'gerych_builder';
  const verification = nodeData.verification_status || 'verified';
  const isHighlighted = !!nodeData.is_time_travel_highlighted;

  // Level of Detail: 
  // - Zoom < 0.4x -> Macro (LOD 0.2x)
  // - Zoom > 1.8x -> Micro (LOD 2.5x)
  // - Otherwise -> Meso (LOD 1.0x)
  const lodLevel = zoom < 0.4 ? 'macro' : zoom > 1.8 ? 'micro' : 'meso';

  // Quick Mutation Handler
  const handleQuickMutate = async (newStatus: 'todo' | 'in_progress' | 'completed') => {
    setIsMutating(true);
    const newProgress = newStatus === 'completed' ? 100 : newStatus === 'in_progress' ? 50 : 0;
    try {
      const res = await fetch('/api/v3/task_forest/node/mutate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: id || nodeData.id,
          status: newStatus,
          progress: newProgress
        })
      });
      if (res.ok) {
        if (nodeData.onMutate) {
          nodeData.onMutate(id || nodeData.id || '', newStatus, newProgress);
        }
      }
    } catch (err) {
      console.error('Failed to mutate Task Forest node', err);
    } finally {
      setIsMutating(false);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'text-emerald-400 bg-emerald-950/70 border-emerald-500/40';
      case 'in_progress':
        return 'text-amber-400 bg-amber-950/70 border-amber-500/40';
      case 'cancelled':
        return 'text-rose-400 bg-rose-950/70 border-rose-500/40';
      default:
        return 'text-slate-400 bg-slate-900/70 border-slate-700/50';
    }
  };

  const getProgressBarColor = () => {
    if (progress === 100) return 'bg-emerald-500';
    if (progress > 50) return 'bg-cyan-500';
    if (progress > 0) return 'bg-amber-500';
    return 'bg-slate-700';
  };

  // -------------------------------------------------------------
  // 1. MACRO VIEW (LOD 0.2x): Heatmap Card & High-level Aggregation
  // -------------------------------------------------------------
  if (lodLevel === 'macro') {
    return (
      <div
        className={`relative group rounded-2xl bg-slate-950/95 border transition-all duration-300 backdrop-blur-md p-3 w-[220px] select-none ${
          isHighlighted
            ? 'border-amber-400 ring-4 ring-amber-400/50 shadow-[0_0_30px_rgba(251,191,36,0.6)] animate-pulse'
            : selected
            ? 'border-cyan-400 ring-2 ring-cyan-400/40 shadow-xl'
            : 'border-slate-800 shadow-md hover:border-slate-700'
        }`}
      >
        <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-cyan-400 !border-0" />
        <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-cyan-400 !border-0" />

        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-1.5 truncate">
            <span className="text-base leading-none">{plantIcon}</span>
            <span className="text-xs font-bold text-slate-100 truncate">{title}</span>
          </div>
          <span className="text-xs font-extrabold font-mono text-emerald-400 shrink-0">
            {progress}% {progress === 100 ? '🟢' : progress > 0 ? '🟡' : '⚪'}
          </span>
        </div>

        {/* Heatmap Mini Progress Bar */}
        <div className="w-full bg-slate-800/80 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Sub-item count or scale label */}
        <div className="flex items-center justify-between text-[10px] text-slate-400 mt-2 font-mono">
          <span className="capitalize">{plantScale}</span>
          {nodeData.children_count !== undefined && (
            <span>{nodeData.children_count} items</span>
          )}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 2. MICRO VIEW (LOD 2.5x): High-Fidelity Atomic Execution & Diff
  // -------------------------------------------------------------
  if (lodLevel === 'micro') {
    return (
      <div
        className={`relative group rounded-2xl bg-slate-950/95 border transition-all duration-300 backdrop-blur-xl p-4 w-[420px] select-none text-white ${
          isHighlighted
            ? 'border-amber-400 ring-4 ring-amber-400/50 shadow-[0_0_35px_rgba(251,191,36,0.7)] animate-pulse'
            : selected
            ? 'border-cyan-400 ring-2 ring-cyan-400/40 shadow-2xl'
            : 'border-slate-800 shadow-xl hover:border-slate-700'
        }`}
      >
        <Handle type="target" position={Position.Top} className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-slate-950" />
        <Handle type="source" position={Position.Bottom} className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-slate-950" />
        <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-slate-950" />
        <Handle type="source" position={Position.Right} className="!w-3 !h-3 !bg-cyan-400 !border-2 !border-slate-950" />

        {/* Top Header Badge */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5 mb-3">
          <div className="flex items-center gap-2 truncate">
            <span className="text-xl">{plantIcon}</span>
            <div>
              <span className="text-[10px] font-mono tracking-wider uppercase text-cyan-400 block">
                {PLANT_LABELS[plantScale] || plantScale}
              </span>
              <h4 className="text-sm font-bold text-slate-100 truncate max-w-[240px]" title={title}>
                {title}
              </h4>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono font-semibold ${getStatusColor()}`}>
              {status}
            </span>
            <span className="text-xs font-mono font-bold text-emerald-400">
              {progress}%
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-900 rounded-full h-2 mb-3 overflow-hidden border border-slate-800">
          <div
            className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Assigned Agent & Verification Pill */}
        <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <Bot className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <div className="truncate">
              <span className="text-[10px] text-slate-400 block leading-none">Agent</span>
              <span className="font-mono text-slate-200 truncate block font-medium">{assignedAgent}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 p-2 rounded-lg bg-slate-900/80 border border-slate-800/80">
            {verification === 'verified' ? (
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            ) : (
              <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            )}
            <div className="truncate">
              <span className="text-[10px] text-slate-400 block leading-none">Verification</span>
              <span className="font-mono text-slate-200 capitalize font-medium">{verification}</span>
            </div>
          </div>
        </div>

        {/* Git Diff Inspection Accordion */}
        {nodeData.git_diff && (
          <div className="mb-3 rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden">
            <button
              onClick={() => setIsDiffExpanded(!isDiffExpanded)}
              className="w-full flex items-center justify-between p-2 text-xs font-mono text-slate-300 hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <GitCommit className="w-3.5 h-3.5 text-cyan-400" />
                <span>Git Diff & Atomic Patch</span>
              </div>
              {isDiffExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              )}
            </button>
            {isDiffExpanded && (
              <div className="p-2 border-t border-slate-800 bg-black/70 max-h-36 overflow-y-auto">
                <pre className="text-[10px] font-mono text-emerald-300 whitespace-pre-wrap leading-tight">
                  {nodeData.git_diff}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* DTO Contract Accordion */}
        {nodeData.dto_contract && Object.keys(nodeData.dto_contract).length > 0 && (
          <div className="mb-3 rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden">
            <button
              onClick={() => setIsDtoExpanded(!isDtoExpanded)}
              className="w-full flex items-center justify-between p-2 text-xs font-mono text-slate-300 hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <Code className="w-3.5 h-3.5 text-amber-400" />
                <span>DTO Contract Schema</span>
              </div>
              {isDtoExpanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              )}
            </button>
            {isDtoExpanded && (
              <div className="p-2 border-t border-slate-800 bg-black/70 max-h-36 overflow-y-auto">
                <pre className="text-[10px] font-mono text-amber-300 whitespace-pre-wrap leading-tight">
                  {JSON.stringify(nodeData.dto_contract, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Quick Atomic Mutation Controls */}
        <div className="border-t border-slate-800/80 pt-2.5">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
            Quick Atomic Mutation
          </span>
          <div className="grid grid-cols-3 gap-1.5">
            <button
              disabled={isMutating || status === 'todo'}
              onClick={() => handleQuickMutate('todo')}
              className={`px-2 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1 border ${
                status === 'todo'
                  ? 'bg-slate-800 text-white border-slate-600'
                  : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white'
              }`}
            >
              <Clock className="w-3 h-3" /> Todo
            </button>
            <button
              disabled={isMutating || status === 'in_progress'}
              onClick={() => handleQuickMutate('in_progress')}
              className={`px-2 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1 border ${
                status === 'in_progress'
                  ? 'bg-amber-950 text-amber-300 border-amber-500'
                  : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:border-amber-500/50 hover:text-amber-300'
              }`}
            >
              <Play className="w-3 h-3 fill-current" /> Active
            </button>
            <button
              disabled={isMutating || status === 'completed'}
              onClick={() => handleQuickMutate('completed')}
              className={`px-2 py-1.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-1 border ${
                status === 'completed'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-500'
                  : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:border-emerald-500/50 hover:text-emerald-300'
              }`}
            >
              <CheckCircle2 className="w-3 h-3" /> Done
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 3. MESO VIEW (LOD 1.0x): Structural Hierarchy (Tree & Bush)
  // -------------------------------------------------------------
  return (
    <div
      className={`relative group rounded-2xl bg-slate-950/95 border transition-all duration-300 backdrop-blur-md p-3.5 w-[320px] select-none text-white ${
        isHighlighted
          ? 'border-amber-400 ring-4 ring-amber-400/50 shadow-[0_0_30px_rgba(251,191,36,0.6)] animate-pulse'
          : selected
          ? 'border-cyan-400 ring-2 ring-cyan-400/40 shadow-xl'
          : 'border-slate-800 shadow-lg hover:border-slate-700'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-950" />
      <Handle type="source" position={Position.Bottom} className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-950" />
      <Handle type="target" position={Position.Left} className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-950" />
      <Handle type="source" position={Position.Right} className="!w-2.5 !h-2.5 !bg-cyan-400 !border-2 !border-slate-950" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
        <div className="flex items-center gap-2 truncate">
          <span className="text-lg leading-none">{plantIcon}</span>
          <div className="truncate">
            <span className="text-[9px] font-mono uppercase tracking-wider text-cyan-400 block">
              {plantScale}
            </span>
            <span className="text-xs font-bold text-slate-100 truncate block max-w-[170px]" title={title}>
              {title}
            </span>
          </div>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-mono font-medium ${getStatusColor()}`}>
          {status}
        </span>
      </div>

      {/* Progress Metric */}
      <div className="flex items-center justify-between text-xs font-mono mb-1.5">
        <span className="text-slate-400 text-[10px]">Progress</span>
        <span className="font-bold text-emerald-400">{progress}%</span>
      </div>
      <div className="w-full bg-slate-900 rounded-full h-1.5 mb-3 overflow-hidden border border-slate-800">
        <div
          className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Footer Info: Assigned Agent & Sub-items */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 font-mono">
        <div className="flex items-center gap-1 truncate max-w-[180px]">
          <Bot className="w-3 h-3 text-cyan-400 shrink-0" />
          <span className="truncate">{assignedAgent}</span>
        </div>
        {nodeData.children_count !== undefined ? (
          <span className="text-slate-500">{nodeData.children_count} items</span>
        ) : (
          <span className="text-slate-500 capitalize">{verification}</span>
        )}
      </div>
    </div>
  );
}

export { TaskForestSpatialNode };

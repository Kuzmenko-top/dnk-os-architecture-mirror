// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/CustomTaskNode.tsx"
// purpose: "Custom ReactFlow Node component for DNK Node-Based Tasks & Ideas DAG"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import {
  Lightbulb,
  Layers,
  CheckSquare,
  Code2,
  ShieldAlert,
  Bot,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Flame,
} from 'lucide-react';
import { TaskNodeData, NodeType, ExecutionStage } from '@/types/nodeTasks';
import { useNodeTasksStore } from '@/store/nodeTasksStore';

const TYPE_CONFIG: Record<
  NodeType,
  { label: string; icon: React.ElementType; color: string; bgGradient: string; border: string }
> = {
  idea: {
    label: 'Idea',
    icon: Lightbulb,
    color: 'text-amber-400',
    bgGradient: 'from-amber-950/40 via-zinc-900 to-zinc-900',
    border: 'border-amber-500/50 hover:border-amber-400',
  },
  epic: {
    label: 'Epic',
    icon: Layers,
    color: 'text-purple-400',
    bgGradient: 'from-purple-950/40 via-zinc-900 to-zinc-900',
    border: 'border-purple-500/50 hover:border-purple-400',
  },
  task: {
    label: 'Task',
    icon: CheckSquare,
    color: 'text-cyan-400',
    bgGradient: 'from-cyan-950/40 via-zinc-900 to-zinc-900',
    border: 'border-cyan-500/50 hover:border-cyan-400',
  },
  slice: {
    label: 'Slice',
    icon: Code2,
    color: 'text-emerald-400',
    bgGradient: 'from-emerald-950/40 via-zinc-900 to-zinc-900',
    border: 'border-emerald-500/50 hover:border-emerald-400',
  },
  gate: {
    label: 'Gate',
    icon: ShieldAlert,
    color: 'text-rose-400',
    bgGradient: 'from-rose-950/40 via-zinc-900 to-zinc-900',
    border: 'border-rose-500/50 hover:border-rose-400',
  },
};

const STAGE_CONFIG: Record<ExecutionStage, { label: string; badge: string }> = {
  ideation: { label: 'Ideation', badge: 'bg-amber-900/40 text-amber-300 border-amber-600/40' },
  architecture: { label: 'Architecture', badge: 'bg-indigo-900/40 text-indigo-300 border-indigo-600/40' },
  ready: { label: 'Ready', badge: 'bg-sky-900/40 text-sky-300 border-sky-600/40' },
  in_progress: { label: 'In Progress', badge: 'bg-blue-900/50 text-blue-300 border-blue-500 animate-pulse' },
  blocked: { label: 'Blocked', badge: 'bg-red-950/70 text-red-300 border-red-500 animate-pulse' },
  testing: { label: 'Testing', badge: 'bg-purple-900/40 text-purple-300 border-purple-600/40' },
  completed: { label: 'Completed', badge: 'bg-emerald-950/50 text-emerald-300 border-emerald-600/40' },
};

export const CustomTaskNode = memo(({ data, selected }: NodeProps) => {
  const node = data as unknown as TaskNodeData;
  const setSelectedNodeId = useNodeTasksStore((s) => s.setSelectedNodeId);
  const selectedNodeIds = useNodeTasksStore((s) => s.selectedNodeIds);
  const setSelectedNodeIds = useNodeTasksStore((s) => s.setSelectedNodeIds);
  const convertIdea = useNodeTasksStore((s) => s.convertIdea);
  const showCriticalPath = useNodeTasksStore((s) => s.showCriticalPath);
  const criticalPathNodeIds = useNodeTasksStore((s) => s.criticalPathNodeIds);
  const criticalPathMetrics = useNodeTasksStore((s) => s.criticalPathMetrics);

  const isCritical = showCriticalPath && criticalPathNodeIds.includes(node.id);
  const cpmMetric = showCriticalPath ? criticalPathMetrics[node.id] : undefined;

  const typeConfig = TYPE_CONFIG[node.node_type] || TYPE_CONFIG.task;
  const stageConfig = STAGE_CONFIG[node.stage] || STAGE_CONFIG.ready;
  const IconComponent = typeConfig.icon;

  const isBlocked = node.is_blocked || (node.blockers && node.blockers.length > 0);
  const isRunning = node.stage === 'in_progress' || (node.status as string) === 'in_progress';

  const handleClick = (e: React.MouseEvent) => {
    if (e.shiftKey || e.metaKey || e.ctrlKey) {
      e.stopPropagation();
      const current = selectedNodeIds || [];
      if (current.includes(node.id)) {
        setSelectedNodeIds(current.filter((id) => id !== node.id));
      } else {
        setSelectedNodeIds([...current, node.id]);
      }
    } else {
      setSelectedNodeId(node.id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`relative w-[280px] rounded-xl border bg-gradient-to-b ${typeConfig.bgGradient} p-4 text-xs shadow-xl backdrop-blur-md transition-[border-color,box-shadow,opacity] duration-150 cursor-grab active:cursor-grabbing ${
        isCritical
          ? 'ring-2 ring-rose-500 border-rose-500 shadow-[0_0_24px_rgba(244,63,94,0.45)]'
          : isRunning
          ? 'ring-2 ring-emerald-400 border-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.35)] animate-pulse'
          : selected
          ? 'ring-2 ring-cyan-400 border-cyan-400 shadow-cyan-500/20'
          : typeConfig.border
      } ${isBlocked ? 'border-red-500/70 shadow-red-900/30' : ''} ${
        showCriticalPath && !isCritical ? 'opacity-40 saturate-50 hover:opacity-100 hover:saturate-100' : ''
      }`}
    >
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="!w-3 !h-3 !bg-zinc-700 !border-2 !border-zinc-300 hover:!bg-cyan-400 transition-colors"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="!w-3 !h-3 !bg-zinc-700 !border-2 !border-zinc-300 hover:!bg-cyan-400 transition-colors"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="!w-2.5 !h-2.5 !bg-zinc-700 !border !border-zinc-400 hover:!bg-cyan-400 opacity-60 hover:opacity-100"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="!w-2.5 !h-2.5 !bg-zinc-700 !border !border-zinc-400 hover:!bg-cyan-400 opacity-60 hover:opacity-100"
      />

      {/* Critical Path Header Badge */}
      {showCriticalPath && cpmMetric && (
        <div
          className={`mb-2 px-2 py-1 rounded-md flex items-center justify-between text-[10px] font-mono border ${
            isCritical
              ? 'bg-rose-950/80 border-rose-500/70 text-rose-200'
              : 'bg-zinc-850/80 border-zinc-700 text-zinc-400'
          }`}
        >
          <div className="flex items-center gap-1">
            <Flame className={`w-3 h-3 ${isCritical ? 'text-rose-400 animate-pulse' : 'text-zinc-500'}`} />
            <span className="font-semibold">{isCritical ? 'CRITICAL PATH' : 'NON-CRITICAL'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span>Dur: {cpmMetric.duration_hours}h</span>
            <span>Slack: {cpmMetric.slack}h</span>
          </div>
        </div>
      )}

      {/* Header Row */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <div className={`p-1.5 rounded-lg bg-zinc-800/80 ${typeConfig.color}`}>
            <IconComponent className="w-3.5 h-3.5" />
          </div>
          <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-400">
            {typeConfig.label}
          </span>
        </div>

        {/* Priority Badge */}
        <span
          className={`px-1.5 py-0.5 rounded text-[9px] font-semibold font-mono ${
            node.priority === 'P0_Critical'
              ? 'bg-red-900/60 text-red-300 border border-red-700/50'
              : node.priority === 'P1_High'
              ? 'bg-amber-900/60 text-amber-300 border border-amber-700/50'
              : 'bg-zinc-800 text-zinc-400'
          }`}
        >
          {node.priority.replace('_', ' ')}
        </span>
      </div>

      {/* Title */}
      <h4 className="font-medium text-zinc-100 text-sm leading-snug mb-1 line-clamp-2">
        {node.title}
      </h4>

      {/* Description */}
      {node.description && (
        <p className="text-zinc-400 text-[11px] line-clamp-2 mb-3 leading-relaxed">
          {node.description}
        </p>
      )}

      {/* Blocked Warning Banner */}
      {isBlocked && (
        <div className="mb-2.5 flex items-center gap-1.5 rounded-md bg-red-950/60 border border-red-500/40 px-2 py-1 text-[10px] text-red-300 font-medium">
          <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
          <span className="truncate">
            Blocked by {node.blockers?.length || 1} prerequisite{node.blockers?.length > 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* Progress Bar (if Task, Epic, or Slice) */}
      {node.node_type !== 'idea' && (
        <div className="mb-3">
          <div className="flex justify-between items-center text-[10px] text-zinc-400 mb-1">
            <span>Progress</span>
            <span className="font-mono font-medium text-zinc-300">{node.progress}%</span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                node.progress === 100
                  ? 'bg-emerald-500'
                  : isBlocked
                  ? 'bg-red-500'
                  : 'bg-cyan-500'
              }`}
              style={{ width: `${node.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer Meta Row */}
      <div className="flex items-center justify-between pt-2 border-t border-zinc-800/80 gap-2">
        {/* Stage Pill */}
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${stageConfig.badge}`}
        >
          {stageConfig.label}
        </span>

        {/* Swarm Agent Badge */}
        {node.assigned_agent ? (
          <div className={`flex items-center gap-1.5 text-[10px] px-1.5 py-0.5 rounded max-w-[130px] truncate border ${
            isRunning 
              ? 'bg-emerald-950/80 border-emerald-500/60 text-emerald-300 font-mono' 
              : 'bg-zinc-800/80 border-zinc-700/60 text-zinc-300'
          }`}>
            {isRunning ? (
              <span className="relative flex h-2 w-2 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            ) : (
              <Bot className="w-3 h-3 text-cyan-400 shrink-0" />
            )}
            <span className="truncate">{node.assigned_agent.replace('dnk_', '')}</span>
          </div>
        ) : (
          <span className="text-[10px] text-zinc-500">Unassigned</span>
        )}
      </div>

      {/* Quick Idea Conversion Button */}
      {node.node_type === 'idea' && (
        <div className="mt-2.5 pt-2 border-t border-amber-900/40 flex justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation();
              convertIdea(node.id, 'task');
            }}
            className="nodrag flex items-center gap-1 text-[10px] font-medium text-amber-300 hover:text-amber-200 bg-amber-900/40 hover:bg-amber-900/60 border border-amber-600/40 px-2 py-1 rounded transition-colors"
          >
            <Sparkles className="w-3 h-3" />
            <span>Convert to Task</span>
            <ArrowRight className="w-2.5 h-2.5" />
          </button>
        </div>
      )}
    </div>
  );
});

CustomTaskNode.displayName = 'CustomTaskNode';

// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/canvas/TaskForestNode.tsx"
// purpose: "Interactive Task Forest canvas node with type-specific styling, stage badges, progress bars, and actions."
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
  CheckSquare,
  Lightbulb,
  Target,
  Bug,
  BookOpen,
  ArrowRight,
  Trash2,
  AlertCircle,
  Clock,
  Sparkles,
  Bot,
  Play,
  Loader2,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import {
  TaskNodeData,
  NodeType,
  ExecutionStage,
  Priority,
  useTaskForestStore,
} from '@/store/taskForestStore';

const SWARM_AGENTS = [
  { id: 'gerych_builder', label: 'Builder 🎨', desc: 'UI & React' },
  { id: 'dnk_dev_fullstack', label: 'Backend ⚡', desc: 'FastAPI & DB' },
  { id: 'gerych_researcher', label: 'Researcher 🔍', desc: 'GitHub & SOTA' },
  { id: 'gerych_auditor', label: 'Auditor 🛡️', desc: 'QA & Security' },
  { id: 'dnk_shopify', label: 'Shopify 🛍️', desc: 'Liquid & Theme' },
  { id: 'dnk_video_ai_creator', label: 'Video AI 🎬', desc: 'Remotion Studio' },
  { id: 'herich_librarian', label: 'Librarian 📚', desc: 'Obsidian & ADR' },
];

const TYPE_CONFIG: Record<
  NodeType,
  { label: string; icon: React.ComponentType<{ className?: string }>; color: string; border: string; bg: string }
> = {
  task: {
    label: 'Task',
    icon: CheckSquare,
    color: 'text-blue-400',
    border: 'border-blue-500/40',
    bg: 'bg-blue-950/20',
  },
  idea: {
    label: 'Idea',
    icon: Lightbulb,
    color: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-950/20',
  },
  goal: {
    label: 'Goal',
    icon: Target,
    color: 'text-emerald-400',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-950/20',
  },
  bug: {
    label: 'Bug',
    icon: Bug,
    color: 'text-rose-400',
    border: 'border-rose-500/40',
    bg: 'bg-rose-950/20',
  },
  documentation: {
    label: 'Doc',
    icon: BookOpen,
    color: 'text-purple-400',
    border: 'border-purple-500/40',
    bg: 'bg-purple-950/20',
  },
};

const STAGE_CONFIG: Record<ExecutionStage, { label: string; color: string; bg: string }> = {
  backlog: { label: 'Backlog', color: 'text-slate-400', bg: 'bg-slate-800' },
  planned: { label: 'Planned', color: 'text-indigo-400', bg: 'bg-indigo-950/60' },
  in_progress: { label: 'In Progress', color: 'text-cyan-400', bg: 'bg-cyan-950/60' },
  review: { label: 'Review', color: 'text-amber-400', bg: 'bg-amber-950/60' },
  done: { label: 'Done', color: 'text-emerald-400', bg: 'bg-emerald-950/60' },
};

const PRIORITY_BADGES: Record<Priority, { label: string; color: string }> = {
  low: { label: 'Low', color: 'text-slate-400 border-slate-700' },
  medium: { label: 'Med', color: 'text-blue-400 border-blue-800' },
  high: { label: 'High', color: 'text-amber-400 border-amber-800' },
  critical: { label: 'Crit', color: 'text-rose-400 border-rose-800' },
};

export const TaskForestNode = memo(({ id, data, selected }: NodeProps) => {
  const nodeData = data as unknown as TaskNodeData;
  const deleteNode = useTaskForestStore((s) => s.deleteNode);
  const setNodeStage = useTaskForestStore((s) => s.setNodeStage);
  const setSelectedNodeId = useTaskForestStore((s) => s.setSelectedNodeId);
  const assignAgent = useTaskForestStore((s) => s.assignAgent);
  const dispatchAgent = useTaskForestStore((s) => s.dispatchAgent);

  const [isAssigning, setIsAssigning] = React.useState(false);

  const type = (nodeData.type || 'task') as NodeType;
  const stage = (nodeData.stage || 'backlog') as ExecutionStage;
  const priority = (nodeData.priority || 'medium') as Priority;
  const assignedAgent = nodeData.assignedAgent;
  const agentStatus = nodeData.agentStatus || 'idle';

  const assignedAgentMeta = SWARM_AGENTS.find((a) => a.id === assignedAgent);

  const typeInfo = TYPE_CONFIG[type] || TYPE_CONFIG.task;
  const stageInfo = STAGE_CONFIG[stage] || STAGE_CONFIG.backlog;
  const priorityInfo = PRIORITY_BADGES[priority] || PRIORITY_BADGES.medium;
  const IconComponent = typeInfo.icon;

  // Next stage transition logic
  const getNextStage = (curr: ExecutionStage): ExecutionStage | null => {
    switch (curr) {
      case 'backlog':
        return 'planned';
      case 'planned':
        return 'in_progress';
      case 'in_progress':
        return 'review';
      case 'review':
        return 'done';
      case 'done':
        return null;
    }
  };

  const nextStage = getNextStage(stage);

  const handleAdvanceStage = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (nextStage) {
      setNodeStage(id, nextStage);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteNode(id);
  };

  // Progress calculation for Task or Goal
  let progressPercent: number | null = null;
  if (type === 'task') {
    if (stage === 'done') progressPercent = 100;
    else if (stage === 'review') progressPercent = 85;
    else if (stage === 'in_progress') progressPercent = 50;
    else if (stage === 'planned') progressPercent = 20;
    else progressPercent = 0;
  } else if (type === 'goal') {
    const rawProgress = nodeData.metadata?.progress;
    progressPercent = typeof rawProgress === 'number' ? Math.round(rawProgress * 100) : (stage === 'done' ? 100 : 30);
  }

  return (
    <div
      onClick={() => setSelectedNodeId(id)}
      className={`relative min-w-[240px] max-w-[280px] rounded-xl border bg-slate-900/90 backdrop-blur-md p-3.5 shadow-xl transition-all duration-200 ${
        typeInfo.border
      } ${typeInfo.bg} ${
        selected ? 'ring-2 ring-cyan-400 ring-offset-2 ring-offset-slate-950 scale-[1.02]' : 'hover:border-slate-600'
      }`}
    >
      {/* Input Handle (Dependencies incoming from prerequisite tasks) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-slate-900 transition-colors hover:!bg-cyan-400"
      />

      {/* Header: Type icon + label + stage badge + priority */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <IconComponent className={`w-4 h-4 ${typeInfo.color}`} />
          <span className={`text-xs font-semibold uppercase tracking-wider ${typeInfo.color}`}>
            {typeInfo.label}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${priorityInfo.color}`}>
            {priorityInfo.label}
          </span>
          <span
            className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${stageInfo.bg} ${stageInfo.color}`}
          >
            {stageInfo.label}
          </span>
        </div>
      </div>

      {/* Title */}
      <h4 className="text-sm font-semibold text-slate-100 leading-snug line-clamp-2 mb-1.5">
        {nodeData.title || 'Untitled Node'}
      </h4>

      {/* Description */}
      {nodeData.description && (
        <p className="text-xs text-slate-400 line-clamp-2 mb-2.5">{nodeData.description}</p>
      )}

      {/* Progress Bar (if Task or Goal) */}
      {progressPercent !== null && (
        <div className="mb-2.5">
          <div className="flex justify-between text-[10px] text-slate-400 mb-1">
            <span>Progress</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                progressPercent === 100
                  ? 'bg-emerald-500'
                  : progressPercent > 50
                  ? 'bg-cyan-500'
                  : 'bg-indigo-500'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Tags */}
      {nodeData.tags && nodeData.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2.5">
          {nodeData.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] bg-slate-800/80 text-slate-300 px-1.5 py-0.5 rounded font-mono"
            >
              #{tag}
            </span>
          ))}
          {nodeData.tags.length > 3 && (
            <span className="text-[10px] text-slate-500">+{nodeData.tags.length - 3}</span>
          )}
        </div>
      )}

      {/* Swarm Agent Integration (Variant A) */}
      <div className="mb-2.5 p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Swarm Agent</span>
          </div>

          {assignedAgent && (
            <div className="flex items-center gap-1">
              {agentStatus === 'running' && (
                <span className="flex items-center gap-1 text-[9px] text-cyan-300 font-mono animate-pulse">
                  <Loader2 className="w-2.5 h-2.5 animate-spin" /> running
                </span>
              )}
              {agentStatus === 'completed' && (
                <span className="flex items-center gap-1 text-[9px] text-emerald-400 font-mono">
                  <CheckCircle2 className="w-2.5 h-2.5" /> done
                </span>
              )}
              {agentStatus === 'failed' && (
                <span className="flex items-center gap-1 text-[9px] text-rose-400 font-mono">
                  <AlertCircle className="w-2.5 h-2.5" /> fail
                </span>
              )}
            </div>
          )}
        </div>

        {assignedAgentMeta ? (
          <div className="flex items-center justify-between gap-1.5 mt-0.5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsAssigning(!isAssigning);
              }}
              className="text-left flex-1 text-[11px] font-medium text-slate-200 hover:text-cyan-300 transition-colors truncate"
              title={`${assignedAgentMeta.label} (${assignedAgentMeta.desc})`}
            >
              {assignedAgentMeta.label}
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                dispatchAgent(id);
              }}
              disabled={agentStatus === 'running'}
              className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded transition-all shadow-sm ${
                agentStatus === 'running'
                  ? 'bg-cyan-950 text-cyan-500 cursor-not-allowed border border-cyan-800/50'
                  : 'bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500 hover:text-slate-950 border border-cyan-500/40'
              }`}
              title="Dispatch Swarm Worker"
            >
              <Zap className="w-3 h-3" />
              <span>{agentStatus === 'running' ? 'Running' : 'Dispatch'}</span>
            </button>
          </div>
        ) : (
          <div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsAssigning(!isAssigning);
              }}
              className="w-full text-center py-1 text-[10px] font-medium text-slate-400 hover:text-cyan-300 border border-dashed border-slate-700/80 hover:border-cyan-500/50 rounded transition-colors"
            >
              + Assign Swarm Agent
            </button>
          </div>
        )}

        {/* Quick Assign Popover */}
        {isAssigning && (
          <div
            onClick={(e) => e.stopPropagation()}
            className="mt-1.5 p-1.5 bg-slate-900 border border-slate-700/80 rounded-lg shadow-2xl flex flex-col gap-1 max-h-36 overflow-y-auto"
          >
            {SWARM_AGENTS.map((agent) => (
              <button
                key={agent.id}
                onClick={() => {
                  assignAgent(id, agent.id);
                  setIsAssigning(false);
                }}
                className={`flex items-center justify-between text-left px-2 py-1 rounded text-[10px] transition-colors ${
                  assignedAgent === agent.id
                    ? 'bg-cyan-950/80 text-cyan-300 font-semibold'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <span>{agent.label}</span>
                <span className="text-[9px] text-slate-500">{agent.desc}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Actions footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 mt-1">
        {nextStage ? (
          <button
            onClick={handleAdvanceStage}
            className="flex items-center gap-1 text-[11px] font-medium text-slate-300 hover:text-cyan-300 bg-slate-800/80 hover:bg-slate-800 px-2 py-1 rounded transition-colors"
            title={`Advance to ${STAGE_CONFIG[nextStage].label}`}
          >
            <span>{STAGE_CONFIG[nextStage].label}</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        ) : (
          <span className="text-[10px] text-emerald-400 font-medium flex items-center gap-1">
            ✓ Completed
          </span>
        )}

        <button
          onClick={handleDelete}
          className="text-slate-500 hover:text-rose-400 p-1 rounded hover:bg-rose-950/40 transition-colors"
          title="Delete Node"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Output Handle (Dependent tasks connect to this) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-slate-400 !border-2 !border-slate-900 transition-colors hover:!bg-cyan-400"
      />
    </div>
  );
});

TaskForestNode.displayName = 'TaskForestNode';
export default TaskForestNode;

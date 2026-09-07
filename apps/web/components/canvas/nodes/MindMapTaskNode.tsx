// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_MindMapTaskNode"
// purpose: "Mind Map Task Card (Indigo/Blue card) with interactive status toggle, priority badge, and assignee metadata"
// author: "DNK-e.com Maksym & Antigravity Mentor"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { NodeProps } from '@xyflow/react';
import { CheckSquare, User, AlertCircle, Clock, CheckCircle2 } from 'lucide-react';
import BaseMindMapNode from './BaseMindMapNode';
import { useCanvasStore } from '../../../store/canvasStore';

export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

export interface MindMapTaskData {
  title?: string;
  description?: string;
  task_status?: TaskStatus;
  priority?: TaskPriority;
  assignee?: string;
  [key: string]: any;
}

const PRIORITY_COLORS: Record<TaskPriority, { text: string; bg: string; border: string }> = {
  low: { text: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700' },
  medium: { text: 'text-blue-300', bg: 'bg-blue-950/60', border: 'border-blue-500/30' },
  high: { text: 'text-amber-300', bg: 'bg-amber-950/60', border: 'border-amber-500/30' },
  critical: { text: 'text-red-300', bg: 'bg-red-950/60', border: 'border-red-500/30' },
};

export default function MindMapTaskNode(props: NodeProps) {
  const { id, data } = props;
  const nodeData = (data || {}) as MindMapTaskData;
  const updateNodeData = useCanvasStore((state) => state.updateNodeData);

  const taskStatus = nodeData.task_status || 'todo';
  const priority = nodeData.priority || 'high';
  const assignee = nodeData.assignee || 'Gerych';

  const pStyle = PRIORITY_COLORS[priority] || PRIORITY_COLORS.medium;

  const cycleStatus = () => {
    const next: Record<TaskStatus, TaskStatus> = {
      todo: 'in_progress',
      in_progress: 'done',
      done: 'todo',
    };
    updateNodeData(id, { task_status: next[taskStatus] });
  };

  return (
    <BaseMindMapNode
      {...props}
      themeColor="blue"
      icon={<CheckSquare className="w-4 h-4" />}
      categoryLabel="Task"
    >
      <div className="flex flex-col gap-2">
        {/* Status Toggle & Priority Pill */}
        <div className="flex items-center justify-between">
          <button
            onClick={cycleStatus}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-900 border border-slate-700/80 hover:border-blue-400 text-xs text-slate-200 transition-colors cursor-pointer"
          >
            {taskStatus === 'done' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
            {taskStatus === 'in_progress' && <Clock className="w-3.5 h-3.5 text-blue-400 animate-spin" />}
            {taskStatus === 'todo' && <div className="w-3.5 h-3.5 rounded-sm border border-slate-500" />}
            <span className="font-mono text-[10px] capitalize">
              {taskStatus.replace('_', ' ')}
            </span>
          </button>

          <span
            className={`px-2 py-0.5 rounded text-[10px] font-mono border uppercase tracking-wider ${pStyle.bg} ${pStyle.text} ${pStyle.border}`}
          >
            {priority}
          </span>
        </div>

        {/* Assignee Footer */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-400">
          <div className="flex items-center gap-1">
            <User className="w-3 h-3 text-blue-400" />
            <span>Assignee: <strong className="text-slate-200">{assignee}</strong></span>
          </div>
        </div>
      </div>
    </BaseMindMapNode>
  );
}

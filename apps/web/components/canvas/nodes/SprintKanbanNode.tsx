// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_SprintKanbanNode"
// purpose: "CapCut Sprint Tasks Kanban Note Card (Card 4) with 3 columns (To Do, In Progress, Done), task cards with dates, and assigned collaborator avatars"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Kanban, 
  MoreVertical, 
  Plus, 
  Calendar,
  Clock,
  CheckCircle2
} from 'lucide-react';
import { CopilotToolbar } from '../../../src/canvas/copilot/CopilotToolbar';

interface KanbanTask {
  id: string;
  title: string;
  date: string;
  userAvatar: string;
  userColor: string;
}

export default function SprintKanbanNode({ id, data, selected }: NodeProps) {
  const [todoTasks, setTodoTasks] = useState<KanbanTask[]>([
    { id: '1', title: 'Panel task', date: 'Dec 03', userAvatar: 'AK', userColor: 'bg-emerald-500' },
    { id: '2', title: 'Remastering', date: 'Dec 22', userAvatar: 'MR', userColor: 'bg-pink-500' },
    { id: '3', title: 'Decom today', date: 'Dec 27', userAvatar: 'DS', userColor: 'bg-cyan-500' },
  ]);

  const [inProgressTasks, setInProgressTasks] = useState<KanbanTask[]>([
    { id: '4', title: 'Protections', date: 'Dec 03', userAvatar: 'AK', userColor: 'bg-emerald-500' },
    { id: '5', title: 'Sion span', date: 'Mar 26', userAvatar: 'MR', userColor: 'bg-pink-500' },
  ]);

  const [doneTasks, setDoneTasks] = useState<KanbanTask[]>([
    { id: '6', title: 'Duban tasks', date: 'Mar 03', userAvatar: 'DS', userColor: 'bg-cyan-500' },
  ]);

  useEffect(() => {
    if (data?.tasks) {
      setTodoTasks(data.tasks as KanbanTask[]);
    } else if (data?.injectedTask) {
      const task = data.injectedTask as KanbanTask;
      setTodoTasks((prev) => {
        if (prev.some((t) => t.id === task.id)) return prev;
        return [task, ...prev];
      });
    }
  }, [data?.tasks, data?.injectedTask]);

  return (
    <div className={`w-[360px] rounded-2xl bg-[#121620]/95 backdrop-blur-2xl border border-[#232938] p-4 text-slate-200 shadow-2xl transition-all font-sans ${
      selected ? 'border-amber-500 ring-2 ring-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.25)]' : ''
    }`}>
      {/* 4-Way Smooth Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-amber-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#fbbf24]" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-amber-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#fbbf24]" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-amber-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#fbbf24]" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-amber-400 border-2 border-[#121620] rounded-full shadow-[0_0_8px_#fbbf24]" />

      {/* Header */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#232938]">
        <div className="flex items-center gap-2">
          <Kanban className="w-4 h-4 text-amber-400" />
          <span className="font-bold text-sm text-white">Sprint Tasks</span>
        </div>
        <button className="p-1 rounded text-slate-500 hover:text-white transition-colors cursor-pointer">
          <MoreVertical className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 3-Column Kanban Board Layout */}
      <div className="grid grid-cols-3 gap-2">
        {/* Column 1: To Do */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-semibold text-slate-300 pb-1 border-b border-[#232938]">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              <span>To Do</span>
            </span>
            <span className="text-[9px] text-slate-500 font-mono">{todoTasks.length}</span>
          </div>

          <div className="space-y-1.5">
            {todoTasks.map((t) => (
              <div key={t.id} className="p-2 rounded-xl bg-[#090b10] border border-[#1a1f2c] text-[10px] hover:border-slate-600 transition-colors">
                <span className="font-medium text-slate-200 block truncate mb-1.5">{t.title}</span>
                <div className="flex items-center justify-between">
                  <div className={`w-4 h-4 rounded-full ${t.userColor} text-white font-bold text-[8px] flex items-center justify-center`}>
                    {t.userAvatar}
                  </div>
                  <span className="text-[8px] text-slate-500 font-mono">{t.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 2: In Progress */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-semibold text-amber-300 pb-1 border-b border-[#232938]">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              <span>In Progress</span>
            </span>
            <span className="text-[9px] text-amber-400 font-mono">{inProgressTasks.length}</span>
          </div>

          <div className="space-y-1.5">
            {inProgressTasks.map((t) => (
              <div key={t.id} className="p-2 rounded-xl bg-[#090b10] border border-amber-500/20 text-[10px] hover:border-amber-500/40 transition-colors">
                <span className="font-medium text-slate-200 block truncate mb-1.5">{t.title}</span>
                <div className="flex items-center justify-between">
                  <div className={`w-4 h-4 rounded-full ${t.userColor} text-white font-bold text-[8px] flex items-center justify-center`}>
                    {t.userAvatar}
                  </div>
                  <span className="text-[8px] text-slate-500 font-mono">{t.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 3: Done */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-semibold text-emerald-400 pb-1 border-b border-[#232938]">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Done</span>
            </span>
            <span className="text-[9px] text-emerald-400 font-mono">{doneTasks.length}</span>
          </div>

          <div className="space-y-1.5">
            {doneTasks.map((t) => (
              <div key={t.id} className="p-2 rounded-xl bg-[#090b10] border border-emerald-500/20 text-[10px] hover:border-emerald-500/40 transition-colors">
                <span className="font-medium text-slate-300 block truncate mb-1.5 line-through">{t.title}</span>
                <div className="flex items-center justify-between">
                  <div className={`w-4 h-4 rounded-full ${t.userColor} text-white font-bold text-[8px] flex items-center justify-center`}>
                    {t.userAvatar}
                  </div>
                  <span className="text-[8px] text-slate-500 font-mono">{t.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <CopilotToolbar
        nodeId={id}
        nodeType="SprintKanbanNode"
        defaultAgentId="gerych_builder"
      />
    </div>
  );
}

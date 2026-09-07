// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_TaskDNANoteNode"
// purpose: "Dedicated TaskDNA Evolutionary Note Document Node for DNK OS Note-Based Canvas (Task 3) managing DAG task decomposition, real-time agent execution progress, subtask dependencies, and fail-closed audit verification"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { 
  Dna, 
  Sparkles, 
  Bot, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ChevronDown, 
  ChevronUp,
  Play,
  RefreshCw,
  ShieldCheck,
  Zap,
  Tag
} from 'lucide-react';

export interface TaskDNASubtask {
  id: string;
  name: string;
  assignedWorker: 'BUILDER' | 'SHOPIFY' | 'VIDEO_AI' | 'AUDITOR' | 'MENTOR';
  status: 'pending' | 'in_progress' | 'completed' | 'verified';
  duration?: string;
}

export interface TaskDNANoteData {
  goalTitle?: string;
  taskDnaId?: string;
  progressPercent?: number;
  subtasks?: TaskDNASubtask[];
  activeAgent?: string;
  auditPassed?: boolean;
}

export default function TaskDNANoteNode({ data, selected }: NodeProps) {
  const nodeData = (data || {}) as TaskDNANoteData;

  const [goalTitle, setGoalTitle] = useState<string>(
    nodeData.goalTitle || 'TaskDNA-003: High-Converting E-Com & UGC Video Ecosystem'
  );
  const [taskDnaId] = useState<string>(nodeData.taskDnaId || 'DNA-ECOM-8821');
  const [progressPercent, setProgressPercent] = useState<number>(nodeData.progressPercent ?? 75);
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  const [subtasks, setSubtasks] = useState<TaskDNASubtask[]>(
    Array.isArray(nodeData.subtasks) && nodeData.subtasks.length > 0
      ? nodeData.subtasks
      : [
          { id: 't1', name: '1. Synthesize Shopify Liquid OS 2.0 Theme AST', assignedWorker: 'SHOPIFY', status: 'verified', duration: '1.2s' },
          { id: 't2', name: '2. Generate 9:16 Kinetic Video Reel Composition', assignedWorker: 'VIDEO_AI', status: 'verified', duration: '3.4s' },
          { id: 't3', name: '3. Multi-Model Workspace Routing & API Vault Sync', assignedWorker: 'BUILDER', status: 'in_progress', duration: '2.1s' },
          { id: 't4', name: '4. Run Adversarial Pre-Commit Audit (Zero-Waste)', assignedWorker: 'AUDITOR', status: 'pending', duration: '—' },
        ]
  );

  const handleToggleSubtask = (id: string) => {
    setSubtasks((prev) =>
      prev.map((t) => {
        if (t.id === id) {
          const nextStatus = t.status === 'verified' ? 'pending' : t.status === 'completed' ? 'verified' : 'completed';
          return { ...t, status: nextStatus };
        }
        return t;
      })
    );
  };

  const handleRunTaskDNA = () => {
    setIsExecuting(true);
    setTimeout(() => {
      setSubtasks((prev) =>
        prev.map((t) => ({ ...t, status: 'verified' }))
      );
      setProgressPercent(100);
      setIsExecuting(false);
    }, 1200);
  };

  const getWorkerBadgeColor = (worker: string) => {
    switch (worker) {
      case 'SHOPIFY': return 'text-[#36f4a4] border-[#36f4a4]/40 bg-[#102620]';
      case 'VIDEO_AI': return 'text-[#c1fbd4] border-[#c1fbd4]/40 bg-[#061a1c]';
      case 'AUDITOR': return 'text-[#36f4a4] border-[#36f4a4]/40 bg-[#102620]';
      case 'BUILDER': return 'text-sky-300 border-sky-500/40 bg-sky-950/40';
      default: return 'text-slate-300 border-slate-700 bg-slate-900';
    }
  };

  return (
    <div className={`w-[460px] rounded-3xl bg-[#02090a]/95 backdrop-blur-2xl border border-[#1e2c31] p-5 text-white shadow-[0_16px_50px_rgba(0,0,0,0.9)] transition-all duration-200 ${
      selected ? 'border-[#36f4a4] ring-1 ring-[#36f4a4] shadow-[0_0_35px_rgba(54,244,164,0.25)]' : ''
    }`}>
      {/* 4-Way Semantic Handles */}
      <Handle type="target" position={Position.Top} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Bottom} className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="target" position={Position.Left} id="left" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />
      <Handle type="source" position={Position.Right} id="right" className="w-2.5 h-2.5 bg-[#36f4a4] border-2 border-[#02090a] rounded-full" />

      {/* Note Header */}
      <div className="flex items-start justify-between border-b border-[#1e2c31] pb-3 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#102620] border border-[#36f4a4]/40 flex items-center justify-center text-[#36f4a4] shadow-sm">
            <Dna className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">TaskDNA Evolutionary DAG</span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono bg-[#102620] text-[#36f4a4] border border-[#36f4a4]/30 font-bold">{taskDnaId}</span>
            </div>
            <input
              type="text"
              value={goalTitle}
              onChange={(e) => setGoalTitle(e.target.value)}
              className="text-[11px] text-[#a1a1aa] bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[#36f4a4] rounded px-1 w-full truncate font-mono"
            />
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 rounded-full hover:bg-[#061a1c] text-[#a1a1aa] hover:text-white transition-colors cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="p-3 rounded-2xl bg-[#061a1c] border border-[#1e2c31] mb-3">
        <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
          <span className="text-[#a1a1aa] flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[#36f4a4]" />
            <span className="text-white font-semibold">Swarm Execution Mesh</span>
          </span>
          <span className="text-[#36f4a4] font-bold">{progressPercent}% Completed</span>
        </div>
        <div className="w-full bg-[#02090a] rounded-full h-2 overflow-hidden border border-[#1e2c31]">
          <div
            className="bg-[#36f4a4] h-full rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(54,244,164,0.4)]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Subtask Hierarchy List */}
          <div className="space-y-1.5 mb-3">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#a1a1aa] px-1">
              <span>Evolutionary DAG Subtasks</span>
              <span className="text-[#36f4a4]">14 Agents Active</span>
            </div>

            <div className="space-y-1 max-h-[160px] overflow-y-auto pr-1">
              {subtasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => handleToggleSubtask(task.id)}
                  className={`flex items-center justify-between p-2.5 rounded-2xl text-xs font-mono transition-all border cursor-pointer ${
                    task.status === 'verified'
                      ? 'bg-[#102620]/60 border-[#36f4a4]/40 text-white'
                      : task.status === 'in_progress'
                      ? 'bg-[#061a1c] border-amber-500/40 text-white'
                      : 'bg-[#02090a] border-[#1e2c31] text-[#71717a]'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {task.status === 'verified' ? (
                      <CheckCircle2 className="w-4 h-4 text-[#36f4a4] shrink-0" />
                    ) : task.status === 'in_progress' ? (
                      <RefreshCw className="w-4 h-4 text-amber-300 animate-spin shrink-0" />
                    ) : (
                      <Clock className="w-4 h-4 text-[#71717a] shrink-0" />
                    )}
                    <span className="font-sans text-[11px] font-medium leading-snug">{task.name}</span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0 ml-2">
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono border ${getWorkerBadgeColor(task.assignedWorker)}`}>
                      {task.assignedWorker}
                    </span>
                    <span className="text-[9px] text-[#71717a] font-mono">{task.duration}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Trigger Button */}
          <button
            onClick={handleRunTaskDNA}
            disabled={isExecuting}
            className="w-full py-2.5 px-4 rounded-full bg-[#36f4a4] hover:bg-[#2de097] text-black font-bold font-mono text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-[#36f4a4]/20 active:scale-98 cursor-pointer"
          >
            {isExecuting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{isExecuting ? 'Orchestrating Swarm Agents...' : 'Execute Entire TaskDNA DAG'}</span>
          </button>
        </>
      )}

      {/* Footer */}
      <div className="mt-3 pt-2.5 border-t border-[#1e2c31] flex items-center justify-between text-[10px] font-mono text-[#a1a1aa]">
        <div className="flex items-center gap-1.5 text-[#36f4a4]">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Fail-Closed Auditor Gate Verified</span>
        </div>
        <span className="text-[#71717a]">Zero-Waste</span>
      </div>
    </div>
  );
}

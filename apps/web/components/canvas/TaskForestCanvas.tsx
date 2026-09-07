// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/canvas/TaskForestCanvas.tsx"
// purpose: "Interactive ReactFlow canvas for Task Forest visualization with stage filters, type filters, and quick creation."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  BackgroundVariant,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  CheckSquare,
  Lightbulb,
  Target,
  Bug,
  BookOpen,
  Plus,
  RefreshCw,
  Filter,
  Layers,
  Sparkles,
  Bot,
  Zap,
} from 'lucide-react';

import {
  useTaskForestStore,
  NodeType,
  ExecutionStage,
  TaskNodeData,
} from '@/store/taskForestStore';
import { TaskForestNode } from './TaskForestNode';

const nodeTypes = {
  taskForestNode: TaskForestNode,
};

export default function TaskForestCanvas() {
  const nodes = useTaskForestStore((s) => s.nodes);
  const edges = useTaskForestStore((s) => s.edges);
  const onNodesChange = useTaskForestStore((s) => s.onNodesChange);
  const onEdgesChange = useTaskForestStore((s) => s.onEdgesChange);
  const onConnect = useTaskForestStore((s) => s.onConnect);
  const addNode = useTaskForestStore((s) => s.addNode);
  const loadFromTaskDNA = useTaskForestStore((s) => s.loadFromTaskDNA);

  const [selectedTypeFilter, setSelectedTypeFilter] = useState<NodeType | 'all'>('all');
  const [selectedStageFilter, setSelectedStageFilter] = useState<ExecutionStage | 'all'>('all');
  const [isSyncing, setIsSyncing] = useState(false);
  const [isGeneratingDNA, setIsGeneratingDNA] = useState(false);

  // Filter nodes according to type and stage filters
  const filteredNodes = useMemo(() => {
    if (!Array.isArray(nodes)) return [];
    return nodes.map((node) => {
      const data = (node?.data || {}) as unknown as TaskNodeData;
      const matchesType = selectedTypeFilter === 'all' || data.type === selectedTypeFilter;
      const matchesStage = selectedStageFilter === 'all' || data.stage === selectedStageFilter;
      const isVisible = matchesType && matchesStage;

      return {
        ...node,
        hidden: !isVisible,
      };
    });
  }, [nodes, selectedTypeFilter, selectedStageFilter]);

  // Quick addition handler
  const handleQuickAdd = useCallback(
    (type: NodeType) => {
      const offset = (nodes?.length || 0) * 30;
      const x = 150 + (offset % 400);
      const y = 100 + (offset % 300);
      addNode(type, { x, y });
    },
    [nodes?.length, addNode]
  );

  // Sync with Obsidian / Backend
  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch('/api/task-forest/sync', { method: 'POST' });
      if (res.ok) {
        console.log('Task Forest successfully synced with Obsidian Vault');
      }
    } catch (e) {
      console.warn('Sync notice:', e);
    } finally {
      setTimeout(() => setIsSyncing(false), 600);
    }
  };

  // Generate / Import TaskDNA DAG handler
  const handleGenerateTaskDNA = async () => {
    const goal = window.prompt(
      'Enter Goal or Feature request for Autonomous Swarm TaskDNA:',
      'Autonomous Swarm Integration for Task Forest'
    );
    if (!goal) return;

    setIsGeneratingDNA(true);
    try {
      const res = await fetch('/api/task-dna/decompose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, workspace_id: 'ws-alpha-001' }),
      });

      if (res.ok) {
        const data = await res.json();
        loadFromTaskDNA(data);
      } else {
        // Fallback: Generate structured Swarm DAG client-side
        loadFromTaskDNA({
          task_id: `dna-${Date.now()}`,
          goal,
          dag_tree: [
            {
              id: `dna-task-1`,
              title: `Architect: ${goal}`,
              assigned_agent: 'gerych_researcher',
              dependencies: [],
              risk_level: 'low',
            },
            {
              id: `dna-task-2`,
              title: `Implementation & Fullstack Engine`,
              assigned_agent: 'dnk_dev_fullstack',
              dependencies: [`dna-task-1`],
              risk_level: 'medium',
            },
            {
              id: `dna-task-3`,
              title: `UI Canvas & Spatial Node Components`,
              assigned_agent: 'gerych_builder',
              dependencies: [`dna-task-2`],
              risk_level: 'medium',
            },
            {
              id: `dna-task-4`,
              title: `Adversarial Gate & Security Audit`,
              assigned_agent: 'gerych_auditor',
              dependencies: [`dna-task-3`],
              risk_level: 'high',
            },
          ],
        });
      }
    } catch {
      // Fallback fallback
      loadFromTaskDNA({
        task_id: `dna-${Date.now()}`,
        goal,
        dag_tree: [
          {
            id: `dna-task-1`,
            title: `Plan: ${goal}`,
            assigned_agent: 'gerych_researcher',
            dependencies: [],
            risk_level: 'low',
          },
          {
            id: `dna-task-2`,
            title: `Builder Execution`,
            assigned_agent: 'gerych_builder',
            dependencies: [`dna-task-1`],
            risk_level: 'medium',
          },
        ],
      });
    } finally {
      setIsGeneratingDNA(false);
    }
  };

  // Metrics
  const stats = useMemo(() => {
    let total = nodes.length;
    let inProgress = 0;
    let done = 0;
    let backlog = 0;

    nodes.forEach((n) => {
      const s = (n.data as unknown as TaskNodeData)?.stage;
      if (s === 'done') done++;
      else if (s === 'in_progress') inProgress++;
      else if (s === 'backlog') backlog++;
    });

    return { total, inProgress, done, backlog };
  }, [nodes]);

  return (
    <div className="relative w-full h-full min-h-[650px] bg-slate-950 text-slate-100 font-sans overflow-hidden border border-slate-800 rounded-xl shadow-2xl">
      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-slate-950"
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
        <Controls className="!bg-slate-900 !border-slate-800 !fill-slate-200 shadow-lg" />
        <MiniMap
          nodeStrokeWidth={3}
          nodeColor={(node: Node) => {
            const type = (node.data as unknown as TaskNodeData)?.type;
            switch (type) {
              case 'task':
                return '#3b82f6';
              case 'idea':
                return '#f59e0b';
              case 'goal':
                return '#10b981';
              case 'bug':
                return '#f43f5e';
              case 'documentation':
                return '#a855f7';
              default:
                return '#64748b';
            }
          }}
          className="!bg-slate-900/90 !border-slate-800 rounded-lg shadow-xl"
        />

        {/* Top Control Bar */}
        <Panel position="top-left" className="m-3 flex flex-wrap items-center gap-3">
          {/* Quick Create Group */}
          <div className="flex items-center gap-1 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1.5 rounded-lg shadow-lg">
            <span className="text-xs text-slate-400 font-medium px-2 flex items-center gap-1">
              <Plus className="w-3.5 h-3.5" /> Add:
            </span>
            <button
              onClick={() => handleQuickAdd('task')}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-blue-950/60 text-blue-300 border border-blue-500/30 hover:bg-blue-900/60 transition-colors"
            >
              <CheckSquare className="w-3.5 h-3.5" /> Task
            </button>
            <button
              onClick={() => handleQuickAdd('idea')}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-amber-950/60 text-amber-300 border border-amber-500/30 hover:bg-amber-900/60 transition-colors"
            >
              <Lightbulb className="w-3.5 h-3.5" /> Idea
            </button>
            <button
              onClick={() => handleQuickAdd('goal')}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-900/60 transition-colors"
            >
              <Target className="w-3.5 h-3.5" /> Goal
            </button>
            <button
              onClick={() => handleQuickAdd('bug')}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-rose-950/60 text-rose-300 border border-rose-500/30 hover:bg-rose-900/60 transition-colors"
            >
              <Bug className="w-3.5 h-3.5" /> Bug
            </button>
            <button
              onClick={() => handleQuickAdd('documentation')}
              className="flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-purple-950/60 text-purple-300 border border-purple-500/30 hover:bg-purple-900/60 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" /> Doc
            </button>
          </div>

          {/* Sync Button */}
          <button
            onClick={handleSync}
            disabled={isSyncing}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg bg-slate-900/90 backdrop-blur-md border border-slate-800 text-slate-200 hover:text-cyan-300 hover:border-slate-700 shadow-lg transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-cyan-400' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Obsidian'}</span>
          </button>

          {/* Import / Decompose TaskDNA */}
          <button
            onClick={handleGenerateTaskDNA}
            disabled={isGeneratingDNA}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg bg-cyan-950/80 backdrop-blur-md border border-cyan-500/40 text-cyan-300 hover:bg-cyan-900/80 hover:text-cyan-200 shadow-lg transition-all"
            title="Decompose Goal into Swarm DAG"
          >
            <Bot className={`w-3.5 h-3.5 ${isGeneratingDNA ? 'animate-pulse text-cyan-400' : ''}`} />
            <span>{isGeneratingDNA ? 'Decomposing...' : 'Import TaskDNA'}</span>
          </button>
        </Panel>

        {/* Top Right: Filters & Metrics */}
        <Panel position="top-right" className="m-3 flex items-center gap-3">
          {/* Metrics Pill */}
          <div className="flex items-center gap-2 bg-slate-900/90 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-xs shadow-lg">
            <span className="text-slate-400">Total: <strong className="text-slate-200">{stats.total}</strong></span>
            <span className="text-slate-700">•</span>
            <span className="text-cyan-400">Active: <strong>{stats.inProgress}</strong></span>
            <span className="text-slate-700">•</span>
            <span className="text-emerald-400">Done: <strong>{stats.done}</strong></span>
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-1 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1 rounded-lg shadow-lg">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            <select
              value={selectedTypeFilter}
              onChange={(e) => setSelectedTypeFilter(e.target.value as NodeType | 'all')}
              className="bg-transparent text-xs text-slate-200 border-none focus:outline-none pr-1 py-1 cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">All Types</option>
              <option value="task" className="bg-slate-900 text-blue-300">Task</option>
              <option value="idea" className="bg-slate-900 text-amber-300">Idea</option>
              <option value="goal" className="bg-slate-900 text-emerald-300">Goal</option>
              <option value="bug" className="bg-slate-900 text-rose-300">Bug</option>
              <option value="documentation" className="bg-slate-900 text-purple-300">Doc</option>
            </select>
          </div>

          {/* Stage Filter */}
          <div className="flex items-center gap-1 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1 rounded-lg shadow-lg">
            <Layers className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            <select
              value={selectedStageFilter}
              onChange={(e) => setSelectedStageFilter(e.target.value as ExecutionStage | 'all')}
              className="bg-transparent text-xs text-slate-200 border-none focus:outline-none pr-1 py-1 cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-slate-200">All Stages</option>
              <option value="backlog" className="bg-slate-900 text-slate-300">Backlog</option>
              <option value="planned" className="bg-slate-900 text-indigo-300">Planned</option>
              <option value="in_progress" className="bg-slate-900 text-cyan-300">In Progress</option>
              <option value="review" className="bg-slate-900 text-amber-300">Review</option>
              <option value="done" className="bg-slate-900 text-emerald-300">Done</option>
            </select>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

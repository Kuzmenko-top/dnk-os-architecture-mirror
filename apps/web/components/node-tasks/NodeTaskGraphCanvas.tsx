// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx"
// purpose: "Visual ReactFlow DAG Canvas for Node Based Tasks & Ideas System in DNK OS"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useEffect, useCallback, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  Connection,
  Edge,
  Node,
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  SelectionMode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Plus,
  Link2,
  LayoutGrid,
  RefreshCw,
  FileText,
  Search,
  Filter,
  AlertTriangle,
  Sparkles,
  Wand2,
  Layers,
  CheckCircle2,
  XCircle,
  Bot,
  Flame,
} from 'lucide-react';

import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { CustomTaskNode } from './CustomTaskNode';
import { CustomDependencyEdge } from './CustomDependencyEdge';
import { NodeTaskDetailDrawer } from './NodeTaskDetailDrawer';
import { CreateNodeModal } from './CreateNodeModal';
import { CreateEdgeModal } from './CreateEdgeModal';
import { CanvasBatchOperationsDock } from './CanvasBatchOperationsDock';
import { GerychTaskPromptDock } from './GerychTaskPromptDock';
import { GerychTaskChatDrawer } from './GerychTaskChatDrawer';
import { ProjectSwitcherDropdown } from './ProjectSwitcherDropdown';
import { NodeType, ExecutionStage } from '@/types/nodeTasks';

const nodeTypes = {
  taskNode: CustomTaskNode,
};

const edgeTypes = {
  customDependency: CustomDependencyEdge,
};

function CanvasInner() {
  const { fitView } = useReactFlow();
  const isChatOpen = useNodeTasksStore((s) => s.isChatOpen);
  const setIsChatOpen = useNodeTasksStore((s) => s.setIsChatOpen);

  const rfNodes = useNodeTasksStore((s) => s.rfNodes);
  const rfEdges = useNodeTasksStore((s) => s.rfEdges);
  const onNodesChange = useNodeTasksStore((s) => s.onNodesChange);
  const onEdgesChange = useNodeTasksStore((s) => s.onEdgesChange);
  const saveNodePosition = useNodeTasksStore((s) => s.saveNodePosition);
  const fetchGraph = useNodeTasksStore((s) => s.fetchGraph);
  const fetchProjects = useNodeTasksStore((s) => s.fetchProjects);
  const createEdge = useNodeTasksStore((s) => s.createEdge);
  const autoLayoutDAG = useNodeTasksStore((s) => s.autoLayoutDAG);
  const syncObsidianBidirectional = useNodeTasksStore((s) => s.syncObsidianBidirectional);
  const resetBaseline = useNodeTasksStore((s) => s.resetBaseline);

  const stats = useNodeTasksStore((s) => s.stats);
  const isLoading = useNodeTasksStore((s) => s.isLoading);
  const isSyncing = useNodeTasksStore((s) => s.isSyncing);
  const isResetting = useNodeTasksStore((s) => s.isResetting);
  const selectedNodeIds = useNodeTasksStore((s) => s.selectedNodeIds);
  const setSelectedNodeIds = useNodeTasksStore((s) => s.setSelectedNodeIds);
  const setSelectedNodeId = useNodeTasksStore((s) => s.setSelectedNodeId);

  // Filters
  const filterType = useNodeTasksStore((s) => s.filterType);
  const setFilterType = useNodeTasksStore((s) => s.setFilterType);
  const filterStage = useNodeTasksStore((s) => s.filterStage);
  const setFilterStage = useNodeTasksStore((s) => s.setFilterStage);
  const filterAgent = useNodeTasksStore((s) => s.filterAgent);
  const setFilterAgent = useNodeTasksStore((s) => s.setFilterAgent);
  const searchQuery = useNodeTasksStore((s) => s.searchQuery);
  const setSearchQuery = useNodeTasksStore((s) => s.setSearchQuery);

  const initWebSocket = useNodeTasksStore((s) => s.initWebSocket);
  const wsConnected = useNodeTasksStore((s) => s.wsConnected);

  const setCreateNodeModalOpen = useNodeTasksStore((s) => s.setCreateNodeModalOpen);
  const setCreateEdgeModalOpen = useNodeTasksStore((s) => s.setCreateEdgeModalOpen);

  const showCriticalPath = useNodeTasksStore((s) => s.showCriticalPath);
  const setShowCriticalPath = useNodeTasksStore((s) => s.setShowCriticalPath);
  const criticalPathTotalDuration = useNodeTasksStore((s) => s.criticalPathTotalDuration);
  const criticalPathBottlenecks = useNodeTasksStore((s) => s.criticalPathBottlenecks);
  const criticalPathNodeIds = useNodeTasksStore((s) => s.criticalPathNodeIds);

  useEffect(() => {
    fetchProjects();
    fetchGraph().then(() => {
      setTimeout(() => fitView({ padding: 0.2 }), 100);
    });
    const cleanupWs = initWebSocket();
    return () => {
      cleanupWs();
    };
  }, [fetchProjects, fetchGraph, fitView, initWebSocket]);

  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [isLayingOut, setIsLayingOut] = useState(false);

  const showToast = useCallback((text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => {
      setToastMessage((prev) => (prev?.text === text ? null : prev));
    }, 4000);
  }, []);

  const isValidConnection = useCallback(
    (connection: Connection | Edge) => {
      if (!connection.source || !connection.target) return false;
      if (connection.source === connection.target) return false;
      const visited = new Set<string>();
      const queue = [connection.target];
      while (queue.length > 0) {
        const curr = queue.shift()!;
        if (curr === connection.source) return false;
        visited.add(curr);
        for (const edge of rfEdges) {
          if (edge.source === curr && !visited.has(edge.target)) {
            queue.push(edge.target);
          }
        }
      }
      return true;
    },
    [rfEdges]
  );

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      if (connection.source === connection.target) {
        showToast('Неможливо створити залежність вузла на самого себе', 'error');
        return;
      }
      if (!isValidConnection(connection)) {
        showToast('Помилка: цей зв’язок утворює циклічну залежність у графі (DAG Cycle)', 'error');
        return;
      }
      const success = await createEdge(connection.source, connection.target, 'depends_on');
      if (success) {
        showToast(`Зв'язок створено: ${connection.source} ➔ ${connection.target}`, 'success');
      } else {
        const err = useNodeTasksStore.getState().error;
        showToast(err || 'Не вдалося створити зв’язок', 'error');
      }
    },
    [createEdge, isValidConnection, showToast]
  );

  const handleNodeDragStop = useCallback(
    (_event: unknown, node: Node) => {
      saveNodePosition(node.id, Math.round(node.position.x), Math.round(node.position.y));
    },
    [saveNodePosition]
  );

  const handleAutoLayout = async () => {
    setIsLayingOut(true);
    try {
      const res = await autoLayoutDAG();
      setTimeout(() => fitView({ duration: 500, padding: 0.2 }), 50);
      showToast(`✨ Топологію графа впорядковано (${res?.count ?? 0} вузлів) та збережено!`, 'success');
    } catch {
      showToast('Помилка при автовирівнюванні графа', 'error');
    } finally {
      setIsLayingOut(false);
    }
  };

  const handleSyncObsidian = async () => {
    try {
      const res = await syncObsidianBidirectional();
      if (res.success) {
        showToast(`🔄 Двостороння синхронізація: ${res.imported ?? 0} нових, ${res.updated ?? 0} оновлено, ${res.exported ?? 0} експортовано!`, 'success');
      } else {
        showToast('Помилка при синхронізації з Obsidian Vault', 'error');
      }
    } catch {
      showToast('Помилка при синхронізації з Obsidian Vault', 'error');
    }
  };

  const handleResetBaseline = async () => {
    if (confirm('Reset graph back to DNK OS Core MVP baseline? All changes will be restored to initial seed.')) {
      await resetBaseline();
      setTimeout(() => fitView({ duration: 500, padding: 0.2 }), 100);
      showToast('✨ Граф успішно відновлено до чистого стану DNK OS MVP!', 'success');
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-64px)] bg-zinc-950 overflow-hidden flex flex-col">
      {/* Top Bar: Stats & Controls */}
      <header className="z-20 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-md px-6 py-3 flex flex-col gap-3">
        {/* Row 1: Metrics & Global Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-bold text-zinc-100 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              Node-Based Task & Ideas DAG
            </h1>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                wsConnected
                  ? 'bg-emerald-950/60 border-emerald-700/60 text-emerald-300'
                  : 'bg-amber-950/60 border-amber-700/60 text-amber-300'
              }`}
            >
              {wsConnected ? '● Live WS' : '○ Connecting...'}
            </span>

            {/* Multi-Tenant Project Switcher */}
            <ProjectSwitcherDropdown />

            {/* Quick Metrics */}
            {stats && (
              <div className="hidden lg:flex items-center gap-2 ml-4">
                <span className="px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-[11px] text-zinc-300">
                  Total: <b className="text-zinc-100">{stats.total_nodes ?? 0}</b>
                </span>
                <span className="px-2 py-0.5 rounded-full bg-amber-950/60 border border-amber-800/60 text-[11px] text-amber-300">
                  Ideas: <b>{stats.ideas_count ?? stats.by_type?.idea ?? 0}</b>
                </span>
                <span className="px-2 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-[11px] text-cyan-300">
                  Tasks: <b>{stats.tasks_count ?? stats.by_type?.task ?? 0}</b>
                </span>
                <span className="px-2 py-0.5 rounded-full bg-purple-950/60 border border-purple-800/60 text-[11px] text-purple-300">
                  Epics: <b>{stats.epics_count ?? stats.by_type?.epic ?? 0}</b>
                </span>
                {(stats.blocked_nodes_count ?? stats.blocked_count ?? 0) > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-red-950/80 border border-red-700/80 text-[11px] text-red-300 flex items-center gap-1 font-semibold animate-pulse">
                    <AlertTriangle className="w-3 h-3" />
                    Blocked: {stats.blocked_nodes_count ?? stats.blocked_count ?? 0}
                  </span>
                )}
                <span className="px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-[11px] text-emerald-300">
                  Progress: <b>{stats.overall_progress_pct ?? stats.overall_progress ?? 0}%</b>
                </span>
              </div>
            )}
          </div>

          {/* Action Toolbar */}
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm ${
                isChatOpen
                  ? 'bg-[#33EE75] text-black border-[#33EE75] shadow-[0_0_15px_rgba(51,238,117,0.4)]'
                  : 'bg-[#12141c] hover:bg-[#1a1d28] border-white/10 text-emerald-400 hover:border-[#33EE75]/40'
              }`}
              title="Відкрити чат з Геричем для створення задач"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Чат з Геричем</span>
            </button>

            <button
              onClick={handleAutoLayout}
              disabled={isLayingOut}
              className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title="Впорядкувати топологію DAG зліва направо за рівнями залежностей та зберегти позиції"
            >
              <Wand2 className={`w-3.5 h-3.5 text-cyan-400 ${isLayingOut ? 'animate-spin' : ''}`} />
              <span>{isLayingOut ? 'Впорядкування...' : '🪄 Auto-Layout'}</span>
            </button>

            <button
              onClick={() => setShowCriticalPath(!showCriticalPath)}
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition-all ${
                showCriticalPath
                  ? 'bg-rose-950/80 border-rose-500 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.35)]'
                  : 'bg-zinc-900 hover:bg-zinc-800 border-zinc-800 text-zinc-300'
              }`}
              title="Розрахувати та виділити критичний шлях (CPM), тривалість та блокуючі вузькі місця"
            >
              <Flame className={`w-3.5 h-3.5 ${showCriticalPath ? 'text-rose-400 animate-pulse' : 'text-zinc-400'}`} />
              <span>{showCriticalPath ? `🔥 CPM (${criticalPathTotalDuration}h)` : '🔥 Критичний шлях'}</span>
              {showCriticalPath && criticalPathBottlenecks.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-rose-500/30 text-rose-300 border border-rose-500/50 text-[10px]">
                  {criticalPathBottlenecks.length} блокерів
                </span>
              )}
            </button>

            <button
              onClick={handleSyncObsidian}
              disabled={isSyncing}
              className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title="Повна двостороння синхронізація між DAG-канвасом та Obsidian Vault"
            >
              <FileText className={`w-3.5 h-3.5 text-purple-400 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Синхронізація...' : '🔄 2-Way Sync'}</span>
            </button>

            <button
              onClick={handleResetBaseline}
              disabled={isResetting}
              className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
              title="Reset baseline graph to initial seed"
            >
              <RefreshCw className="w-3.5 h-3.5 text-zinc-400" />
              <span>Reset</span>
            </button>

            <button
              onClick={() => setCreateEdgeModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Link2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Link Dependency</span>
            </button>

            <button
              onClick={() => setCreateNodeModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-cyan-900/30"
            >
              <Plus className="w-4 h-4" />
              <span>New Node</span>
            </button>
          </div>
        </div>

        {/* Row 2: Search & Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-zinc-850">
          {/* Search box */}
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search nodes, tags, agents..."
              className="w-full bg-zinc-900/90 border border-zinc-800 rounded-lg pl-8 pr-3 py-1 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          {/* Type filters */}
          <div className="flex items-center gap-1 overflow-x-auto">
            {(['all', 'idea', 'task', 'epic', 'slice', 'gate'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  filterType === t
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                    : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800 hover:text-zinc-200'
                }`}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Stage filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-zinc-500" />
            <select
              value={filterStage}
              onChange={(e) => setFilterStage(e.target.value as ExecutionStage | 'all')}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1 text-xs text-zinc-300 focus:outline-none focus:border-cyan-400"
            >
              <option value="all">All Stages</option>
              <option value="ideation">Ideation</option>
              <option value="architecture">Architecture</option>
              <option value="ready">Ready</option>
              <option value="in_progress">In Progress</option>
              <option value="testing">Testing</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      </header>

      {/* ReactFlow Canvas */}
      <div className="flex-1 w-full h-full relative">
        {/* CPM Insights Banner */}
        {showCriticalPath && (
          <div className="absolute top-4 left-6 z-20 flex items-center gap-3 px-3.5 py-2 rounded-xl bg-zinc-950/90 border border-rose-500/50 backdrop-blur-md shadow-[0_0_25px_rgba(244,63,94,0.2)] text-xs animate-in fade-in slide-in-from-top-1">
            <div className="flex items-center gap-1.5 text-rose-400 font-semibold font-mono">
              <Flame className="w-4 h-4 animate-pulse" />
              <span>CPM АНАЛІЗ:</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-300 font-mono text-[11px]">
              <span className="bg-zinc-900/90 px-2 py-0.5 rounded border border-zinc-800">
                Загальний час: <strong className="text-rose-300">{criticalPathTotalDuration} год</strong>
              </span>
              <span className="bg-zinc-900/90 px-2 py-0.5 rounded border border-zinc-800">
                Критичних задач: <strong className="text-rose-300">{criticalPathNodeIds.length}</strong>
              </span>
              {criticalPathBottlenecks.length > 0 && (
                <span className="bg-zinc-900/90 px-2 py-0.5 rounded border border-zinc-800 text-amber-300">
                  Головний блокер: <strong className="text-amber-200">{criticalPathBottlenecks[0].title}</strong> ({criticalPathBottlenecks[0].blocking_count} залежностей)
                </span>
              )}
            </div>
          </div>
        )}

        {toastMessage && (
          <div
            className={`absolute top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl border shadow-2xl backdrop-blur-md flex items-center gap-2.5 text-xs font-medium transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
              toastMessage.type === 'success'
                ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300 shadow-[0_0_25px_rgba(16,185,129,0.2)]'
                : 'bg-red-950/80 border-red-500/40 text-red-300 shadow-[0_0_25px_rgba(239,68,68,0.2)]'
            }`}
          >
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-red-400 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        )}

        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeDragStop={handleNodeDragStop}
          nodesDraggable={true}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          selectionMode={SelectionMode.Partial}
          selectionKeyCode="Shift"
          multiSelectionKeyCode={['Shift', 'Meta', 'Control']}
          onPaneClick={() => {
            setSelectedNodeIds([]);
            setSelectedNodeId(null);
          }}
          fitView
          minZoom={0.2}
          maxZoom={1.5}
          className="bg-zinc-950"
        >
          <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#27272a" />
          <Controls className="!bg-zinc-900 !border-zinc-800 !fill-zinc-300 !text-zinc-300" />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as { node_type?: NodeType };
              switch (data?.node_type) {
                case 'idea':
                  return '#f59e0b';
                case 'epic':
                  return '#a855f7';
                case 'task':
                  return '#06b6d4';
                case 'slice':
                  return '#10b981';
                case 'gate':
                  return '#f43f5e';
                default:
                  return '#71717a';
              }
            }}
            className="!bg-zinc-950/90 !border-zinc-800"
          />
        </ReactFlow>

        {/* CapCut & Stitch Status Badge */}
        <div className="absolute bottom-6 left-6 z-20 hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#12141c]/90 border border-white/10 backdrop-blur-md text-[11px] text-zinc-300 shadow-xl pointer-events-auto">
          <span className="w-2 h-2 rounded-full bg-[#33EE75] animate-pulse" />
          <span className="font-semibold text-white">Gerych Prime</span>
          <span className="text-zinc-600">|</span>
          <span className="text-emerald-400 font-mono">Task Intake Ready</span>
        </div>

        {/* Canvas Multi-Selection & Batch Operations Dock */}
        <CanvasBatchOperationsDock />

        {/* Google Stitch & CapCut Floating Prompt Dock */}
        <GerychTaskPromptDock />

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-30">
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-xs text-cyan-300 font-mono">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Loading Node Graph...</span>
            </div>
          </div>
        )}
      </div>

      {/* Slide-over Gerych Chat drawer */}
      <GerychTaskChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

      {/* Slide-over details drawer */}
      <NodeTaskDetailDrawer />

      {/* Modals */}
      <CreateNodeModal />
      <CreateEdgeModal />
    </div>
  );
}

export function NodeTaskGraphCanvas() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  );
}

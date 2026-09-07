// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/NodeTaskDetailDrawer.tsx"
// purpose: "Detail drawer for inspecting, transitioning, and executing Swarm Agents on Node Tasks"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Play,
  Sparkles,
  AlertTriangle,
  Trash2,
  ExternalLink,
  Bot,
  CheckCircle2,
  Clock,
  Layers,
  FileCode,
  Tag,
  Sliders,
  Send,
  Loader2,
  Terminal,
  RefreshCw,
  Film,
} from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { ExecutionStage, NodeType, PriorityLevel } from '@/types/nodeTasks';
import { NodeTaskArtifactDiffViewer } from './NodeTaskArtifactDiffViewer';
import { NodeTaskMarketingVideoViewer } from './NodeTaskMarketingVideoViewer';

const ALL_STAGES: ExecutionStage[] = [
  'ideation',
  'architecture',
  'ready',
  'in_progress',
  'testing',
  'completed',
];

const SWARM_AGENTS = [
  'dnk_dev_fullstack',
  'gerych_builder',
  'dnk_video_ai_creator',
  'dnk_shopify',
  'dnk_scones_memory',
  'gerych_auditor',
  'herich_librarian',
];

export function NodeTaskDetailDrawer() {
  const selectedNodeId = useNodeTasksStore((s) => s.selectedNodeId);
  const setSelectedNodeId = useNodeTasksStore((s) => s.setSelectedNodeId);
  const nodesMap = useNodeTasksStore((s) => s.nodesMap);
  const edgesList = useNodeTasksStore((s) => s.edgesList);
  const stageTransition = useNodeTasksStore((s) => s.stageTransition);
  const convertIdea = useNodeTasksStore((s) => s.convertIdea);
  const executeAgent = useNodeTasksStore((s) => s.executeAgent);
  const decomposeNode = useNodeTasksStore((s) => s.decomposeNode);
  const deleteNode = useNodeTasksStore((s) => s.deleteNode);
  const deleteEdge = useNodeTasksStore((s) => s.deleteEdge);
  const createOrUpdateNode = useNodeTasksStore((s) => s.createOrUpdateNode);
  const isAgentRunning = useNodeTasksStore((s) => s.isAgentRunning);
  const agentFeedback = useNodeTasksStore((s) => s.agentFeedback);
  const nodeLogs = useNodeTasksStore((s) => s.nodeLogs);
  const nodeArtifacts = useNodeTasksStore((s) => s.nodeArtifacts);
  const marketingVideos = useNodeTasksStore((s) => s.marketingVideos);
  const fetchNodeLogs = useNodeTasksStore((s) => s.fetchNodeLogs);
  const setCreateEdgeModalOpen = useNodeTasksStore((s) => s.setCreateEdgeModalOpen);

  const [activeTab, setActiveTab] = useState<'overview' | 'terminal' | 'diff' | 'video'>('overview');
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [showForceTransition, setShowForceTransition] = useState(false);
  const [pendingTargetStage, setPendingTargetStage] = useState<ExecutionStage | null>(null);
  const [isDecomposing, setIsDecomposing] = useState(false);
  const [decomposeFeedback, setDecomposeFeedback] = useState<string | null>(null);

  const [agentInstructions, setAgentInstructions] = useState('');
  const [agentMode, setAgentMode] = useState<'simulation' | 'autonomous_subagent' | 'auto_complete'>('simulation');

  const [ideaConvertType, setIdeaConvertType] = useState<NodeType>('task');
  const [ideaConvertAgent, setIdeaConvertAgent] = useState('dnk_dev_fullstack');

  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedNodeId) {
      fetchNodeLogs(selectedNodeId);
    }
  }, [selectedNodeId, fetchNodeLogs]);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [nodeLogs, selectedNodeId]);

  if (!selectedNodeId || !nodesMap[selectedNodeId]) {
    return null;
  }

  const node = nodesMap[selectedNodeId];

  // Dependencies calculations
  const incomingDependencies = edgesList.filter((e) => e.target === node.id);
  const outgoingDependencies = edgesList.filter((e) => e.source === node.id);

  const handleStageClick = async (targetStage: ExecutionStage, force = false) => {
    setTransitionError(null);
    setShowForceTransition(false);
    const res = await stageTransition(node.id, targetStage, force);
    if (!res.success) {
      setTransitionError(res.detail || 'Stage transition rejected.');
      setShowForceTransition(true);
      setPendingTargetStage(targetStage);
    }
  };

  const handleAgentExecute = async () => {
    await executeAgent(node.id, agentMode, agentInstructions);
  };

  const handleDecompose = async () => {
    setIsDecomposing(true);
    setDecomposeFeedback(null);
    const res = await decomposeNode(node.id, agentInstructions);
    setIsDecomposing(false);
    if (res.success) {
      setDecomposeFeedback(`✅ Успішно декомпозовано на ${res.createdCount ?? 3} підзадач рою!`);
      setTimeout(() => setDecomposeFeedback(null), 5000);
    } else {
      setDecomposeFeedback(`❌ ${res.message || 'Помилка декомпозиції'}`);
    }
  };

  const handleProgressChange = (newProgress: number) => {
    createOrUpdateNode({
      ...node,
      progress: newProgress,
      stage: newProgress === 100 ? 'completed' : node.stage,
    });
  };

  return (
    <aside className="fixed inset-y-0 right-0 z-40 w-[440px] md:w-[500px] bg-zinc-950/95 border-l border-zinc-800 shadow-2xl backdrop-blur-xl flex flex-col text-zinc-100 animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
            {node.node_type}
          </span>
          <span className="font-mono text-xs text-zinc-500">#{node.id}</span>
        </div>
        <button
          onClick={() => setSelectedNodeId(null)}
          className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs Bar: [Огляд] | [Live Термінал] | [Diff Артефактів] */}
      <div className="flex items-center border-b border-zinc-800 bg-zinc-950 px-4 pt-1 gap-1 text-xs select-none">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition ${
            activeTab === 'overview'
              ? 'border-purple-500 text-purple-300 bg-purple-950/10'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Огляд</span>
        </button>
        <button
          onClick={() => setActiveTab('terminal')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition ${
            activeTab === 'terminal'
              ? 'border-purple-500 text-purple-300 bg-purple-950/10'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Live Термінал</span>
          {nodeLogs[node.id]?.length ? (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-300 font-mono">
              {nodeLogs[node.id].length}
            </span>
          ) : null}
        </button>
        <button
          onClick={() => setActiveTab('diff')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition ${
            activeTab === 'diff'
              ? 'border-purple-500 text-purple-300 bg-purple-950/10'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>Diff Артефактів</span>
          {nodeArtifacts[node.id]?.files?.length ? (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-purple-900/60 text-purple-300 border border-purple-700/50 font-mono">
              {nodeArtifacts[node.id].files.length}
            </span>
          ) : null}
        </button>
        <button
          onClick={() => setActiveTab('video')}
          className={`flex items-center gap-1.5 px-3 py-2 border-b-2 font-medium transition ${
            activeTab === 'video'
              ? 'border-purple-500 text-purple-300 bg-purple-950/10'
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Film className="w-3.5 h-3.5 text-purple-400" />
          <span>🎬 Відео</span>
          {marketingVideos[node.id] ? (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-purple-900/60 text-purple-300 border border-purple-700/50 font-mono">
              9:16
            </span>
          ) : null}
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 overflow-y-auto p-5">
        {activeTab === 'overview' && (
          <div className="space-y-6">
        {/* Title & Description */}
        <div>
          <h2 className="text-lg font-semibold text-zinc-100 leading-snug">{node.title}</h2>
          <p className="mt-2 text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap">
            {node.description || 'No description provided.'}
          </p>
        </div>

        {/* AI Decompose Section for Epic / Idea / Task */}
        {(node.node_type === 'epic' || node.node_type === 'idea' || node.node_type === 'task') && (
          <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-violet-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                Декомпозиція через Герича
              </span>
              <span className="text-[10px] text-violet-400/80 font-mono">3x Swarm Tasks</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              Автоматично розбити цей {node.node_type === 'epic' ? 'епік' : 'вузол'} на атомний DAG-ланцюжок (Spec ➔ Build ➔ Gate) з призначенням відповідних воркерів.
            </p>
            <button
              onClick={handleDecompose}
              disabled={isDecomposing || isAgentRunning}
              className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-violet-900/30 transition-all disabled:opacity-50"
            >
              {isDecomposing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Декомпозиція роєм...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>⚡ Декомпозувати через Герича</span>
                </>
              )}
            </button>
            {decomposeFeedback && (
              <p className="text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 rounded p-2">
                {decomposeFeedback}
              </p>
            )}
          </div>
        )}

        {/* Priority & Tags */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium ${
              node.priority === 'P0_Critical'
                ? 'bg-red-950 text-red-300 border border-red-800'
                : node.priority === 'P1_High'
                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
            }`}
          >
            {node.priority}
          </span>

          {node.tags?.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-400"
            >
              <Tag className="w-2.5 h-2.5" />
              {tag}
            </span>
          ))}
        </div>

        {/* Stage Progression Stepper */}
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              Execution Stage
            </h3>
            <span className="text-[11px] font-mono text-cyan-400 capitalize">{node.stage}</span>
          </div>

          <div className="grid grid-cols-3 gap-1.5">
            {ALL_STAGES.map((st) => {
              const isActive = node.stage === st;
              return (
                <button
                  key={st}
                  onClick={() => handleStageClick(st)}
                  className={`px-2 py-1.5 rounded-lg text-[10px] font-medium border text-center transition-all ${
                    isActive
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200 font-semibold ring-1 ring-cyan-400'
                      : 'bg-zinc-800/50 border-zinc-700/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              );
            })}
          </div>

          {/* Blocked or Gate Transition Warning */}
          {transitionError && (
            <div className="mt-3 p-3 rounded-lg bg-red-950/70 border border-red-500/50 text-xs text-red-200 space-y-2">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <p className="leading-snug">{transitionError}</p>
              </div>
              {showForceTransition && pendingTargetStage && (
                <button
                  onClick={() => handleStageClick(pendingTargetStage, true)}
                  className="w-full mt-2 py-1 px-2 rounded bg-red-600 hover:bg-red-500 text-white font-medium text-[11px] transition-colors"
                >
                  Force Transition to {pendingTargetStage}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Progress Slider (for non-idea) */}
        {node.node_type !== 'idea' && (
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                Progress Completion
              </span>
              <span className="font-mono text-xs font-medium text-emerald-400">
                {node.progress}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={node.progress}
              onChange={(e) => handleProgressChange(parseInt(e.target.value, 10))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>
        )}

        {/* Swarm Agent Dispatch Section */}
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-cyan-400" />
              Swarm Agent Dispatch
            </h3>
            <span className="text-[10px] font-mono text-zinc-400">
              {node.assigned_agent || 'Unassigned'}
            </span>
          </div>

          <div className="flex gap-2">
            <select
              value={agentMode}
              onChange={(e) => setAgentMode(e.target.value as 'simulation' | 'autonomous_subagent' | 'auto_complete')}
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="simulation">Simulation (Safe Run)</option>
              <option value="autonomous_subagent">Autonomous Worker</option>
              <option value="auto_complete">Fast Finish & Verify (100% Green)</option>
            </select>
            <button
              onClick={handleAgentExecute}
              disabled={isAgentRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium text-xs transition-colors shrink-0"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isAgentRunning ? 'Running...' : 'Run Agent'}</span>
            </button>
          </div>

          <textarea
            value={agentInstructions}
            onChange={(e) => setAgentInstructions(e.target.value)}
            placeholder="Optional prompt / instructions for Swarm Worker..."
            rows={2}
            className="w-full bg-zinc-800/80 border border-zinc-700/80 rounded-lg p-2 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-cyan-400 resize-none"
          />

          {agentFeedback && (
            <div className="p-2.5 rounded-lg bg-zinc-850 border border-zinc-700 text-xs text-zinc-300 font-mono space-y-2">
              <div className="flex items-center gap-2">
                {node.stage === 'in_progress' && (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping shrink-0" />
                )}
                <span className="whitespace-pre-wrap">{agentFeedback}</span>
              </div>
              {node.stage === 'in_progress' && (
                <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-400 h-1.5 transition-all duration-700 rounded-full animate-pulse"
                    style={{ width: `${Math.max(node.progress, 20)}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Live Agent Terminal Logs */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-950/90 p-3 space-y-2 font-mono text-[11px]">
            <div className="flex items-center justify-between pb-1.5 border-b border-zinc-800/80">
              <div className="flex items-center gap-1.5 text-zinc-400">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-semibold text-zinc-300">Live Swarm Terminal</span>
                {node.stage === 'in_progress' && (
                  <span className="inline-flex items-center gap-1 text-[9px] text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    LIVE
                  </span>
                )}
              </div>
              <button
                onClick={() => fetchNodeLogs(node.id)}
                className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200 transition-colors"
                title="Оновити логи"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 select-text">
              {nodeLogs[node.id] && nodeLogs[node.id].length > 0 ? (
                <>
                  {nodeLogs[node.id].map((log, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 leading-relaxed">
                      <span className="text-[10px] text-zinc-500 shrink-0">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--'}
                      </span>
                      <span
                        className={`text-[9px] px-1 py-0.2 rounded font-bold uppercase shrink-0 ${
                          log.level === 'SUCCESS'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                            : log.level === 'ERROR'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : log.level === 'STEP'
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                            : 'bg-zinc-800 text-zinc-300'
                        }`}
                      >
                        {log.level}
                      </span>
                      <span className="text-[10px] text-cyan-400 font-semibold shrink-0">
                        [{log.agent}]:
                      </span>
                      <span className="text-zinc-300 break-words">{log.message}</span>
                    </div>
                  ))}
                  <div ref={terminalEndRef} />
                </>
              ) : (
                <div className="text-zinc-500 italic py-2 text-center text-[10px]">
                  No execution logs yet. Run agent or enter instructions above.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Idea Conversion Box (If Idea) */}
        {node.node_type === 'idea' && (
          <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-4 space-y-3">
            <h3 className="text-xs font-semibold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Convert Idea to Execution Task
            </h3>
            <p className="text-[11px] text-zinc-400">
              Spawns a new active Task/Epic in Architecture stage with an origin dependency link.
            </p>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Target Type</label>
                <select
                  value={ideaConvertType}
                  onChange={(e) => setIdeaConvertType(e.target.value as NodeType)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1 text-xs text-zinc-200"
                >
                  <option value="task">Task</option>
                  <option value="epic">Epic</option>
                  <option value="slice">Slice</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-zinc-400 block mb-1">Assign Agent</label>
                <select
                  value={ideaConvertAgent}
                  onChange={(e) => setIdeaConvertAgent(e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1 text-xs text-zinc-200"
                >
                  {SWARM_AGENTS.map((ag) => (
                    <option key={ag} value={ag}>
                      {ag}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={() => convertIdea(node.id, ideaConvertType, ideaConvertAgent)}
              className="w-full py-2 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Spawn {ideaConvertType.toUpperCase()}</span>
            </button>
          </div>
        )}

        {/* Dependencies Section */}
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              DAG Dependencies
            </h3>
            <button
              onClick={() => setCreateEdgeModalOpen(true)}
              className="text-[10px] text-cyan-400 hover:text-cyan-300 font-medium"
            >
              + Link Dependency
            </button>
          </div>

          {/* Incoming Prerequisites */}
          <div>
            <span className="text-[10px] font-medium text-zinc-400 block mb-1.5">
              Prerequisites ({incomingDependencies.length})
            </span>
            {incomingDependencies.length === 0 ? (
              <p className="text-[11px] text-zinc-500 italic">No incoming blockers or prerequisites.</p>
            ) : (
              <div className="space-y-1.5">
                {incomingDependencies.map((dep) => {
                  const prereq = nodesMap[dep.source];
                  if (!prereq) return null;
                  const isDone = prereq.stage === 'completed' || prereq.progress === 100;
                  return (
                    <div
                      key={dep.id}
                      onClick={() => setSelectedNodeId(prereq.id)}
                      className={`group flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                        isDone
                          ? 'bg-zinc-800/40 border-emerald-900/40 text-zinc-300 hover:border-emerald-500/50'
                          : 'bg-red-950/30 border-red-900/40 text-red-200 hover:border-red-500/50'
                      }`}
                    >
                      <div className="flex items-center gap-1.5 truncate flex-1 min-w-0 mr-2">
                        {isDone ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                        )}
                        <span className="truncate">{prereq.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                          {prereq.stage}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteEdge(dep.id);
                          }}
                          title="Unlink dependency"
                          className="opacity-40 group-hover:opacity-100 p-1 rounded hover:bg-red-950 text-zinc-400 hover:text-red-400 transition-all"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Outgoing Dependents */}
          <div>
            <span className="text-[10px] font-medium text-zinc-400 block mb-1.5">
              Dependents Waiting ({outgoingDependencies.length})
            </span>
            {outgoingDependencies.length === 0 ? (
              <p className="text-[11px] text-zinc-500 italic">No downstream nodes depend on this.</p>
            ) : (
              <div className="space-y-1.5">
                {outgoingDependencies.map((dep) => {
                  const child = nodesMap[dep.target];
                  if (!child) return null;
                  return (
                    <div
                      key={dep.id}
                      onClick={() => setSelectedNodeId(child.id)}
                      className="group flex items-center justify-between p-2 rounded-lg border border-zinc-800 bg-zinc-800/40 text-xs text-zinc-300 hover:border-cyan-500/50 cursor-pointer transition-colors"
                    >
                      <span className="truncate flex-1 min-w-0 mr-2">{child.title}</span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                          {dep.dependency_type}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteEdge(dep.id);
                          }}
                          title="Unlink dependent"
                          className="opacity-40 group-hover:opacity-100 p-1 rounded hover:bg-red-950 text-zinc-400 hover:text-red-400 transition-all"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    )}

        {/* Tab 2: Live Terminal */}
        {activeTab === 'terminal' && (
          <div className="flex flex-col h-full space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${isAgentRunning ? 'bg-emerald-500 animate-ping' : 'bg-zinc-600'}`} />
                <span className="text-xs font-mono text-zinc-300">
                  {isAgentRunning ? 'Воркер активний (виконання потоку)...' : 'Термінал воркера'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => fetchNodeLogs(node.id)}
                className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-zinc-200 transition"
                title="Оновити логи"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex-1 min-h-[400px] overflow-y-auto space-y-1.5 p-3 rounded-xl border border-zinc-800 bg-zinc-950 font-mono text-[11px] select-text">
              {nodeLogs[node.id] && nodeLogs[node.id].length > 0 ? (
                <>
                  {nodeLogs[node.id].map((log, idx) => (
                    <div key={idx} className="flex items-start gap-2 leading-relaxed">
                      <span className="text-[10px] text-zinc-500 shrink-0 select-none">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--'}
                      </span>
                      <span
                        className={`px-1 py-0.2 rounded text-[9px] uppercase font-bold shrink-0 select-none ${
                          log.level === 'error'
                            ? 'bg-rose-950 text-rose-400 border border-rose-900/60'
                            : log.level === 'warn'
                            ? 'bg-amber-950 text-amber-400 border border-amber-900/60'
                            : 'bg-zinc-900 text-zinc-400'
                        }`}
                      >
                        {log.level}
                      </span>
                      <span className="text-zinc-300 whitespace-pre-wrap break-all flex-1">{log.message}</span>
                    </div>
                  ))}
                  <div ref={terminalEndRef} />
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-zinc-500 text-xs space-y-2">
                  <Terminal className="w-6 h-6 text-zinc-600" />
                  <span>Немає логів для цього вузла</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Artifacts Diff */}
        {activeTab === 'diff' && (
          <NodeTaskArtifactDiffViewer nodeId={node.id} />
        )}

        {/* Tab 4: Marketing Video */}
        {activeTab === 'video' && (
          <NodeTaskMarketingVideoViewer nodeId={node.id} />
        )}
      </div>

      {/* Footer / Delete */}
      <div className="p-4 border-t border-zinc-800 flex items-center justify-between">
        <button
          onClick={() => {
            if (confirm(`Delete node "${node.title}"? This will remove connected edges.`)) {
              deleteNode(node.id);
            }
          }}
          className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-950/50 px-3 py-1.5 rounded-lg border border-red-900/50 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Delete Node</span>
        </button>
      </div>
    </aside>
  );
}

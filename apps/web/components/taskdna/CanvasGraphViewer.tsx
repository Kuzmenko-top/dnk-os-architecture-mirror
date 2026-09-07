// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_taskdna_CanvasGraphViewer"
// purpose: "Interactive TaskDNA Canvas Graph Viewer component with node selection and inspector panel"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';

interface NodeData {
  id?: string;
  name?: string;
  title?: string;
  status?: string;
  phase?: string;
  role?: string;
  branch?: string;
  dod?: string;
  evidence?: string;
  number?: number;
  state?: string;
  checks?: string;
}

interface GraphNode {
  id: string;
  type: 'taskNode' | 'agentNode' | 'gateNode' | 'prNode' | string;
  position: { x: number; y: number };
  data: NodeData;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

interface CanvasGraphViewerProps {
  taskId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function CanvasGraphViewer({ taskId, nodes, edges }: CanvasGraphViewerProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(nodes[0] || null);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'taskNode':
        return '🧬';
      case 'agentNode':
        return '🤖';
      case 'gateNode':
        return '🛡️';
      case 'prNode':
        return '🔀';
      default:
        return '📦';
    }
  };

  const getNodeBadgeColor = (status?: string) => {
    switch (status) {
      case 'PASSED':
      case 'COMPLETED':
      case 'SUCCESS':
      case 'MERGED':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'IN_PROGRESS':
      case 'ACTIVE':
      case 'OPEN':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'PENDING':
      case 'IDLE':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
      case 'FAILED':
      case 'BLOCKED':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="flex flex-col lg:flex-row h-[550px] bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-md shadow-2xl">
      {/* Canvas Graph View Area */}
      <div className="flex-1 relative bg-slate-950/80 p-6 overflow-auto">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:28px_28px] opacity-25" />

        <div className="relative z-10 flex flex-col gap-6 min-w-[700px]">
          <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-3 rounded-xl">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-300 font-mono">
                Граф Задачі (Task Graph Topology):
              </span>
              <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs font-mono font-bold rounded">
                {taskId}
              </span>
            </div>
            <div className="text-xs text-slate-500 font-mono">
              Всього нод: {nodes.length} | Ребер: {edges.length}
            </div>
          </div>

          {/* Render Nodes Grid / Topology */}
          <div className="grid grid-cols-3 gap-6 pt-4">
            {nodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-2 relative shadow-lg ${
                    isSelected
                      ? 'bg-blue-900/40 border-blue-500 ring-2 ring-blue-500/40 shadow-blue-500/20'
                      : 'bg-slate-900/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{getNodeIcon(node.type)}</span>
                      <span className="text-xs font-mono text-slate-400 uppercase font-bold">
                        {node.type}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${getNodeBadgeColor(
                        node.data.status || node.data.state || node.data.checks
                      )}`}
                    >
                      {node.data.status || node.data.state || node.data.checks || 'NODE'}
                    </span>
                  </div>

                  <div className="font-bold text-sm text-white truncate pt-1">
                    {node.data.title || node.data.name || `PR #${node.data.number}` || node.id}
                  </div>

                  {node.data.branch && (
                    <div className="text-[11px] text-slate-400 font-mono truncate">
                      {node.data.branch}
                    </div>
                  )}

                  {node.data.evidence && (
                    <div className="text-[10px] text-slate-500 font-mono truncate">
                      Ev: {node.data.evidence}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Connections / Edges Indicator */}
          <div className="mt-4 p-3 bg-slate-900/40 border border-slate-800/80 rounded-xl">
            <div className="text-[11px] font-bold text-slate-400 font-mono mb-2">
              🔗 Зв'язки між нодами (Graph Edges):
            </div>
            <div className="flex flex-wrap gap-2">
              {edges.map((e) => (
                <span
                  key={e.id}
                  className="text-[10px] font-mono bg-slate-950 border border-slate-800 text-slate-300 px-2 py-1 rounded flex items-center gap-1"
                >
                  <span className="text-blue-400">{e.source}</span>
                  <span className="text-slate-500">─({e.label})→</span>
                  <span className="text-emerald-400">{e.target}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detail Inspector Panel */}
      <div className="w-full lg:w-80 bg-slate-900 border-t lg:border-t-0 lg:border-l border-slate-800 p-5 flex flex-col gap-4 overflow-y-auto shrink-0">
        <div className="border-b border-slate-800 pb-3">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
            Node Detail Inspector
          </div>
          <h3 className="text-base font-extrabold text-white flex items-center gap-2 mt-1">
            <span>{selectedNode ? getNodeIcon(selectedNode.type) : '🔍'}</span>
            <span>{selectedNode ? selectedNode.id : 'Виберіть ноду'}</span>
          </h3>
        </div>

        {selectedNode ? (
          <div className="flex flex-col gap-3.5 text-xs">
            <div>
              <span className="text-slate-500 font-mono font-bold block text-[10px]">Node Type:</span>
              <span className="text-blue-300 font-mono font-bold">{selectedNode.type}</span>
            </div>

            <div>
              <span className="text-slate-500 font-mono font-bold block text-[10px]">Title / Name:</span>
              <span className="text-white font-bold">
                {selectedNode.data.title || selectedNode.data.name || `PR #${selectedNode.data.number}`}
              </span>
            </div>

            {selectedNode.data.status && (
              <div>
                <span className="text-slate-500 font-mono font-bold block text-[10px]">Status:</span>
                <span
                  className={`inline-block text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase mt-1 ${getNodeBadgeColor(
                    selectedNode.data.status
                  )}`}
                >
                  {selectedNode.data.status}
                </span>
              </div>
            )}

            {selectedNode.data.phase && (
              <div>
                <span className="text-slate-500 font-mono font-bold block text-[10px]">Phase:</span>
                <span className="text-slate-300 font-mono">{selectedNode.data.phase}</span>
              </div>
            )}

            {selectedNode.data.branch && (
              <div>
                <span className="text-slate-500 font-mono font-bold block text-[10px]">Branch:</span>
                <span className="text-slate-300 font-mono text-[11px] break-all">
                  {selectedNode.data.branch}
                </span>
              </div>
            )}

            {selectedNode.data.dod && (
              <div>
                <span className="text-slate-500 font-mono font-bold block text-[10px]">DoD Progress:</span>
                <span className="text-emerald-400 font-mono font-bold">{selectedNode.data.dod}</span>
              </div>
            )}

            {selectedNode.data.evidence && (
              <div>
                <span className="text-slate-500 font-mono font-bold block text-[10px]">Evidence Reference:</span>
                <span className="text-indigo-300 font-mono text-[11px] break-all bg-slate-950 p-2 rounded border border-slate-800 block">
                  {selectedNode.data.evidence}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="text-slate-500 text-xs py-8 text-center">
            Клацніть на будь-яку ноду на графі для перегляду детальних метаданих.
          </div>
        )}
      </div>
    </div>
  );
}
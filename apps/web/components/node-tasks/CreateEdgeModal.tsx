// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/CreateEdgeModal.tsx"
// purpose: "Interactive modal for building directed dependency links with visual preview, preselection, and direction swap"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { X, Link2, AlertCircle, ArrowLeftRight, Check, Sparkles } from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { DependencyType } from '@/types/nodeTasks';

const RELATION_STYLES: Record<DependencyType, { label: string; badge: string; desc: string }> = {
  depends_on: {
    label: 'depends_on',
    badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
    desc: 'Target node requires Source to be completed first',
  },
  blocks: {
    label: 'blocks',
    badge: 'bg-red-950/80 text-red-300 border-red-700/60',
    desc: 'Source physically blocks progress of Target',
  },
  spawns_from: {
    label: 'spawns_from',
    badge: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
    desc: 'Target task originated from Source idea',
  },
  relates_to: {
    label: 'relates_to',
    badge: 'bg-zinc-800/80 text-zinc-300 border-zinc-700',
    desc: 'Informational link without strict execution blocking',
  },
};

export function CreateEdgeModal() {
  const isOpen = useNodeTasksStore((s) => s.isCreateEdgeModalOpen);
  const setIsOpen = useNodeTasksStore((s) => s.setCreateEdgeModalOpen);
  const nodesMap = useNodeTasksStore((s) => s.nodesMap);
  const selectedNodeId = useNodeTasksStore((s) => s.selectedNodeId);
  const createEdge = useNodeTasksStore((s) => s.createEdge);
  const error = useNodeTasksStore((s) => s.error);

  const [source, setSource] = useState('');
  const [target, setTarget] = useState('');
  const [depType, setDepType] = useState<DependencyType>('depends_on');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Pre-populate target with the selected node when opening from the detail drawer
  useEffect(() => {
    if (isOpen) {
      if (selectedNodeId && nodesMap[selectedNodeId]) {
        setTarget(selectedNodeId);
        setSource('');
      } else {
        setSource('');
        setTarget('');
      }
      setDescription('');
    }
  }, [isOpen, selectedNodeId, nodesMap]);

  if (!isOpen) return null;

  const nodeList = Object.values(nodesMap);
  const sourceNode = source ? nodesMap[source] : null;
  const targetNode = target ? nodesMap[target] : null;

  const handleSwap = () => {
    const temp = source;
    setSource(target);
    setTarget(temp);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!source || !target || source === target) return;

    setIsSubmitting(true);
    const success = await createEdge(source, target, depType, description.trim());
    setIsSubmitting(false);

    if (success) {
      setSource('');
      setTarget('');
      setDescription('');
      setIsOpen(false);
    }
  };

  const isSelfLoop = source && target && source === target;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl text-zinc-100 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-950/60 text-cyan-400 border border-cyan-800/50">
              <Link2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-zinc-100">Add Dependency Link</h3>
              <p className="text-[11px] text-zinc-400">Connect nodes in the DAG execution tree</p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-950/60 border border-red-800 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {isSelfLoop && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-950/60 border border-amber-800 text-xs text-amber-300">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>A node cannot depend on itself (Self-loop forbidden in DAG).</span>
          </div>
        )}

        {/* Dynamic Connection Visual Preview */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3.5 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-zinc-400 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              Live Connection Preview
            </span>
            <button
              type="button"
              onClick={handleSwap}
              disabled={!source && !target}
              title="Swap connection direction"
              className="flex items-center gap-1.5 text-[11px] font-medium text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/40 border border-cyan-800/50 px-2.5 py-1 rounded-md transition-colors disabled:opacity-40 disabled:pointer-events-none"
            >
              <ArrowLeftRight className="w-3 h-3" />
              <span>Swap Direction</span>
            </button>
          </div>

          <div className="flex items-center justify-between gap-2 text-xs">
            {/* Source card */}
            <div
              className={`flex-1 p-2.5 rounded-lg border text-center transition-colors truncate ${
                sourceNode
                  ? 'border-zinc-700 bg-zinc-850/80 text-zinc-100'
                  : 'border-dashed border-zinc-800 bg-zinc-900/20 text-zinc-500'
              }`}
            >
              <span className="text-[9px] font-mono uppercase tracking-wider text-zinc-400 block mb-0.5">
                Source (Prerequisite)
              </span>
              <div className="truncate font-semibold text-xs text-zinc-200">
                {sourceNode ? sourceNode.title : 'Select source node'}
              </div>
              {sourceNode && (
                <span className="text-[9px] font-mono text-zinc-400 px-1.5 py-0.2 rounded bg-zinc-800 inline-block mt-1">
                  [{sourceNode.node_type.toUpperCase()}] {sourceNode.stage}
                </span>
              )}
            </div>

            {/* Relationship connector */}
            <div className="flex flex-col items-center shrink-0 px-1">
              <span className="text-zinc-500 text-sm font-bold">➔</span>
              <span
                className={`text-[9px] font-mono font-semibold px-2 py-0.5 rounded-full border mt-0.5 ${
                  RELATION_STYLES[depType].badge
                }`}
              >
                {RELATION_STYLES[depType].label}
              </span>
            </div>

            {/* Target card */}
            <div
              className={`flex-1 p-2.5 rounded-lg border text-center transition-colors truncate ${
                targetNode
                  ? 'border-cyan-800/80 bg-cyan-950/30 text-cyan-100'
                  : 'border-dashed border-zinc-800 bg-zinc-900/20 text-zinc-500'
              }`}
            >
              <span className="text-[9px] font-mono uppercase tracking-wider text-cyan-400/80 block mb-0.5">
                Target (Downstream)
              </span>
              <div className="truncate font-semibold text-xs text-cyan-200">
                {targetNode ? targetNode.title : 'Select target node'}
              </div>
              {targetNode && (
                <span className="text-[9px] font-mono text-cyan-300 px-1.5 py-0.2 rounded bg-cyan-900/50 inline-block mt-1">
                  [{targetNode.node_type.toUpperCase()}] {targetNode.stage}
                </span>
              )}
            </div>
          </div>

          <p className="text-[10px] text-zinc-400 italic text-center pt-1">
            {RELATION_STYLES[depType].desc}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Source Node */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Source Node (Prerequisite / Origin)
            </label>
            <select
              required
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="">Select source node...</option>
              {nodeList.map((n) => (
                <option key={n.id} value={n.id} disabled={n.id === target}>
                  [{n.node_type.toUpperCase()}] {n.title} ({n.stage})
                </option>
              ))}
            </select>
          </div>

          {/* Dependency Type */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Relationship Type</label>
            <select
              value={depType}
              onChange={(e) => setDepType(e.target.value as DependencyType)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="depends_on">depends_on — Target requires Source completion</option>
              <option value="blocks">blocks — Source physically blocks Target execution</option>
              <option value="spawns_from">spawns_from — Target originated from Source Idea</option>
              <option value="relates_to">relates_to — Contextual reference (non-blocking)</option>
            </select>
          </div>

          {/* Target Node */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Target Node (Dependent / Downstream)
            </label>
            <select
              required
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="">Select target node...</option>
              {nodeList.map((n) => (
                <option key={n.id} value={n.id} disabled={n.id === source}>
                  [{n.node_type.toUpperCase()}] {n.title} ({n.stage})
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Description / Reason (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Requires SCONES L3 memory layer before OCC graph merge"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-4 py-2 rounded-lg text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !source || !target || isSelfLoop}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium text-xs transition-colors flex items-center gap-1.5"
            >
              <Link2 className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Linking...' : 'Create Link'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

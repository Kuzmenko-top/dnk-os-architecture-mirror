// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/CreateNodeModal.tsx"
// purpose: "Modal for creating new Task, Idea, Epic, Slice, or Gate nodes in the DAG"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { X, Plus, Sparkles, CheckSquare, Layers, Code2, ShieldAlert } from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { NodeType, ExecutionStage, PriorityLevel } from '@/types/nodeTasks';

const SWARM_AGENTS = [
  'dnk_dev_fullstack',
  'gerych_builder',
  'dnk_video_ai_creator',
  'dnk_shopify',
  'dnk_scones_memory',
  'gerych_auditor',
  'herich_librarian',
  'dnk_analytics',
  'dnk_finance_cfo',
];

export function CreateNodeModal() {
  const isOpen = useNodeTasksStore((s) => s.isCreateNodeModalOpen);
  const setIsOpen = useNodeTasksStore((s) => s.setCreateNodeModalOpen);
  const createOrUpdateNode = useNodeTasksStore((s) => s.createOrUpdateNode);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [nodeType, setNodeType] = useState<NodeType>('task');
  const [stage, setStage] = useState<ExecutionStage>('ready');
  const [priority, setPriority] = useState<PriorityLevel>('P2_Medium');
  const [assignedAgent, setAssignedAgent] = useState('dnk_dev_fullstack');
  const [tagsInput, setTagsInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const success = await createOrUpdateNode({
      title: title.trim(),
      description: description.trim(),
      node_type: nodeType,
      stage: nodeType === 'idea' ? 'ideation' : stage,
      priority,
      assigned_agent: assignedAgent,
      tags,
      progress: stage === 'completed' ? 100 : 0,
    });

    setIsSubmitting(false);
    if (success) {
      setTitle('');
      setDescription('');
      setTagsInput('');
      setIsOpen(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl text-zinc-100 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-cyan-950/60 text-cyan-400 border border-cyan-800/50">
              <Plus className="w-4 h-4" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100">Create New Node</h3>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Node Type Selector */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1.5">Node Type</label>
            <div className="grid grid-cols-5 gap-1.5">
              {[
                { type: 'idea', label: 'Idea', icon: Sparkles, color: 'hover:border-amber-400' },
                { type: 'task', label: 'Task', icon: CheckSquare, color: 'hover:border-cyan-400' },
                { type: 'epic', label: 'Epic', icon: Layers, color: 'hover:border-purple-400' },
                { type: 'slice', label: 'Slice', icon: Code2, color: 'hover:border-emerald-400' },
                { type: 'gate', label: 'Gate', icon: ShieldAlert, color: 'hover:border-rose-400' },
              ].map(({ type, label, icon: Icon, color }) => {
                const isSelected = nodeType === type;
                return (
                  <button
                    key={type}
                    type="button"
                    onClick={() => {
                      setNodeType(type as NodeType);
                      if (type === 'idea') setStage('ideation');
                    }}
                    className={`flex flex-col items-center gap-1 p-2 rounded-xl border text-xs font-medium transition-all ${
                      isSelected
                        ? 'bg-zinc-800 border-cyan-400 text-cyan-300 ring-1 ring-cyan-400'
                        : `bg-zinc-900/60 border-zinc-800 text-zinc-400 ${color}`
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Implement SCONES L3 Graph Neural Sync"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-400"
            />
          </div>

          {/* Description */}
          <div>
            <label className="text-xs font-medium text-zinc-400 block mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Outline objectives, acceptance criteria, or architectural notes..."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-400 resize-none"
            />
          </div>

          {/* Grid Attributes */}
          <div className="grid grid-cols-2 gap-3">
            {/* Stage */}
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Stage</label>
              <select
                disabled={nodeType === 'idea'}
                value={stage}
                onChange={(e) => setStage(e.target.value as ExecutionStage)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400 disabled:opacity-50"
              >
                <option value="ideation">Ideation</option>
                <option value="architecture">Architecture</option>
                <option value="ready">Ready</option>
                <option value="in_progress">In Progress</option>
                <option value="testing">Testing</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as PriorityLevel)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
              >
                <option value="P0_Critical">P0 Critical</option>
                <option value="P1_High">P1 High</option>
                <option value="P2_Medium">P2 Medium</option>
                <option value="P3_Low">P3 Low</option>
              </select>
            </div>

            {/* Assigned Agent */}
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Assigned Agent</label>
              <select
                value={assignedAgent}
                onChange={(e) => setAssignedAgent(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-cyan-400"
              >
                {SWARM_AGENTS.map((ag) => (
                  <option key={ag} value={ag}>
                    {ag}
                  </option>
                ))}
              </select>
            </div>

            {/* Tags */}
            <div>
              <label className="text-xs font-medium text-zinc-400 block mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="core, canvas, sota"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          {/* Submit */}
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
              disabled={isSubmitting || !title.trim()}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium text-xs transition-colors flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Creating...' : 'Create Node'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

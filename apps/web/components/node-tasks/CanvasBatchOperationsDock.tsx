// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/CanvasBatchOperationsDock.tsx"
// purpose: "Floating dock for canvas multi-selection & batch operations (stage transition, delete, swarm run)"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { ExecutionStage } from '@/types/nodeTasks';
import {
  Layers,
  Zap,
  Trash2,
  X,
  ChevronDown,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';

const STAGE_OPTIONS: { value: ExecutionStage; label: string; color: string }[] = [
  { value: 'ideation', label: '💡 Ideation', color: 'text-amber-400' },
  { value: 'architecture', label: '📐 Architecture', color: 'text-purple-400' },
  { value: 'ready', label: '🎯 Ready', color: 'text-sky-400' },
  { value: 'in_progress', label: '⚡ In Progress', color: 'text-blue-400' },
  { value: 'testing', label: '🧪 Testing', color: 'text-emerald-400' },
  { value: 'completed', label: '✅ Completed', color: 'text-green-400' },
  { value: 'blocked', label: '🛑 Blocked', color: 'text-rose-400' },
];

export function CanvasBatchOperationsDock() {
  const selectedNodeIds = useNodeTasksStore((s) => s.selectedNodeIds);
  const setSelectedNodeIds = useNodeTasksStore((s) => s.setSelectedNodeIds);
  const setSelectedNodeId = useNodeTasksStore((s) => s.setSelectedNodeId);
  const batchStageTransition = useNodeTasksStore((s) => s.batchStageTransition);
  const batchDeleteNodes = useNodeTasksStore((s) => s.batchDeleteNodes);
  const batchExecuteAgent = useNodeTasksStore((s) => s.batchExecuteAgent);
  const isSyncing = useNodeTasksStore((s) => s.isSyncing);
  const isAgentRunning = useNodeTasksStore((s) => s.isAgentRunning);

  const [isStageMenuOpen, setIsStageMenuOpen] = useState(false);
  const [forceTransition, setForceTransition] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'warn' | 'error' } | null>(null);

  if (!selectedNodeIds || selectedNodeIds.length <= 1) {
    return null;
  }

  const handleClearSelection = () => {
    setSelectedNodeIds([]);
    setSelectedNodeId(null);
    setShowDeleteConfirm(false);
    setIsStageMenuOpen(false);
    setFeedback(null);
  };

  const handleStageSelect = async (stage: ExecutionStage) => {
    setIsStageMenuOpen(false);
    setFeedback(null);
    const result = await batchStageTransition(stage, forceTransition);
    if (result.success) {
      const skippedText = result.skippedCount && result.skippedCount > 0 ? ` (${result.skippedCount} пропущено)` : '';
      setFeedback({
        message: `Оновлено ${result.updatedCount} вузлів -> ${stage}${skippedText}`,
        type: result.skippedCount && result.skippedCount > 0 ? 'warn' : 'success',
      });
      setTimeout(() => setFeedback(null), 4000);
    } else {
      setFeedback({
        message: 'Помилка пакетного переходу стадії',
        type: 'error',
      });
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const handleExecuteBatch = async () => {
    setFeedback(null);
    const result = await batchExecuteAgent();
    if (result.success) {
      setFeedback({
        message: `Рій запущено для ${result.executedCount} задач`,
        type: 'success',
      });
      setTimeout(() => setFeedback(null), 4000);
    } else {
      setFeedback({
        message: 'Помилка пакетного запуску рою',
        type: 'error',
      });
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const handleDeleteBatch = async () => {
    setShowDeleteConfirm(false);
    setFeedback(null);
    const count = selectedNodeIds.length;
    const result = await batchDeleteNodes();
    if (result.success) {
      setFeedback({
        message: `Видалено ${result.deletedCount || count} вузлів та їхні ребра`,
        type: 'success',
      });
      setTimeout(() => setFeedback(null), 3000);
    } else {
      setFeedback({
        message: 'Помилка пакетного видалення',
        type: 'error',
      });
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  return (
    <div className="absolute top-20 left-1/2 -translate-x-1/2 z-40 pointer-events-auto flex flex-col items-center gap-2">
      {/* Main floating dock bar */}
      <div className="flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-[#12141c]/95 border border-cyan-500/40 shadow-2xl backdrop-blur-2xl text-xs text-zinc-200 animate-in fade-in slide-in-from-top-3 duration-200">
        {/* Selection Count Badge */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 font-medium">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
          </span>
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Виділено: <strong className="text-white">{selectedNodeIds.length}</strong></span>
        </div>

        <div className="h-4 w-px bg-zinc-700/60 mx-1" />

        {/* Batch Stage Transition Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsStageMenuOpen((prev) => !prev)}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-800/80 hover:bg-zinc-700/80 border border-zinc-700/80 text-zinc-200 hover:text-white transition-all disabled:opacity-50"
            title="Пакетний перехід між стадіями"
          >
            {isSyncing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
            ) : (
              <RotateCcw className="w-3.5 h-3.5 text-sky-400" />
            )}
            <span>Перевести стадію</span>
            <ChevronDown className="w-3 h-3 text-zinc-400 ml-0.5" />
          </button>

          {isStageMenuOpen && (
            <div className="absolute top-full mt-2 left-0 w-52 p-1.5 rounded-xl bg-[#181b26] border border-zinc-700 shadow-2xl backdrop-blur-xl z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-2 py-1 text-[10px] uppercase font-semibold text-zinc-400 tracking-wider">
                Оберіть цільову стадію
              </div>

              {/* Force Toggle */}
              <label className="flex items-center gap-2 px-2 py-1.5 mb-1 rounded-lg hover:bg-zinc-800/60 cursor-pointer text-[11px] text-zinc-300 border-b border-zinc-800">
                <input
                  type="checkbox"
                  checked={forceTransition}
                  onChange={(e) => setForceTransition(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-900 text-cyan-500 focus:ring-0 focus:ring-offset-0"
                />
                <span>Форсувати (Force mode)</span>
              </label>

              <div className="space-y-0.5">
                {STAGE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleStageSelect(opt.value)}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-zinc-800 text-xs text-zinc-200 hover:text-white flex items-center justify-between transition-colors"
                  >
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Batch Swarm Run Button */}
        <button
          onClick={handleExecuteBatch}
          disabled={isAgentRunning || isSyncing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/70 hover:bg-emerald-900/80 border border-emerald-500/40 text-emerald-300 hover:text-emerald-100 transition-all disabled:opacity-50"
          title="Запустити ройове виконання виділених задач"
        >
          {isAgentRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
          ) : (
            <Zap className="w-3.5 h-3.5 text-emerald-400 fill-emerald-400/20" />
          )}
          <span>Запустити рій</span>
        </button>

        {/* Batch Delete Button */}
        {showDeleteConfirm ? (
          <div className="flex items-center gap-1 bg-rose-950/80 border border-rose-500/50 rounded-xl px-2 py-1">
            <span className="text-[11px] text-rose-300 font-medium mr-1">Видалити {selectedNodeIds.length}?</span>
            <button
              onClick={handleDeleteBatch}
              disabled={isSyncing}
              className="px-2 py-0.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-[11px] transition-colors"
            >
              Так
            </button>
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="px-2 py-0.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] transition-colors"
            >
              Ні
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-zinc-800/80 hover:bg-rose-950/60 border border-zinc-700/80 hover:border-rose-500/40 text-zinc-300 hover:text-rose-300 transition-all disabled:opacity-50"
            title="Видалити виділені вузли"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Видалити</span>
          </button>
        )}

        <div className="h-4 w-px bg-zinc-700/60 mx-1" />

        {/* Deselect / Clear Button */}
        <button
          onClick={handleClearSelection}
          className="p-1.5 rounded-xl hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
          title="Зняти виділення"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Inline Feedback Toast */}
      {feedback && (
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs shadow-lg backdrop-blur-md animate-in fade-in slide-in-from-top-1 duration-150 ${
            feedback.type === 'success'
              ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
              : feedback.type === 'warn'
              ? 'bg-amber-950/90 border-amber-500/40 text-amber-200'
              : 'bg-rose-950/90 border-rose-500/40 text-rose-200'
          }`}
        >
          {feedback.type === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
          {feedback.type === 'warn' && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
          {feedback.type === 'error' && <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />}
          <span>{feedback.message}</span>
        </div>
      )}
    </div>
  );
}

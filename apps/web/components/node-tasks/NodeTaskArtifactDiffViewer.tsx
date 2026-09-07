// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/node-tasks/NodeTaskArtifactDiffViewer.tsx"
// purpose: "Live Diff Inspector & Artifacts Certification Viewer for Swarm Generated Node Tasks"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import {
  FileCode,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  RefreshCw,
  Loader2,
  ShieldCheck,
  ShieldAlert,
  ChevronRight,
  Plus,
  Minus,
  Sparkles,
  Layers,
} from 'lucide-react';
import { useNodeTasksStore } from '@/store/nodeTasksStore';
import { ArtifactFileDiff, NodeArtifactReport } from '@/types/nodeTasks';

interface NodeTaskArtifactDiffViewerProps {
  nodeId: string;
}

export function NodeTaskArtifactDiffViewer({ nodeId }: NodeTaskArtifactDiffViewerProps) {
  const node = useNodeTasksStore((s) => s.nodesMap[nodeId]);
  const nodeArtifacts = useNodeTasksStore((s) => s.nodeArtifacts[nodeId]);
  const isArtifactsLoading = useNodeTasksStore((s) => s.isArtifactsLoading);
  const isVerifying = useNodeTasksStore((s) => s.isVerifying);
  const verificationResult = useNodeTasksStore((s) => s.verificationResults[nodeId]);

  const fetchNodeArtifacts = useNodeTasksStore((s) => s.fetchNodeArtifacts);
  const acceptNodeArtifacts = useNodeTasksStore((s) => s.acceptNodeArtifacts);
  const rejectNodeArtifacts = useNodeTasksStore((s) => s.rejectNodeArtifacts);
  const runNodeVerification = useNodeTasksStore((s) => s.runNodeVerification);

  const [selectedFileIdx, setSelectedFileIdx] = useState(0);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [isActing, setIsActing] = useState(false);

  useEffect(() => {
    if (nodeId) {
      fetchNodeArtifacts(nodeId);
    }
  }, [nodeId, fetchNodeArtifacts]);

  const report: NodeArtifactReport | undefined = nodeArtifacts;
  const files: ArtifactFileDiff[] = report?.files || [];
  const currentFile: ArtifactFileDiff | undefined = files[selectedFileIdx] || files[0];

  const handleAccept = async () => {
    setIsActing(true);
    setActionFeedback(null);
    const res = await acceptNodeArtifacts(nodeId);
    setIsActing(false);
    if (res.success) {
      setActionFeedback('✅ Артефакти схвалено! Задачу переведено в статус completed.');
      setTimeout(() => setActionFeedback(null), 4000);
    } else {
      setActionFeedback(`❌ Помилка: ${res.message || 'Не вдалося схвалити'}`);
    }
  };

  const handleReject = async () => {
    setIsActing(true);
    setActionFeedback(null);
    const res = await rejectNodeArtifacts(nodeId, rejectReason || undefined);
    setIsActing(false);
    setShowRejectModal(false);
    setRejectReason('');
    if (res.success) {
      setActionFeedback('⚠️ Артефакти відхилено. Задачу повернуто в in_progress (50%).');
      setTimeout(() => setActionFeedback(null), 4000);
    } else {
      setActionFeedback(`❌ Помилка: ${res.message || 'Не вдалося відхилити'}`);
    }
  };

  const handleVerify = async () => {
    setActionFeedback(null);
    const res = await runNodeVerification(nodeId);
    if (res.verified) {
      setActionFeedback('🛡️ Автоматичний верифікаційний тест успішно ПРОЙДЕНО (exit code 0)!');
    } else {
      setActionFeedback(`❌ Верифікаційний тест НЕ пройдено: ${res.message || 'перевірте логи'}`);
    }
    setTimeout(() => setActionFeedback(null), 6000);
  };

  if (isArtifactsLoading && !report) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-zinc-400 space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
        <span className="text-xs">Генерація та отримання артефактів від агента...</span>
      </div>
    );
  }

  if (!report || files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center text-zinc-400 space-y-4">
        <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
          <FileCode className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-zinc-200">Артефакти ще не згенеровано</p>
          <p className="text-xs text-zinc-500 max-w-xs">
            Запустіть виконання агента рою або переведіть задачу в стадію тестування для формування дифу.
          </p>
        </div>
        <button
          onClick={() => fetchNodeArtifacts(nodeId)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-600/20 text-purple-300 border border-purple-500/30 hover:bg-purple-600/30 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Оновити артефакти
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Top Meta Summary */}
      <div className="p-3 bg-zinc-900/60 rounded-xl border border-zinc-800/80 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
              {report.agent}
            </span>
            <span className="text-zinc-500 font-mono">
              {files.length} {files.length === 1 ? 'файл' : 'файли'}
            </span>
          </div>
          <div className="flex items-center gap-2 font-mono text-[11px]">
            <span className="text-emerald-400 flex items-center">
              <Plus className="w-3 h-3" />
              {report.total_additions}
            </span>
            <span className="text-rose-400 flex items-center">
              <Minus className="w-3 h-3" />
              {report.total_deletions}
            </span>
            <button
              onClick={() => fetchNodeArtifacts(nodeId)}
              disabled={isArtifactsLoading}
              title="Перезавантажити diff"
              className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isArtifactsLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Verification Alert Banner if present */}
        {verificationResult && (
          <div
            className={`p-2 rounded-lg border text-xs flex items-center justify-between ${
              verificationResult.verified
                ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-950/30 border-rose-500/30 text-rose-300'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              {verificationResult.verified ? (
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : (
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <span className="font-mono truncate">
                {verificationResult.verified ? 'Gate PASSED (exit code 0)' : `Gate FAILED (exit code ${verificationResult.exit_code})`}
              </span>
            </div>
          </div>
        )}

        {/* Feedback message */}
        {actionFeedback && (
          <div className="p-2 text-xs rounded bg-zinc-800 border border-zinc-700 text-zinc-200 animate-in fade-in">
            {actionFeedback}
          </div>
        )}
      </div>

      {/* File selector tabs */}
      {files.length > 1 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          {files.map((f, idx) => (
            <button
              key={f.path}
              onClick={() => setSelectedFileIdx(idx)}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg border whitespace-nowrap transition ${
                selectedFileIdx === idx
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-100 font-medium'
                  : 'bg-zinc-950/50 border-zinc-800/80 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}
            >
              <FileCode className="w-3.5 h-3.5 text-purple-400" />
              <span className="truncate max-w-[140px] font-mono text-[11px]">{f.path.split('/').pop()}</span>
              <span className="text-[10px] text-emerald-400 font-mono">+{f.additions}</span>
            </button>
          ))}
        </div>
      )}

      {/* Active file diff header */}
      {currentFile && (
        <div className="flex items-center justify-between px-2.5 py-1.5 bg-zinc-900/90 rounded-t-lg border border-zinc-800 text-xs font-mono">
          <div className="flex items-center gap-2 truncate">
            <span
              className={`px-1.5 py-0.5 text-[10px] uppercase font-bold rounded ${
                currentFile.change_type === 'added'
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : currentFile.change_type === 'deleted'
                  ? 'bg-rose-500/20 text-rose-300'
                  : 'bg-blue-500/20 text-blue-300'
              }`}
            >
              {currentFile.change_type}
            </span>
            <span className="text-zinc-300 truncate text-[11px]">{currentFile.path}</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 shrink-0">
            <span className="text-emerald-400">+{currentFile.additions}</span>
            <span className="text-rose-400">-{currentFile.deletions}</span>
          </div>
        </div>
      )}

      {/* Diff Code Container */}
      <div className="flex-1 min-h-[220px] max-h-[360px] overflow-y-auto overflow-x-auto bg-zinc-950 border border-zinc-800 rounded-b-lg font-mono text-[11px] leading-5 p-2 select-text scrollbar-thin">
        {currentFile ? (
          currentFile.diff_content.split('\n').map((line, idx) => {
            const isAdd = line.startsWith('+') && !line.startsWith('+++');
            const isDel = line.startsWith('-') && !line.startsWith('---');
            const isHunk = line.startsWith('@@');
            const isHeader = line.startsWith('---') || line.startsWith('+++');

            let lineClass = 'text-zinc-400 px-1 py-0.5';
            if (isAdd) {
              lineClass = 'bg-emerald-950/40 text-emerald-300 border-l-2 border-emerald-500 px-1 py-0.5';
            } else if (isDel) {
              lineClass = 'bg-rose-950/40 text-rose-300 border-l-2 border-rose-500 px-1 py-0.5';
            } else if (isHunk) {
              lineClass = 'bg-purple-950/30 text-purple-300 px-1 py-0.5 font-bold';
            } else if (isHeader) {
              lineClass = 'text-zinc-500 bg-zinc-900/50 px-1 py-0.5';
            }

            return (
              <div key={idx} className={`${lineClass} whitespace-pre`}>
                <span className="inline-block w-6 text-right pr-2 text-zinc-600 select-none">
                  {idx + 1}
                </span>
                {line}
              </div>
            );
          })
        ) : (
          <div className="p-4 text-center text-zinc-500 text-xs">Немає вмісту дифу</div>
        )}
      </div>

      {/* Reject Modal / Input Drawer */}
      {showRejectModal && (
        <div className="p-3 bg-rose-950/30 border border-rose-800/50 rounded-xl space-y-2 animate-in fade-in">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-300">Причина відхилення артефактів:</span>
            <button
              onClick={() => setShowRejectModal(false)}
              className="text-xs text-zinc-400 hover:text-zinc-200"
            >
              Скасувати
            </button>
          </div>
          <input
            type="text"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Напр. зламано валідацію або не відповідає спеці..."
            className="w-full px-2.5 py-1.5 text-xs bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-rose-500"
          />
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={handleReject}
              disabled={isActing}
              className="px-3 py-1 text-xs font-medium bg-rose-600 hover:bg-rose-500 text-white rounded-lg transition flex items-center gap-1.5"
            >
              {isActing && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Підтвердити відхилення
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons Toolbar */}
      <div className="pt-2 flex flex-col gap-2">
        <div className="grid grid-cols-2 gap-2">
          {/* Accept Button */}
          <button
            onClick={handleAccept}
            disabled={isActing || isVerifying || node.stage === 'completed'}
            className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 transition shadow-lg shadow-emerald-950/40"
          >
            {isActing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5" />
            )}
            Схвалити артефакти
          </button>

          {/* Reject Button */}
          <button
            onClick={() => setShowRejectModal(!showRejectModal)}
            disabled={isActing || isVerifying}
            className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-zinc-800 hover:bg-rose-950/60 hover:text-rose-300 text-zinc-300 border border-zinc-700 hover:border-rose-700/50 transition"
          >
            <RotateCcw className="w-3.5 h-3.5 text-rose-400" />
            Відхилити (Rollback)
          </button>
        </div>

        {/* Verification Gate Trigger Button */}
        <button
          onClick={handleVerify}
          disabled={isVerifying || isActing}
          className="flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg bg-purple-900/30 hover:bg-purple-900/50 text-purple-200 border border-purple-700/50 disabled:opacity-50 transition"
        >
          {isVerifying ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
          ) : (
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          )}
          Запустити верифікаційний тест (Pytest Gate)
        </button>
      </div>
    </div>
  );
}

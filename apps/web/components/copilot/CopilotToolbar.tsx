// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/components/copilot/CopilotToolbar.tsx"
// purpose: "Contextual Floating Swarm Co-Pilot Toolbar (Cmd+K) with Real-Time Intent Resolution, Budget Guard & Downstream Graph Cascade"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-3-COPILOT-TOOLBAR"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useMemo, useEffect, useRef } from 'react';
import { Sparkles, Send, X, Coins, Zap, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { intentResolver, IntentActionType, SwarmAgentId } from '../../lib/intentResolver';
import { budgetGuard } from '../../lib/budgetGuard';
import { useCanvasStore } from '../../store/canvasStore';
import { useSconesStore } from '../../store/sconesStore';
import { SwarmPropagationEngine } from '../../src/canvas/swarm/swarmPropagation';

export interface CopilotToolbarProps {
  selectedNodeIds: string[];
  anchorPosition?: { x: number; y: number };
  onClose: () => void;
  onSuccessToast?: (msg: string) => void;
}

const QUICK_ACTIONS: { id: IntentActionType; label: string; icon: string }[] = [
  { id: 'expand', label: 'Розгорнути деталі', icon: '📖' },
  { id: 'reskin', label: 'Рескінінг (Brand DNA)', icon: '🎨' },
  { id: 'liquid', label: 'Транспіляція в Liquid', icon: '🛒' },
  { id: 'storyboard', label: 'Розкадровка (9:16)', icon: '🎬' },
  { id: 'audit', label: 'Аудит якості', icon: '🛡️' },
];

export const CopilotToolbar: React.FC<CopilotToolbarProps> = ({
  selectedNodeIds,
  anchorPosition = { x: 420, y: 140 },
  onClose,
  onSuccessToast,
}) => {
  const [prompt, setPrompt] = useState('');
  const [activeAction, setActiveAction] = useState<IntentActionType>('generate');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingProgress, setStreamingProgress] = useState(0);

  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  const { nodes, edges, updateNodeData } = useCanvasStore();
  const { currentBrand } = useSconesStore();

  // Find primary target node
  const primaryNodeId = selectedNodeIds[0] || null;
  const primaryNode = useMemo(() => {
    return nodes.find((n) => n.id === primaryNodeId) || null;
  }, [nodes, primaryNodeId]);

  // Focus on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Compute live intent & budget
  const intent = useMemo(() => {
    return intentResolver.resolve(
      prompt,
      {
        selectedNodeIds,
        selectedNodeType: primaryNode?.type,
        selectedNodeTitle: (primaryNode?.data as any)?.title,
        brandContext: {
          brandName: currentBrand?.brandName,
          tone: currentBrand?.toneOfVoice,
        },
      },
      activeAction !== 'generate' ? activeAction : undefined
    );
  }, [prompt, selectedNodeIds, primaryNode, currentBrand, activeAction]);

  const handleQuickAction = (actionId: IntentActionType) => {
    setActiveAction(actionId);
    if (!prompt.trim()) {
      if (actionId === 'expand') setPrompt('Розгорни стратегічні кроки та ключові KPI');
      if (actionId === 'reskin') setPrompt(`Адаптуй стилістику та колірну гаму під бренд ${currentBrand?.brandName || 'DNK'}`);
      if (actionId === 'liquid') setPrompt('Згенеруй готову Shopify OS 2.0 Liquid секцію');
      if (actionId === 'storyboard') setPrompt('Створи 3-сценну 9:16 розкадровку з хуком у перші 3 секунди');
      if (actionId === 'audit') setPrompt('Перевір якість верстки, доступність та відповідність стандартам DNK');
    }
  };

  const handleSubmit = async () => {
    if (!prompt.trim() && activeAction === 'generate') return;
    if (isStreaming) return;

    setIsStreaming(true);
    setStreamingProgress(15);

    // Simulated progressive streaming for rapid interactive response
    const interval = setInterval(() => {
      setStreamingProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 25;
      });
    }, 180);

    setTimeout(() => {
      clearInterval(interval);
      setStreamingProgress(100);

      // 1. Update target node data
      if (primaryNodeId) {
        const patchData: Record<string, any> = {
          ...intent.suggestedPatch,
          lastPrompt: prompt,
          assignedAgent: intent.agent,
          aiCompletedAt: new Date().toLocaleTimeString(),
        };

        if (intent.action === 'expand') {
          patchData.expandedContent = `### AI Expansion by ${intent.agentLabel}\n- Фокус на конверсії та швидкому масштабуванні.\n- Синхронізовано з Brand DNA (${currentBrand?.brandName || 'DNK'}).`;
        }

        updateNodeData(primaryNodeId, patchData);

        // 2. Cascade downstream updates through the graph via SwarmPropagationEngine
        if (currentBrand) {
          const currentNodes = useCanvasStore.getState().nodes;
          const currentEdges = useCanvasStore.getState().edges;
          const propagation = SwarmPropagationEngine.propagate(
            primaryNodeId,
            { prompt, action: intent.action, patch: patchData },
            currentNodes,
            currentEdges,
            currentBrand
          );

          if (propagation.propagatedCount > 0) {
            useCanvasStore.getState().setNodes(propagation.nodes);
          }
        }
      }

      setIsStreaming(false);
      if (onSuccessToast) {
        onSuccessToast(`Swarm Co-Pilot: ${intent.agentLabel} успішно оновив вузли ⚡`);
      }
      onClose();
    }, 850);
  };

  const riskBadgeColor =
    intent.budget.riskLevel === 'low'
      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
      : intent.budget.riskLevel === 'medium'
      ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
      : 'text-rose-400 bg-rose-500/10 border-rose-500/20';

  return (
    <div
      className="fixed z-50 flex flex-col w-[540px] max-w-[95vw] bg-[#02090a]/95 backdrop-blur-2xl border border-cyan-500/30 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8),0_0_30px_rgba(6,182,212,0.15)] overflow-hidden transition-all duration-200"
      style={{
        left: Math.min(window.innerWidth - 560, Math.max(20, anchorPosition.x)),
        top: Math.min(window.innerHeight - 340, Math.max(70, anchorPosition.y)),
      }}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-cyan-950/40 via-purple-950/20 to-black/40 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-6 h-6 rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-300">
            <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          </div>
          <span className="text-xs font-semibold tracking-wider text-cyan-200 uppercase">
            Swarm Co-Pilot
          </span>
          <span className="px-1.5 py-0.5 text-[10px] font-mono text-zinc-400 bg-white/5 rounded border border-white/5">
            Cmd+K
          </span>
        </div>

        <button
          onClick={onClose}
          className="p-1 text-zinc-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Action Chips */}
      <div className="flex items-center gap-1.5 px-3 py-2 bg-black/40 border-b border-white/5 overflow-x-auto scrollbar-none">
        {QUICK_ACTIONS.map((action) => {
          const isActive = activeAction === action.id;
          return (
            <button
              key={action.id}
              onClick={() => handleQuickAction(action.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg whitespace-nowrap transition-all duration-150 border ${
                isActive
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.2)]'
                  : 'bg-white/[0.03] border-white/5 text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.08]'
              }`}
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          );
        })}
      </div>

      {/* Input Prompt Area */}
      <div className="p-3">
        <textarea
          ref={inputRef}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={`Звернися до рою: "Геричу, згенеруй секцію під ${currentBrand?.brandName || 'DNK'}..."`}
          rows={3}
          className="w-full px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 bg-white/[0.03] border border-white/10 rounded-xl focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 resize-none transition-all"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            } else if (e.key === 'Escape') {
              onClose();
            }
          }}
        />
      </div>

      {/* Streaming Progress Bar */}
      {isStreaming && (
        <div className="w-full bg-white/5 h-1 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-400 to-purple-500 transition-all duration-150"
            style={{ width: `${streamingProgress}%` }}
          />
        </div>
      )}

      {/* Bottom Control & Budget Guard Bar */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-black/60 border-t border-white/5 text-xs">
        {/* Dynamic Agent Routing & Budget Preview */}
        <div className="flex items-center gap-2.5">
          {/* Resolved Agent */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-zinc-300">
            <span>{intent.agentAvatar}</span>
            <span className="font-medium text-[11px]">{intent.agentLabel}</span>
          </div>

          {/* Budget Guard Badge */}
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-[11px] font-mono ${riskBadgeColor}`}
            title={`Орієнтовна вартість: ${intent.budget.formattedCost} (~${intent.budget.estimatedTokens} токенів)`}
          >
            <Coins className="w-3 h-3" />
            <span>{intent.budget.formattedCost}</span>
            <span className="text-[9px] opacity-70">({intent.budget.estimatedTokens} tok)</span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={isStreaming}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-xs rounded-xl shadow-[0_0_15px_rgba(6,182,212,0.35)] transition-all disabled:opacity-50"
        >
          {isStreaming ? (
            <>
              <Zap className="w-3.5 h-3.5 animate-spin text-cyan-200" />
              <span>Генерація...</span>
            </>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              <span>Запустити роєм</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

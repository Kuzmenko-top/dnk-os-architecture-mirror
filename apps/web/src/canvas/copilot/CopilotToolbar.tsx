// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/copilot/CopilotToolbar.tsx"
// purpose: "Interactive [⚡ AI Co-Pilot] Toolbar component embedded in Canvas cards to trigger autonomous swarm agent actions with real-time streaming status."
// canonical_source: true
// alters_files: []
// triggers_tasks: ["TaskDNA-PHASE-3-AGENT-COPILOT"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Sparkles, Bot, Loader2, CheckCircle2 } from 'lucide-react';
import { AgentCopilotService, SwarmAgentId } from './agentCopilotService';
import { useSconesStore } from '../../../store/sconesStore';
import { useCanvasStore } from '../../../store/canvasStore';

interface CopilotToolbarProps {
  nodeId: string;
  nodeType: string;
  defaultAgentId: SwarmAgentId;
  onDataGenerated?: (data: Record<string, any>) => void;
}

export function CopilotToolbar({ nodeId, nodeType, defaultAgentId, onDataGenerated }: CopilotToolbarProps) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<SwarmAgentId>(defaultAgentId);
  const { currentBrand } = useSconesStore();

  const handleRunCoPilot = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setLoading(true);
    setSuccess(false);
    setStreamText('');

    try {
      const response = await AgentCopilotService.executeCoPilot({
        nodeId,
        nodeType,
        agentId: selectedAgent,
        brand: currentBrand,
        onStreamToken: (_token, full) => {
          setStreamText(full);
        },
      });

      if (response.success) {
        useCanvasStore.getState().updateNodeData(nodeId, response.generatedData);
        useCanvasStore.getState().propagateSwarm(nodeId, response.generatedData, currentBrand);

        if (onDataGenerated) {
          onDataGenerated(response.generatedData);
        }
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('[CopilotToolbar] Execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-2 pt-2 border-t border-[#232938] flex flex-col gap-1.5 font-sans">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value as SwarmAgentId)}
            onClick={(e) => e.stopPropagation()}
            className="bg-[#090b10] border border-[#232938] rounded px-1.5 py-0.5 text-[10px] text-indigo-200 font-mono cursor-pointer focus:outline-none focus:border-indigo-500"
          >
            <option value="dnk_marketing_cmo">CMO Agent</option>
            <option value="dnk_video_ai_creator">Video Creator</option>
            <option value="dnk_shopify">Shopify AST</option>
            <option value="dnk_dev_fullstack">Fullstack API</option>
            <option value="gerych_builder">Gerych Builder</option>
          </select>
        </div>

        <button
          onClick={handleRunCoPilot}
          disabled={loading}
          className="px-2 py-1 rounded-lg bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-medium text-[10px] flex items-center gap-1 shadow-md transition-all cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : success ? (
            <CheckCircle2 className="w-3 h-3 text-emerald-300" />
          ) : (
            <Sparkles className="w-3 h-3 text-amber-300" />
          )}
          <span>{loading ? 'Streaming...' : success ? 'Done!' : 'AI Co-Pilot'}</span>
        </button>
      </div>

      {streamText && (
        <div className="rounded bg-[#090b10] border border-indigo-500/30 p-1.5 text-[9px] font-mono text-indigo-300 max-h-20 overflow-y-auto">
          {streamText}
        </div>
      )}
    </div>
  );
}

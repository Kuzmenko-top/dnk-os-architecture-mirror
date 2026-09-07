// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_StitchAgentLog"
// purpose: "Google Stitch Floating Agent Log Pill Widget with Live Swarm WebSocket Streaming"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "3.1.0"
// updated_at: "2026-09-04"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { 
  Rocket, 
  ChevronDown, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Info, 
  Trash2, 
  Play, 
  Filter,
  Terminal,
  Activity
} from 'lucide-react';
import { useCanvasStore } from '../../store/canvasStore';

export default function StitchAgentLog() {
  const [isOpen, setIsOpen] = useState(false);
  const [filterBySelected, setFilterBySelected] = useState(false);
  const logsEndRef = useRef<HTMLDivElement | null>(null);

  const activeLogs = useCanvasStore((state) => state.activeLogs || []);
  const selectedNodeId = useCanvasStore((state) => state.selectedNodeId);
  const nodes = useCanvasStore((state) => state.nodes);
  const clearActiveLogs = useCanvasStore((state) => state.clearActiveLogs);
  const triggerNodeAgent = useCanvasStore((state) => state.triggerNodeAgent);

  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId);
  }, [nodes, selectedNodeId]);

  const selectedNodeStatus = 
    (selectedNode?.data?.status as string) || 
    (selectedNode?.data?.agentStatus as string) || 
    (selectedNode as any)?.status || 
    'idle';
  const isSelectedNodeBusy = selectedNodeStatus === 'thinking' || selectedNodeStatus === 'running';

  const anyNodeBusy = useMemo(() => {
    return nodes.some((n) => {
      const s = (n.data?.status as string) || (n.data?.agentStatus as string) || (n as any)?.status;
      return s === 'thinking' || s === 'running';
    });
  }, [nodes]);

  const displayedLogs = useMemo(() => {
    if (filterBySelected && selectedNodeId) {
      return activeLogs.filter((log) => log.nodeId === selectedNodeId);
    }
    return activeLogs;
  }, [activeLogs, filterBySelected, selectedNodeId]);

  useEffect(() => {
    if (isOpen && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [displayedLogs, isOpen]);

  const handleTriggerSelected = () => {
    if (selectedNodeId) {
      triggerNodeAgent(selectedNodeId);
    }
  };

  return (
    <div className="relative">
      {/* Floating Pill Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-[#16181f]/95 border border-white/10 rounded-full px-3.5 py-2 shadow-2xl backdrop-blur-2xl text-neutral-300 hover:text-white hover:bg-white/5 active:scale-95 transition-all"
        title="Open Swarm Agent Log Stream"
      >
        <div className="relative">
          <Rocket className="w-3.5 h-3.5 text-[#33EE75]" />
          {anyNodeBusy && (
            <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#33EE75] animate-ping" />
          )}
        </div>
        <span className="text-[11px] font-semibold tracking-wide">Agent log</span>
        {activeLogs.length > 0 && (
          <span className="text-[10px] bg-white/10 text-neutral-200 px-1.5 py-0.2 rounded-full font-mono">
            {activeLogs.length}
          </span>
        )}
        <ChevronDown className={`w-3 h-3 text-neutral-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Expanded Log Panel */}
      {isOpen && (
        <div className="absolute bottom-12 left-0 w-96 bg-[#16181f]/98 border border-white/10 rounded-2xl p-4 shadow-2xl backdrop-blur-2xl animate-in fade-in slide-in-from-bottom-2 duration-200 z-50">
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[#33EE75]" />
              <span className="text-xs font-bold text-neutral-200 uppercase tracking-wider">Swarm Stream</span>
            </div>
            
            <div className="flex items-center gap-2">
              {activeLogs.length > 0 && (
                <button
                  onClick={clearActiveLogs}
                  className="text-[11px] text-neutral-400 hover:text-rose-400 p-1 rounded transition-colors"
                  title="Clear logs"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}

              <span className="flex items-center gap-1 text-[10px] bg-[#33EE75]/10 text-[#33EE75] px-2 py-0.5 rounded-full font-semibold">
                <span className={`w-1.5 h-1.5 rounded-full bg-[#33EE75] ${anyNodeBusy ? 'animate-pulse' : ''}`} />
                {anyNodeBusy ? 'Running' : 'Ready'}
              </span>
            </div>
          </div>

          {/* Node Context & Actions */}
          {selectedNode && (
            <div className="mb-3 p-2.5 rounded-xl bg-white/[0.03] border border-white/5 flex items-center justify-between">
              <div className="min-w-0 pr-2">
                <p className="text-[10px] uppercase font-semibold text-neutral-400 tracking-wider truncate">
                  Target: {(selectedNode.data?.title as string) || selectedNode.id}
                </p>
                <p className="text-[11px] text-neutral-300 font-mono capitalize">
                  Status: <span className={
                    selectedNodeStatus === 'completed' ? 'text-[#33EE75]' :
                    selectedNodeStatus === 'error' ? 'text-rose-400' :
                    isSelectedNodeBusy ? 'text-amber-400' : 'text-neutral-400'
                  }>{selectedNodeStatus}</span>
                </p>
                {selectedNode.data?.agentTraceId && (
                  <p className="text-[10px] text-neutral-400 font-mono mt-0.5 flex items-center gap-1 truncate">
                    <span className="text-neutral-500">Trace:</span>
                    <span className="text-[#33EE75] truncate max-w-[140px]">{selectedNode.data.agentTraceId as string}</span>
                  </p>
                )}
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => setFilterBySelected(!filterBySelected)}
                  className={`p-1.5 rounded-lg border text-xs transition-all ${
                    filterBySelected 
                      ? 'bg-[#33EE75]/20 border-[#33EE75]/40 text-[#33EE75]' 
                      : 'bg-white/5 border-white/10 text-neutral-400 hover:text-white'
                  }`}
                  title={filterBySelected ? 'Show all logs' : 'Filter by this node'}
                >
                  <Filter className="w-3 h-3" />
                </button>

                <button
                  onClick={handleTriggerSelected}
                  disabled={isSelectedNodeBusy}
                  className="flex items-center gap-1 text-[11px] font-semibold bg-[#33EE75] hover:bg-[#2dd869] text-black px-2.5 py-1 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md active:scale-95"
                  title="Trigger Swarm Task execution on selected node"
                >
                  {isSelectedNodeBusy ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Play className="w-3 h-3 fill-current" />
                  )}
                  <span>Run</span>
                </button>
              </div>
            </div>
          )}

          {/* Log Stream Container */}
          <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {displayedLogs.length === 0 ? (
              <div className="py-6 text-center text-[11px] text-neutral-500 font-mono">
                {filterBySelected 
                  ? 'No logs for selected node yet.' 
                  : 'No active agent stream logs. Select a node & click Run.'}
              </div>
            ) : (
              displayedLogs.map((log) => {
                const timeStr = new Date(log.timestamp).toLocaleTimeString();
                const isSuccess = log.level === 'success';
                const isError = log.level === 'error';
                const isWarn = log.level === 'warning';

                return (
                  <div 
                    key={log.id} 
                    className="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-colors"
                  >
                    <div className="mt-0.5 shrink-0">
                      {isSuccess ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#33EE75]" />
                      ) : isError ? (
                        <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                      ) : isWarn ? (
                        <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                      ) : (
                        <Info className="w-3.5 h-3.5 text-indigo-400" />
                      )}
                    </div>

                    <div className="text-[11px] font-mono min-w-0 flex-1">
                      <div className="flex items-center justify-between text-[10px] text-neutral-500 mb-0.5">
                        <span className="text-neutral-400 font-semibold uppercase">{log.agent}</span>
                        {log.step && (
                          <span className="text-neutral-500 truncate max-w-[120px]">[{log.step}]</span>
                        )}
                        <span>{timeStr}</span>
                      </div>
                      <p className={`leading-relaxed break-words ${
                        isSuccess ? 'text-neutral-200' :
                        isError ? 'text-rose-300' :
                        'text-neutral-300'
                      }`}>
                        {log.message || log.text}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}

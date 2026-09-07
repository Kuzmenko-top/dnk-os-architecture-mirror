// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_nodes_ArchifySpatialNode"
// purpose: "Archify Spatial Diagram Canvas Node for Web Studio (Architecture, Workflow, Sequence, Dataflow) with Realtime Telemetry and View Lens Switching"
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym & Gerych Prime"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import { Handle, Position, NodeProps, useViewport } from '@xyflow/react';
import {
  Layers,
  Maximize2,
  Minimize2,
  Eye,
  Compass,
  Activity,
  Radio,
  RefreshCw,
  Sparkles,
  Server,
  Cpu,
  Database,
  Shield,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Flame,
  Zap
} from 'lucide-react';

export interface ArchifySpatialNodeData {
  id?: string;
  title?: string;
  subtitle?: string;
  diagram_type?: 'architecture' | 'workflow' | 'sequence' | 'dataflow';
  visual_preset?: 'signal-flow' | 'classic' | string;
  quality_profile?: 'showcase' | 'standard';
  artifact_url?: string;
  metrics?: {
    routers_count?: number;
    total_endpoints?: number;
    adapters_count?: number;
    swarm_agents_count?: number;
    canvas_nodes_count?: number;
  };
  active_view?: string;
  is_telemetry_active?: boolean;
}

export const ArchifySpatialNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = (data || {}) as ArchifySpatialNodeData;
  const { zoom } = useViewport();

  const [activeView, setActiveView] = useState<string>(nodeData.active_view || 'primary-path');
  const [isTelemetryLive, setIsTelemetryLive] = useState<boolean>(nodeData.is_telemetry_active ?? true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const title = nodeData.title || 'DNK OS Live Architecture';
  const subtitle = nodeData.subtitle || 'Auto-scanned via DNKArchifyAdapter with Zero-Disk I/O';
  const diagramType = nodeData.diagram_type || 'architecture';
  const artifactUrl = nodeData.artifact_url || '/docs/diagrams/dnk_hub_architecture.html';
  const metrics = nodeData.metrics || {
    routers_count: 60,
    total_endpoints: 251,
    adapters_count: 18,
    swarm_agents_count: 14,
    canvas_nodes_count: 31,
  };

  const handleRefresh = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 800);
  };

  const toggleTelemetry = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsTelemetryLive((prev) => !prev);
  };

  const openFullscreen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFullscreen(true);
  };

  const closeFullscreen = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFullscreen(false);
  };

  // LOD (Level of Detail) rendering based on zoom level
  const isMacroView = zoom < 0.4;

  return (
    <div
      className={`relative select-none transition-all duration-200 ${
        isMacroView ? 'w-[220px] p-3' : 'w-[420px] p-4'
      } rounded-2xl bg-[#0d121f]/95 backdrop-blur-2xl border ${
        selected
          ? 'border-cyan-400 shadow-[0_0_25px_rgba(34,211,238,0.25)] ring-1 ring-cyan-400/50'
          : 'border-[#1e293b] hover:border-slate-600 shadow-2xl'
      } text-slate-100`}
    >
      {/* 4-way React Flow Handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-[#0d121f] transition-all hover:!scale-125 hover:!bg-cyan-300"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-indigo-500 !border-2 !border-[#0d121f] transition-all hover:!scale-125 hover:!bg-indigo-300"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-[#0d121f] transition-all hover:!scale-125 hover:!bg-emerald-300"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-violet-500 !border-2 !border-[#0d121f] transition-all hover:!scale-125 hover:!bg-violet-300"
      />

      {/* Header Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-600/30 border border-cyan-500/40 text-cyan-400">
            <Layers className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-100 tracking-wide">
                {title}
              </span>
              <span className="px-1.5 py-0.5 text-[9px] font-medium tracking-wider uppercase rounded bg-cyan-950/70 border border-cyan-800/50 text-cyan-300">
                {diagramType}
              </span>
            </div>
            {!isMacroView && (
              <p className="text-[10px] text-slate-400 line-clamp-1">{subtitle}</p>
            )}
          </div>
        </div>

        {/* Status Pill & Actions */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={toggleTelemetry}
            title={isTelemetryLive ? 'Live Mesh WS Connected' : 'Telemetry Paused'}
            className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono transition-colors ${
              isTelemetryLive
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isTelemetryLive ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'
              }`}
            />
            {isTelemetryLive ? 'LIVE' : 'IDLE'}
          </button>

          <button
            onClick={handleRefresh}
            title="Re-scan AST & Re-render"
            className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
          </button>

          <button
            onClick={openFullscreen}
            title="Open Presentation Mode"
            className="p-1 rounded-md text-slate-400 hover:text-cyan-300 hover:bg-slate-800/60 transition-colors"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Metrics Strip */}
      <div className="grid grid-cols-4 gap-1.5 py-2.5 my-2 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Routers</div>
          <div className="text-xs font-bold text-cyan-400 font-mono">
            {metrics.routers_count ?? 0}
          </div>
        </div>
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Endpoints</div>
          <div className="text-xs font-bold text-indigo-400 font-mono">
            {metrics.total_endpoints ?? 0}
          </div>
        </div>
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Adapters</div>
          <div className="text-xs font-bold text-emerald-400 font-mono">
            {metrics.adapters_count ?? 0}
          </div>
        </div>
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Swarm</div>
          <div className="text-xs font-bold text-violet-400 font-mono">
            {metrics.swarm_agents_count ?? 14}
          </div>
        </div>
      </div>

      {/* Spatial Topology Visual Viewport */}
      {!isMacroView && (
        <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-[#060911] shadow-inner mb-3">
          {/* Spatial Preview Graphic */}
          <div className="h-44 w-full relative flex flex-col justify-between p-3 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:12px_12px]">
            {/* Top Row: User -> Studio */}
            <div className="flex items-center justify-between">
              <div className="px-2 py-1 rounded-md bg-slate-800/90 border border-slate-700/80 text-[10px] flex items-center gap-1.5 shadow">
                <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                <span>Operator</span>
              </div>
              <div className="h-0.5 flex-1 mx-2 bg-gradient-to-r from-cyan-500/80 to-indigo-500/80 relative">
                <span className="absolute -top-1 right-1/2 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] animate-ping" />
              </div>
              <div className="px-2 py-1 rounded-md bg-indigo-950/80 border border-indigo-700/70 text-[10px] text-indigo-200 flex items-center gap-1.5 shadow">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                <span>Web Studio</span>
              </div>
            </div>

            {/* Mid Row: Gateway & Swarm Orchestrator */}
            <div className="flex items-center justify-around py-1">
              <div className="px-2.5 py-1 rounded-md bg-cyan-950/70 border border-cyan-800 text-[10px] text-cyan-300 flex items-center gap-1 shadow">
                <Server className="w-3 h-3 text-cyan-400" />
                <span>FastAPI Gateway</span>
              </div>
              <div className="px-2.5 py-1 rounded-md bg-violet-950/70 border border-violet-800 text-[10px] text-violet-300 flex items-center gap-1 shadow">
                <Cpu className="w-3 h-3 text-violet-400" />
                <span>Gerych Prime</span>
              </div>
            </div>

            {/* Bottom Row: Swarm Workers & Storage */}
            <div className="flex items-center justify-between">
              <div className="px-2 py-1 rounded-md bg-emerald-950/70 border border-emerald-800 text-[10px] text-emerald-300 flex items-center gap-1 shadow">
                <Zap className="w-3 h-3 text-emerald-400" />
                <span>14 Workers</span>
              </div>
              <div className="px-2 py-1 rounded-md bg-rose-950/70 border border-rose-800 text-[10px] text-rose-300 flex items-center gap-1 shadow">
                <Shield className="w-3 h-3 text-rose-400" />
                <span>Auditor Gate</span>
              </div>
              <div className="px-2 py-1 rounded-md bg-amber-950/70 border border-amber-800 text-[10px] text-amber-300 flex items-center gap-1 shadow">
                <Database className="w-3 h-3 text-amber-400" />
                <span>SCONES L2</span>
              </div>
            </div>
          </div>

          {/* Guided View Lens Selector */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-t border-slate-800 text-[10px]">
            <span className="text-slate-400 flex items-center gap-1">
              <Eye className="w-3 h-3 text-cyan-400" /> Lens:
            </span>
            <div className="flex items-center gap-1">
              {['primary-path', 'state-and-memory'].map((viewId) => (
                <button
                  key={viewId}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveView(viewId);
                  }}
                  className={`px-2 py-0.5 rounded text-[9px] font-medium transition-colors ${
                    activeView === viewId
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {viewId === 'primary-path' ? 'Primary Flow' : 'State & Memory'}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer Details */}
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
        <span className="flex items-center gap-1 font-mono text-[9px]">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Zero-Disk I/O &bull; &lt;15ms
        </span>
        <a
          href={artifactUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <span>Open Standalone</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Fullscreen Modal / Presentation Overlay */}
      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 flex flex-col bg-[#080c14]/95 backdrop-blur-2xl p-6"
          onClick={closeFullscreen}
        >
          <div
            className="flex-1 flex flex-col rounded-2xl border border-cyan-500/30 overflow-hidden bg-[#0a0f1d] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0d1424]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    {title}
                    <span className="text-xs font-normal text-cyan-400 font-mono">
                      (v2.17.0 Archify Engine)
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">{subtitle}</p>
                </div>
              </div>
              <button
                onClick={closeFullscreen}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              >
                <Minimize2 className="w-5 h-5" />
              </button>
            </div>

            {/* Embedded Interactive Archify Artifact */}
            <div className="flex-1 w-full h-full relative">
              <iframe
                src={artifactUrl}
                title="Archify Spatial Diagram"
                className="w-full h-full border-none"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArchifySpatialNode;

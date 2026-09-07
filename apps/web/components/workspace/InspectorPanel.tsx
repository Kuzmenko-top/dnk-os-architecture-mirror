// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_InspectorPanel"
// purpose: "Inspector Panel displaying typed contracts, live Liquid Section Editor, Video Studio Controls, Smart Note Editor, risk assessment, and node lifecycle"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.3.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React from 'react';
import { 
  X, 
  ShieldCheck, 
  ShieldAlert, 
  Bot, 
  ArrowRight, 
  Layers, 
  CheckCircle2, 
  Play, 
  Terminal,
  Activity,
  Lock,
  Trash2,
  Video,
  Film,
  Sparkles,
  FileText,
  Sliders,
  Type,
  Clock
} from 'lucide-react';
import { NODE_REGISTRY_MAP } from '../canvas/NodeRegistry';
import ShopifyInspectorSection from './ShopifyInspectorSection';

interface InspectorPanelProps {
  selectedNode: any | null;
  onClose: () => void;
  onExecuteNode?: (nodeId: string) => void;
  onDeleteNode?: (nodeId: string) => void;
  onUpdateNodeData?: (nodeId: string, updatedData: any) => void;
}

export default function InspectorPanel({
  selectedNode,
  onClose,
  onExecuteNode,
  onDeleteNode,
  onUpdateNodeData
}: InspectorPanelProps) {
  if (!selectedNode) return null;

  const nodeType = selectedNode.type || 'TaskNode';
  const isShopifyNode = nodeType === 'ShopifyBuilderNode' || nodeType.toLowerCase().includes('shopify');
  const isVideoNode = nodeType === 'VideoCreatorNode' || nodeType.toLowerCase().includes('video');
  const isNoteNode = nodeType === 'SmartNoteNode' || nodeType.toLowerCase().includes('note');
  const isSwarmNode = nodeType === 'SwarmAgentNode' || nodeType.toLowerCase().includes('swarm');

  const meta = NODE_REGISTRY_MAP[nodeType] || {
    title: selectedNode.data?.title || 'Canvas Node',
    category: isShopifyNode ? 'ecommerce' : isVideoNode ? 'media' : isNoteNode ? 'note' : 'task',
    description: isShopifyNode 
      ? 'Spatial Shopify OS 2.0 theme builder node with live AST & Liquid rendering.' 
      : isVideoNode
      ? 'Spatial video generation studio supporting 9:16 vertical reels, 16:9 cinematic widescreen, Remotion composition, and AI motion rendering.'
      : 'Custom execution node on DNK Canvas.',
    riskLevel: isShopifyNode || isVideoNode ? 'medium' : 'low',
    inputs: [],
    outputs: [],
    capabilities: []
  };

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'high':
      case 'critical':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-500/50 text-[10px] font-mono font-bold">
            <ShieldAlert className="w-3 h-3 text-rose-400" /> High Risk Gate
          </span>
        );
      case 'medium':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-500/50 text-[10px] font-mono font-bold">
            <ShieldAlert className="w-3 h-3 text-amber-400" /> Medium Risk
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 text-[10px] font-mono">
            <ShieldCheck className="w-3 h-3 text-emerald-400" /> Low Risk (Safe)
          </span>
        );
    }
  };

  return (
    <aside className="w-88 bg-slate-950/95 backdrop-blur-2xl border-l border-slate-800/80 text-slate-200 flex flex-col h-full z-20 shadow-2xl overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between sticky top-0 bg-slate-950/90 backdrop-blur-md z-10">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span className="font-bold text-xs uppercase tracking-wider text-slate-300 font-mono">
            Node Inspector
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Node Profile */}
      <div className="p-4 flex flex-col gap-4 flex-1">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold tracking-wider">
              {nodeType}
            </span>
            {getRiskBadge(meta.riskLevel)}
          </div>
          <h3 className="font-bold text-base text-white leading-snug">
            {selectedNode.data?.title || selectedNode.data?.agentName || meta.title}
          </h3>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            {meta.description}
          </p>
        </div>

        {/* Node ID */}
        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between text-xs">
          <span className="text-slate-400 font-mono text-[11px]">Node ID</span>
          <span className="font-mono text-[11px] text-slate-300 font-semibold">{selectedNode.id}</span>
        </div>

        {/* Specialized Shopify Builder Inspector */}
        {isShopifyNode && (
          <ShopifyInspectorSection
            nodeId={selectedNode.id}
            data={selectedNode.data || {}}
            onUpdateData={(nodeId, updatedData) => {
              if (onUpdateNodeData) {
                onUpdateNodeData(nodeId, updatedData);
              }
            }}
          />
        )}

        {/* Specialized Video Studio Inspector */}
        {isVideoNode && (
          <div className="flex flex-col gap-3 p-3.5 rounded-2xl bg-slate-900/80 border border-indigo-500/20">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
                <Film className="w-3 h-3" /> Remotion Video AST
              </span>
              <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                v4.0.0
              </span>
            </div>

            {/* Video Prompt Input */}
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">
                Creative Direction / Prompt
              </label>
              <textarea
                value={selectedNode.data?.prompt || ''}
                onChange={(e) => {
                  if (onUpdateNodeData) {
                    onUpdateNodeData(selectedNode.id, { prompt: e.target.value });
                  }
                }}
                rows={3}
                placeholder="High-energy kinetic product reveal with glowing particles..."
                className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 transition-all resize-none"
              />
            </div>

            {/* Aspect Ratio Selector */}
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1.5">
                Format / Aspect Ratio
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                {['9:16', '16:9', '1:1'].map((aspect) => {
                  const isSelected = (selectedNode.data?.aspectRatio || '9:16') === aspect;
                  return (
                    <button
                      key={aspect}
                      onClick={() => {
                        if (onUpdateNodeData) {
                          onUpdateNodeData(selectedNode.id, { aspectRatio: aspect });
                        }
                      }}
                      className={`py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                        isSelected
                          ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                          : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
                      }`}
                    >
                      {aspect}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Motion Style */}
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">
                Motion Aesthetic
              </label>
              <select
                value={selectedNode.data?.motionStyle || 'Cyberpunk Neon Motion'}
                onChange={(e) => {
                  if (onUpdateNodeData) {
                    onUpdateNodeData(selectedNode.id, { motionStyle: e.target.value });
                  }
                }}
                className="w-full p-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Cyberpunk Neon Motion">Cyberpunk Neon Motion</option>
                <option value="Minimalist Luxury 3D">Minimalist Luxury 3D</option>
                <option value="High-Impact Kinetic Typography">High-Impact Kinetic Typography</option>
                <option value="Organic Studio Product Flow">Organic Studio Product Flow</option>
              </select>
            </div>

            {/* Duration Slider */}
            <div>
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-slate-400">Duration</span>
                <span className="font-mono text-indigo-400 font-bold">{selectedNode.data?.duration || 15}s</span>
              </div>
              <input
                type="range"
                min={5}
                max={30}
                step={5}
                value={selectedNode.data?.duration || 15}
                onChange={(e) => {
                  if (onUpdateNodeData) {
                    onUpdateNodeData(selectedNode.id, { duration: parseInt(e.target.value, 10) });
                  }
                }}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* Specialized Smart Note Inspector */}
        {isNoteNode && (
          <div className="flex flex-col gap-3 p-3.5 rounded-2xl bg-slate-900/80 border border-cyan-500/20">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold tracking-wider flex items-center gap-1.5">
                <FileText className="w-3 h-3" /> Note Content
              </span>
            </div>
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">Title</label>
              <input
                type="text"
                value={selectedNode.data?.title || ''}
                onChange={(e) => {
                  if (onUpdateNodeData) {
                    onUpdateNodeData(selectedNode.id, { title: e.target.value });
                  }
                }}
                className="w-full p-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-[11px] text-slate-400 font-medium block mb-1">Body Text / Markdown</label>
              <textarea
                value={selectedNode.data?.content || ''}
                onChange={(e) => {
                  if (onUpdateNodeData) {
                    onUpdateNodeData(selectedNode.id, { content: e.target.value });
                  }
                }}
                rows={5}
                className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono resize-none"
              />
            </div>
          </div>
        )}

        {/* Assigned Agent (for general nodes) */}
        {!isShopifyNode && selectedNode.data?.assigned_agent && (
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-semibold text-slate-300">
                {selectedNode.data.assigned_agent}
              </span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 font-mono border border-cyan-800">
              Swarm Worker
            </span>
          </div>
        )}

        {/* Typed Input Ports */}
        {!isShopifyNode && (
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2 font-mono">
              Input Ports ({meta.inputs.length})
            </span>
            {meta.inputs.length > 0 ? (
              <div className="flex flex-col gap-1.5">
                {meta.inputs.map((port, i) => (
                  <div key={i} className="p-2 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{port.name}</span>
                    <span className="text-[10px] font-mono text-indigo-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {port.dataType}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-2 rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-[11px] text-slate-500 text-center">
                Autonomous Origin Node
              </div>
            )}
          </div>
        )}

        {/* Typed Output Ports */}
        {!isShopifyNode && (
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2 font-mono">
              Output Ports ({meta.outputs.length})
            </span>
            {meta.outputs.length > 0 ? (
              <div className="flex flex-col gap-1.5">
                {meta.outputs.map((port, i) => (
                  <div key={i} className="p-2 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{port.name}</span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {port.dataType}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-2 rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-[11px] text-slate-500 text-center">
                Terminal Execution Sink
              </div>
            )}
          </div>
        )}

        {/* Live Execution Controls & Actions */}
        <div className="pt-2 flex flex-col gap-2 border-t border-slate-800/80 mt-auto">
          {onExecuteNode && (
            <button
              onClick={() => onExecuteNode(selectedNode.id)}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Execute Node Pipeline
            </button>
          )}

          {/* Delete Node Action */}
          {onDeleteNode && (
            <button
              onClick={() => onDeleteNode(selectedNode.id)}
              className="w-full py-2 rounded-xl bg-slate-900/80 hover:bg-rose-950/60 border border-slate-800 hover:border-rose-500/50 text-slate-400 hover:text-rose-300 text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              Remove Node
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

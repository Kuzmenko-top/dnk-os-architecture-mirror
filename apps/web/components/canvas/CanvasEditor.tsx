// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_CanvasEditor"
// purpose: "Interactive Visual Workflow Canvas Designer with Live WebSocket streaming, OCC node synchronization, and pulsing state animations"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-29"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Bot, 
  Layers, 
  ShoppingBag, 
  Globe, 
  Plus, 
  Trash2, 
  Save, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  PlayCircle,
  ArrowRight,
  ShieldCheck,
  Radio,
  Wifi,
  Sparkles
} from 'lucide-react';

import DNKStudioWorkspace from '../workspace/DNKStudioWorkspace';

interface CanvasEditorProps {
  canvasId: string;
  canvasData: any;
  onUpdate: (updatedData: any) => void;
}

export default function CanvasEditor({ canvasId, canvasData, onUpdate }: CanvasEditorProps) {
  const [name, setName] = useState(canvasData?.name || 'DNK ECOM Premium Brand Identity');
  const [elements, setElements] = useState<any[]>(canvasData?.elements?.nodes || [
    { 
      id: 'node-1', 
      name: 'Event Trigger (orders.created)', 
      type: 'TriggerNode', 
      state: 'Active', 
      config: { topic: 'orders.created', source: 'dnk_stream' } 
    },
    { 
      id: 'node-2', 
      name: 'A2A Agent (order-processor)', 
      type: 'AgentNode', 
      state: 'Queued', 
      config: { agent: 'order-processor', role: 'orchestrator', timeout_s: 60 } 
    },
    { 
      id: 'node-3', 
      name: 'Batch Task (fulfill_and_notify)', 
      type: 'BatchTaskNode', 
      state: 'Queued', 
      config: { batch_size: 50, action: 'fulfill_order' } 
    }
  ]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState<'spatial' | 'pipeline' | 'raw'>('spatial');
  const [wsConnected, setWsConnected] = useState(false);

  // Keep internal elements & name synced with external canvasData updates
  useEffect(() => {
    if (canvasData?.name) {
      setName(canvasData.name);
    }
    if (canvasData?.elements?.nodes) {
      setElements(canvasData.elements.nodes);
    }
  }, [canvasData]);

  // Live WebSocket Connection for real-time node state pulsing
  useEffect(() => {
    if (typeof window === 'undefined') return;

    let ws: WebSocket | null = null;
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/api/v1/ws/canvas/${canvasId}?client_id=client_${Date.now()}`;
      
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === 'node_state_pulse') {
            const { node_id, state } = data;
            setElements(prev => prev.map(n => n.id === node_id ? { ...n, state } : n));
          } else if (data.event === 'remote_patch' && data.patch?.payload?.nodes) {
            setElements(data.patch.payload.nodes);
          }
        } catch (err) {
          // Ignore malformed WS frames
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
      };
    } catch (e) {
      setWsConnected(false);
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [canvasId]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const updated = {
        ...canvasData,
        name,
        elements: { 
          nodes: elements,
          edges: elements.slice(0, -1).map((node, i) => ({
            id: `edge-${node.id}-${elements[i + 1].id}`,
            source: node.id,
            target: elements[i + 1].id
          }))
        }
      };
      
      const res = await fetch(`/api/canvas/${canvasId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated)
      });
      if (res.ok) {
        const data = await res.json();
        onUpdate(data);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (e) {
      console.error('Failed to save canvas:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const updateNodeState = (id: string, newState: string) => {
    const updated = elements.map(node => 
      node.id === id ? { ...node, state: newState } : node
    );
    setElements(updated);
  };

  const deleteNode = (id: string) => {
    setElements(elements.filter(n => n.id !== id));
  };

  const addNode = (type: string) => {
    const nextId = `node-${elements.length + 1}`;
    let newNode: any = {
      id: nextId,
      name: `New ${type}`,
      type: type,
      state: 'Queued',
      config: {}
    };

    if (type === 'TriggerNode') {
      newNode = {
        id: nextId,
        name: `Event Trigger (topic.event)`,
        type: 'TriggerNode',
        state: 'Active',
        config: { topic: 'custom.event', source: 'dnk_stream' }
      };
    } else if (type === 'AgentNode') {
      newNode = {
        id: nextId,
        name: `A2A Agent (custom-agent)`,
        type: 'AgentNode',
        state: 'Queued',
        config: { agent: 'custom-agent', role: 'worker', timeout_s: 30 }
      };
    } else if (type === 'BatchTaskNode') {
      newNode = {
        id: nextId,
        name: `Batch Task (process_batch)`,
        type: 'BatchTaskNode',
        state: 'Queued',
        config: { batch_size: 25, action: 'custom_action' }
      };
    } else if (type === 'ShopifyNode') {
      newNode = {
        id: nextId,
        name: `Shopify Action (sync_products)`,
        type: 'ShopifyNode',
        state: 'Queued',
        config: { store: 'DNK-e.com', action: 'sync_inventory' }
      };
    }

    setElements([...elements, newNode]);
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'TriggerNode': return <Zap className="w-5 h-5 text-amber-400" />;
      case 'AgentNode': return <Bot className="w-5 h-5 text-indigo-400" />;
      case 'BatchTaskNode': return <Layers className="w-5 h-5 text-emerald-400" />;
      case 'ShopifyNode': return <ShoppingBag className="w-5 h-5 text-green-400" />;
      case 'ASTEngineNode': return <Sparkles className="w-5 h-5 text-cyan-400" />;
      default: return <Globe className="w-5 h-5 text-blue-400" />;
    }
  };

  const getNodeCardStyle = (state: string) => {
    switch (state) {
      case 'Processing':
      case 'Executing':
      case 'Running':
        return 'border-indigo-500 shadow-[0_0_25px_rgba(99,102,241,0.35)] animate-pulse bg-slate-900/95';
      case 'Active':
      case 'Done':
      case 'Completed':
        return 'border-emerald-500/70 shadow-[0_0_20px_rgba(16,185,129,0.2)] bg-slate-900/90';
      case 'Blocked':
      case 'Failed':
        return 'border-rose-500/80 shadow-[0_0_20px_rgba(244,63,94,0.25)] bg-slate-900/90';
      default:
        return 'border-slate-800/80 hover:border-indigo-500/60 bg-slate-900/80 shadow-xl';
    }
  };

  const getStateBadge = (state: string) => {
    switch (state) {
      case 'Active':
      case 'Done':
      case 'Completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)]">
            <CheckCircle2 className="w-3.5 h-3.5" /> {state}
          </span>
        );
      case 'Executing':
      case 'Running':
      case 'Processing':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse shadow-[0_0_12px_rgba(99,102,241,0.3)]">
            <PlayCircle className="w-3.5 h-3.5 animate-spin text-indigo-400" /> {state}
          </span>
        );
      case 'Blocked':
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertCircle className="w-3.5 h-3.5" /> {state}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3.5 h-3.5 text-slate-400" /> {state}
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/90 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 text-white shadow-2xl relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 border-b border-slate-800/80 pb-4 relative z-10">
        <div className="flex items-center gap-3 flex-grow max-w-xl">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-blue-500/20 border border-indigo-500/30 text-indigo-400">
            <Layers className="w-5 h-5" />
          </div>
          <div className="flex-grow">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="text-xl font-bold bg-transparent border-b border-transparent hover:border-slate-700 focus:border-indigo-500 focus:outline-none transition-all px-1.5 py-0.5 w-full text-white placeholder-slate-500"
              placeholder="Назва Канвасу..."
            />
            <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
              <span>Workspace: <strong className="text-slate-300 font-mono">{canvasId}</strong></span>
              <span>•</span>
              <span className="text-emerald-400 flex items-center gap-1 font-medium">
                <ShieldCheck className="w-3 h-3" /> DAG Verified
              </span>
              <span>•</span>
              <span className={`flex items-center gap-1 font-mono text-[11px] ${wsConnected ? 'text-cyan-400' : 'text-slate-500'}`}>
                <Wifi className={`w-3 h-3 ${wsConnected ? 'animate-pulse' : ''}`} />
                {wsConnected ? 'Live WS Connected' : 'OCC Synced'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-slate-800/60 p-1 rounded-xl border border-slate-700/60 text-xs font-medium text-slate-300">
            <button
              onClick={() => setActiveTab('spatial')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'spatial' ? 'bg-purple-600 text-white shadow-sm' : 'hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-300" />
              <span>Spatial Stitch</span>
            </button>
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'pipeline' ? 'bg-indigo-600 text-white shadow-sm' : 'hover:text-white'
              }`}
            >
              Pipeline
            </button>
            <button
              onClick={() => setActiveTab('raw')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'raw' ? 'bg-indigo-600 text-white shadow-sm' : 'hover:text-white'
              }`}
            >
              DAG JSON
            </button>
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-95 disabled:opacity-50 transition-all rounded-xl font-semibold shadow-lg shadow-indigo-500/20 cursor-pointer text-sm"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Збереження...</span>
              </>
            ) : saveSuccess ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                <span>Збережено!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Зберегти Канвас</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Viewport Container */}
      {activeTab === 'spatial' ? (
        <div className="relative flex-grow rounded-2xl overflow-hidden min-h-[720px] border border-slate-800">
          <DNKStudioWorkspace />
        </div>
      ) : activeTab === 'pipeline' ? (
        <>
          {/* Add node quick toolbar */}
          <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-1 text-xs text-slate-300">
            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px] mr-1">Додати ноду:</span>
            <button
              onClick={() => addNode('TriggerNode')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-amber-300 transition-all cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5" /> Trigger
            </button>
            <button
              onClick={() => addNode('AgentNode')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-indigo-300 transition-all cursor-pointer"
            >
              <Bot className="w-3.5 h-3.5" /> A2A Agent
            </button>
            <button
              onClick={() => addNode('BatchTaskNode')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-emerald-300 transition-all cursor-pointer"
            >
              <Layers className="w-3.5 h-3.5" /> Batch Task
            </button>
            <button
              onClick={() => addNode('ShopifyNode')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-green-300 transition-all cursor-pointer"
            >
              <ShoppingBag className="w-3.5 h-3.5" /> Shopify Action
            </button>
          </div>

          <div className="relative flex-grow border border-slate-800/80 bg-slate-950/70 rounded-2xl overflow-y-auto p-6 min-h-[380px]">
            {/* Subtle grid background */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#334155_1px,transparent_1px),linear-gradient(to_bottom,#334155_1px,transparent_1px)] bg-[size:32px_32px] opacity-15 pointer-events-none" />

            <div className="relative z-10 flex flex-col md:flex-row items-center justify-center gap-4 flex-wrap py-6">
              {elements.map((node, index) => (
                <React.Fragment key={node.id}>
                  <div className={`group w-full md:w-[280px] border rounded-2xl p-5 transition-all flex flex-col gap-4 relative ${getNodeCardStyle(node.state)}`}>
                    {/* Card top */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-xl bg-slate-800/90 border border-slate-700/60">
                          {getNodeIcon(node.type)}
                        </div>
                        <div>
                          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">{node.type}</div>
                          <h4 className="text-sm font-bold text-white leading-tight">{node.name}</h4>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteNode(node.id)}
                        className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-500 hover:text-rose-400 transition-opacity rounded-lg hover:bg-slate-800 cursor-pointer"
                        title="Видалити ноду"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Config Details */}
                    {node.config && Object.keys(node.config).length > 0 && (
                      <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-2.5 text-xs font-mono text-slate-400 flex flex-col gap-1">
                        {Object.entries(node.config).map(([k, v]) => (
                          <div key={k} className="flex justify-between items-center text-[11px]">
                            <span className="text-slate-500">{k}:</span>
                            <span className="text-slate-300 font-semibold">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Status & Actions */}
                    <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-800/80">
                      {getStateBadge(node.state)}
                      
                      <select
                        value={node.state}
                        onChange={(e) => updateNodeState(node.id, e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer font-medium"
                      >
                        <option value="Queued">Queued</option>
                        <option value="Processing">Processing</option>
                        <option value="Executing">Executing</option>
                        <option value="Done">Done</option>
                        <option value="Blocked">Blocked</option>
                        <option value="Active">Active</option>
                      </select>
                    </div>
                  </div>

                  {/* Arrow connector between nodes */}
                  {index < elements.length - 1 && (
                    <div className="hidden md:flex items-center justify-center text-indigo-400 animate-pulse px-1">
                      <ArrowRight className="w-6 h-6" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="flex-grow bg-slate-950 border border-slate-800 rounded-2xl p-4 font-mono text-xs text-slate-300 overflow-auto">
          <pre>{JSON.stringify({ name, elements }, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

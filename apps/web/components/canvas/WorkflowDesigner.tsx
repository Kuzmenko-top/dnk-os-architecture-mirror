// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_workflow_designer"
// purpose: "Visual Canvas MVP Interactive Workflow Designer with React Flow (DNK-CANVAS-001 Phase 3)"
// author: "DNK-e.com Maksym"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-29"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  Node,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  A2AAgentNode,
  EventTriggerNode,
  BatchTaskNode,
  ShopifyActionNode,
  HardwareActionNode
} from './nodes/WorkflowCustomNodes';
import {
  Play,
  Square,
  CheckCircle2,
  Save,
  Plus,
  RefreshCw,
  Layers,
  Sparkles,
  Zap,
  Bot,
  Cpu,
  ShoppingBag,
  Radio,
  Sliders,
  AlertCircle
} from 'lucide-react';

const nodeTypes = {
  a2a_agent: A2AAgentNode,
  event_trigger: EventTriggerNode,
  batch_task: BatchTaskNode,
  shopify_action: ShopifyActionNode,
  hardware_action: HardwareActionNode
};

const initialNodes: Node[] = [
  {
    id: 'trigger-1',
    type: 'event_trigger',
    position: { x: 250, y: 50 },
    data: {
      label: 'Shopify Webhook Trigger',
      node_type: 'event_trigger',
      config: { stream_name: 'shopify-stream', event_type: 'orders/create', debounce_ms: 100 }
    }
  },
  {
    id: 'agent-1',
    type: 'a2a_agent',
    position: { x: 250, y: 220 },
    data: {
      label: 'Fraud & Inventory Auditor',
      node_type: 'a2a_agent',
      config: { agent_id: 'gerych_auditor', protocol: 'DNK-A2A-004', consensus_threshold: 0.85 }
    }
  },
  {
    id: 'shopify-1',
    type: 'shopify_action',
    position: { x: 100, y: 400 },
    data: {
      label: 'Shopify Fulfillment',
      node_type: 'shopify_action',
      config: { action_type: 'create_order', api_version: '2026-07' }
    }
  },
  {
    id: 'hardware-1',
    type: 'hardware_action',
    position: { x: 400, y: 400 },
    data: {
      label: 'ReBurn Packaging Actuator',
      node_type: 'hardware_action',
      config: { device_id: 'reburn-station-01', action_type: 'trigger_actuator' }
    }
  }
];

const initialEdges: Edge[] = [
  { id: 'e-t1-a1', source: 'trigger-1', target: 'agent-1', animated: true },
  { id: 'e-a1-s1', source: 'agent-1', target: 'shopify-1' },
  { id: 'e-a1-h1', source: 'agent-1', target: 'hardware-1' }
];

export default function WorkflowDesigner() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflowId, setWorkflowId] = useState('wf-visual-canvas-001');
  const [workflowName, setWorkflowName] = useState('Smart Order & ReBurn Hardware Automation');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; message: string } | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [activeTab, setActiveTab] = useState<'canvas' | 'templates' | 'logs'>('canvas');

  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)), [setEdges]);

  const addNode = (type: string) => {
    const id = `${type}-${Date.now()}`;
    let label = 'New Node';
    let config: Record<string, any> = {};

    switch (type) {
      case 'a2a_agent':
        label = 'A2A Agent Node';
        config = { agent_id: 'dnk_dev_fullstack', protocol: 'DNK-A2A-004', consensus_threshold: 0.8 };
        break;
      case 'event_trigger':
        label = 'Event Trigger';
        config = { stream_name: 'dnk-stream', event_type: 'system/event', debounce_ms: 0 };
        break;
      case 'batch_task':
        label = 'Batch DAG Task';
        config = { task_type: 'data_processing', timeout_sec: 300 };
        break;
      case 'shopify_action':
        label = 'Shopify Action';
        config = { action_type: 'update_inventory', api_version: '2026-07' };
        break;
      case 'hardware_action':
        label = 'ReBurn Hardware Action';
        config = { device_id: 'reburn-ctrl-01', action_type: 'gpio_write' };
        break;
    }

    const newNode: Node = {
      id,
      type,
      position: { x: 250 + (Math.random() * 80 - 40), y: 200 + (Math.random() * 80 - 40) },
      data: { label, node_type: type, config }
    };

    setNodes((nds) => [...nds, newNode]);
  };

  const validateDAG = async () => {
    try {
      const payload = {
        id: workflowId,
        name: workflowName,
        nodes: nodes.map((n) => ({
          id: n.id,
          name: n.data?.label || n.id,
          node_type: n.type || 'a2a_agent',
          position_x: n.position.x,
          position_y: n.position.y,
          config: n.data?.config || {}
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target
        }))
      };

      const res = await fetch('/api/v1/canvas/workflows/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setValidationResult({
          valid: true,
          message: `DAG Valid! ${data.nodes_count} nodes, ${data.edges_count} edges. Topo order: ${data.topological_order?.join(' → ')}`
        });
      } else {
        const err = await res.json();
        setValidationResult({
          valid: false,
          message: `Validation Error: ${err.detail || 'Invalid DAG structure'}`
        });
      }
    } catch (e: any) {
      setValidationResult({ valid: false, message: `Validation Error: ${e.message}` });
    }
  };

  const saveWorkflow = async () => {
    try {
      const payload = {
        id: workflowId,
        name: workflowName,
        workspace_id: 'ws-alpha-001',
        nodes: nodes.map((n) => ({
          id: n.id,
          name: n.data?.label || n.id,
          node_type: n.type || 'a2a_agent',
          position_x: n.position.x,
          position_y: n.position.y,
          config: n.data?.config || {}
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target
        }))
      };

      const res = await fetch('/api/v1/canvas/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setExecutionLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ✅ Workflow saved successfully!`]);
      }
    } catch (e: any) {
      setExecutionLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ❌ Save failed: ${e.message}`]);
    }
  };

  const executeWorkflow = async () => {
    setIsExecuting(true);
    setExecutionLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] 🚀 Initiating DAG Execution...`]);
    await saveWorkflow();

    try {
      const res = await fetch(`/api/v1/canvas/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ execution_mode: 'sequential', initial_payload: { trigger_source: 'manual' } })
      });

      if (res.ok) {
        const summary = await res.json();
        setExecutionLogs((prev) => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] ✅ Execution finished! Status: ${summary.status}, Duration: ${summary.duration_ms}ms`,
          ...Object.entries(summary.step_results || {}).map(
            ([step, res]: any) => `  ↳ [${step}]: ${res.status} (${res.node_type})`
          )
        ]);
        // Update nodes status
        setNodes((nds) =>
          nds.map((n) => ({
            ...n,
            data: {
              ...n.data,
              status: summary.step_results?.[n.id]?.status || 'completed'
            }
          }))
        );
      }
    } catch (e: any) {
      setExecutionLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ❌ Execution failed: ${e.message}`]);
    } finally {
      setIsExecuting(false);
    }
  };

  const applyTemplate = (templateType: string) => {
    if (templateType === 'shopify-fulfillment') {
      setWorkflowName('Shopify Automated Order Fulfillment');
      setNodes([
        {
          id: 'trig-ord',
          type: 'event_trigger',
          position: { x: 250, y: 50 },
          data: { label: 'New Order Webhook', node_type: 'event_trigger', config: { stream_name: 'shopify-orders', event_type: 'orders/create' } }
        },
        {
          id: 'agent-verify',
          type: 'a2a_agent',
          position: { x: 250, y: 200 },
          data: { label: 'A2A Auditor Agent', node_type: 'a2a_agent', config: { agent_id: 'gerych_auditor', consensus_threshold: 0.9 } }
        },
        {
          id: 'shop-fulfill',
          type: 'shopify_action',
          position: { x: 250, y: 350 },
          data: { label: 'Create Fulfillment', node_type: 'shopify_action', config: { action_type: 'create_order', api_version: '2026-07' } }
        }
      ]);
      setEdges([
        { id: 'e1', source: 'trig-ord', target: 'agent-verify', animated: true },
        { id: 'e2', source: 'agent-verify', target: 'shop-fulfill', animated: true }
      ]);
    } else if (templateType === 'reburn-hardware') {
      setWorkflowName('ReBurn IoT Sensor Monitor & Actuator Alert');
      setNodes([
        {
          id: 'hw-sensor',
          type: 'hardware_action',
          position: { x: 250, y: 50 },
          data: { label: 'ReBurn Thermal Sensor', node_type: 'hardware_action', config: { device_id: 'reburn-temp-01', action_type: 'read_sensor' } }
        },
        {
          id: 'agent-diag',
          type: 'a2a_agent',
          position: { x: 250, y: 200 },
          data: { label: 'Diagnostic Agent', node_type: 'a2a_agent', config: { agent_id: 'dnk_security_guard' } }
        },
        {
          id: 'hw-actuator',
          type: 'hardware_action',
          position: { x: 250, y: 350 },
          data: { label: 'Safety Valve Actuator', node_type: 'hardware_action', config: { device_id: 'reburn-valve-01', action_type: 'trigger_actuator' } }
        }
      ]);
      setEdges([
        { id: 'e1', source: 'hw-sensor', target: 'agent-diag', animated: true },
        { id: 'e2', source: 'agent-diag', target: 'hw-actuator', animated: true }
      ]);
    }
    setActiveTab('canvas');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-zinc-950 text-zinc-100">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/80 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-cyan-950 p-2 text-cyan-400 border border-cyan-500/40">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <input
                type="text"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="bg-transparent font-bold text-zinc-100 text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500 rounded px-1"
              />
              <div className="text-[11px] text-zinc-400">ID: {workflowId} • DNK OS Workflow DAG Designer</div>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setActiveTab(activeTab === 'templates' ? 'canvas' : 'templates')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              activeTab === 'templates'
                ? 'bg-cyan-600 text-white border-cyan-500'
                : 'bg-zinc-800/80 text-zinc-300 border-zinc-700 hover:bg-zinc-700'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Templates
          </button>
          <button
            onClick={validateDAG}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800/80 text-zinc-300 border border-zinc-700 hover:bg-zinc-700 transition"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Validate DAG
          </button>
          <button
            onClick={saveWorkflow}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800/80 text-zinc-300 border border-zinc-700 hover:bg-zinc-700 transition"
          >
            <Save className="w-3.5 h-3.5 text-amber-400" /> Save
          </button>
          <button
            onClick={executeWorkflow}
            disabled={isExecuting}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600 text-white border border-cyan-400 hover:bg-cyan-500 transition disabled:opacity-50 shadow-lg shadow-cyan-900/30"
          >
            <Play className="w-3.5 h-3.5 fill-current" /> {isExecuting ? 'Executing...' : 'Run Workflow'}
          </button>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Node Palette Sidebar */}
        <div className="w-64 border-r border-zinc-800 bg-zinc-900/50 p-4 flex flex-col gap-4">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-400">Node Palette</div>
          <div className="space-y-2">
            <button
              onClick={() => addNode('event_trigger')}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl border border-amber-500/30 bg-amber-950/20 hover:bg-amber-950/40 text-amber-300 text-xs font-semibold transition text-left"
            >
              <Zap className="w-4 h-4" /> Event Trigger Node
            </button>
            <button
              onClick={() => addNode('a2a_agent')}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl border border-cyan-500/30 bg-cyan-950/20 hover:bg-cyan-950/40 text-cyan-300 text-xs font-semibold transition text-left"
            >
              <Bot className="w-4 h-4" /> A2A Agent Node
            </button>
            <button
              onClick={() => addNode('shopify_action')}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 hover:bg-emerald-950/40 text-emerald-300 text-xs font-semibold transition text-left"
            >
              <ShoppingBag className="w-4 h-4" /> Shopify Action Node
            </button>
            <button
              onClick={() => addNode('hardware_action')}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl border border-purple-500/30 bg-purple-950/20 hover:bg-purple-950/40 text-purple-300 text-xs font-semibold transition text-left"
            >
              <Radio className="w-4 h-4" /> Hardware Action Node
            </button>
            <button
              onClick={() => addNode('batch_task')}
              className="w-full flex items-center gap-2.5 p-2.5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 hover:bg-indigo-950/40 text-indigo-300 text-xs font-semibold transition text-left"
            >
              <Cpu className="w-4 h-4" /> Batch Task Node
            </button>
          </div>

          {validationResult && (
            <div
              className={`p-3 rounded-xl border text-[11px] mt-2 ${
                validationResult.valid
                  ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                  : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
              }`}
            >
              {validationResult.message}
            </div>
          )}

          {/* Execution Logs Drawer */}
          <div className="flex-1 flex flex-col mt-2 border-t border-zinc-800 pt-3">
            <div className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 mb-2">Live Execution Log</div>
            <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-1 bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80">
              {executionLogs.length === 0 && <span className="text-zinc-600">No execution events yet...</span>}
              {executionLogs.map((log, idx) => (
                <div key={idx} className="text-zinc-300">{log}</div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Canvas / Templates View */}
        <div className="flex-1 relative bg-zinc-950">
          {activeTab === 'templates' ? (
            <div className="p-8 max-w-4xl mx-auto space-y-6">
              <div>
                <h2 className="text-xl font-bold text-zinc-100">Workflow Templates Gallery</h2>
                <p className="text-sm text-zinc-400">Select a pre-built e-commerce or ReBurn hardware integration template to import into Visual Canvas.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  onClick={() => applyTemplate('shopify-fulfillment')}
                  className="p-5 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 hover:border-emerald-500 cursor-pointer transition flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                      <ShoppingBag className="w-5 h-5" /> Shopify Order Fulfillment
                    </div>
                    <p className="text-xs text-zinc-400">Listens for new orders, performs fraud & stock audit via A2A mesh, and creates fulfillment in Shopify.</p>
                  </div>
                  <span className="text-xs font-semibold text-emerald-400">Import Template →</span>
                </div>

                <div
                  onClick={() => applyTemplate('reburn-hardware')}
                  className="p-5 rounded-2xl border border-purple-500/30 bg-purple-950/10 hover:border-purple-500 cursor-pointer transition flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-purple-400 font-semibold text-sm">
                      <Radio className="w-5 h-5" /> ReBurn Hardware Monitor & Actuator
                    </div>
                    <p className="text-xs text-zinc-400">Reads real-time thermal/pressure sensors, runs diagnostic agent, and triggers automated safety valves.</p>
                  </div>
                  <span className="text-xs font-semibold text-purple-400">Import Template →</span>
                </div>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
              className="bg-zinc-950"
            >
              <Background color="#27272a" gap={16} size={1} variant={BackgroundVariant.Dots} />
              <Controls className="!bg-zinc-900 !border-zinc-800 !text-zinc-200" />
              <MiniMap
                className="!bg-zinc-900/90 !border-zinc-800"
                nodeColor={(n) => {
                  switch (n.type) {
                    case 'a2a_agent': return '#06b6d4';
                    case 'event_trigger': return '#f59e0b';
                    case 'shopify_action': return '#10b981';
                    case 'hardware_action': return '#a855f7';
                    case 'batch_task': return '#6366f1';
                    default: return '#71717a';
                  }
                }}
              />
            </ReactFlow>
          )}
        </div>
      </div>
    </div>
  );
}

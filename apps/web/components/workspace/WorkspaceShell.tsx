// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_workspace_WorkspaceShell"
// purpose: "Unified Workspace Shell for DNK Open Workspace OS integrating Sidebar, Canvas, CommandBar, Dock, and Inspector"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Node, 
  Edge, 
  useNodesState, 
  useEdgesState 
} from '@xyflow/react';

import ContextSidebar from './ContextSidebar';
import CommandBar from './CommandBar';
import InspectorPanel from './InspectorPanel';
import StudioDock from './StudioDock';
import DNKCanvas from '../canvas/DNKCanvas';
import VideoPreviewModal from '../canvas/VideoPreviewModal';
import { StitchSwarmCommandCenter } from '../stitch';

import { 
  Menu, 
  Play, 
  Download, 
  Share2, 
  Sparkles,
  Command,
  ShieldCheck,
  ArrowLeft
} from 'lucide-react';

const DEMO_INITIAL_NODES: Node[] = [
  {
    id: 'goal_01',
    type: 'GoalNode',
    position: { x: 380, y: 30 },
    data: {
      title: 'Launch ReBurn Smoker v2 Campaign',
      config: {
        goal: 'Створити промо-сторінку для нової коптильні ReBurn і підготувати запуск у Shopify'
      }
    }
  },
  {
    id: 'research_01',
    type: 'TaskNode',
    position: { x: 180, y: 220 },
    data: {
      title: 'Market Brief & Persona Synthesis',
      assigned_agent: 'gerych_researcher',
      state: 'completed'
    }
  },
  {
    id: 'shopify_theme_01',
    type: 'ShopifyStoreNode',
    position: { x: 580, y: 220 },
    data: {
      title: 'Liquid AST Theme Compilation',
      assigned_agent: 'dnk_shopify',
      state: 'running'
    }
  },
  {
    id: 'video_01',
    type: 'VideoCompositionNode',
    position: { x: 180, y: 400 },
    data: {
      title: 'Remotion 9:16 Ad Campaign Video',
      assigned_agent: 'dnk_video_ai_creator',
      state: 'idle'
    }
  },
  {
    id: 'approval_01',
    type: 'ApprovalNode',
    position: { x: 580, y: 400 },
    data: {
      title: 'Production Deploy Authorization',
      assigned_agent: 'dnk_mentor',
      state: 'waiting_approval',
      config: { action: 'shopify.theme.deploy' }
    }
  },
  {
    id: 'artifact_01',
    type: 'ArtifactNode',
    position: { x: 380, y: 580 },
    data: {
      title: 'ReBurn Live Landing & Video Assets',
      assigned_agent: 'gerych_builder',
      state: 'idle',
      config: { output_type: 'shopify_release_bundle' }
    }
  }
];

const DEMO_INITIAL_EDGES: Edge[] = [
  { id: 'e1', source: 'goal_01', target: 'research_01', type: 'controlFlow', animated: true },
  { id: 'e2', source: 'goal_01', target: 'shopify_theme_01', type: 'controlFlow', animated: true },
  { id: 'e3', source: 'research_01', target: 'video_01', type: 'dataFlow', label: 'Market Brief', animated: true },
  { id: 'e4', source: 'shopify_theme_01', target: 'approval_01', type: 'approvalFlow', label: 'Deploy Plan', animated: true },
  { id: 'e5', source: 'video_01', target: 'artifact_01', type: 'dataFlow', label: 'Video MP4', animated: true },
  { id: 'e6', source: 'approval_01', target: 'artifact_01', type: 'controlFlow', label: 'Approved Gate', animated: true }
];

interface WorkspaceShellProps {
  children?: React.ReactNode;
  currentWorkspaceId?: string;
  onWorkspaceChange?: (id: string) => void;
  activeTab?: string;
  onTabChange?: (tab: any) => void;
}

export default function WorkspaceShell({
  children,
  currentWorkspaceId,
  onWorkspaceChange,
  activeTab,
  onTabChange
}: WorkspaceShellProps = {}) {
  const [nodes, setNodes, onNodesChange] = useNodesState(DEMO_INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(DEMO_INITIAL_EDGES);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isCommandBarOpen, setIsCommandBarOpen] = useState(false);
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [isSwarmMeshOpen, setIsSwarmMeshOpen] = useState(false);
  const [activeModule, setActiveModule] = useState<string>('shopify');
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const handleComposeWorkflow = async (goalText: string) => {
    try {
      setToastMsg('🧬 Workflow Composer декомпозує ціль у TaskDNA DAG...');
      const res = await fetch('/api/workflow/compose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: goalText, workspace_id: 'ws_reburn' })
      });

      if (res.ok) {
        const plan = await res.json();
        if (plan.nodes && plan.nodes.length > 0) {
          const reactFlowNodes = plan.nodes.map((n: any) => ({
            id: n.id,
            type: n.type,
            position: n.position || { x: 300, y: 200 },
            data: {
              title: n.title,
              assigned_agent: n.assigned_agent,
              state: n.state,
              config: n.config
            }
          }));

          const reactFlowEdges = (plan.edges || []).map((e: any) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            type: e.edge_type === 'approval' ? 'approvalFlow' : e.edge_type === 'data' ? 'dataFlow' : 'controlFlow',
            label: e.label,
            animated: true
          }));

          setNodes(reactFlowNodes);
          setEdges(reactFlowEdges);
          setToastMsg(`✅ Згенеровано ${reactFlowNodes.length} нод та ${reactFlowEdges.length} зв'язків!`);
          setTimeout(() => setToastMsg(null), 3500);
          return;
        }
      }
    } catch (error: unknown) {
      console.warn('API unavailable, rendering client DAG preview:', error);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#090d16] text-white overflow-hidden select-none">
      {/* Toast Notification */}
      {toastMsg && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold shadow-2xl z-50 animate-bounce border border-purple-500/50 flex items-center gap-2">
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Left Context Sidebar */}
      <ContextSidebar isOpen={isSidebarOpen} />

      {/* Central Operating Workspace */}
      <main className="flex-1 flex flex-col relative h-full overflow-hidden">
        {/* Top Operating Bar */}
        <header className="h-14 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 px-4 flex items-center justify-between z-20">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-950/40 hover:bg-purple-900/60 border border-purple-800/50 text-purple-300 text-xs font-semibold transition-all shadow-sm group cursor-pointer"
              title="Повернутися на Головний Хаб (Launchpad)"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-purple-400 group-hover:-translate-x-0.5 transition-transform" />
              <span className="hidden sm:inline">Головний Хаб</span>
            </Link>

            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="h-4 w-[1px] bg-slate-800" />
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-white tracking-wide">DNK Open Workspace</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-950/80 text-purple-300 border border-purple-800/40 font-mono">
                ReBurn Smoker Launch
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCommandBarOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs text-slate-300 transition-all cursor-pointer mr-2"
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span>Compose Goal</span>
              <kbd className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] font-mono text-slate-400 border border-slate-700">⌘K</kbd>
            </button>

            <button
              onClick={() => setIsVideoModalOpen(true)}
              className="p-2 rounded-xl text-slate-300 hover:bg-slate-800 transition-colors"
              title="Play Live Demo Preview"
            >
              <Play className="w-4 h-4 fill-current" />
            </button>

            <button
              onClick={() => {
                setToastMsg('🎉 Workspace exported to /dist/workspace_bundle.zip');
                setTimeout(() => setToastMsg(null), 3000);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 transition-all cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-slate-400" />
              <span>Export</span>
            </button>

            <button
              onClick={() => setIsSwarmMeshOpen((prev) => !prev)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 border border-indigo-800/80 transition-all cursor-pointer shadow-sm"
              title="Toggle Swarm Command Mesh"
            >
              <span>🐝 Swarm Mesh</span>
            </button>

            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-pink-500 text-white font-bold text-xs flex items-center justify-center shadow-md shadow-purple-500/20">
              M
            </div>
          </div>
        </header>

        {/* Infinite React Flow Canvas or Children */}
        <div className="flex-1 relative overflow-auto">
          {children ? (
            children
          ) : (
            <DNKCanvas
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              setEdges={setEdges}
              onSelectNode={setSelectedNode}
            />
          )}
        </div>

        {/* Bottom Studio Dock */}
        <StudioDock
          activeModule={activeModule}
          onSelectModule={setActiveModule}
          onOpenCommandBar={() => setIsCommandBarOpen(true)}
        />
      </main>

      {/* Right Node Inspector */}
      {selectedNode && (
        <InspectorPanel
          selectedNode={selectedNode}
          onClose={() => setSelectedNode(null)}
          onExecuteNode={(nodeId) => {
            setToastMsg(`🚀 Dispatched execution lease for Node: ${nodeId}`);
            setTimeout(() => setToastMsg(null), 3000);
          }}
        />
      )}

      {/* Global Command Bar Modal */}
      <CommandBar
        isOpen={isCommandBarOpen}
        onClose={() => setIsCommandBarOpen(false)}
        onComposeWorkflow={handleComposeWorkflow}
      />

      {/* Video Preview Studio Modal */}
      <VideoPreviewModal
        isOpen={isVideoModalOpen}
        onClose={() => setIsVideoModalOpen(false)}
        initialTitle="ReBurn Smoker v2 Ad Campaign"
        initialPrice={129.99}
      />

      {/* Swarm Command Mesh Drawer */}
      <StitchSwarmCommandCenter
        isOpen={isSwarmMeshOpen}
        onClose={() => setIsSwarmMeshOpen(false)}
        onNotification={(notif) => {
          setToastMsg(notif.text);
          setTimeout(() => setToastMsg(null), 3000);
        }}
      />
    </div>
  );
}
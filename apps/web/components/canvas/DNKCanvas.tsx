// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_DNKCanvas"
// purpose: "Interactive Executable Canvas for DNK Open Workspace OS integrating typed nodes, custom edges, and selection inspector"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-08-31"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { 
  ReactFlow, 
  Background, 
  BackgroundVariant, 
  Controls,
  addEdge, 
  Connection, 
  Edge, 
  Node, 
  OnNodesChange, 
  OnEdgesChange,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import SwarmAgentNode from './nodes/SwarmAgentNode';
import ShopifyBuilderNode from './nodes/ShopifyBuilderNode';
import SmartNoteNode from './nodes/SmartNoteNode';
import VideoCreatorNode from './nodes/VideoCreatorNode';
import GoalNode from './nodes/GoalNode';
import TaskNode from './nodes/TaskNode';
import AgentNode from './nodes/AgentNode';
import ApprovalNode from './nodes/ApprovalNode';
import ArtifactNode from './nodes/ArtifactNode';
import LiveWebPreviewNode from './LiveWebPreviewNode';
import ComponentSliceNode from './ComponentSliceNode';
import TaskForestSpatialNode from './nodes/TaskForestSpatialNode';
import ArchifySpatialNode from './nodes/ArchifySpatialNode';

import DataFlowEdge from './edges/DataFlowEdge';
import ControlFlowEdge from './edges/ControlFlowEdge';
import ApprovalFlowEdge from './edges/ApprovalFlowEdge';

interface DNKCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  setEdges: React.Dispatch<React.SetStateAction<Edge[]>>;
  onSelectNode: (node: Node | null) => void;
}

function DNKCanvasInner({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  setEdges,
  onSelectNode
}: DNKCanvasProps) {
  const [gridVariant, setGridVariant] = useState<BackgroundVariant>(BackgroundVariant.Dots);
  const [gridGap, setGridGap] = useState<number>(24);

  const nodeTypes = useMemo(() => ({
    // Live Spatial Nodes
    SwarmAgentNode,
    ShopifyBuilderNode,
    SmartNoteNode,
    VideoCreatorNode,

    // Core Domain Nodes
    GoalNode,
    TaskNode,
    AgentNode,
    ApprovalNode,
    ArtifactNode,

    // Media & Visual Preview Nodes
    LiveWebPreviewNode,
    ShopifyStoreNode: ShopifyBuilderNode,
    ShopifySectionSliceNode: ComponentSliceNode,
    ComponentSliceNode,

    // Task Forest Spatial HQ Nodes (LOD 0.2x / 1.0x / 2.5x)
    TaskForestSpatialNode,
    taskForestSpatial: TaskForestSpatialNode,
    taskForestNode: TaskForestSpatialNode,

    // Archify Spatial Architecture Nodes
    ArchifySpatialNode,
    archifySpatial: ArchifySpatialNode,
    archifySpatialNode: ArchifySpatialNode,
  }), []);

  const edgeTypes = useMemo(() => ({
    dataFlow: DataFlowEdge,
    controlFlow: ControlFlowEdge,
    approvalFlow: ApprovalFlowEdge,
  }), []);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onSelectNode(node);
    },
    [onSelectNode]
  );

  const handlePaneClick = useCallback(() => {
    onSelectNode(null);
  }, [onSelectNode]);

  return (
    <div className="w-full h-full relative bg-[#090d16]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultViewport={{ x: 120, y: 80, zoom: 0.75 }}
        minZoom={0.1}
        maxZoom={2.0}
        fitViewOptions={{ padding: 0.2 }}
        className="bg-[#060a12]"
      >
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={24} 
          size={1.5} 
          color="rgba(99, 102, 241, 0.2)" 
        />
        <Controls 
          className="bg-slate-900 border border-slate-800 text-white rounded-xl shadow-xl p-1" 
          showInteractive={false}
        />
      </ReactFlow>
    </div>
  );
}

export default function DNKCanvas(props: DNKCanvasProps) {
  return (
    <ReactFlowProvider>
      <DNKCanvasInner {...props} />
    </ReactFlowProvider>
  );
}

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_canvas_CanvasEngine"
// purpose: "React Flow Canvas Engine with HTML5 Drag-and-Drop Spawning, Custom Living Note Nodes, Controls, and Viewport Sync for DNK OS Unified Working Canvas"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-03"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useCallback } from 'react';
import { ReactFlow, Background, BackgroundVariant, Controls, MiniMap, useReactFlow, ReactFlowProvider } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useCanvasStore } from '../../store/canvasStore';
import { CanvasApiClient, canvasApiClient } from '../../lib/canvasApi';

// Import all custom living notes nodes
import StrategyMarkdownNode from './nodes/StrategyMarkdownNode';
import ShopifySpecNoteNode from './nodes/ShopifySpecNoteNode';
import PhotoStudioNode from './nodes/PhotoStudioNode';
import VideoStoryboardNoteNode from './nodes/VideoStoryboardNoteNode';
import StitchArtboardNode from './nodes/StitchArtboardNode';
import MindMapIdeaNode from './nodes/MindMapIdeaNode';
import MindMapGoalNode from './nodes/MindMapGoalNode';
import MindMapTaskNode from './nodes/MindMapTaskNode';
import MindMapAgentNode from './nodes/MindMapAgentNode';
import MindMapEvidenceNode from './nodes/MindMapEvidenceNode';
import MindMapClusterNode from './nodes/MindMapClusterNode';

// Import custom flow edges
import DependencyEdge from './edges/DependencyEdge';
import RelationEdge from './edges/RelationEdge';
import MilestoneEdge from './edges/MilestoneEdge';
import { ObsidianSyncBar } from './ObsidianSyncBar';
import { SwarmHealthWidget } from './SwarmHealthWidget';
import TaskForestSpatialNode from './nodes/TaskForestSpatialNode';
import TimeTravelRail, { EvolutionHistoryItem } from './TimeTravelRail';

const nodeTypes = {
  StrategyMarkdownNode,
  ShopifySpecNoteNode,
  PhotoStudioNode,
  VideoStoryboardNoteNode,
  StitchArtboardNode,
  stitchArtboard: StitchArtboardNode,
  MindMapIdeaNode,
  mindMapIdea: MindMapIdeaNode,
  MindMapGoalNode,
  mindMapGoal: MindMapGoalNode,
  MindMapTaskNode,
  mindMapTask: MindMapTaskNode,
  MindMapAgentNode,
  mindMapAgent: MindMapAgentNode,
  MindMapEvidenceNode,
  mindMapEvidence: MindMapEvidenceNode,
  MindMapClusterNode,
  mindMapCluster: MindMapClusterNode,
  TaskForestSpatialNode,
  taskForestSpatial: TaskForestSpatialNode,
  taskForestNode: TaskForestSpatialNode,
};

const edgeTypes = {
  dependency: DependencyEdge,
  DependencyEdge,
  relation: RelationEdge,
  RelationEdge,
  milestone: MilestoneEdge,
  MilestoneEdge,
};

function CanvasFlowContent() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, setNodes, setEdges } = useCanvasStore();
  const { screenToFlowPosition, fitView } = useReactFlow();
  const [isLoadingForest, setIsLoadingForest] = React.useState(false);

  // Time-Travel event selection handler: highlight the mutated node
  const handleSelectTimeTravelEvent = useCallback((event: EvolutionHistoryItem | null) => {
    if (!event) return;
    setNodes(
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          is_time_travel_highlighted: n.id === event.node_id,
        },
      }))
    );
  }, [nodes, setNodes]);

  // Return to live head: remove all time-travel highlights
  const handleReturnToLiveHead = useCallback(() => {
    setNodes(
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          is_time_travel_highlighted: false,
        },
      }))
    );
  }, [nodes, setNodes]);

  // Load Task Forest 5-Level Spatial Hierarchy from Backend REST API
  const handleLoadTaskForest = useCallback(async () => {
    setIsLoadingForest(true);
    try {
      const res = await fetch('/api/v3/task_forest/graph');
      if (!res.ok) throw new Error('Failed to fetch task forest graph');
      const data = await res.json();
      const rawNodes = Array.isArray(data.nodes)
        ? data.nodes
        : typeof data.nodes === 'object' && data.nodes !== null
        ? Object.values(data.nodes)
        : data.raw_nodes || [];

      // Hierarchy layout positions
      const scaleY: Record<string, number> = {
        field: 60,
        sector: 260,
        tree: 560,
        bush: 920,
        flower: 1300,
      };

      const scaleCounts: Record<string, number> = {
        field: 0,
        sector: 0,
        tree: 0,
        bush: 0,
        flower: 0,
      };

      const scaleSpacing: Record<string, number> = {
        field: 500,
        sector: 460,
        tree: 420,
        bush: 380,
        flower: 360,
      };

      const newNodes = rawNodes.map((n: any) => {
        const scale = (n.plant_scale || 'flower').toLowerCase();
        const index = scaleCounts[scale] || 0;
        scaleCounts[scale] = index + 1;

        const x = 120 + index * (scaleSpacing[scale] || 400);
        const y = scaleY[scale] || 1000;

        return {
          id: n.id,
          type: 'taskForestSpatial',
          position: { x, y },
          data: {
            ...n,
            is_time_travel_highlighted: false,
          },
        };
      });

      // Construct hierarchical edges from parent_id
      const newEdges: any[] = [];
      rawNodes.forEach((n: any) => {
        if (n.parent_id) {
          newEdges.push({
            id: `edge-${n.parent_id}-${n.id}`,
            source: n.parent_id,
            target: n.id,
            type: 'dependency',
            animated: n.status === 'in_progress',
            style: { stroke: n.status === 'completed' ? '#10b981' : '#6366f1', strokeWidth: 2 },
          });
        }
      });

      setNodes(newNodes);
      setEdges(newEdges);
      setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 100);
    } catch (err) {
      console.error('Error loading Task Forest Spatial Graph:', err);
    } finally {
      setIsLoadingForest(false);
    }
  }, [setNodes, setEdges, fitView]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      const rawData = event.dataTransfer.getData('application/reactflow-data');

      if (!type) {
        return;
      }

      // Convert drop screen coordinates to flow coordinates
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      let defaultData = {};
      try {
        if (rawData) {
          defaultData = JSON.parse(rawData);
        }
      } catch (err) {
        console.error('Failed to parse dropped node data', err);
      }

      // Spawn the node using CanvasApiClient
      await (canvasApiClient || new CanvasApiClient()).spawnNode({
        type,
        title: (defaultData as any).title || 'New Spun Template',
        position,
        data: defaultData,
      }, 'node-strategy');
    },
    [screenToFlowPosition]
  );

  return (
    <div className="w-full h-full relative" onDragOver={onDragOver} onDrop={onDrop}>
      {/* Top Floating Control Bar: Obsidian Sync, Swarm Health & Task Forest Spatial HQ Loader */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 pointer-events-auto flex items-center gap-3">
        <ObsidianSyncBar />
        <button
          onClick={handleLoadTaskForest}
          disabled={isLoadingForest}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900/80 hover:text-white transition-all text-xs font-mono font-bold shadow-lg shadow-emerald-950/40 backdrop-blur-md cursor-pointer disabled:opacity-50"
        >
          <span className="text-sm">🌲</span>
          {isLoadingForest ? 'Loading Forest...' : 'Task Forest Spatial HQ'}
        </button>
        <SwarmHealthWidget />
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
      >
        <Background gap={24} size={1.5} color="#262830" variant={BackgroundVariant.Dots} />
      </ReactFlow>

      {/* Interactive Time-Travel Timeline Scrubber Rail */}
      <TimeTravelRail
        onSelectEvent={handleSelectTimeTravelEvent}
        onReturnToLiveHead={handleReturnToLiveHead}
      />
    </div>
  );
}

export default function CanvasEngine() {
  return (
    <ReactFlowProvider>
      <CanvasFlowContent />
    </ReactFlowProvider>
  );
}

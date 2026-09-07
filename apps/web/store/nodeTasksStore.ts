// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/store/nodeTasksStore.ts"
// purpose: "Zustand state store for Node Based Task & Ideas DAG System with REST API sync"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import { create } from 'zustand';
import { Node, Edge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange } from '@xyflow/react';
import {
  TaskNodeData,
  TaskEdgeData,
  GraphStats,
  NodeType,
  ExecutionStage,
  PriorityLevel,
  DependencyType,
  TaskGraphResponse,
  ArtifactFileDiff,
  NodeArtifactReport,
  VerificationResult,
  ProjectInfo,
  MarketingVideoScene,
  MarketingVideoPayload,
} from '@/types/nodeTasks';

interface NodeTasksState {
  // Projects (Multi-Tenant)
  projects: ProjectInfo[];
  activeProjectId: string;
  isProjectsLoading: boolean;

  // Raw Data
  nodesMap: Record<string, TaskNodeData>;
  edgesList: TaskEdgeData[];
  stats: GraphStats | null;
  topologicalOrder: string[];

  // Artifacts & Verification
  nodeArtifacts: Record<string, NodeArtifactReport>;
  isArtifactsLoading: boolean;
  isVerifying: boolean;
  verificationResults: Record<string, VerificationResult>;

  // Marketing Video (Slice 2)
  marketingVideos: Record<string, MarketingVideoPayload>;
  isGeneratingVideo: boolean;
  audioUrls: Record<string, string>;
  isSynthesizingVoice: Record<string, boolean>;
  isExportingVideo: Record<string, boolean>;
  videoExportStatuses: Record<string, { status: string; download_url?: string; progress?: number; duration_sec?: number; video_path?: string }>;

  // ReactFlow representations
  rfNodes: Node[];
  rfEdges: Edge[];

  // UI state
  isLoading: boolean;
  isSyncing: boolean;
  isResetting: boolean;
  isAgentRunning: boolean;
  isChatIntakeLoading: boolean;
  agentFeedback: string | null;
  chatIntakeReply: string | null;
  error: string | null;
  selectedNodeId: string | null;
  selectedNodeIds: string[];
  nodeLogs: Record<string, Array<{ timestamp: string; level: string; agent: string; message: string }>>;

  // Filters
  filterType: NodeType | 'all';
  filterStage: ExecutionStage | 'all';
  filterAgent: string;
  searchQuery: string;

  // Critical Path Method (CPM)
  showCriticalPath: boolean;
  criticalPathNodeIds: string[];
  criticalEdgeIds: string[];
  criticalPathTotalDuration: number;
  criticalPathBottlenecks: Array<{
    node_id: string;
    title: string;
    assigned_agent?: string;
    blocking_count: number;
    duration_hours: number;
    priority: string;
  }>;
  criticalPathMetrics: Record<string, {
    duration_hours: number;
    early_start: number;
    early_finish: number;
    late_start: number;
    late_finish: number;
    slack: number;
    is_critical: boolean;
  }>;
  setShowCriticalPath: (show: boolean) => void;
  fetchCriticalPath: () => Promise<void>;

  // Modals & Drawers
  isCreateNodeModalOpen: boolean;
  isCreateEdgeModalOpen: boolean;
  isChatOpen: boolean;
  chatMessages: Array<{
    id: string;
    sender: 'user' | 'gerych';
    text: string;
    timestamp: string;
    createdCount?: number;
  }>;

  // Actions
  setIsChatOpen: (open: boolean) => void;
  addChatMessage: (sender: 'user' | 'gerych', text: string, createdCount?: number) => void;
  fetchProjects: () => Promise<void>;
  setActiveProject: (projectId: string) => Promise<void>;
  createProject: (payload: {
    id?: string;
    name: string;
    slug?: string;
    description?: string;
    color?: string;
    icon?: string;
    is_active?: boolean;
  }) => Promise<{ success: boolean; project?: ProjectInfo; error?: string }>;
  fetchGraph: (projectId?: string) => Promise<void>;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedNodeIds: (ids: string[]) => void;
  setFilterType: (type: NodeType | 'all') => void;
  setFilterStage: (stage: ExecutionStage | 'all') => void;
  setFilterAgent: (agent: string) => void;
  setSearchQuery: (query: string) => void;
  setCreateNodeModalOpen: (open: boolean) => void;
  setCreateEdgeModalOpen: (open: boolean) => void;

  // Operations
  saveNodePosition: (id: string, x: number, y: number) => Promise<boolean>;
  createOrUpdateNode: (payload: Partial<TaskNodeData> & { id?: string; title: string }) => Promise<boolean>;
  deleteNode: (nodeId: string) => Promise<boolean>;
  createEdge: (source: string, target: string, depType?: DependencyType, desc?: string) => Promise<boolean>;
  deleteEdge: (edgeId: string) => Promise<boolean>;
  stageTransition: (nodeId: string, targetStage: ExecutionStage, force?: boolean) => Promise<{ success: boolean; detail?: string }>;
  convertIdea: (ideaId: string, newNodeType?: NodeType, assignedAgent?: string) => Promise<boolean>;
  syncObsidianBidirectional: () => Promise<{
    success: boolean;
    scanned?: number;
    imported?: number;
    updated?: number;
    exported?: number;
    edges_synced?: number;
  }>;
  syncObsidian: () => Promise<{
    success: boolean;
    syncedCount?: number;
    scanned?: number;
    imported?: number;
    updated?: number;
    exported?: number;
    edges_synced?: number;
  }>;
  resetBaseline: () => Promise<boolean>;
  executeAgent: (nodeId: string, mode?: string, instructions?: string) => Promise<{ success: boolean; message?: string }>;
  fetchNodeLogs: (nodeId: string) => Promise<void>;
  fetchMarketingVideo: (nodeId: string) => Promise<MarketingVideoPayload | null>;
  generateMarketingVideo: (nodeId: string) => Promise<{ success: boolean; data?: MarketingVideoPayload; error?: string }>;
  synthesizeVoiceover: (nodeId: string, voiceId?: string) => Promise<{ success: boolean; audioUrl?: string; error?: string }>;
  exportVideoMp4: (nodeId: string) => Promise<{ success: boolean; data?: { status: string; download_url?: string; progress?: number; duration_sec?: number; video_path?: string }; error?: string }>;
  fetchVideoExportStatus: (nodeId: string) => Promise<{ status: string; download_url?: string; progress?: number; duration_sec?: number; video_path?: string } | null>;
  decomposeNode: (nodeId: string, instructions?: string) => Promise<{ success: boolean; message?: string; createdCount?: number }>;
  chatIntake: (prompt: string, workspaceId?: string, defaultAgent?: string) => Promise<{ success: boolean; reply?: string; createdNodesCount?: number }>;
  autoLayoutDAG: () => Promise<{ success: boolean; count?: number }>;
  batchStageTransition: (targetStage: string, force?: boolean) => Promise<{ success: boolean; updatedCount?: number; skippedCount?: number }>;
  batchDeleteNodes: () => Promise<{ success: boolean; deletedCount?: number }>;
  batchExecuteAgent: (agentOverride?: string) => Promise<{ success: boolean; executedCount?: number }>;

  // Artifacts & Verification Actions
  fetchNodeArtifacts: (nodeId: string) => Promise<NodeArtifactReport | null>;
  acceptNodeArtifacts: (nodeId: string) => Promise<{ success: boolean; message?: string }>;
  rejectNodeArtifacts: (nodeId: string, reason?: string) => Promise<{ success: boolean; message?: string }>;
  runNodeVerification: (nodeId: string, testCommand?: string) => Promise<{ success: boolean; verified: boolean; message?: string; output?: string }>;

  // WebSocket Streaming
  ws: WebSocket | null;
  wsConnected: boolean;
  initWebSocket: () => () => void;
  closeWebSocket: () => void;
}

const STAGE_X_OFFSETS: Record<ExecutionStage, number> = {
  ideation: 50,
  architecture: 380,
  ready: 710,
  in_progress: 1040,
  testing: 1370,
  completed: 1700,
  blocked: 1040,
};

function buildRFNodesAndEdges(
  nodesMap: Record<string, TaskNodeData>,
  edgesList: TaskEdgeData[],
  selectedId: string | null,
  filterType: NodeType | 'all',
  filterStage: ExecutionStage | 'all',
  filterAgent: string,
  searchQuery: string,
  selectedIds: string[] = []
): { nodes: Node[]; edges: Edge[] } {
  const query = searchQuery.toLowerCase().trim();

  // Determine stage layout rows
  const stageCounters: Record<string, number> = {
    ideation: 0,
    architecture: 0,
    ready: 0,
    in_progress: 0,
    testing: 0,
    completed: 0,
    blocked: 0,
  };

  const rfNodes: Node[] = Object.values(nodesMap).map((taskNode) => {
    const matchesType = filterType === 'all' || taskNode.node_type === filterType;
    const matchesStage = filterStage === 'all' || taskNode.stage === filterStage;
    const matchesAgent = !filterAgent || filterAgent === 'all' || taskNode.assigned_agent.toLowerCase().includes(filterAgent.toLowerCase());
    const matchesQuery =
      !query ||
      taskNode.title.toLowerCase().includes(query) ||
      taskNode.description.toLowerCase().includes(query) ||
      taskNode.id.toLowerCase().includes(query);

    const isVisible = matchesType && matchesStage && matchesAgent && matchesQuery;

    // Use persisted positions if available, otherwise fallback to stage column layout
    const rawPos = (taskNode as any).position;
    let posX = rawPos?.x ?? taskNode.position_x;
    let posY = rawPos?.y ?? taskNode.position_y;

    if (posX === undefined || posX === null || posY === undefined || posY === null) {
      const stageKey = taskNode.stage in stageCounters ? taskNode.stage : 'ready';
      const colX = STAGE_X_OFFSETS[stageKey] || 710;
      const rowY = 50 + stageCounters[stageKey] * 150;
      stageCounters[stageKey]++;
      posX = colX;
      posY = rowY;
    }

    const isSelected = selectedIds.length > 0 ? selectedIds.includes(taskNode.id) : selectedId === taskNode.id;

    return {
      id: taskNode.id,
      type: 'taskNode',
      position: { x: posX, y: posY },
      hidden: !isVisible,
      selected: isSelected,
      data: {
        ...taskNode,
      },
    };
  });

  const rfEdges: Edge[] = edgesList.map((edge) => {
    const isSourceVisible = nodesMap[edge.source] !== undefined;
    const isTargetVisible = nodesMap[edge.target] !== undefined;

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'customDependency',
      hidden: !isSourceVisible || !isTargetVisible,
      data: {
        dependency_type: edge.dependency_type,
        description: edge.description,
        is_satisfied: edge.is_satisfied,
      },
    };
  });

  return { nodes: rfNodes, edges: rfEdges };
}

export const useNodeTasksStore = create<NodeTasksState>((set, get) => ({
  projects: [],
  activeProjectId: 'dnk_core',
  isProjectsLoading: false,

  nodesMap: {},
  edgesList: [],
  stats: null,
  topologicalOrder: [],
  rfNodes: [],
  rfEdges: [],
  ws: null,
  wsConnected: false,

  isLoading: false,
  isSyncing: false,
  isResetting: false,
  isAgentRunning: false,
  isChatIntakeLoading: false,
  agentFeedback: null,
  chatIntakeReply: null,
  error: null,
  selectedNodeId: null,
  selectedNodeIds: [],
  nodeLogs: {},
  nodeArtifacts: {},
  isArtifactsLoading: false,
  isVerifying: false,
  verificationResults: {},
  marketingVideos: {},
  isGeneratingVideo: false,
  audioUrls: {},
  isSynthesizingVoice: {},
  isExportingVideo: {},
  videoExportStatuses: {},

  filterType: 'all',
  filterStage: 'all',
  filterAgent: 'all',
  searchQuery: '',

  showCriticalPath: false,
  criticalPathNodeIds: [],
  criticalEdgeIds: [],
  criticalPathTotalDuration: 0,
  criticalPathBottlenecks: [],
  criticalPathMetrics: {},

  setShowCriticalPath: (show: boolean) => {
    set({ showCriticalPath: show });
    if (show) {
      get().fetchCriticalPath();
    }
  },

  fetchCriticalPath: async () => {
    try {
      const activeProj = get().activeProjectId;
      const url = activeProj ? `/api/v3/node_tasks/critical_path?project_id=${encodeURIComponent(activeProj)}` : '/api/v3/node_tasks/critical_path';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch critical path');
      const data = await res.json();
      if (data.status === 'success') {
        set({
          criticalPathNodeIds: data.critical_path_node_ids || [],
          criticalEdgeIds: data.critical_edge_ids || [],
          criticalPathTotalDuration: data.total_duration_hours || 0,
          criticalPathBottlenecks: data.bottlenecks || [],
          criticalPathMetrics: data.node_metrics || {},
        });
      }
    } catch (e) {
      console.error('Error fetching critical path:', e);
    }
  },

  isCreateNodeModalOpen: false,
  isCreateEdgeModalOpen: false,
  isChatOpen: false,
  chatMessages: [
    {
      id: 'm-init',
      sender: 'gerych',
      text: 'Привіт, Максиме! Я Герич — твій AI Swarm Manager. Опиши ідею, задачу чи ціль, і я миттєво трансформую її в структуровані ноди графа з правильними агентами та залежностями.',
      timestamp: 'Щойно',
    },
  ],

  setIsChatOpen: (open: boolean) => set({ isChatOpen: open }),
  addChatMessage: (sender: 'user' | 'gerych', text: string, createdCount?: number) => {
    set((state) => ({
      chatMessages: [
        ...state.chatMessages,
        {
          id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
          sender,
          text,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          createdCount,
        },
      ],
    }));
  },

  fetchProjects: async () => {
    set({ isProjectsLoading: true });
    try {
      const res = await fetch('/api/v3/node_tasks/projects');
      if (!res.ok) {
        throw new Error(`Failed to load projects: ${res.statusText}`);
      }
      const data = await res.json().catch(() => null);
      if (data && Array.isArray(data.projects)) {
        set({ projects: data.projects, isProjectsLoading: false });
      } else {
        set({ isProjectsLoading: false });
      }
    } catch (err: unknown) {
      console.error('[nodeTasksStore] fetchProjects error:', err);
      set({ isProjectsLoading: false });
    }
  },

  setActiveProject: async (projectId: string) => {
    set({ activeProjectId: projectId, selectedNodeId: null, selectedNodeIds: [] });
    await get().fetchGraph(projectId);
  },

  createProject: async (payload: {
    id?: string;
    name: string;
    slug?: string;
    description?: string;
    color?: string;
    icon?: string;
    is_active?: boolean;
  }) => {
    try {
      const res = await fetch('/api/v3/node_tasks/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => null);
      if (!res.ok || (data && data.status === 'error')) {
        return { success: false, error: data?.detail || 'Failed to create project' };
      }
      await get().fetchProjects();
      if (data?.project?.id) {
        await get().setActiveProject(data.project.id);
      }
      return { success: true, project: data?.project };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, error: msg };
    }
  },

  fetchGraph: async (projectId?: string) => {
    set({ isLoading: true, error: null });
    try {
      const targetProjectId = projectId || get().activeProjectId || 'dnk_core';
      const res = await fetch(`/api/v3/node_tasks/graph?project_id=${encodeURIComponent(targetProjectId)}`);
      if (!res.ok) {
        throw new Error(`Failed to load graph: ${res.statusText}`);
      }
      const data: TaskGraphResponse | null = await res.json().catch(() => null);
      if (!data || !data.graph) {
        throw new Error('Received invalid or empty graph data from server');
      }
      const rawNodes = data.graph.nodes || {};
      const nodesMap: Record<string, TaskNodeData> = {};
      Object.entries(rawNodes).forEach(([id, item]) => {
        const rawPos = (item as any).position;
        const px = rawPos?.x ?? item.position_x;
        const py = rawPos?.y ?? item.position_y;
        nodesMap[id] = {
          ...item,
          position_x: px,
          position_y: py,
          position: px !== undefined && py !== undefined ? { x: px, y: py } : undefined,
        };
      });
      const rawEdges = data.graph.edges || [];
      const edgesList: TaskEdgeData[] = rawEdges.map((edge: any) => ({
        ...edge,
        dependency_type: edge.dependency_type || edge.relation || 'depends_on',
        relation: edge.relation || edge.dependency_type || 'depends_on',
      }));

      const { nodes, edges } = buildRFNodesAndEdges(
        nodesMap,
        edgesList,
        get().selectedNodeId,
        get().filterType,
        get().filterStage,
        get().filterAgent,
        get().searchQuery
      );

      const rawStats = (data.stats || {}) as any;
      const normalizedStats: GraphStats = {
        total_nodes: rawStats.total_nodes ?? Object.keys(nodesMap).length,
        ideas_count: rawStats.ideas_count ?? rawStats.by_type?.idea ?? 0,
        epics_count: rawStats.epics_count ?? rawStats.by_type?.epic ?? 0,
        tasks_count: rawStats.tasks_count ?? rawStats.by_type?.task ?? 0,
        slices_count: rawStats.slices_count ?? rawStats.by_type?.slice ?? 0,
        gates_count: rawStats.gates_count ?? rawStats.by_type?.gate ?? 0,
        blocked_count: rawStats.blocked_count ?? rawStats.blocked_nodes_count ?? 0,
        ready_count: rawStats.ready_count ?? rawStats.by_stage?.ready ?? 0,
        in_progress_count: rawStats.in_progress_count ?? rawStats.by_stage?.in_progress ?? 0,
        completed_count: rawStats.completed_count ?? rawStats.by_stage?.completed ?? 0,
        overall_progress: rawStats.overall_progress ?? rawStats.overall_progress_pct ?? 0,
        agent_workload: rawStats.agent_workload || {},
        by_type: rawStats.by_type || {
          idea: rawStats.ideas_count ?? 0,
          epic: rawStats.epics_count ?? 0,
          task: rawStats.tasks_count ?? 0,
          slice: rawStats.slices_count ?? 0,
          gate: rawStats.gates_count ?? 0,
        },
        by_stage: rawStats.by_stage || {
          ready: rawStats.ready_count ?? 0,
          in_progress: rawStats.in_progress_count ?? 0,
          completed: rawStats.completed_count ?? 0,
        },
        blocked_nodes_count: rawStats.blocked_nodes_count ?? rawStats.blocked_count ?? 0,
        overall_progress_pct: rawStats.overall_progress_pct ?? rawStats.overall_progress ?? 0,
        edge_count: edgesList.length,
      };

      set({
        nodesMap,
        edgesList,
        stats: normalizedStats,
        topologicalOrder: data.topological_order || [],
        rfNodes: nodes,
        rfEdges: edges,
        isLoading: false,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg, isLoading: false });
    }
  },

  onNodesChange: (changes: NodeChange[]) => {
    set((state) => {
      const nextNodes = applyNodeChanges(changes, state.rfNodes);
      // Persist dragged positions into nodesMap
      const updatedMap = { ...state.nodesMap };
      changes.forEach((ch) => {
        if (ch.type === 'position' && ch.position && updatedMap[ch.id]) {
          updatedMap[ch.id] = {
            ...updatedMap[ch.id],
            position_x: ch.position.x,
            position_y: ch.position.y,
            position: { x: ch.position.x, y: ch.position.y },
          };
        }
      });

      let selectedNodeIds = state.selectedNodeIds;
      const selectChanges = changes.filter((ch) => ch.type === 'select');
      if (selectChanges.length > 0) {
        selectedNodeIds = nextNodes.filter((n) => n.selected).map((n) => n.id);
      }

      return {
        rfNodes: nextNodes,
        nodesMap: updatedMap,
        selectedNodeIds,
        selectedNodeId: selectedNodeIds.length === 1 ? selectedNodeIds[0] : (selectedNodeIds.length === 0 ? null : state.selectedNodeId),
      };
    });
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    set((state) => ({
      rfEdges: applyEdgeChanges(changes, state.rfEdges),
    }));
  },

  setSelectedNodeId: (id: string | null) => {
    set((state) => {
      const selectedIds = id ? [id] : [];
      const rfNodes = state.rfNodes.map((n) => ({
        ...n,
        selected: n.id === id,
      }));
      return {
        selectedNodeId: id,
        selectedNodeIds: selectedIds,
        agentFeedback: null,
        rfNodes,
      };
    });
  },

  setSelectedNodeIds: (ids: string[]) => {
    set((state) => {
      const singleId = ids.length === 1 ? ids[0] : (ids.length === 0 ? null : state.selectedNodeId);
      const rfNodes = state.rfNodes.map((n) => ({
        ...n,
        selected: ids.includes(n.id),
      }));
      return {
        selectedNodeIds: ids,
        selectedNodeId: singleId,
        rfNodes,
      };
    });
  },

  setFilterType: (filterType: NodeType | 'all') => {
    set((state) => {
      const { nodes, edges } = buildRFNodesAndEdges(
        state.nodesMap,
        state.edgesList,
        state.selectedNodeId,
        filterType,
        state.filterStage,
        state.filterAgent,
        state.searchQuery
      );
      return { filterType, rfNodes: nodes, rfEdges: edges };
    });
  },

  setFilterStage: (filterStage: ExecutionStage | 'all') => {
    set((state) => {
      const { nodes, edges } = buildRFNodesAndEdges(
        state.nodesMap,
        state.edgesList,
        state.selectedNodeId,
        state.filterType,
        filterStage,
        state.filterAgent,
        state.searchQuery
      );
      return { filterStage, rfNodes: nodes, rfEdges: edges };
    });
  },

  setFilterAgent: (filterAgent: string) => {
    set((state) => {
      const { nodes, edges } = buildRFNodesAndEdges(
        state.nodesMap,
        state.edgesList,
        state.selectedNodeId,
        state.filterType,
        state.filterStage,
        filterAgent,
        state.searchQuery
      );
      return { filterAgent, rfNodes: nodes, rfEdges: edges };
    });
  },

  setSearchQuery: (searchQuery: string) => {
    set((state) => {
      const { nodes, edges } = buildRFNodesAndEdges(
        state.nodesMap,
        state.edgesList,
        state.selectedNodeId,
        state.filterType,
        state.filterStage,
        state.filterAgent,
        searchQuery
      );
      return { searchQuery, rfNodes: nodes, rfEdges: edges };
    });
  },

  setCreateNodeModalOpen: (open: boolean) => set({ isCreateNodeModalOpen: open }),
  setCreateEdgeModalOpen: (open: boolean) => set({ isCreateEdgeModalOpen: open }),

  saveNodePosition: async (id: string, x: number, y: number) => {
    const state = get();
    const existingNode = state.nodesMap[id];
    if (!existingNode) return false;

    const updatedMap = {
      ...state.nodesMap,
      [id]: {
        ...existingNode,
        position_x: x,
        position_y: y,
        position: { x, y },
      },
    };
    const updatedRfNodes = state.rfNodes.map((n) =>
      n.id === id ? { ...n, position: { x, y } } : n
    );
    set({ nodesMap: updatedMap, rfNodes: updatedRfNodes });

    try {
      const res = await fetch('/api/v3/node_tasks/batch_positions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          positions: {
            [id]: { x, y },
          },
        }),
      });
      return res.ok;
    } catch (err) {
      console.error('Failed to persist node position:', err);
      return false;
    }
  },

  createOrUpdateNode: async (payload) => {
    try {
      const enrichedPayload = {
        project_id: payload.project_id || get().activeProjectId || 'dnk_core',
        ...payload,
      };
      const res = await fetch('/api/v3/node_tasks/node', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(enrichedPayload),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to save node');
      }
      await get().fetchGraph();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return false;
    }
  },

  deleteNode: async (nodeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/node/${encodeURIComponent(nodeId)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete node');
      if (get().selectedNodeId === nodeId) {
        set({ selectedNodeId: null });
      }
      await get().fetchGraph();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return false;
    }
  },

  createEdge: async (source, target, depType = 'depends_on', desc = '') => {
    try {
      const res = await fetch('/api/v3/node_tasks/edge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source,
          target,
          relation: depType,
          dependency_type: depType,
          description: desc,
        }),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create edge (may create a cycle)');
      }
      await get().fetchGraph();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return false;
    }
  },

  deleteEdge: async (edgeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/edge/${encodeURIComponent(edgeId)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete edge');
      await get().fetchGraph();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return false;
    }
  },

  stageTransition: async (nodeId, targetStage, force = false) => {
    try {
      const res = await fetch('/api/v3/node_tasks/stage_transition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: nodeId,
          target_stage: targetStage,
          force,
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        return { success: false, detail: errJson.detail || 'Transition rejected' };
      }
      await get().fetchGraph();
      return { success: true };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, detail: msg };
    }
  },

  convertIdea: async (ideaId, newNodeType = 'task', assignedAgent) => {
    try {
      const res = await fetch('/api/v3/node_tasks/convert_idea', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idea_id: ideaId,
          new_node_type: newNodeType,
          assigned_agent: assignedAgent,
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to convert idea');
      }
      const data = await res.json().catch(() => ({}));
      await get().fetchGraph();
      if (data.spawned_task) {
        get().setSelectedNodeId(data.spawned_task.id);
      }
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return false;
    }
  },

  syncObsidianBidirectional: async () => {
    set({ isSyncing: true, error: null });
    try {
      const activeProjectId = get().activeProjectId || 'dnk_core';
      const res = await fetch('/api/v3/node_tasks/sync_bidirectional', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project_id: activeProjectId }),
      });
      if (!res.ok) throw new Error('Obsidian bidirectional sync failed');
      const data = await res.json().catch(() => ({}));
      await get().fetchGraph(activeProjectId);
      set({ isSyncing: false });
      return {
        success: true,
        scanned: data.scanned,
        imported: data.imported,
        updated: data.updated,
        exported: data.exported,
        edges_synced: data.edges_synced,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg, isSyncing: false });
      return { success: false };
    }
  },

  syncObsidian: async () => {
    const res = await get().syncObsidianBidirectional();
    return { ...res, syncedCount: res.exported };
  },

  resetBaseline: async () => {
    set({ isResetting: true, error: null });
    try {
      const res = await fetch('/api/v3/node_tasks/reset_baseline', {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to reset baseline');
      await get().fetchGraph();
      set({ isResetting: false, selectedNodeId: null });
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg, isResetting: false });
      return false;
    }
  },

  executeAgent: async (nodeId, mode = 'simulation', instructions) => {
    set({ isAgentRunning: true, agentFeedback: null });
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: nodeId,
          task_instructions: instructions,
          auto_complete: mode === 'auto_complete',
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Agent execution failed');

      if (data.logs && Array.isArray(data.logs)) {
        set((state) => ({
          nodeLogs: {
            ...state.nodeLogs,
            [nodeId]: data.logs,
          },
        }));
      }

      await get().fetchGraph();
      set({
        isAgentRunning: false,
        agentFeedback: `[${data.assigned_agent}] ${data.message} (Stage: ${data.stage}, Progress: ${data.progress}%)`,
      });
      return { success: true, message: data.message };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ isAgentRunning: false, agentFeedback: `Error: ${msg}` });
      return { success: false, message: msg };
    }
  },

  fetchNodeLogs: async (nodeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/logs`);
      if (!res.ok) return;
      const data = await res.json().catch(() => ({}));
      if (data.logs && Array.isArray(data.logs)) {
        set((state) => ({
          nodeLogs: {
            ...state.nodeLogs,
            [nodeId]: data.logs,
          },
        }));
      }
    } catch (err) {
      console.error(`Failed to fetch logs for node ${nodeId}`, err);
    }
  },

  fetchMarketingVideo: async (nodeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/marketing_video`);
      if (!res.ok) return null;
      const data = await res.json().catch(() => ({}));
      const videoPayload = (data.video || data) as MarketingVideoPayload;
      if (videoPayload && videoPayload.composition_id) {
        set((state) => ({
          marketingVideos: {
            ...state.marketingVideos,
            [nodeId]: videoPayload,
          },
        }));
        return videoPayload;
      }
      return null;
    } catch (err) {
      console.error(`Failed to fetch marketing video for node ${nodeId}`, err);
      return null;
    }
  },

  generateMarketingVideo: async (nodeId: string) => {
    set({ isGeneratingVideo: true });
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/generate_marketing_video`, {
        method: 'POST',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate marketing video');
      }
      const videoPayload = (data.video || data) as MarketingVideoPayload;
      set((state) => ({
        isGeneratingVideo: false,
        marketingVideos: {
          ...state.marketingVideos,
          [nodeId]: videoPayload,
        },
      }));
      return { success: true, data: videoPayload };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ isGeneratingVideo: false });
      return { success: false, error: msg };
    }
  },

  synthesizeVoiceover: async (nodeId: string, voiceId?: string) => {
    set((state) => ({
      isSynthesizingVoice: {
        ...state.isSynthesizingVoice,
        [nodeId]: true,
      },
      error: null,
    }));
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/synthesize_voiceover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: voiceId || 'aura-1' }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to synthesize voiceover');
      }
      const streamUrl = `/api/v3/node_tasks/${nodeId}/voiceover_audio?t=${Date.now()}`;
      set((state) => ({
        audioUrls: {
          ...state.audioUrls,
          [nodeId]: streamUrl,
        },
        isSynthesizingVoice: {
          ...state.isSynthesizingVoice,
          [nodeId]: false,
        },
      }));
      return { success: true, audioUrl: streamUrl };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`Failed to synthesize voiceover for node ${nodeId}`, err);
      set((state) => ({
        isSynthesizingVoice: {
          ...state.isSynthesizingVoice,
          [nodeId]: false,
        },
        error: msg,
      }));
      return { success: false, error: msg };
    }
  },

  exportVideoMp4: async (nodeId: string) => {
    set((state) => ({
      isExportingVideo: {
        ...state.isExportingVideo,
        [nodeId]: true,
      },
      error: null,
    }));
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/export_video_mp4`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to export MP4 video');
      }
      set((state) => ({
        videoExportStatuses: {
          ...state.videoExportStatuses,
          [nodeId]: data,
        },
        isExportingVideo: {
          ...state.isExportingVideo,
          [nodeId]: false,
        },
      }));
      return { success: true, data };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(`Failed to export MP4 video for node ${nodeId}`, err);
      set((state) => ({
        isExportingVideo: {
          ...state.isExportingVideo,
          [nodeId]: false,
        },
        error: msg,
      }));
      return { success: false, error: msg };
    }
  },

  fetchVideoExportStatus: async (nodeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/video_export_status`);
      if (!res.ok) return null;
      const data = await res.json();
      set((state) => ({
        videoExportStatuses: {
          ...state.videoExportStatuses,
          [nodeId]: data,
        },
      }));
      return data;
    } catch (err) {
      console.error(`Failed to fetch video export status for node ${nodeId}`, err);
      return null;
    }
  },

  fetchNodeArtifacts: async (nodeId: string) => {
    set({ isArtifactsLoading: true });
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/artifacts`);
      if (!res.ok) {
        set({ isArtifactsLoading: false });
        return null;
      }
      const data: NodeArtifactReport = await res.json();
      set((state) => ({
        isArtifactsLoading: false,
        nodeArtifacts: {
          ...state.nodeArtifacts,
          [nodeId]: data,
        },
      }));
      return data;
    } catch (err) {
      console.error(`Failed to fetch artifacts for node ${nodeId}`, err);
      set({ isArtifactsLoading: false });
      return null;
    }
  },

  acceptNodeArtifacts: async (nodeId: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/accept_artifacts`, {
        method: 'POST',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to accept artifacts');
      }
      await get().fetchGraph();
      await get().fetchNodeLogs(nodeId);
      await get().fetchNodeArtifacts(nodeId);
      return { success: true, message: data.message };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, message: msg };
    }
  },

  rejectNodeArtifacts: async (nodeId: string, reason?: string) => {
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/reject_artifacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to reject artifacts');
      }
      await get().fetchGraph();
      await get().fetchNodeLogs(nodeId);
      await get().fetchNodeArtifacts(nodeId);
      return { success: true, message: data.message };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      return { success: false, message: msg };
    }
  },

  runNodeVerification: async (nodeId: string, testCommand?: string) => {
    set({ isVerifying: true });
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/run_verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_command: testCommand }),
      });
      const data: VerificationResult = await res.json().catch(() => ({} as VerificationResult));
      await get().fetchNodeLogs(nodeId);
      set((state) => ({
        isVerifying: false,
        verificationResults: {
          ...state.verificationResults,
          [nodeId]: data,
        },
      }));
      return {
        success: data.status === 'success',
        verified: !!data.verified,
        message: data.message,
        output: data.output,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ isVerifying: false });
      return {
        success: false,
        verified: false,
        message: msg,
      };
    }
  },

  decomposeNode: async (nodeId, instructions) => {
    set({ isAgentRunning: true, error: null });
    try {
      const res = await fetch(`/api/v3/node_tasks/${nodeId}/decompose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instructions,
          workspace_id: 'ws-alpha-001',
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Failed to decompose node with AI');

      await get().fetchGraph();
      set({
        isAgentRunning: false,
        agentFeedback: data.message || `Декомпозовано на ${data.created_nodes?.length ?? 3} підзадач`,
      });
      return {
        success: true,
        message: data.message,
        createdCount: data.created_nodes?.length ?? 0,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ isAgentRunning: false, error: msg });
      return { success: false, message: msg };
    }
  },

  chatIntake: async (prompt, workspaceId = 'ws-alpha-001', defaultAgent) => {
    set({ isChatIntakeLoading: true, error: null });
    get().addChatMessage('user', prompt);

    const history = get().chatMessages.slice(-6).map((m) => ({
      sender: m.sender,
      text: m.text,
    }));

    try {
      const res = await fetch('/api/v3/node_tasks/chat_intake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          workspace_id: workspaceId,
          default_agent: defaultAgent,
          history,
          selected_node_id: get().selectedNodeId,
        }),
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => res.statusText);
        let detail = errText;
        try {
          const parsed = JSON.parse(errText);
          if (parsed && parsed.detail) detail = parsed.detail;
        } catch {
          // keep errText
        }
        throw new Error(detail || `Помилка сервера (${res.status})`);
      }

      const data = await res.json().catch(() => ({}));

      await get().fetchGraph();
      if (data.created_nodes && data.created_nodes.length > 0) {
        get().setSelectedNodeId(data.created_nodes[0].id);
      }

      // If auto-layout was triggered or new nodes were added, instantly run autoLayoutDAG so nodes never overlap
      if (data.action === 'auto_layout' || (data.created_nodes && data.created_nodes.length > 0)) {
        await get().autoLayoutDAG();
      }

      // If task execution was triggered, select the target node and execute the swarm worker
      if (data.action === 'execute' && data.target_node_id) {
        get().setSelectedNodeId(data.target_node_id);
        get().executeAgent(data.target_node_id, 'simulation');
      }

      set({
        isChatIntakeLoading: false,
        chatIntakeReply: data.reply,
        agentFeedback: data.reply,
      });

      const count = data.created_nodes?.length || 0;
      get().addChatMessage('gerych', data.reply || 'Задачу успішно опрацьовано.', count);

      return { success: true, reply: data.reply, createdNodesCount: count };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ isChatIntakeLoading: false, error: msg });
      get().addChatMessage('gerych', `Помилка обробки: ${msg}`);
      return { success: false, reply: msg };
    }
  },

  autoLayoutDAG: async () => {
    const { nodesMap, topologicalOrder, edgesList } = get();
    const updatedMap = { ...nodesMap };

    // Compute topological depth levels
    const depthMap: Record<string, number> = {};

    // Build incoming lookup supporting both relation and dependency_type
    const incoming: Record<string, string[]> = {};
    edgesList.forEach((e) => {
      const rel = e.dependency_type || (e as any).relation;
      if (
        rel === 'depends_on' ||
        rel === 'spawns_from' ||
        rel === 'blocks' ||
        rel === 'parent_of' ||
        rel === 'validates'
      ) {
        if (!incoming[e.target]) incoming[e.target] = [];
        incoming[e.target].push(e.source);
      }
    });

    const STAGE_MIN_DEPTH: Record<string, number> = {
      ideation: 0,
      architecture: 1,
      ready: 2,
      in_progress: 2,
      blocked: 2,
      testing: 3,
      verification: 3,
      completed: 4,
    };

    const order =
      topologicalOrder && topologicalOrder.length > 0
        ? topologicalOrder
        : Object.keys(updatedMap);

    order.forEach((nodeId) => {
      const node = updatedMap[nodeId];
      const stageMin = node ? (STAGE_MIN_DEPTH[node.stage] ?? 0) : 0;
      const parents = incoming[nodeId] || [];
      if (parents.length === 0) {
        depthMap[nodeId] = stageMin;
      } else {
        const maxParentDepth = Math.max(...parents.map((p) => depthMap[p] ?? 0));
        depthMap[nodeId] = Math.max(stageMin, maxParentDepth + 1);
      }
    });

    // Group nodes by depth
    const levels: Record<number, string[]> = {};
    Object.keys(updatedMap).forEach((id) => {
      const d = depthMap[id] ?? 0;
      if (!levels[d]) levels[d] = [];
      levels[d].push(id);
    });

    // Sort nodes within each level using Barycenter heuristic to minimize edge crossings
    const levelKeys = Object.keys(levels)
      .map((k) => parseInt(k, 10))
      .sort((a, b) => a - b);
    const assignedY: Record<string, number> = {};

    levelKeys.forEach((lvl) => {
      const nodeIds = levels[lvl];
      if (lvl === 0) {
        const prioScore: Record<string, number> = {
          critical: 4,
          high: 3,
          medium: 2,
          low: 1,
        };
        nodeIds.sort((a, b) => {
          const pA = prioScore[updatedMap[a]?.priority?.toLowerCase() || ''] ?? 0;
          const pB = prioScore[updatedMap[b]?.priority?.toLowerCase() || ''] ?? 0;
          return pB - pA;
        });
      } else {
        nodeIds.sort((a, b) => {
          const parentsA = incoming[a] || [];
          const parentsB = incoming[b] || [];
          const avgYA =
            parentsA.length > 0
              ? parentsA.reduce((sum, p) => sum + (assignedY[p] ?? 0), 0) /
                parentsA.length
              : 0;
          const avgYB =
            parentsB.length > 0
              ? parentsB.reduce((sum, p) => sum + (assignedY[p] ?? 0), 0) /
                parentsB.length
              : 0;
          return avgYA - avgYB;
        });
      }

      // Assign coordinates: horizontal pitch 420px, vertical pitch 240px
      nodeIds.forEach((nodeId, idx) => {
        const x = 60 + lvl * 420;
        const y = 100 + idx * 240;
        assignedY[nodeId] = y;

        if (updatedMap[nodeId]) {
          updatedMap[nodeId] = {
            ...updatedMap[nodeId],
            position_x: x,
            position_y: y,
            position: { x, y },
          };
        }
      });
    });

    const { nodes, edges: rfEdges } = buildRFNodesAndEdges(
      updatedMap,
      get().edgesList,
      get().selectedNodeId,
      get().filterType,
      get().filterStage,
      get().filterAgent,
      get().searchQuery
    );

    set({ nodesMap: updatedMap, rfNodes: nodes, rfEdges });

    // Persist layout to backend batch endpoint
    try {
      const positionsPayload: Record<string, { x: number; y: number }> = {};
      Object.entries(updatedMap).forEach(([id, item]) => {
        positionsPayload[id] = { x: item.position_x, y: item.position_y };
      });

      const res = await fetch('/api/v3/node_tasks/batch_positions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ positions: positionsPayload }),
      });

      if (res.ok) {
        return { success: true, count: Object.keys(positionsPayload).length };
      }
    } catch {
      // Offline fallback: client layout was already applied
    }

    return { success: true, count: Object.keys(updatedMap).length };
  },

  batchStageTransition: async (targetStage: string, force = false) => {
    const { selectedNodeIds } = get();
    if (!selectedNodeIds || selectedNodeIds.length === 0) {
      return { success: false, updatedCount: 0, skippedCount: 0 };
    }

    set({ isSyncing: true, error: null });
    try {
      const res = await fetch('/api/v3/node_tasks/batch_stage_transition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_ids: selectedNodeIds,
          target_stage: targetStage,
          force,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to perform batch stage transition');
      }

      const data = await res.json();
      await get().fetchGraph();
      return {
        success: true,
        updatedCount: data.total_updated ?? (data.updated_ids ? data.updated_ids.length : 0),
        skippedCount: data.skipped ? data.skipped.length : 0,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return { success: false, updatedCount: 0, skippedCount: 0 };
    } finally {
      set({ isSyncing: false });
    }
  },

  batchDeleteNodes: async () => {
    const { selectedNodeIds } = get();
    if (!selectedNodeIds || selectedNodeIds.length === 0) {
      return { success: false, deletedCount: 0 };
    }

    set({ isSyncing: true, error: null });
    try {
      const res = await fetch('/api/v3/node_tasks/batch_delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_ids: selectedNodeIds,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to delete selected nodes in batch');
      }

      const data = await res.json();
      set({ selectedNodeIds: [], selectedNodeId: null });
      await get().fetchGraph();
      return {
        success: true,
        deletedCount: data.deleted_ids ? data.deleted_ids.length : selectedNodeIds.length,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return { success: false, deletedCount: 0 };
    } finally {
      set({ isSyncing: false });
    }
  },

  batchExecuteAgent: async (agentOverride?: string) => {
    const { selectedNodeIds } = get();
    if (!selectedNodeIds || selectedNodeIds.length === 0) {
      return { success: false, executedCount: 0 };
    }

    set({ isAgentRunning: true, error: null });
    try {
      const res = await fetch('/api/v3/node_tasks/batch_execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_ids: selectedNodeIds,
          agent_override: agentOverride,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to trigger batch execution');
      }

      const data = await res.json();
      await get().fetchGraph();
      return {
        success: true,
        executedCount: data.total_executed ?? (data.executed_ids ? data.executed_ids.length : 0),
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      set({ error: msg });
      return { success: false, executedCount: 0 };
    } finally {
      set({ isAgentRunning: false });
    }
  },

  initWebSocket: () => {
    if (typeof window === 'undefined') {
      return () => {};
    }

    const existingWs = get().ws;
    if (existingWs && (existingWs.readyState === WebSocket.OPEN || existingWs.readyState === WebSocket.CONNECTING)) {
      return () => {
        get().closeWebSocket();
      };
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host || 'localhost:8000';
      const wsUrl = `${protocol}//${host}/api/ws`;

      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        set({ ws: socket, wsConnected: true });
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          let eventType = data.event_type || data.type;
          if (eventType === 'RUNTIME_EVENT' && data.event_type) {
            eventType = data.event_type;
          }

          const payload = data.payload || {};
          const nodeId = data.node_id || data.nodeId || payload.node_id;

          // 1. Reactive node status and progress updates
          if (nodeId && (
            eventType === 'node.status_changed' ||
            eventType === 'node.executed' ||
            eventType === 'node.started' ||
            eventType === 'node.updated'
          )) {
            const currentNodes = { ...get().nodesMap };
            const node = currentNodes[nodeId];
            if (node) {
              const newStatus = (payload.status || data.status || (eventType === 'node.executed' ? 'completed' : node.status)) as string;
              const newStage = (payload.stage || data.stage || (eventType === 'node.executed' ? 'completed' : node.stage)) as ExecutionStage;
              const newProgress = typeof payload.progress === 'number'
                ? payload.progress
                : (typeof data.progress === 'number' ? data.progress : (eventType === 'node.executed' ? 100 : node.progress));
              const newAgent = payload.agent || data.agent || node.assigned_agent;

              currentNodes[nodeId] = {
                ...node,
                status: newStatus,
                stage: newStage,
                progress: newProgress,
                assigned_agent: newAgent,
              };

              const { nodes, edges: rfEdges } = buildRFNodesAndEdges(
                currentNodes,
                get().edgesList,
                get().selectedNodeId,
                get().filterType,
                get().filterStage,
                get().filterAgent,
                get().searchQuery
              );

              set({
                nodesMap: currentNodes,
                rfNodes: nodes,
                rfEdges,
              });
            }

            if (payload.logs && Array.isArray(payload.logs)) {
              set((state) => ({
                nodeLogs: {
                  ...state.nodeLogs,
                  [nodeId]: payload.logs,
                },
              }));
            }
          }

          // 2. Reactive node execution logs stream
          if (eventType === 'node.log') {
            const logEntry = payload.log || data.log || {
              timestamp: payload.timestamp || data.timestamp || new Date().toISOString(),
              level: payload.level || data.level || 'INFO',
              agent: payload.agent || data.agent || 'swarm',
              message: payload.message || data.message || '',
            };
            if (nodeId && logEntry.message) {
              set((state) => {
                const existing = state.nodeLogs[nodeId] || [];
                return {
                  nodeLogs: {
                    ...state.nodeLogs,
                    [nodeId]: [...existing, logEntry],
                  },
                };
              });
            }
          }

          // 3. Reactive edge created & deleted sync
          if (eventType === 'edge.created') {
            const edgePayload: TaskEdgeData = payload.edge || {
              id: payload.edge_id || data.edge_id || `edge-${payload.source}-to-${payload.target}`,
              source: payload.source || data.source,
              target: payload.target || data.target,
              relation: payload.relation || 'depends_on',
              dependency_type: payload.relation || payload.dependency_type || 'depends_on',
              description: payload.description || '',
              is_satisfied: true,
            };
            const currentEdges = get().edgesList.filter((e) => e.id !== edgePayload.id);
            const updatedEdges = [...currentEdges, edgePayload];
            const { nodes, edges: rfEdges } = buildRFNodesAndEdges(
              get().nodesMap,
              updatedEdges,
              get().selectedNodeId,
              get().filterType,
              get().filterStage,
              get().filterAgent,
              get().searchQuery
            );
            set({
              edgesList: updatedEdges,
              rfNodes: nodes,
              rfEdges,
            });
          }

          if (eventType === 'edge.deleted') {
            const edgeId = payload.edge_id || data.edge_id || data.node_id;
            if (edgeId) {
              const updatedEdges = get().edgesList.filter((e) => e.id !== edgeId);
              const { nodes, edges: rfEdges } = buildRFNodesAndEdges(
                get().nodesMap,
                updatedEdges,
                get().selectedNodeId,
                get().filterType,
                get().filterStage,
                get().filterAgent,
                get().searchQuery
              );
              set({
                edgesList: updatedEdges,
                rfNodes: nodes,
                rfEdges,
              });
            }
          }
        } catch {
          // Ignore non-JSON or heartbeat frames
        }
      };

      socket.onerror = () => {
        set({ wsConnected: false });
      };

      socket.onclose = () => {
        set({ ws: null, wsConnected: false });
      };

      set({ ws: socket });

      return () => {
        socket.close();
        set({ ws: null, wsConnected: false });
      };
    } catch {
      return () => {};
    }
  },

  closeWebSocket: () => {
    const socket = get().ws;
    if (socket) {
      socket.close();
      set({ ws: null, wsConnected: false });
    }
  },
}));

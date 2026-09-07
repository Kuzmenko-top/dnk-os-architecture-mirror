// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/store/canvasStore.ts"
// purpose: "Canvas Store with PostgreSQL 16 (hub_memory) Delta Sync, WebSocket Collaboration, IndexedDB Hydration & Whiteboard"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-09-03"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { create } from 'zustand';
import {
  Node,
  Edge,
  Connection,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange
} from '@xyflow/react';
import { reactFlowToJSONCanvas, jsonCanvasToReactFlow } from '../src/canvas/json-canvas/converter';
import type { JSONCanvasDocument } from '../src/canvas/json-canvas/types';
import { SwarmPropagationEngine, PropagationResult } from '../src/canvas/swarm/swarmPropagation';
import type { BrandDNA } from './sconesStore';
import {
  canvasApiClient,
  CanvasDelta,
  CanvasRevisionInfo
} from '../lib/canvasApi';

export interface WhiteboardElement {
  id: string;
  type: 'pencil' | 'rect' | 'ellipse' | 'arrow' | 'note' | 'text' | 'eraser';
  x: number;
  y: number;
  width?: number;
  height?: number;
  points?: { x: number; y: number }[];
  color: string;
  fill?: string;
  strokeWidth: number;
  content?: string;
  author: string;
}

export interface AgentLogEntry {
  id: string;
  nodeId: string;
  agent: string;
  level: 'info' | 'success' | 'warning' | 'error';
  step?: string;
  text: string;
  message?: string;
  timestamp: number | string;
}

export interface CanvasHistorySnapshot {
  nodes: Node[];
  edges: Edge[];
  whiteboardElements?: WhiteboardElement[];
}

export interface CanvasState {
  // Core Graph State
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  history: CanvasHistorySnapshot[];
  historyIndex: number;

  // Persistence & Server Delta Sync (PostgreSQL 16 hub_memory schema)
  canvasId: string;
  workspaceId: string;
  currentRevision: number;
  revisionId: string | null;
  isSyncing: boolean;
  lastSyncedAt: string | null;
  syncError: string | null;
  pendingDelta: CanvasDelta;
  collaborators: Record<string, { x: number; y: number; name: string }>;
  revisions: CanvasRevisionInfo[];

  // Whiteboard / Sketch Overlay Layer
  isWhiteboardActive: boolean;
  whiteboardElements: WhiteboardElement[];
  toggleWhiteboard: () => void;
  setWhiteboardActive: (active: boolean) => void;
  setWhiteboardElements: (elements: WhiteboardElement[]) => void;
  addWhiteboardElement: (element: WhiteboardElement) => void;
  updateWhiteboardElement: (id: string, patch: Partial<WhiteboardElement>) => void;
  removeWhiteboardElement: (id: string) => void;
  clearWhiteboard: () => void;

  // React Flow Native Handlers
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  selectNode: (id: string | null) => void;

  // Node Mutations
  addNode: (type: string, position: { x: number; y: number }, initialData?: Record<string, any>) => string;
  updateNodeData: (id: string, patch: Record<string, any>) => void;
  updateNode: (id: string, patch: Record<string, any>) => void;
  removeNode: (id: string) => void;

  // Data-Flow Propagation (Flowgram.ai Reactive Engine)
  propagateDataFlow: (sourceNodeId: string, outputPayload: Record<string, any>) => void;
  propagateSwarm: (sourceNodeId: string, outputPayload: Record<string, any>, brand: BrandDNA) => PropagationResult;

  // Delta Sync & Server Operations
  initCanvasSync: (canvasId?: string, workspaceId?: string) => Promise<void>;
  queueDelta: (delta: Partial<CanvasDelta>) => void;
  flushDeltaSync: () => Promise<void>;
  applyRemoteDelta: (delta: any) => void;
  fetchRevisions: () => Promise<CanvasRevisionInfo[]>;
  restoreRevision: (revisionId: string) => Promise<void>;
  connectCollaboration: () => void;
  disconnectCollaboration: () => void;

  // Swarm Live Stream & Execution Bridge
  activeProjectId: string;
  userSoul?: Record<string, any>;
  websocket: WebSocket | null;
  activeLogs: AgentLogEntry[];
  clearActiveLogs: () => void;
  triggerNodeAgent: (nodeId: string, prompt?: string, taskType?: string) => Promise<void> | void;

  // History Actions (Client session undo/redo)
  pushHistory: () => void;
  undo: () => void;
  redo: () => void;

  // JSON Canvas I/O
  exportJSONCanvas: () => JSONCanvasDocument;
  importJSONCanvas: (doc: JSONCanvasDocument) => void;
  resetToDefault: () => void;

  // Obsidian Vault Sync Engine
  obsidianSyncStatus: 'idle' | 'syncing' | 'success' | 'error';
  obsidianSyncMessage: string | null;
  syncToObsidian: (
    direction?: 'export' | 'import' | 'sync',
    options?: { vaultPath?: string; canvasName?: string; conflictStrategy?: string }
  ) => Promise<{ status: 'success' | 'error'; message?: string; nodes?: Node[]; edges?: Edge[] }>;

  // Mind Map AI Auto-Clusterization & Layout
  isClustering: boolean;
  clusterMetadata: Array<{ clusterId: string; name: string; color: string; nodeIds: string[] }>;
  autoClusterNodes: (options?: { language?: string; k?: number }) => Promise<{ status: string; clusters: any[] }>;
  autoClusterMindMap: (options?: { language?: string; k?: number }) => Promise<{ status: string; clusters: any[] }>;
}

const MAX_HISTORY = 30;
let syncDebounceTimer: any = null;
let activeWebSocket: WebSocket | null = null;

export const useCanvasStore = create<CanvasState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  history: [{ nodes: [], edges: [], whiteboardElements: [] }],
  historyIndex: 0,

  // Server sync defaults
  canvasId: 'default-canvas',
  workspaceId: 'ws-alpha-001',
  currentRevision: 0,
  revisionId: null,
  isSyncing: false,
  lastSyncedAt: null,
  syncError: null,
  pendingDelta: {},
  collaborators: {},
  revisions: [],

  // Mind Map AI Auto-Clusterization
  isClustering: false,
  clusterMetadata: [],

  // Swarm Live Stream & Execution Bridge
  activeProjectId: 'dnk_os_core',
  userSoul: { user_name: 'Maxim', tone_of_voice: 'ReBurn Founder' },
  websocket: null,
  activeLogs: [],
  clearActiveLogs: () => set({ activeLogs: [] }),

  // Obsidian Vault Sync Defaults
  obsidianSyncStatus: 'idle',
  obsidianSyncMessage: null,

  // Whiteboard Defaults
  isWhiteboardActive: false,
  whiteboardElements: [],

  toggleWhiteboard: () => set((state) => ({ isWhiteboardActive: !state.isWhiteboardActive })),
  setWhiteboardActive: (active) => set({ isWhiteboardActive: active }),
  setWhiteboardElements: (whiteboardElements) => set({ whiteboardElements }),

  addWhiteboardElement: (elem) => {
    set((state) => ({
      whiteboardElements: [...state.whiteboardElements, elem]
    }));
    get().pushHistory();
    get().queueDelta({
      sketches: get().whiteboardElements
    });
  },

  updateWhiteboardElement: (id, patch) => {
    set((state) => ({
      whiteboardElements: state.whiteboardElements.map((el) => (el.id === id ? { ...el, ...patch } : el))
    }));
    get().queueDelta({
      sketches: get().whiteboardElements
    });
  },

  removeWhiteboardElement: (id) => {
    set((state) => ({
      whiteboardElements: state.whiteboardElements.filter((el) => el.id !== id)
    }));
    get().pushHistory();
    get().queueDelta({
      sketches: get().whiteboardElements
    });
  },

  clearWhiteboard: () => {
    set({ whiteboardElements: [] });
    get().pushHistory();
    get().queueDelta({
      sketches: []
    });
  },

  setNodes: (nodesOrUpdater) => {
    set((state) => {
      const nextNodes = typeof nodesOrUpdater === 'function'
        ? (nodesOrUpdater as Function)(state.nodes)
        : nodesOrUpdater;
      return { nodes: nextNodes };
    });
  },

  setEdges: (edgesOrUpdater) => {
    set((state) => {
      const nextEdges = typeof edgesOrUpdater === 'function'
        ? (edgesOrUpdater as Function)(state.edges)
        : edgesOrUpdater;
      return { edges: nextEdges };
    });
  },

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes)
    });
    // Check if changes contain position changes or remove changes
    const hasPositionOrRemove = changes.some((c) => c.type === 'position' || c.type === 'remove');
    if (hasPositionOrRemove) {
      const removedIds = changes.filter((c) => c.type === 'remove').map((c: any) => c.id);
      get().queueDelta({
        upsert_nodes: get().nodes,
        delete_node_ids: removedIds.length > 0 ? removedIds : undefined
      });
    }
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges)
    });
    const removedIds = changes.filter((c) => c.type === 'remove').map((c: any) => c.id);
    if (removedIds.length > 0) {
      get().queueDelta({
        delete_edge_ids: removedIds
      });
    }
  },

  onConnect: (connection) => {
    get().pushHistory();
    const newEdge: Edge = {
      ...connection,
      id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
      type: 'default',
      animated: true,
      source: connection.source || '',
      target: connection.target || ''
    };
    const nextEdges = addEdge(newEdge, get().edges);
    set({ edges: nextEdges });
    get().queueDelta({
      upsert_edges: [newEdge]
    });
  },

  selectNode: (id) => set({ selectedNodeId: id }),

  addNode: (type, position, initialData = {}) => {
    const id = `node-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    const newNode: Node = {
      id,
      type,
      position,
      data: {
        title: initialData.title || type.replace('Node', ''),
        ...initialData
      }
    };

    set({
      nodes: [...get().nodes, newNode],
      selectedNodeId: id
    });
    get().pushHistory();

    // Queue delta for PostgreSQL auto-save
    get().queueDelta({
      upsert_nodes: [newNode]
    });

    return id;
  },

  updateNodeData: (id, patch) => {
    let updatedNode: Node | null = null;
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === id) {
          const updated = {
            ...node,
            ...(patch.status ? { status: patch.status } : {}),
            data: {
              ...node.data,
              ...patch
            }
          };
          updatedNode = updated;
          return updated;
        }
        return node;
      })
    });

    if (updatedNode) {
      get().queueDelta({
        upsert_nodes: [updatedNode]
      });
    }
  },

  updateNode: (id, patch) => get().updateNodeData(id, patch),

  removeNode: (id) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== id),
      edges: get().edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId
    });
    get().pushHistory();

    get().queueDelta({
      delete_node_ids: [id]
    });
  },

  propagateDataFlow: (sourceNodeId, outputPayload) => {
    const { edges, nodes } = get();
    const downstreamEdges = edges.filter((e) => e.source === sourceNodeId);
    if (downstreamEdges.length === 0) return;

    const targetNodeIds = new Set(downstreamEdges.map((e) => e.target));

    const updatedNodes = nodes.map((node) => {
      if (targetNodeIds.has(node.id)) {
        const inputCtx = (node.data && typeof node.data.inputContext === 'object' && node.data.inputContext !== null)
          ? node.data.inputContext
          : {};
        return {
          ...node,
          data: {
            ...node.data,
            inputContext: {
              ...inputCtx,
              ...outputPayload
            }
          }
        };
      }
      return node;
    });

    set({ nodes: updatedNodes });
    get().pushHistory();

    get().queueDelta({
      upsert_nodes: updatedNodes.filter((n) => targetNodeIds.has(n.id))
    });
  },

  propagateSwarm: (sourceNodeId, outputPayload, brand) => {
    const { nodes, edges } = get();
    const result = SwarmPropagationEngine.propagate(sourceNodeId, outputPayload, nodes, edges, brand);
    if (result.propagatedCount > 0) {
      set({ nodes: result.nodes });
      get().pushHistory();
      get().queueDelta({
        upsert_nodes: result.nodes
      });
    }
    return result;
  },

  // ---------------------------------------------------------------------------
  // Server Delta Sync & IndexedDB Hydration
  // ---------------------------------------------------------------------------

  initCanvasSync: async (canvasId = 'default-canvas', workspaceId = 'ws-alpha-001') => {
    set({ canvasId, workspaceId, isSyncing: true, syncError: null });
    try {
      const serverState = await canvasApiClient.loadCanvas(canvasId, workspaceId) as any;
      if (serverState) {
        const scene = serverState.scene || {};
        const nodes: Node[] = Array.isArray(scene.nodes) ? scene.nodes : [];
        const edges: Edge[] = Array.isArray(scene.edges) ? scene.edges : [];
        const sketches = Array.isArray(scene.sketches) ? scene.sketches : [];

        set({
          nodes,
          edges,
          whiteboardElements: sketches,
          currentRevision: serverState.revision_number || 1,
          revisionId: serverState.current_revision_id || null,
          lastSyncedAt: new Date().toISOString(),
          isSyncing: false,
          history: [{ nodes, edges, whiteboardElements: sketches }],
          historyIndex: 0
        });
      }
    } catch (err: any) {
      console.warn('Init canvas sync error (falling back to local):', err);
      set({ isSyncing: false, syncError: err?.message || 'Sync failed' });
    }

    // Connect WebSocket for live multi-user collaboration
    get().connectCollaboration();
  },

  queueDelta: (deltaPatch) => {
    const current = get().pendingDelta;
    const merged: CanvasDelta = {
      ...current,
      ...deltaPatch,
      upsert_nodes: deltaPatch.upsert_nodes
        ? [...(current.upsert_nodes || []).filter(
            (cn) => !deltaPatch.upsert_nodes!.some((dn) => dn.id === cn.id)
          ), ...deltaPatch.upsert_nodes]
        : current.upsert_nodes,
      delete_node_ids: deltaPatch.delete_node_ids
        ? Array.from(new Set([...(current.delete_node_ids || []), ...deltaPatch.delete_node_ids]))
        : current.delete_node_ids,
      upsert_edges: deltaPatch.upsert_edges
        ? [...(current.upsert_edges || []).filter(
            (ce) => !deltaPatch.upsert_edges!.some((de) => de.id === ce.id)
          ), ...deltaPatch.upsert_edges]
        : current.upsert_edges,
      delete_edge_ids: deltaPatch.delete_edge_ids
        ? Array.from(new Set([...(current.delete_edge_ids || []), ...deltaPatch.delete_edge_ids]))
        : current.delete_edge_ids,
      sketches: deltaPatch.sketches !== undefined ? deltaPatch.sketches : current.sketches,
      client_revision: get().currentRevision,
      workspace_id: get().workspaceId
    };

    set({ pendingDelta: merged });

    // Debounce flush to backend (750ms)
    if (syncDebounceTimer) {
      clearTimeout(syncDebounceTimer);
    }
    syncDebounceTimer = setTimeout(() => {
      get().flushDeltaSync();
    }, 750);
  },

  flushDeltaSync: async () => {
    const { canvasId, pendingDelta, currentRevision, isSyncing } = get();
    if (!pendingDelta || Object.keys(pendingDelta).length === 0) return;
    if (isSyncing) return;

    set({ isSyncing: true, syncError: null });

    const deltaToSend = { ...pendingDelta, client_revision: currentRevision };
    // Clear pending delta optimistically
    set({ pendingDelta: {} });

    try {
      const response = await canvasApiClient.syncDelta(canvasId, deltaToSend);
      if (response && response.success) {
        set({
          currentRevision: response.revision_number,
          revisionId: response.revision_id,
          lastSyncedAt: new Date().toISOString(),
          isSyncing: false
        });
      } else {
        set({ isSyncing: false });
      }
    } catch (err: any) {
      console.error('Failed to flush delta sync:', err);
      // Re-queue delta so it isn't lost
      get().queueDelta(deltaToSend);
      set({ isSyncing: false, syncError: err?.message || 'Sync flush error' });
    }
  },

  applyRemoteDelta: (deltaData) => {
    if (!deltaData) return;
    const { nodes: currentNodes, edges: currentEdges, whiteboardElements: currentSketches } = get();

    let newNodes = [...currentNodes];
    let newEdges = [...currentEdges];
    let newSketches = [...currentSketches];

    if (deltaData.upsert_nodes && Array.isArray(deltaData.upsert_nodes)) {
      const incomingMap = new Map(deltaData.upsert_nodes.map((n: any) => [n.id, n]));
      newNodes = newNodes.map((n) => (incomingMap.has(n.id) ? (incomingMap.get(n.id) as Node) : n));
      deltaData.upsert_nodes.forEach((n: any) => {
        if (!newNodes.some((existing) => existing.id === n.id)) {
          newNodes.push(n as Node);
        }
      });
    }

    if (deltaData.delete_node_ids && Array.isArray(deltaData.delete_node_ids)) {
      const delSet = new Set(deltaData.delete_node_ids);
      newNodes = newNodes.filter((n) => !delSet.has(n.id));
    }

    if (deltaData.upsert_edges && Array.isArray(deltaData.upsert_edges)) {
      const incomingMap = new Map(deltaData.upsert_edges.map((e: any) => [e.id, e]));
      newEdges = newEdges.map((e) => (incomingMap.has(e.id) ? (incomingMap.get(e.id) as Edge) : e));
      deltaData.upsert_edges.forEach((e: any) => {
        if (!newEdges.some((existing) => existing.id === e.id)) {
          newEdges.push(e as Edge);
        }
      });
    }

    if (deltaData.delete_edge_ids && Array.isArray(deltaData.delete_edge_ids)) {
      const delSet = new Set(deltaData.delete_edge_ids);
      newEdges = newEdges.filter((e) => !delSet.has(e.id));
    }

    if (deltaData.sketches && Array.isArray(deltaData.sketches)) {
      newSketches = deltaData.sketches;
    }

    set({
      nodes: newNodes,
      edges: newEdges,
      whiteboardElements: newSketches,
      currentRevision: deltaData.revision_number || get().currentRevision,
      revisionId: deltaData.revision_id || get().revisionId
    });
  },

  fetchRevisions: async () => {
    const { canvasId } = get();
    try {
      const revs = await canvasApiClient.listRevisions(canvasId);
      set({ revisions: revs });
      return revs;
    } catch (err: any) {
      console.warn('Failed to fetch revisions:', err);
      return [];
    }
  },

  restoreRevision: async (revisionId: string) => {
    const { canvasId } = get();
    set({ isSyncing: true });
    try {
      const result = await canvasApiClient.restoreRevision(canvasId, revisionId);
      if (result && result.scene) {
        const scene = result.scene;
        set({
          nodes: scene.nodes || [],
          edges: scene.edges || [],
          whiteboardElements: scene.sketches || [],
          currentRevision: result.revision_number,
          revisionId: result.revision_id,
          isSyncing: false,
          lastSyncedAt: new Date().toISOString()
        });
        get().pushHistory();
      }
    } catch (err: any) {
      console.error('Failed to restore revision:', err);
      set({ isSyncing: false, syncError: err?.message || 'Restore revision failed' });
    }
  },

  connectCollaboration: () => {
    if (typeof window === 'undefined') return;
    const { canvasId } = get();

    if (activeWebSocket) {
      try {
        activeWebSocket.close();
      } catch (e) {}
    }

    activeWebSocket = canvasApiClient.connectWebSocket(
      canvasId,
      (msg) => {
        if (msg.type === 'canvas_delta' && msg.delta) {
          get().applyRemoteDelta(msg.delta);
        } else if (msg.type === 'cursor_update') {
          set((state) => ({
            collaborators: {
              ...state.collaborators,
              [msg.actor_id]: {
                x: msg.cursor?.x || 0,
                y: msg.cursor?.y || 0,
                name: msg.user_name || 'Collaborator'
              }
            }
          }));
        } else if (msg.type === 'TASK_STATUS' || msg.event === 'TASK_STATUS') {
          const targetNodeId = msg.nodeId || msg.node_id;
          if (targetNodeId) {
            get().updateNodeData(targetNodeId, {
              status: msg.status,
              agentStatus: msg.status,
              agentType: msg.agent,
              agentTraceId: msg.trace_id,
              agentResult: msg.result,
              agentMetrics: msg.metrics,
              agentUpdatedAt: msg.timestamp || Date.now()
            });
          }
        } else if (msg.type === 'AGENT_LOG' || msg.event === 'AGENT_LOG') {
          const logEntry: AgentLogEntry = {
            id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
            nodeId: msg.nodeId || msg.node_id || '',
            agent: msg.agent || 'system',
            level: msg.level || 'info',
            step: msg.step,
            text: msg.text || msg.message || '',
            message: msg.message || msg.text || '',
            timestamp: typeof msg.timestamp === 'number'
              ? (msg.timestamp > 1e11 ? msg.timestamp : Math.round(msg.timestamp * 1000))
              : Date.now()
          };
          set((state) => ({
            activeLogs: [logEntry, ...state.activeLogs].slice(0, 200)
          }));
        } else if (msg.type === 'OBSIDIAN_SYNC_STATUS' || msg.event === 'OBSIDIAN_SYNC_STATUS') {
          if (msg.status === 'success') {
            if ((msg.direction === 'import' || msg.direction === 'sync') && Array.isArray(msg.nodes)) {
              set({
                nodes: msg.nodes,
                edges: Array.isArray(msg.edges) ? msg.edges : get().edges,
                obsidianSyncStatus: 'success',
                obsidianSyncMessage: `Synced ${msg.nodes.length} nodes from Obsidian`
              });
              get().pushHistory();
            } else {
              set({
                obsidianSyncStatus: 'success',
                obsidianSyncMessage: 'Export to Obsidian completed successfully'
              });
            }
          } else {
            set({
              obsidianSyncStatus: 'error',
              obsidianSyncMessage: msg.error || 'Obsidian sync failed'
            });
          }
        }
      },
      (err) => {
        console.warn('Canvas WS collaboration error:', err);
      }
    );
    set({ websocket: activeWebSocket });
  },

  disconnectCollaboration: () => {
    if (activeWebSocket) {
      try {
        activeWebSocket.close();
      } catch (e) {}
      activeWebSocket = null;
    }
    set({ websocket: null });
  },

  triggerNodeAgent: async (nodeId: string, prompt?: string, taskType?: string) => {
    const { nodes, canvasId, activeProjectId, userSoul } = get();
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) {
      console.warn(`[CanvasStore] Node ${nodeId} not found for triggerNodeAgent`);
      return;
    }

    const resolvedTaskType =
      taskType ||
      (node.data?.taskType as string) ||
      (node.data?.agentType as string) ||
      'gerych_builder';
    const resolvedPrompt =
      prompt ||
      (node.data?.prompt as string) ||
      (node.data?.title as string) ||
      `Execute task for ${nodeId}`;
    const projectId = activeProjectId || canvasId || 'dnk_os_core';
    const soul = userSoul || { user_name: 'Maxim', tone_of_voice: 'ReBurn Founder' };

    // Optimistically update node status to thinking
    get().updateNodeData(nodeId, {
      status: 'thinking',
      agentStatus: 'thinking',
      agentType: resolvedTaskType
    });

    const executionPayload = {
      type: 'TASK_EXECUTE',
      action: 'TASK_EXECUTE',
      nodeId,
      node_id: nodeId,
      taskType: resolvedTaskType,
      context: {
        projectId,
        prompt: resolvedPrompt,
        userSoul: soul
      }
    };

    const ws = get().websocket || activeWebSocket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(executionPayload));
    } else {
      console.info('[CanvasStore] activeWebSocket not open, attempting connection and queuing dispatch');
      get().connectCollaboration();
      setTimeout(() => {
        const currentWs = get().websocket || activeWebSocket;
        if (currentWs && currentWs.readyState === WebSocket.OPEN) {
          currentWs.send(JSON.stringify(executionPayload));
        }
      }, 500);
    }
  },

  // ---------------------------------------------------------------------------
  // Session Undo/Redo & JSON Canvas
  // ---------------------------------------------------------------------------

  pushHistory: () => {
    const { nodes, edges, whiteboardElements, history, historyIndex } = get();
    const newSnapshot: CanvasHistorySnapshot = {
      nodes: JSON.parse(JSON.stringify(nodes)),
      edges: JSON.parse(JSON.stringify(edges)),
      whiteboardElements: JSON.parse(JSON.stringify(whiteboardElements || []))
    };

    const nextHistory = history.slice(0, historyIndex + 1);
    if (nextHistory.length >= MAX_HISTORY) {
      nextHistory.shift();
    }
    nextHistory.push(newSnapshot);

    set({
      history: nextHistory,
      historyIndex: nextHistory.length - 1
    });
  },

  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex > 0) {
      const prevIndex = historyIndex - 1;
      const snapshot = history[prevIndex];
      set({
        nodes: JSON.parse(JSON.stringify(snapshot.nodes)),
        edges: JSON.parse(JSON.stringify(snapshot.edges)),
        whiteboardElements: JSON.parse(JSON.stringify(snapshot.whiteboardElements || [])),
        historyIndex: prevIndex,
        selectedNodeId: null
      });
      get().queueDelta({
        upsert_nodes: snapshot.nodes,
        upsert_edges: snapshot.edges,
        sketches: snapshot.whiteboardElements
      });
    }
  },

  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < history.length - 1) {
      const nextIndex = historyIndex + 1;
      const snapshot = history[nextIndex];
      set({
        nodes: JSON.parse(JSON.stringify(snapshot.nodes)),
        edges: JSON.parse(JSON.stringify(snapshot.edges)),
        whiteboardElements: JSON.parse(JSON.stringify(snapshot.whiteboardElements || [])),
        historyIndex: nextIndex,
        selectedNodeId: null
      });
      get().queueDelta({
        upsert_nodes: snapshot.nodes,
        upsert_edges: snapshot.edges,
        sketches: snapshot.whiteboardElements
      });
    }
  },

  exportJSONCanvas: () => {
    const { nodes, edges, whiteboardElements } = get();
    const doc = reactFlowToJSONCanvas(nodes, edges);
    if (whiteboardElements && whiteboardElements.length > 0) {
      (doc as any).whiteboard = whiteboardElements;
    }
    return doc;
  },

  importJSONCanvas: (doc) => {
    get().pushHistory();
    const { nodes, edges } = jsonCanvasToReactFlow(doc);
    const whiteboard = (doc as any).whiteboard || [];
    set({ nodes, edges, whiteboardElements: whiteboard, selectedNodeId: null });
    get().queueDelta({
      upsert_nodes: nodes,
      upsert_edges: edges,
      sketches: whiteboard
    });
  },

  resetToDefault: () => {
    set({
      nodes: [],
      edges: [],
      selectedNodeId: null,
      history: [{ nodes: [], edges: [], whiteboardElements: [] }],
      historyIndex: 0,
      isWhiteboardActive: false,
      whiteboardElements: [],
      currentRevision: 0,
      revisionId: null,
      pendingDelta: {},
      collaborators: {}
    });
  },

  syncToObsidian: async (direction = 'export', options = {}) => {
    set({
      obsidianSyncStatus: 'syncing',
      obsidianSyncMessage: `Syncing ${direction === 'export' ? 'to' : direction === 'import' ? 'from' : 'with'} Obsidian...`
    });

    try {
      const { nodes, edges, canvasId } = get();
      const ws = get().websocket || activeWebSocket;
      const targetDir = options.vaultPath || './docs/notes';
      const canvasName = options.canvasName || `canvas_${canvasId}`;
      const conflictStrategy = options.conflictStrategy || 'last-write-wins';

      // Compute relative canvas file path for SSOT REST bridge
      const cleanDir = targetDir.replace(/\/$/, '');
      const canvasPath = cleanDir.endsWith('.canvas') 
        ? cleanDir 
        : `${cleanDir}/${canvasName.replace(/\.canvas$/, '')}.canvas`;

      // 1. Primary REST Canvas Bridge Execution
      let restSucceeded = false;
      try {
        if (direction === 'export' || direction === 'sync') {
          const exportRes = await canvasApiClient.exportToObsidianCanvas(canvasPath, {
            nodes: nodes.map((n) => ({
              id: n.id,
              type: n.type,
              position: n.position,
              dimensions: { width: n.width ?? 250, height: n.height ?? 160 },
              data: n.data || {}
            })),
            edges: edges.map((e) => ({
              id: e.id,
              source: e.source,
              target: e.target,
              label: e.label,
              data: (e as any).data
            }))
          });
          if (exportRes && exportRes.status === 'success') {
            restSucceeded = true;
            set({
              obsidianSyncStatus: 'success',
              obsidianSyncMessage: `Exported ${exportRes.node_count ?? nodes.length} nodes to ${canvasPath}`
            });
          }
        } else if (direction === 'import') {
          const importRes = await canvasApiClient.importFromObsidianCanvas(canvasPath);
          if (importRes && importRes.status === 'success' && importRes.react_flow) {
            restSucceeded = true;
            set({
              nodes: importRes.react_flow.nodes || [],
              edges: importRes.react_flow.edges || [],
              obsidianSyncStatus: 'success',
              obsidianSyncMessage: `Imported ${importRes.react_flow.nodes?.length ?? 0} nodes from ${canvasPath}`
            });
            get().pushHistory();
          }
        }
      } catch (restErr) {
        console.warn('[CanvasStore] REST Canvas Bridge attempt failed, attempting WS channel:', restErr);
      }

      // 2. Secondary WebSocket broadcast for real-time collaboration peers
      const payload = {
        type: 'OBSIDIAN_SYNC_REQUEST',
        event: 'OBSIDIAN_SYNC_REQUEST',
        direction,
        canvas_id: canvasId,
        canvas_name: canvasName,
        target_dir: targetDir,
        vault_path: targetDir,
        canvas_path: canvasPath,
        conflict_strategy: conflictStrategy,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type,
          x: n.position?.x ?? 0,
          y: n.position?.y ?? 0,
          position: n.position,
          width: n.width ?? 250,
          height: n.height ?? 160,
          data: n.data || {}
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          fromNode: e.source,
          toNode: e.target,
          fromSide: (e as any).fromSide || (e as any).sourceHandle,
          toSide: (e as any).toSide || (e as any).targetHandle,
          label: e.label,
          data: (e as any).data
        }))
      };

      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
      } else if (!restSucceeded) {
        const fallbackWs = canvasApiClient.connectWebSocket(
          canvasId,
          (msg) => {
            if (msg.type === 'OBSIDIAN_SYNC_STATUS' || msg.event === 'OBSIDIAN_SYNC_STATUS') {
              if (msg.status === 'success') {
                if ((msg.direction === 'import' || msg.direction === 'sync') && Array.isArray(msg.nodes)) {
                  set({
                    nodes: msg.nodes,
                    edges: Array.isArray(msg.edges) ? msg.edges : get().edges,
                    obsidianSyncStatus: 'success',
                    obsidianSyncMessage: `Synced ${msg.nodes.length} nodes from Obsidian`
                  });
                  get().pushHistory();
                } else {
                  set({
                    obsidianSyncStatus: 'success',
                    obsidianSyncMessage: 'Export to Obsidian completed successfully'
                  });
                }
              } else {
                set({
                  obsidianSyncStatus: 'error',
                  obsidianSyncMessage: msg.error || 'Obsidian sync failed'
                });
              }
            }
          }
        );
        activeWebSocket = fallbackWs;
        set({ websocket: fallbackWs });

        setTimeout(() => {
          if (fallbackWs && fallbackWs.readyState === WebSocket.OPEN) {
            fallbackWs.send(JSON.stringify(payload));
          }
        }, 500);
      }

      return { status: 'success', message: 'Sync request completed' };
    } catch (err: any) {
      console.error('[CanvasStore] syncToObsidian error:', err);
      const errorMsg = String(err?.message || err);
      set({
        obsidianSyncStatus: 'error',
        obsidianSyncMessage: `Sync failed: ${errorMsg}`
      });
      return { status: 'error', message: errorMsg };
    }
  },

  autoClusterNodes: async (options?: { language?: string; k?: number }) => {
    set({ isClustering: true });
    try {
      const allNodes = get().nodes;
      const contentNodes = allNodes.filter(
        (n) => n.type !== 'MindMapClusterNode' && n.type !== 'mindMapCluster'
      );

      if (contentNodes.length < 2) {
        set({ isClustering: false });
        return { status: 'empty', clusters: [] };
      }

      let clusterData: any = null;

      try {
        const response = await fetch('/api/mindmap/cluster', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            nodes: contentNodes,
            k: options?.k,
            language: options?.language || 'uk'
          })
        });
        if (response.ok) {
          clusterData = await response.json();
        }
      } catch (_e) {
        // Fallback to client-side clustering
      }

      if (!clusterData || !clusterData.clusters || clusterData.clusters.length === 0) {
        const palette = [
          { color: '#3B82F6', name: 'Architecture & Backend' },
          { color: '#10B981', name: 'Frontend & UI' },
          { color: '#8B5CF6', name: 'AI Swarm & Logic' },
          { color: '#F59E0B', name: 'Security & Gates' },
          { color: '#EC4899', name: 'Marketing & Ops' }
        ];

        const targetK = options?.k || (contentNodes.length >= 10 ? Math.min(5, Math.ceil(contentNodes.length / 3)) : Math.min(3, Math.ceil(contentNodes.length / 2)));
        const groups: Record<number, any[]> = {};
        for (let i = 0; i < targetK; i++) groups[i] = [];

        contentNodes.forEach((node, idx) => {
          const text = ((node.data?.label || node.data?.title || node.data?.content || '') + ' ' + (node.type || '')).toLowerCase();
          let assigned = idx % targetK;
          if (text.includes('api') || text.includes('db') || text.includes('backend') || text.includes('server')) assigned = 0 % targetK;
          else if (text.includes('ui') || text.includes('canvas') || text.includes('component') || text.includes('front')) assigned = 1 % targetK;
          else if (text.includes('ai') || text.includes('agent') || text.includes('swarm') || text.includes('llm')) assigned = 2 % targetK;
          else if (text.includes('test') || text.includes('sec') || text.includes('audit') || text.includes('gate')) assigned = 3 % targetK;
          groups[assigned].push(node);
        });

        const clusters: any[] = [];
        const repositionedNodes: any[] = [];
        const clusterNodes: any[] = [];

        let currentClusterX = 100;
        let currentClusterY = 100;

        Object.entries(groups).forEach(([cIdxStr, cNodes], colIdx) => {
          if (cNodes.length === 0) return;
          const cIdx = parseInt(cIdxStr, 10);
          const theme = palette[cIdx % palette.length];
          const clusterId = `cluster-${cIdx}`;
          const clusterName = theme.name;

          const cols = 2;
          const nodeWidth = 260;
          const nodeHeight = 160;
          const padX = 40;
          const padY = 60;
          const gapX = 30;
          const gapY = 30;

          const numRows = Math.ceil(cNodes.length / cols);
          const clusterWidth = Math.max(380, padX * 2 + Math.min(cNodes.length, cols) * nodeWidth + (Math.min(cNodes.length, cols) - 1) * gapX);
          const clusterHeight = Math.max(260, padY + 40 + numRows * nodeHeight + (numRows - 1) * gapY);

          const clusterNode = {
            id: clusterId,
            type: 'MindMapClusterNode',
            position: { x: currentClusterX, y: currentClusterY },
            data: {
              clusterId,
              title: clusterName,
              color: theme.color,
              nodeCount: cNodes.length,
              width: clusterWidth,
              height: clusterHeight
            },
            selectable: true,
            draggable: true
          };
          clusterNodes.push(clusterNode);

          cNodes.forEach((node, nIdx) => {
            const r = Math.floor(nIdx / cols);
            const c = nIdx % cols;
            const nx = currentClusterX + padX + c * (nodeWidth + gapX);
            const ny = currentClusterY + padY + r * (nodeHeight + gapY);

            repositionedNodes.push({
              ...node,
              position: { x: nx, y: ny },
              data: {
                ...node.data,
                clusterId,
                clusterName,
                clusterColor: theme.color
              }
            });
          });

          clusters.push({
            clusterId,
            name: clusterName,
            color: theme.color,
            nodeIds: cNodes.map((n) => n.id)
          });

          currentClusterX += clusterWidth + 120;
          if ((colIdx + 1) % 3 === 0) {
            currentClusterX = 100;
            currentClusterY += 580;
          }
        });

        const finalNodes = [...clusterNodes, ...repositionedNodes];
        set({
          nodes: finalNodes,
          isClustering: false,
          clusterMetadata: clusters
        });
        get().pushHistory();
        get().queueDelta({ upsert_nodes: finalNodes });
        return { status: 'success', clusters };
      }

      const clusters = clusterData.clusters || [];
      const clusterNodes = (clusterData.cluster_nodes || []).map((cn: any) => ({
        id: cn.id || `cluster-${cn.cluster_id}`,
        type: 'MindMapClusterNode',
        position: { x: cn.x ?? cn.bounding_box?.min_x ?? 100, y: cn.y ?? cn.bounding_box?.min_y ?? 100 },
        data: {
          clusterId: cn.cluster_id || cn.id,
          title: cn.name || cn.title || 'Cluster',
          color: cn.color || '#3B82F6',
          nodeCount: cn.node_count || (cn.node_ids || []).length,
          width: cn.width ?? cn.bounding_box?.width ?? 400,
          height: cn.height ?? cn.bounding_box?.height ?? 300
        }
      }));

      const repositionedNodes = (clusterData.repositioned_nodes || []).map((rn: any) => {
        const existing: any = contentNodes.find((n) => n.id === rn.id) || {};
        return {
          ...existing,
          ...rn,
          position: { x: rn.x ?? rn.position?.x ?? 0, y: rn.y ?? rn.position?.y ?? 0 },
          data: {
            ...(existing.data || {}),
            ...(rn.data || {}),
            clusterId: rn.cluster_id,
            clusterName: rn.cluster_name,
            clusterColor: rn.cluster_color
          }
        };
      });

      const finalNodes = [...clusterNodes, ...repositionedNodes];
      set({
        nodes: finalNodes,
        isClustering: false,
        clusterMetadata: clusters
      });
      get().pushHistory();
      get().queueDelta({ upsert_nodes: finalNodes });
      return { status: 'success', clusters };
    } catch (err) {
      console.error('Auto-cluster error:', err);
      set({ isClustering: false });
      return { status: 'error', clusters: [], error: String(err) };
    }
  },

  autoClusterMindMap: async (options?: { language?: string; k?: number }) => {
    return get().autoClusterNodes(options);
  }
}));

export const triggerNodeAgent = (nodeId: string, prompt?: string, taskType?: string) => {
  return useCanvasStore.getState().triggerNodeAgent(nodeId, prompt, taskType);
};

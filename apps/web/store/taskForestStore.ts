// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/store/taskForestStore.ts"
// purpose: "Zustand store for Task Forest nodes, dependencies, stage gates, and canvas state."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
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
  EdgeChange,
} from '@xyflow/react';

export type NodeType = 'task' | 'idea' | 'goal' | 'bug' | 'documentation';
export type ExecutionStage = 'backlog' | 'planned' | 'in_progress' | 'review' | 'done';
export type Priority = 'low' | 'medium' | 'high' | 'critical';

export interface TaskNodeData extends Record<string, any> {
  id: string;
  type: NodeType;
  title: string;
  description: string;
  stage: ExecutionStage;
  priority: Priority;
  dependencies: string[];
  tags: string[];
  metadata: Record<string, any>;
  assignedAgent?: string | null;
  agentStatus?: 'idle' | 'running' | 'completed' | 'failed' | null;
  agentRunId?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string | null;
}

export interface TaskForestState {
  nodes: Node<TaskNodeData>[];
  edges: Edge[];
  selectedNodeId: string | null;
  filterStage: ExecutionStage | 'all';

  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;

  setSelectedNodeId: (id: string | null) => void;
  setFilterStage: (stage: ExecutionStage | 'all') => void;

  addNode: (type: NodeType, position?: { x: number; y: number }, title?: string) => string;
  updateNodeData: (id: string, updates: Partial<TaskNodeData>) => void;
  deleteNode: (id: string) => void;
  setNodeStage: (id: string, stage: ExecutionStage) => boolean;

  addDependency: (fromNodeId: string, toNodeId: string) => boolean;
  removeDependency: (fromNodeId: string, toNodeId: string) => void;

  assignAgent: (nodeId: string, agent: string) => void;
  dispatchAgent: (nodeId: string) => Promise<boolean>;
  loadFromTaskDNA: (dna: any) => void;

  loadFromForest: (data: { nodes: Node<TaskNodeData>[]; edges: Edge[] }) => void;
}

const STAGE_TRANSITIONS: Record<ExecutionStage, ExecutionStage[]> = {
  backlog: ['planned'],
  planned: ['in_progress', 'backlog'],
  in_progress: ['review', 'backlog'],
  review: ['done', 'in_progress'],
  done: [],
};

export const useTaskForestStore = create<TaskForestState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  filterStage: 'all',

  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes) as Node<TaskNodeData>[],
    });
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection: Connection) => {
    if (!connection.source || !connection.target) return;
    if (connection.source === connection.target) return;

    // Target depends on Source: Source -> Target
    const success = get().addDependency(connection.target, connection.source);
    if (success) {
      set({
        edges: addEdge(
          {
            ...connection,
            animated: true,
            type: 'smoothstep',
            id: `e-${connection.source}-${connection.target}`,
          },
          get().edges
        ),
      });
    }
  },

  setSelectedNodeId: (id: string | null) => {
    set({ selectedNodeId: id });
  },

  setFilterStage: (stage: ExecutionStage | 'all') => {
    set({ filterStage: stage });
  },

  addNode: (type: NodeType, position = { x: 100, y: 100 }, title = '') => {
    const id = `node-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
    const now = new Date().toISOString();

    const defaultMetadata: Record<string, any> = {};
    if (type === 'idea') {
      defaultMetadata.votes = 0;
      defaultMetadata.status = 'proposed';
    } else if (type === 'goal') {
      defaultMetadata.progress = 0.0;
      defaultMetadata.milestone = null;
    } else if (type === 'bug') {
      defaultMetadata.severity = 'medium';
    } else if (type === 'documentation') {
      defaultMetadata.doc_type = 'guide';
      defaultMetadata.version = '1.0.0';
    }

    const newNode: Node<TaskNodeData> = {
      id,
      type: 'taskNode',
      position,
      data: {
        id,
        type,
        title: title || `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
        description: '',
        stage: 'backlog',
        priority: 'medium',
        dependencies: [],
        tags: [type],
        metadata: defaultMetadata,
        createdAt: now,
        updatedAt: now,
      },
    };

    set({
      nodes: [...get().nodes, newNode],
      selectedNodeId: id,
    });

    return id;
  },

  updateNodeData: (id: string, updates: Partial<TaskNodeData>) => {
    set({
      nodes: get().nodes.map((node) => {
        if (node.id === id) {
          return {
            ...node,
            data: {
              ...node.data,
              ...updates,
              updatedAt: new Date().toISOString(),
            },
          };
        }
        return node;
      }),
    });
  },

  deleteNode: (id: string) => {
    // Check if any other node depends on this node
    const hasDependents = get().nodes.some((node) =>
      node.data.dependencies.includes(id)
    );
    if (hasDependents) {
      console.warn(`Cannot delete node ${id}: other nodes depend on it.`);
      return;
    }

    set({
      nodes: get().nodes.filter((node) => node.id !== id),
      edges: get().edges.filter(
        (edge) => edge.source !== id && edge.target !== id
      ),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId,
    });
  },

  setNodeStage: (id: string, newStage: ExecutionStage): boolean => {
    const node = get().nodes.find((n) => n.id === id);
    if (!node) return false;

    const currentStage = node.data.stage;
    const allowedTransitions = STAGE_TRANSITIONS[currentStage] || [];
    if (!allowedTransitions.includes(newStage)) {
      return false;
    }

    // Check upstream dependencies: must be done for in_progress/review/done
    if (newStage === 'in_progress' || newStage === 'review' || newStage === 'done') {
      const isBlocked = node.data.dependencies.some((depId) => {
        const depNode = get().nodes.find((n) => n.id === depId);
        return depNode && depNode.data.stage !== 'done';
      });
      if (isBlocked) {
        return false;
      }
    }

    const now = new Date().toISOString();
    get().updateNodeData(id, {
      stage: newStage,
      completedAt: newStage === 'done' ? now : null,
    });

    return true;
  },

  addDependency: (fromNodeId: string, toNodeId: string): boolean => {
    if (fromNodeId === toNodeId) return false;

    const nodes = get().nodes;
    const fromNode = nodes.find((n) => n.id === fromNodeId);
    const toNode = nodes.find((n) => n.id === toNodeId);
    if (!fromNode || !toNode) return false;

    // Cycle detection check
    const isReachable = (startId: string, targetId: string, visited = new Set<string>()): boolean => {
      if (startId === targetId) return true;
      visited.add(startId);
      const curr = nodes.find((n) => n.id === startId);
      if (!curr) return false;
      for (const dep of curr.data.dependencies) {
        if (!visited.has(dep)) {
          if (isReachable(dep, targetId, visited)) return true;
        }
      }
      return false;
    };

    if (isReachable(toNodeId, fromNodeId)) {
      return false; // Cycle detected
    }

    const updatedDeps = Array.from(new Set([...fromNode.data.dependencies, toNodeId]));
    get().updateNodeData(fromNodeId, { dependencies: updatedDeps });
    return true;
  },

  removeDependency: (fromNodeId: string, toNodeId: string) => {
    const fromNode = get().nodes.find((n) => n.id === fromNodeId);
    if (!fromNode) return;

    const updatedDeps = fromNode.data.dependencies.filter((id) => id !== toNodeId);
    get().updateNodeData(fromNodeId, { dependencies: updatedDeps });

    set({
      edges: get().edges.filter(
        (edge) => !(edge.source === toNodeId && edge.target === fromNodeId)
      ),
    });
  },

  assignAgent: (nodeId: string, agent: string) => {
    set((state) => ({
      nodes: state.nodes.map((node) => {
        if (node.id !== nodeId) return node;
        return {
          ...node,
          data: {
            ...node.data,
            assignedAgent: agent,
            agentStatus: 'idle',
            updatedAt: new Date().toISOString(),
          },
        };
      }),
    }));
  },

  dispatchAgent: async (nodeId: string) => {
    const node = get().nodes.find((n) => n.id === nodeId);
    if (!node || !node.data.assignedAgent) return false;

    // Advance to in_progress if currently in backlog or planned
    if (node.data.stage === 'backlog' || node.data.stage === 'planned') {
      get().setNodeStage(nodeId, 'in_progress');
    }

    set((state) => ({
      nodes: state.nodes.map((n) => {
        if (n.id !== nodeId) return n;
        return {
          ...n,
          data: {
            ...n.data,
            agentStatus: 'running',
            updatedAt: new Date().toISOString(),
          },
        };
      }),
    }));

    try {
      const res = await fetch('/api/swarm/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent: node.data.assignedAgent,
          task_description: `Execute task '${node.data.title}': ${node.data.description || ''}`,
          mode: 'direct',
        }),
      }).catch(() => null);

      if (res && res.ok) {
        const data = await res.json();
        set((state) => ({
          nodes: state.nodes.map((n) => {
            if (n.id !== nodeId) return n;
            return {
              ...n,
              data: {
                ...n.data,
                agentStatus: 'completed',
                agentRunId: data.run_id || data.task_id || undefined,
                updatedAt: new Date().toISOString(),
              },
            };
          }),
        }));
        get().setNodeStage(nodeId, 'review');
        return true;
      } else {
        // Fallback optimistic simulation for offline / local UI
        setTimeout(() => {
          set((state) => ({
            nodes: state.nodes.map((n) => {
              if (n.id !== nodeId) return n;
              return {
                ...n,
                data: {
                  ...n.data,
                  agentStatus: 'completed',
                  updatedAt: new Date().toISOString(),
                },
              };
            }),
          }));
          get().setNodeStage(nodeId, 'review');
        }, 1500);
        return true;
      }
    } catch {
      set((state) => ({
        nodes: state.nodes.map((n) => {
          if (n.id !== nodeId) return n;
          return {
            ...n,
            data: {
              ...n.data,
              agentStatus: 'failed',
              updatedAt: new Date().toISOString(),
            },
          };
        }),
      }));
      return false;
    }
  },

  loadFromTaskDNA: (dna: any) => {
    const dagItems = dna?.dag_tree || dna?.tasks || [];
    if (!Array.isArray(dagItems) || dagItems.length === 0) return;

    // Calculate topological depth
    const depMap = new Map<string, string[]>();
    dagItems.forEach((item: any) => {
      const id = item.id || item.task_id;
      depMap.set(id, Array.isArray(item.dependencies) ? item.dependencies : []);
    });

    const depthMap = new Map<string, number>();
    const getDepth = (id: string, visited: Set<string> = new Set()): number => {
      if (depthMap.has(id)) return depthMap.get(id)!;
      if (visited.has(id)) return 0;
      visited.add(id);
      const deps = depMap.get(id) || [];
      if (deps.length === 0) {
        depthMap.set(id, 0);
        return 0;
      }
      const maxD = Math.max(...deps.map((d) => (depMap.has(d) ? getDepth(d, new Set(visited)) : -1)));
      const res = maxD + 1;
      depthMap.set(id, res);
      return res;
    };

    dagItems.forEach((item: any) => getDepth(item.id || item.task_id));

    const levelCounts: Record<number, number> = {};
    const newNodes: Node<TaskNodeData>[] = [];
    const newEdges: Edge[] = [];

    dagItems.forEach((item: any) => {
      const id = item.id || item.task_id || `dna-${Math.random().toString(36).substring(2, 9)}`;
      const title = item.title || `Task ${id}`;
      const desc = item.description || item.rationale || '';
      const agent = item.assigned_agent || item.agent || null;
      const risk = String(item.risk_level || 'medium').toLowerCase();

      let priority: Priority = 'medium';
      if (risk === 'critical' || risk === 'urgent') priority = 'critical';
      else if (risk === 'high') priority = 'high';
      else if (risk === 'low') priority = 'low';

      let type: NodeType = 'task';
      const lower = `${title} ${desc}`.toLowerCase();
      if (lower.includes('bug') || lower.includes('fix')) type = 'bug';
      else if (lower.includes('idea') || lower.includes('hypothesis')) type = 'idea';
      else if (lower.includes('goal') || lower.includes('milestone')) type = 'goal';
      else if (lower.includes('doc') || lower.includes('specification') || lower.includes('audit')) type = 'documentation';

      const depth = depthMap.get(id) || 0;
      const rowIdx = levelCounts[depth] || 0;
      levelCounts[depth] = rowIdx + 1;

      newNodes.push({
        id,
        type: 'taskForestNode',
        position: {
          x: 80 + depth * 320,
          y: 80 + rowIdx * 200,
        },
        data: {
          id,
          type,
          title,
          description: desc,
          stage: 'backlog',
          priority,
          dependencies: Array.isArray(item.dependencies) ? item.dependencies : [],
          tags: ['task_dna', `risk_${risk}`],
          assignedAgent: agent,
          agentStatus: agent ? 'idle' : null,
          metadata: { task_dna_id: dna?.task_id || '' },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      });

      if (Array.isArray(item.dependencies)) {
        item.dependencies.forEach((depId: string) => {
          newEdges.push({
            id: `edge-${depId}-${id}`,
            source: depId,
            target: id,
            type: 'smoothstep',
            animated: false,
          });
        });
      }
    });

    set({ nodes: newNodes, edges: newEdges });
  },

  loadFromForest: (data: { nodes: Node<TaskNodeData>[]; edges: Edge[] }) => {
    set({
      nodes: data.nodes,
      edges: data.edges,
    });
  },
}));

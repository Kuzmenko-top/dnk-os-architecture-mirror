// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/types/nodeTasks.ts"
// purpose: "Type definitions for Node Based Task & Ideas DAG System in DNK OS"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

export type NodeType = 'idea' | 'epic' | 'task' | 'slice' | 'gate';

export type ExecutionStage =
  | 'ideation'
  | 'architecture'
  | 'ready'
  | 'in_progress'
  | 'blocked'
  | 'testing'
  | 'completed';

export type PriorityLevel = 'P0_Critical' | 'P1_High' | 'P2_Medium' | 'P3_Low';

export type DependencyType = 'depends_on' | 'blocks' | 'spawns_from' | 'relates_to';

export interface ProjectInfo {
  id: string;
  name: string;
  slug: string;
  description?: string;
  color?: string;
  icon?: string;
  is_active?: boolean;
  tasks_count?: number;
  created_at?: string;
}

export interface TaskNodeData {
  id: string;
  title: string;
  description: string;
  node_type: NodeType;
  stage: ExecutionStage;
  status: string;
  progress: number;
  assigned_agent: string;
  priority: PriorityLevel;
  tags: string[];
  blockers: string[];
  is_blocked: boolean;
  position_x: number;
  position_y: number;
  position?: { x: number; y: number };
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  project_id?: string;
}

export interface TaskEdgeData {
  id: string;
  source: string;
  target: string;
  dependency_type: DependencyType;
  description: string;
  is_satisfied: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface GraphStats {
  total_nodes: number;
  ideas_count?: number;
  epics_count?: number;
  tasks_count?: number;
  slices_count?: number;
  gates_count?: number;
  blocked_count?: number;
  ready_count?: number;
  in_progress_count?: number;
  completed_count?: number;
  overall_progress?: number;
  agent_workload?: Record<string, number>;
  by_type?: Record<string, number>;
  by_stage?: Record<string, number>;
  blocked_nodes_count?: number;
  overall_progress_pct?: number;
  edge_count?: number;
}

export interface TaskGraphResponse {
  graph: {
    nodes: Record<string, TaskNodeData>;
    edges: TaskEdgeData[];
    metadata: Record<string, unknown>;
  };
  stats: GraphStats;
  topological_order: string[];
}

export interface ArtifactFileDiff {
  path: string;
  change_type: 'added' | 'modified' | 'deleted' | string;
  additions: number;
  deletions: number;
  diff_content: string;
}

export interface NodeArtifactReport {
  node_id: string;
  agent: string;
  status: string;
  files: ArtifactFileDiff[];
  total_additions: number;
  total_deletions: number;
  executed_at: string;
}

export interface VerificationResult {
  status: 'success' | 'failure' | string;
  node_id: string;
  action: string;
  verified: boolean;
  exit_code: number;
  output: string;
  message?: string;
}

export interface MarketingVideoScene {
  id: string;
  title: string;
  subtitle: string;
  duration_frames: number;
  bg_gradient: string;
  accent_color: string;
}

export interface MarketingVideoPayload {
  composition_id: string;
  aspect_ratio: string;
  duration_in_frames: number;
  fps: number;
  scenes: MarketingVideoScene[];
  voiceover_script: string;
  grounded_diffs_summary: string[];
}



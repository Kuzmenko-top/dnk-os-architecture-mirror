// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/types/canvasBridge.ts"
// purpose: "TypeScript definitions for Obsidian Canvas ↔ React Flow SSOT Bridge payload contracts."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK Swarm (gerych_builder)"
// --- END DNK-MRH-HEADER ---

export interface ReactFlowNodePosition {
  x: number;
  y: number;
}

export interface ReactFlowNodeDimensions {
  width: number;
  height: number;
}

export interface ReactFlowNodeData {
  id: string;
  label: string;
  title: string;
  content: string;
  color: string;
  worker?: string;
  obsidian_type?: string;
  [key: string]: unknown;
}

export interface ReactFlowNode {
  id: string;
  type: string;
  position: ReactFlowNodePosition;
  dimensions?: ReactFlowNodeDimensions;
  data: ReactFlowNodeData;
}

export interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  label?: string;
  type?: string;
  data?: Record<string, unknown>;
}

export interface ReactFlowGraphData {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
}

export interface CanvasBridgeResponse {
  status: "success" | "error";
  canvas_path?: string;
  react_flow?: ReactFlowGraphData;
  node_count?: number;
  edge_count?: number;
  message?: string;
}

export interface CanvasTriggerCheckResponse {
  status: "success" | "error";
  canvas_path: string;
  result: Array<{
    node_id: string;
    action_type: "run_tests" | "dispatch_worker";
    command?: string;
    assigned_agent?: string;
    success?: boolean;
    timestamp?: string;
  }>;
}

export type SwarmLifecycleStage = "TASK_STARTED" | "TASK_PROGRESS" | "TASK_COMPLETED" | "TASK_FAILED";

export interface SwarmHudEvent {
  type: "SWARM_HUD_EVENT";
  timestamp: string;
  task_id: string;
  event_type: SwarmLifecycleStage;
  stage: "in_progress" | "completed" | "failed" | "backlog";
  assigned_agent: string;
  agent_badge: string;
  canvas_color: string;
  hex_color: string;
  progress_pct?: number | null;
  progress_bar?: string | null;
  message?: string | null;
  canvas_path?: string | null;
}

export interface SwarmHudEventRequest {
  task_id: string;
  event_type: SwarmLifecycleStage;
  assigned_agent?: string;
  canvas_path?: string;
  progress_pct?: number;
  message?: string;
  update_canvas_disk?: boolean;
}

export interface CanvasOccMergeRequest {
  base: ReactFlowGraphData;
  current: ReactFlowGraphData;
  incoming: ReactFlowGraphData;
  canvas_id?: string;
}

export interface CanvasOccMergeResponse {
  status: "clean" | "conflict";
  merged_graph: ReactFlowGraphData;
  conflicts: Array<{
    type: string;
    id: string;
    description: string;
    base_val?: any;
    current_val?: any;
    incoming_val?: any;
  }>;
  conflict_count: number;
}

export interface SwarmAgentEvent {
  type: string;
  agent: string;
  task_id: string;
  status: string;
  timestamp?: string;
  details?: any;
}

export type SwarmOverallHealthStatus = "healthy" | "degraded" | "unhealthy";

export interface SwarmWorkerHealthCard {
  agent_id: string;
  name: string;
  status: string;
  capabilities: string[];
  badge: string;
  hex: string;
  hex_color: string;
  canvas_color: string;
}

export interface SwarmWorkersHealth {
  total_agents: number;
  total_workers: number;
  ready_count: number;
  ready_workers: number;
  busy_count: number;
  busy_workers: number;
  workers?: SwarmWorkerHealthCard[];
  agents?: SwarmWorkerHealthCard[];
}

export interface SwarmSentinelHealth {
  status: "clean" | "warning" | "critical" | "alerts_active";
  total_active_alerts: number;
  active_alerts_count: number;
  critical_count: number;
  critical_alerts_count: number;
  warning_count: number;
  warning_alerts_count: number;
  pending_self_heal_tasks: number;
  self_heal_plans_count: number;
  alerts: Array<Record<string, any>>;
}

export interface SwarmAccountingHealth {
  workspace_id: string;
  budget_status: "normal" | "near_limit" | "exceeded" | "unknown";
  total_runs: number;
  success_rate_pct: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost_usd: number;
  spend_limit_usd: number;
  spend_saturation_pct: number;
  total_usd_saved: number;
}

export interface SwarmCanvasBridgeHealth {
  status: "active" | "idle" | "unavailable";
  active_connections: number;
  total_connections: number;
  subscribed_canvases_count: number;
  subscribed_canvases: string[];
  total_events_broadcast: number;
}

export interface SwarmSystemMetrics {
  uptime_seconds: number;
  memory_rss_mb: number;
  python_version: string;
  platform: string;
}

export interface SwarmHealthSnapshot {
  overall_status: SwarmOverallHealthStatus;
  timestamp: string;
  status_reasons: string[];
  workspace_id: string;
  active_workers: SwarmWorkersHealth;
  sentinel: SwarmSentinelHealth;
  accounting: SwarmAccountingHealth;
  canvas_bridge: SwarmCanvasBridgeHealth;
  system: SwarmSystemMetrics;
  system_metrics: SwarmSystemMetrics;
  system_resources: SwarmSystemMetrics;
}



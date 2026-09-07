// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_src_lib_dnk_api"
// purpose: "FastAPI Gateway Bridge connecting DNK OS Web App to Gateway (:8000)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "2.0.0"
// updated_at: "2026-08-30"
// --- END DNK-MRH-HEADER ---

export const GATEWAY_BASE_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

export interface WorkspaceItem {
  id: string;
  name: string;
  description?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CanvasNodeData {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface CanvasEdgeData {
  id: string;
  source: string;
  target: string;
  data?: Record<string, unknown>;
}

export interface CanvasStateV1 {
  canvas_id: string;
  nodes: CanvasNodeData[];
  edges: CanvasEdgeData[];
  occ_state?: Record<string, unknown>;
}

export interface CanvasStateV3 {
  canvas_id: string;
  nodes: CanvasNodeData[];
  edges: CanvasEdgeData[];
  occ_state?: Record<string, unknown>;
  version: string;
  updated_at?: string;
}

export interface ShopifyPreviewPayload {
  template_code: string;
  context_data?: Record<string, unknown>;
  theme_id?: string;
}

export interface ShopifyPreviewResult {
  status: 'success' | 'error';
  html?: string;
  css?: string;
  rendered_ast?: Record<string, unknown>;
  error?: string;
}

export interface VideoTimelinePayload {
  timeline_id: string;
  clips: Array<{
    id: string;
    source_url: string;
    start_time: number;
    duration: number;
  }>;
  audio_track?: {
    url: string;
    volume?: number;
  };
  output_format?: 'mp4' | 'webm';
}

export interface VideoTimelineResult {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  video_url?: string;
  error?: string;
}

export interface SwarmDispatchPayload {
  goal: string;
  target_agent?: string;
  context?: Record<string, unknown>;
}

export interface SwarmDispatchResult {
  task_id: string;
  subagent_id?: string;
  status: string;
  output?: string;
  error?: string;
}

/**
 * 1. Workspaces API: GET/POST /api/v1/workspaces
 */
export async function fetchWorkspaces(): Promise<WorkspaceItem[]> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/v1/workspaces`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) ? data : data.workspaces || [];
  } catch (err) {
    console.warn('[DNK-API] fetchWorkspaces fallback to empty list:', err);
    return [];
  }
}

export async function createWorkspace(payload: { name: string; description?: string }): Promise<WorkspaceItem> {
  const res = await fetch(`${GATEWAY_BASE_URL}/api/v1/workspaces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to create workspace: ${res.statusText}`);
  return res.json();
}

/**
 * 2. Canvas API: GET/POST /api/v1/canvas and /api/v3/canvas
 */
export async function getCanvasStateV1(canvasId: string): Promise<CanvasStateV1 | null> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/v1/canvas/${encodeURIComponent(canvasId)}`);
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.warn('[DNK-API] getCanvasStateV1 failed:', err);
    return null;
  }
}

export async function getCanvasStateV3(canvasId: string): Promise<CanvasStateV3 | null> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/v3/canvas/${encodeURIComponent(canvasId)}`);
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.warn('[DNK-API] getCanvasStateV3 failed:', err);
    return null;
  }
}

export async function saveCanvasStateV1(payload: CanvasStateV1): Promise<{ status: string }> {
  const res = await fetch(`${GATEWAY_BASE_URL}/api/v1/canvas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to save canvas v1: ${res.statusText}`);
  return res.json();
}

export async function saveCanvasStateV3(canvasId: string, payload: Partial<CanvasStateV3>): Promise<{ status: string }> {
  const res = await fetch(`${GATEWAY_BASE_URL}/api/v3/canvas/${encodeURIComponent(canvasId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Failed to save canvas v3: ${res.statusText}`);
  return res.json();
}

/**
 * 3. Shopify Preview API: POST /api/shopify/preview/render
 */
export async function renderShopifyPreview(payload: ShopifyPreviewPayload): Promise<ShopifyPreviewResult> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/shopify/preview/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      return { status: 'error', error: `HTTP ${res.status}` };
    }
    return res.json();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { status: 'error', error: msg };
  }
}

/**
 * 4. Video Synthesis API: POST /api/v1/video/timeline/synthesize
 */
export async function synthesizeVideoTimeline(payload: VideoTimelinePayload): Promise<VideoTimelineResult> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/v1/video/timeline/synthesize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      return { job_id: '', status: 'failed', error: `HTTP ${res.status}` };
    }
    return res.json();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { job_id: '', status: 'failed', error: msg };
  }
}

/**
 * 5. Swarm Dispatch API: POST /api/agent/swarm/dispatch
 */
export async function dispatchSwarmAgent(payload: SwarmDispatchPayload): Promise<SwarmDispatchResult> {
  try {
    const res = await fetch(`${GATEWAY_BASE_URL}/api/agent/swarm/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      return { task_id: '', status: 'error', error: `HTTP ${res.status}` };
    }
    return res.json();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { task_id: '', status: 'error', error: msg };
  }
}

/**
 * Helper to construct SSE stream URL for Swarm A2A Federation
 */
export function getA2AFederationStreamUrl(sessionToken?: string): string {
  const token = sessionToken || 'default_session';
  return `${GATEWAY_BASE_URL}/api/v1/a2a/federation/stream/${encodeURIComponent(token)}/events`;
}

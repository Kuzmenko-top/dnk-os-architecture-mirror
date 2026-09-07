// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_canvas_bridge_client"
// purpose: "SSOT Canvas Bridge WebSocket & REST client with auto-reconnect, exponential backoff, event buffering, and OCC merge"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  ReactFlowGraphData,
  CanvasOccMergeRequest,
  CanvasOccMergeResponse,
  SwarmAgentEvent,
} from '../../types/canvasBridge';

function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin.replace(':3000', ':8000');
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

function getWsUrl(canvasId?: string): string {
  const base = getApiBaseUrl();
  const wsProto = base.startsWith('https') ? 'wss' : 'ws';
  const host = base.replace(/^https?:\/\//, '');
  const query = canvasId ? `?canvas_id=${encodeURIComponent(canvasId)}` : '';
  return `${wsProto}://${host}/api/v1/canvas/stream${query}`;
}

export async function mergeCanvasState(req: CanvasOccMergeRequest): Promise<CanvasOccMergeResponse> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/canvas/merge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    throw new Error(`Canvas merge failed: ${res.statusText}`);
  }
  return res.json();
}

export async function broadcastSwarmEvent(event: SwarmAgentEvent): Promise<{ success: boolean; event: string }> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/canvas/swarm/event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  });
  if (!res.ok) {
    throw new Error(`Broadcast event failed: ${res.statusText}`);
  }
  return res.json();
}

export interface UseCanvasBridgeOptions {
  canvasId?: string;
  onCanvasChanged?: (data: any) => void;
  onSwarmAgentStatus?: (event: SwarmAgentEvent) => void;
  onCanvasMerged?: (data: CanvasOccMergeResponse) => void;
}

export interface UseCanvasBridgeResult {
  connected: boolean;
  sendEvent: (payload: any) => void;
  sendOccMerge: (base: ReactFlowGraphData, current: ReactFlowGraphData, incoming: ReactFlowGraphData) => void;
  broadcastAgentStatus: (agent: string, taskId: string, status: string, details?: any) => void;
}

export function useCanvasBridge({
  canvasId,
  onCanvasChanged,
  onSwarmAgentStatus,
  onCanvasMerged,
}: UseCanvasBridgeOptions = {}): UseCanvasBridgeResult {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const outgoingQueueRef = useRef<string[]>([]);
  const isMountedRef = useRef(true);

  // Keep callback refs fresh
  const onCanvasChangedRef = useRef(onCanvasChanged);
  onCanvasChangedRef.current = onCanvasChanged;
  const onSwarmAgentStatusRef = useRef(onSwarmAgentStatus);
  onSwarmAgentStatusRef.current = onSwarmAgentStatus;
  const onCanvasMergedRef = useRef(onCanvasMerged);
  onCanvasMergedRef.current = onCanvasMerged;

  const flushQueue = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    while (outgoingQueueRef.current.length > 0) {
      const msg = outgoingQueueRef.current.shift();
      if (msg) wsRef.current.send(msg);
    }
  }, []);

  const sendEvent = useCallback((payload: any) => {
    const raw = typeof payload === 'string' ? payload : JSON.stringify(payload);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(raw);
    } else {
      // Buffer outgoing events during reconnection
      if (outgoingQueueRef.current.length < 100) {
        outgoingQueueRef.current.push(raw);
      }
    }
  }, []);

  const sendOccMerge = useCallback(
    (base: ReactFlowGraphData, current: ReactFlowGraphData, incoming: ReactFlowGraphData) => {
      sendEvent({
        type: 'CANVAS_OCC_MERGE',
        base,
        current,
        incoming,
        canvas_id: canvasId,
      });
    },
    [canvasId, sendEvent]
  );

  const broadcastAgentStatus = useCallback(
    (agent: string, taskId: string, status: string, details?: any) => {
      sendEvent({
        type: 'SWARM_AGENT_STATUS',
        agent,
        task_id: taskId,
        status,
        timestamp: new Date().toISOString(),
        details,
      });
    },
    [sendEvent]
  );

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    try {
      const url = getWsUrl(canvasId);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setConnected(true);
        reconnectAttemptsRef.current = 0;
        flushQueue();

        // 25s keepalive ping
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const msg = JSON.parse(event.data);
          const msgType = msg.type || msg.event;

          if (msgType === 'CANVAS_CHANGED' && onCanvasChangedRef.current) {
            onCanvasChangedRef.current(msg);
          } else if (msgType === 'SWARM_AGENT_STATUS' && onSwarmAgentStatusRef.current) {
            onSwarmAgentStatusRef.current(msg);
          } else if (msgType === 'CANVAS_MERGED' && onCanvasMergedRef.current) {
            onCanvasMergedRef.current(msg);
          }
        } catch (e) {
          console.warn('[CanvasBridgeWS] Parse error:', e);
        }
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setConnected(false);
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Exponential backoff reconnect: min 1.5s, max 10s
        const backoff = Math.min(1500 * Math.pow(1.5, reconnectAttemptsRef.current), 10000);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, backoff);
      };

      ws.onerror = () => {
        if (!isMountedRef.current) return;
        ws.close();
      };
    } catch (e) {
      console.warn('[CanvasBridgeWS] Connection setup failed:', e);
    }
  }, [canvasId, flushQueue]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    connected,
    sendEvent,
    sendOccMerge,
    broadcastAgentStatus,
  };
}

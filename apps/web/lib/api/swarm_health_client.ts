// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_swarm_health_client"
// purpose: "Swarm Health REST and WebSocket streaming client with auto-reconnect, exponential backoff, and heartbeat"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-06"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useRef, useCallback } from 'react';
import type { SwarmHealthSnapshot } from '../../types/canvasBridge';

function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.protocol}//${window.location.host}`;
  }
  return 'http://localhost:8000';
}

function getWebSocketUrl(): string {
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/api/v1/health/swarm/ws`;
  }
  return 'ws://localhost:8000/api/v1/health/swarm/ws';
}

export async function fetchSwarmHealth(
  workspaceId: string = 'ws-alpha-001',
  details: boolean = true,
  spendLimitUsd?: number
): Promise<SwarmHealthSnapshot> {
  const base = getApiBaseUrl();
  const params = new URLSearchParams({
    workspace_id: workspaceId,
    details: details ? 'true' : 'false',
  });
  if (spendLimitUsd !== undefined) {
    params.set('spend_limit_usd', String(spendLimitUsd));
  }

  const res = await fetch(`${base}/api/v1/health/swarm?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch swarm health: ${res.statusText}`);
  }
  return (await res.json()) as SwarmHealthSnapshot;
}

export async function triggerSwarmHeal(
  alertId?: string,
  action: string = "resolve",
  workspaceId: string = "ws-alpha-001"
): Promise<{ success: boolean; message: string; healed_alerts_count: number }> {
  const url = `${getApiBaseUrl()}/api/v1/health/swarm/heal`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      alert_id: alertId,
      action,
      workspace_id: workspaceId,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to trigger auto-heal: ${res.statusText}`);
  }
  return res.json();
}


export interface UseSwarmHealthStreamResult {
  health: SwarmHealthSnapshot | null;
  connected: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  heal: (alertId?: string) => Promise<void>;
}

export function useSwarmHealthStream(workspaceId: string = 'ws-alpha-001'): UseSwarmHealthStreamResult {
  const [health, setHealth] = useState<SwarmHealthSnapshot | null>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const initialFetch = useCallback(async () => {
    try {
      const initial = await fetchSwarmHealth(workspaceId, true);
      if (isMountedRef.current) {
        setHealth(initial);
        setLoading(false);
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        setError(err.message || 'Initial health fetch failed');
        setLoading(false);
      }
    }
  }, [workspaceId]);

  const sendRefresh = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'refresh', workspace_id: workspaceId, details: true }));
    } else {
      // Fallback to REST fetch
      fetchSwarmHealth(workspaceId, true)
        .then((data) => {
          if (isMountedRef.current) setHealth(data);
        })
        .catch((err) => {
          if (isMountedRef.current) setError(err.message);
        });
    }
  }, [workspaceId]);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;

    try {
      const wsUrl = getWebSocketUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;

        // Heartbeat every 25 seconds
        if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'ping' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'SWARM_HEALTH_SNAPSHOT' || msg.type === 'SWARM_HEALTH_UPDATE' || msg.type === 'SWARM_HEAL_RESULT') {
            if (msg.data) {
              setHealth(msg.data as SwarmHealthSnapshot);
              setLoading(false);
            }
          }
        } catch (parseErr) {
          console.warn('[SwarmHealthWS] Parse error:', parseErr);
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
        setError('WebSocket connection error');
        ws.close();
      };
    } catch (wsErr: any) {
      if (!isMountedRef.current) return;
      setError(wsErr.message || 'Failed to initialize WebSocket');
    }
  }, [workspaceId]);

  const sendHeal = useCallback(async (alertId?: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'heal', alert_id: alertId }));
    } else {
      const res = await triggerSwarmHeal(alertId, 'resolve', workspaceId);
      if (res.success) {
        sendRefresh();
      }
    }
  }, [workspaceId, sendRefresh]);

  useEffect(() => {
    isMountedRef.current = true;
    initialFetch();
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
  }, [initialFetch, connect]);

  return {
    health,
    connected,
    loading,
    error,
    refresh: sendRefresh,
    heal: sendHeal,
  };
}

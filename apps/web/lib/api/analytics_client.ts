// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_analytics_client"
// purpose: "Workspace Analytics REST and WebSocket Client hooks with automatic reconnect and live metrics"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useRef } from 'react';

export interface WorkspaceMetrics {
  activity: any[];
  performance: Record<string, { p50: number; p95: number; p99: number; avg: number; count: number }>;
  errors: any[];
  users: any[];
}

export interface LiveMetricsUpdate {
  type: 'metrics_update';
  workspace_id: string;
  timestamp: string;
  activity_count: number;
  performance: {
    avg_latency: number;
    error_count: number;
  };
}

export function useWorkspaceAnalytics(workspaceId: string, timeRangeHours: number = 24) {
  const [metrics, setMetrics] = useState<WorkspaceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchMetrics() {
      try {
        setLoading(true);
        const [activityRes, performanceRes, errorsRes, usersRes] = await Promise.all([
          fetch(`/api/v1/analytics/workspaces/${workspaceId}/activity?hours=${timeRangeHours}`),
          fetch(`/api/v1/analytics/workspaces/${workspaceId}/performance?hours=${timeRangeHours}`),
          fetch(`/api/v1/analytics/workspaces/${workspaceId}/errors?hours=${timeRangeHours}`),
          fetch(`/api/v1/analytics/workspaces/${workspaceId}/users?hours=${timeRangeHours}`),
        ]);

        const [activity, performance, errors, users] = await Promise.all([
          activityRes.json(),
          performanceRes.json(),
          errorsRes.json(),
          usersRes.json(),
        ]);

        if (isMounted) {
          setMetrics({
            activity: activity.activity || [],
            performance: performance.performance || {},
            errors: errors.errors || [],
            users: users.users || [],
          });
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    if (workspaceId) {
      fetchMetrics();
    }

    return () => {
      isMounted = false;
    };
  }, [workspaceId, timeRangeHours]);

  return { metrics, loading, error };
}

export function useWorkspaceLiveMetrics(workspaceId: string) {
  const [liveMetrics, setLiveMetrics] = useState<LiveMetricsUpdate | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let heartbeat: NodeJS.Timeout | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let isMounted = true;

    const connect = () => {
      if (!isMounted || !workspaceId) return;

      try {
        const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = typeof window !== 'undefined' && window.location.host ? window.location.host : 'localhost:8000';
        ws = new WebSocket(`${protocol}//${host}/api/v1/analytics/workspaces/${workspaceId}/live`);

        ws.onopen = () => {
          if (isMounted) {
            setConnected(true);
            wsRef.current = ws;
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update' && isMounted) {
              setLiveMetrics(data);
            }
          } catch (e) {
            console.error('Failed to parse WS message:', e);
          }
        };

        ws.onclose = () => {
          if (isMounted) {
            setConnected(false);
            // Auto-reconnect after 5 seconds
            reconnectTimer = setTimeout(connect, 5000);
          }
        };

        ws.onerror = () => {
          if (ws) {
            ws.close();
          }
        };

        // Heartbeat (ping/pong)
        heartbeat = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      } catch (err) {
        console.error('WebSocket connection error:', err);
        if (isMounted) {
          reconnectTimer = setTimeout(connect, 5000);
        }
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (heartbeat) clearInterval(heartbeat);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
      }
    };
  }, [workspaceId]);

  return { liveMetrics, connected };
}

export function useAlertRules(workspaceId: string) {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRules = async () => {
    if (!workspaceId) return;
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/analytics/alerts/rules?workspace_id=${workspaceId}`);
      const data = await res.json();
      setRules(data.rules || []);
    } catch (e) {
      console.error('Failed to fetch rules:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, [workspaceId]);

  return { rules, loading, refetch: fetchRules };
}

export function useSLOMonitoring(workspaceId: string) {
  const [status, setStatus] = useState<any | null>(null);
  const [burnRate, setBurnRate] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!workspaceId) return;
    async function loadSLO() {
      try {
        setLoading(true);
        const [statusRes, burnRes] = await Promise.all([
          fetch(`/api/v1/analytics/slo/status?workspace_id=${workspaceId}`),
          fetch(`/api/v1/analytics/slo/burn-rate?workspace_id=${workspaceId}`),
        ]);
        const [statusData, burnData] = await Promise.all([statusRes.json(), burnRes.json()]);
        setStatus(statusData);
        setBurnRate(burnData.chart || []);
      } catch (e) {
        console.error('Failed to fetch SLO:', e);
      } finally {
        setLoading(false);
      }
    }
    loadSLO();
  }, [workspaceId]);

  return { status, burnRate, loading };
}

export function useAnomalyScores(workspaceId: string) {
  const [scores, setScores] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!workspaceId) return;
    async function loadAnomalies() {
      try {
        setLoading(true);
        const [scoresRes, eventsRes] = await Promise.all([
          fetch(`/api/v1/analytics/anomalies/scores?workspace_id=${workspaceId}`),
          fetch(`/api/v1/analytics/anomalies/events?workspace_id=${workspaceId}`),
        ]);
        const [scoresData, eventsData] = await Promise.all([scoresRes.json(), eventsRes.json()]);
        setScores(scoresData.scores || []);
        setEvents(eventsData.events || []);
      } catch (e) {
        console.error('Failed to fetch anomalies:', e);
      } finally {
        setLoading(false);
      }
    }
    loadAnomalies();
  }, [workspaceId]);

  return { scores, events, loading };
}


// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_analytics_anomaly_client"
// purpose: "Real-Time Anomaly Detection & Advanced Alerting TypeScript Client Hooks (DNK-ANALYTICS-004)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useCallback, useRef } from 'react';

export interface AnomalyDetectionConfig {
  id: string;
  workspace_id: string;
  metric_type: string;
  detector_type: 'zscore' | 'iqr' | 'holt_winters' | 'isolation_forest';
  sensitivity: number;
  rolling_window_hours: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface DynamicThreshold {
  id: string;
  workspace_id: string;
  metric_type: string;
  calculated_at: string;
  rolling_window_hours: number;
  mean_value: number;
  std_value: number;
  percentile_p10: number;
  percentile_p50: number;
  percentile_p90: number;
  lower_bound: number;
  upper_bound: number;
}

export interface AnomalyEvent {
  id: string;
  config_id: string;
  workspace_id: string;
  detected_at: string;
  metric_value: number;
  anomaly_score: number;
  detector_used: string;
  threshold_lower?: number;
  threshold_upper?: number;
  is_anomalous: boolean;
  metadata?: Record<string, any>;
}

export interface AdvancedAlertRule {
  id: string;
  workspace_id: string;
  rule_name: string;
  composite_logic: Record<string, any>;
  severity: 'info' | 'warning' | 'critical';
  cooldown_seconds: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdvancedAlertEvent {
  id: string;
  rule_id: string;
  workspace_id: string;
  triggered_at: string;
  severity: string;
  channels_delivered: string[];
  delivery_status: Record<string, string>;
  resolved_at?: string | null;
  resolution_note?: string | null;
  metadata?: Record<string, any>;
}

export interface AlertChannelConfig {
  id: string;
  workspace_id: string;
  channel_type: 'telegram' | 'slack' | 'pagerduty' | 'email';
  channel_config: Record<string, any>;
  enabled: boolean;
  created_at: string;
}

export function useAnomalyDetectionConfigs(workspaceId: string) {
  const [configs, setConfigs] = useState<AnomalyDetectionConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfigs = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/anomaly-detection/configs?workspace_id=${workspaceId}`);
      if (!res.ok) throw new Error('Failed to fetch anomaly configs');
      const data = await res.json();
      setConfigs(data);
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  return { configs, loading, error, refresh: fetchConfigs };
}

export function useAnomalyEvents(workspaceId: string) {
  const [events, setEvents] = useState<AnomalyEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/anomaly-detection/events?workspace_id=${workspaceId}`);
      if (!res.ok) throw new Error('Failed to fetch anomaly events');
      const data = await res.json();
      setEvents(data);
    } catch (error: unknown) {
      console.error('Failed to fetch anomaly events', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return { events, loading, refresh: fetchEvents };
}

export function useAdvancedAlertRules(workspaceId: string) {
  const [rules, setRules] = useState<AdvancedAlertRule[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchRules = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/alerts/rules/advanced?workspace_id=${workspaceId}`);
      if (!res.ok) throw new Error('Failed to fetch alert rules');
      const data = await res.json();
      setRules(data);
    } catch (error: unknown) {
      console.error('Failed to fetch alert rules', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  return { rules, loading, refresh: fetchRules };
}

export function useAlertChannels(workspaceId: string) {
  const [channels, setChannels] = useState<AlertChannelConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchChannels = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/alerts/channels?workspace_id=${workspaceId}`);
      if (!res.ok) throw new Error('Failed to fetch alert channels');
      const data = await res.json();
      setChannels(data);
    } catch (error: unknown) {
      console.error('Failed to fetch alert channels', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchChannels();
  }, [fetchChannels]);

  return { channels, loading, refresh: fetchChannels };
}

export function useAnomalyLiveStream() {
  const [latestTelemetry, setLatestTelemetry] = useState<any>(null);
  const [connected, setConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/anomaly-detection/live`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnected(true);
    ws.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        setLatestTelemetry(payload);
      } catch (e) {
        console.error('Error parsing anomaly telemetry WS payload', e);
      }
    };
    ws.onclose = () => setConnected(false);
    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  return { latestTelemetry, connected };
}

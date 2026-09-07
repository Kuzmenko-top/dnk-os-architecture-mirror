// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_analytics_forecast_client"
// purpose: "Predictive Analytics & ML Forecasting client hooks (Models, Snapshots, Workload Predictions, Accuracy, Live Stream)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useRef, useCallback } from 'react';

export interface ForecastModel {
  id: string;
  workspace_id: string;
  metric_type: string;
  model_name: string;
  model_params: Record<string, any>;
  training_window_days: number;
  retrain_frequency_hours: number;
  enabled: boolean;
  last_trained_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ForecastSnapshot {
  id: string;
  workspace_id: string;
  metric_type: string;
  forecast_horizon_minutes: number;
  predicted_at: string;
  target_time: string;
  predicted_value: number;
  confidence_p10: number;
  confidence_p50: number;
  confidence_p90: number;
  model_used: string;
  confidence_score: number;
}

export interface WorkloadPrediction {
  id: string;
  workspace_id: string;
  pool_id?: string;
  predicted_at: string;
  target_time: string;
  predicted_queue_depth: number;
  confidence_p10_queue: number;
  confidence_p90_queue: number;
  recommended_worker_count: number;
  current_worker_count: number;
  confidence_score: number;
  triggered_scaling: boolean;
}

export interface RecommendedCapacity {
  workspace_id: string;
  pool_id?: string;
  current_worker_count: number;
  peak_predicted_queue_p50: number;
  peak_predicted_queue_p90: number;
  recommended_worker_count: number;
  proactive_scale_recommended: boolean;
  headroom_buffer_percent: number;
  horizon_minutes: number;
}

export interface ForecastAccuracy {
  id: string;
  model_id: string;
  evaluation_time: string;
  mae: number;
  rmse: number;
  mape: number;
  r2_score: number;
  evaluation_window_hours: number;
}

export function useForecastModels(workspaceId: string = 'ws-alpha-001') {
  const [models, setModels] = useState<ForecastModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/analytics/forecast/models?workspace_id=${workspaceId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setModels(data.models || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch models');
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const retrainModel = async (modelId: string) => {
    const res = await fetch(`/api/v1/analytics/forecast/models/${modelId}/train`, { method: 'POST' });
    if (!res.ok) throw new Error('Retrain failed');
    await fetchModels();
    return await res.json();
  };

  return { models, loading, error, refetch: fetchModels, retrainModel };
}

export function useForecastSnapshots(workspaceId: string = 'ws-alpha-001', metricType?: string) {
  const [snapshots, setSnapshots] = useState<ForecastSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSnapshots = useCallback(async () => {
    try {
      setLoading(true);
      const url = metricType
        ? `/api/v1/analytics/forecast/snapshots/${metricType}?workspace_id=${workspaceId}`
        : `/api/v1/analytics/forecast/snapshots?workspace_id=${workspaceId}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSnapshots(data.snapshots || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch snapshots');
    } finally {
      setLoading(false);
    }
  }, [workspaceId, metricType]);

  useEffect(() => {
    fetchSnapshots();
  }, [fetchSnapshots]);

  return { snapshots, loading, error, refetch: fetchSnapshots };
}

export function useWorkloadPredictions(workspaceId: string = 'ws-alpha-001', poolId?: string) {
  const [predictions, setPredictions] = useState<WorkloadPrediction[]>([]);
  const [capacity, setCapacity] = useState<RecommendedCapacity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPredictions = useCallback(async () => {
    try {
      setLoading(true);
      const poolQuery = poolId ? `&pool_id=${poolId}` : '';
      const [predRes, capRes] = await Promise.all([
        fetch(`/api/v1/analytics/workload/predictions?workspace_id=${workspaceId}${poolQuery}`),
        fetch(`/api/v1/analytics/workload/predictions/recommended?workspace_id=${workspaceId}${poolQuery}`),
      ]);
      const [predData, capData] = await Promise.all([predRes.json(), capRes.json()]);

      setPredictions(predData.predictions || []);
      setCapacity(capData || null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workload predictions');
    } finally {
      setLoading(false);
    }
  }, [workspaceId, poolId]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  return { predictions, capacity, loading, error, refetch: fetchPredictions };
}

export function useForecastAccuracy(modelId?: string) {
  const [accuracyList, setAccuracyList] = useState<ForecastAccuracy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAccuracy = useCallback(async () => {
    try {
      setLoading(true);
      const url = modelId
        ? `/api/v1/analytics/forecast/accuracy?model_id=${modelId}`
        : `/api/v1/analytics/forecast/accuracy`;
      const res = await fetch(url);
      const data = await res.json();
      setAccuracyList(data.accuracy_evaluations || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch accuracy');
    } finally {
      setLoading(false);
    }
  }, [modelId]);

  useEffect(() => {
    fetchAccuracy();
  }, [fetchAccuracy]);

  return { accuracyList, loading, error, refetch: fetchAccuracy };
}

export function useLiveForecastStream(onUpdate?: (data: any) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/analytics/forecast/live`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (onUpdate) onUpdate(payload);
      } catch {}
    };

    socket.onclose = () => {
      setConnected(false);
    };

    wsRef.current = socket;

    return () => {
      socket.close();
    };
  }, [onUpdate]);

  return { connected };
}

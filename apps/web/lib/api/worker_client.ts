// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_worker_client"
// purpose: "API Client and Hooks for Worker Pool Orchestration (DNK-PLATFORM-SCALE-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect, useCallback } from 'react';

export interface WorkerPool {
  id: string;
  workspace_id: string;
  name: string;
  min_workers: number;
  max_workers: number;
  target_queue_depth: number;
  scale_up_threshold: number;
  scale_down_idle_seconds: number;
  active_workers?: number;
}

export interface QueueMetrics {
  queue_id: string;
  queue_depth: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  saturation_pct: number;
  active_workers: number;
  max_workers: number;
  throughput_tps: number;
  timestamp: string;
}

export interface DLQEntry {
  id: string;
  original_task_id: string;
  queue_id?: string;
  error_message: string;
  retry_count: number;
  max_retries: number;
  status: string;
}

export function useWorkerPools(workspaceId?: string) {
  const [pools, setPools] = useState<WorkerPool[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPools = useCallback(async () => {
    setLoading(true);
    try {
      const url = workspaceId
        ? `/api/v1/worker/pools?workspace_id=${workspaceId}`
        : '/api/v1/worker/pools';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch worker pools');
      const data = await res.json();
      setPools(data.pools || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error fetching worker pools');
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    fetchPools();
  }, [fetchPools]);

  const scalePool = async (poolId: string, targetWorkers: number) => {
    const res = await fetch(`/api/v1/worker/pools/${poolId}/workers/scale`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_workers: targetWorkers }),
    });
    if (!res.ok) throw new Error('Failed to scale worker pool');
    await fetchPools();
  };

  return { pools, loading, error, refetch: fetchPools, scalePool };
}

export function useQueueMetrics(queueId: string) {
  const [metrics, setMetrics] = useState<QueueMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/worker/queues/${queueId}/metrics`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch {
      // Ignore network errors in demo/mock mode
    } finally {
      setLoading(false);
    }
  }, [queueId]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 3000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return { metrics, loading, refetch: fetchMetrics };
}

"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/useAgentMetrics.ts"
// purpose: "TanStack React Query hook for agent metrics telemetry"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/api";

export interface AgentMetricsData {
  timestamp?: string;
  asr_rate?: number;
  p95_latency_ms?: number;
  error_rate?: number;
  req_per_sec?: number;
  timeline?: Array<{
    timestamp: string;
    asr_rate: number;
    blocked_probes?: number;
  }>;
}

export function useAgentMetrics() {
  return useQuery<AgentMetricsData, Error>({
    queryKey: ["agentMetrics"],
    queryFn: () => apiClient<AgentMetricsData>("/api/v1/agents/metrics"),
    refetchInterval: 5000,
    staleTime: 10000,
    retry: 3,
  });
}

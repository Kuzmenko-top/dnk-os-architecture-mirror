"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/useAgents.ts"
// purpose: "TanStack React Query hook for fetching agent list telemetry"
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

export interface AgentItem {
  id: string;
  name: string;
  model: string;
  status: string;
  latency_p95: number;
  asr: number;
}

export function useAgents() {
  return useQuery<AgentItem[], Error>({
    queryKey: ["agentsList"],
    queryFn: () => apiClient<AgentItem[]>("/api/v1/agents"),
    staleTime: 10000,
    retry: 2,
  });
}

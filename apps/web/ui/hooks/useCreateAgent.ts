"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/useCreateAgent.ts"
// purpose: "TanStack React Query mutation hook for agent provisioning"
// canonical_source: true
// alters_files: []
// triggers_tasks: ["DNK-UI-GEN-003"]
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api";

export interface CreateAgentPayload {
  name: string;
  model: string;
  api_key: string;
  status: boolean;
}

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateAgentPayload) =>
      apiClient("/api/v1/agents", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agentsList"] });
    },
  });
}

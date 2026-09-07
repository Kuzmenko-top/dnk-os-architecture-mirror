"use client";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/ui/hooks/useA2AMonitor.ts"
// purpose: "Custom React hooks for querying A2A Agent state, Locks, and Mesh Topics via SWR"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../lib/api";

export interface A2ATopic {
  name: string;
  subscribers_count: number;
}

export interface ActiveLock {
  resource: string;
  owner: string;
  ttl_remaining: number;
  acquired_at: string;
}

export interface ConsensusProposal {
  proposal_id: string;
  proposer: string;
  topic: string;
  description: string;
  mechanism: string;
  threshold: number;
  status: "pending" | "accepted" | "rejected" | "expired";
  votes: Record<string, string>;
  created_at: string;
  resolved_at?: string;
}

export interface SwarmAgentItem {
  name: string;
  role: string;
  capabilities: string[];
  consensus_weight: number;
  status: string;
  mailbox_size: number;
}

export function useA2AAgents() {
  return useQuery<{ count: number; agents: SwarmAgentItem[] }, Error>({
    queryKey: ["a2a", "agents"],
    queryFn: () => apiClient.get<{ count: number; agents: SwarmAgentItem[] }>("/a2a/agents"),
    refetchInterval: 5000,
  });
}

export function useA2ATopics() {
  return useQuery<{ count: number; topics: string[] }, Error>({
    queryKey: ["a2a", "topics"],
    queryFn: () => apiClient.get<{ count: number; topics: string[] }>("/a2a/topics"),
    refetchInterval: 5000,
  });
}

export function useActiveLocks() {
  return useQuery<{ count: number; locks: ActiveLock[] }, Error>({
    queryKey: ["a2a", "locks"],
    queryFn: () => apiClient.get<{ count: number; locks: ActiveLock[] }>("/a2a/locks"),
    refetchInterval: 3000,
  });
}

export function useConsensusStatus(proposalId: string) {
  return useQuery<{ proposal: ConsensusProposal }, Error>({
    queryKey: ["a2a", "consensus", proposalId],
    queryFn: () => apiClient.get<{ proposal: ConsensusProposal }>(`/a2a/consensus/${proposalId}`),
    enabled: Boolean(proposalId),
    refetchInterval: 2000,
  });
}

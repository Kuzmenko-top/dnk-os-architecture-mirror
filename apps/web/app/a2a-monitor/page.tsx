"use client";

export const dynamic = "force-dynamic";
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/app/a2a-monitor/page.tsx"
// purpose: "A2A Multi-Agent Protocol & Swarm Runtime Monitoring Dashboard"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// author: "DNK-e.com Maksym & Gerych Builder"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { useA2AAgents, useA2ATopics, useActiveLocks } from "../../ui/hooks";
import { Card, CardHeader, CardTitle, CardContent } from "../../ui/components/ui/Card";
import { Table } from "../../ui/components/ui/Table";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function A2AMonitorContent() {
  const { data: agentsData, isLoading: agentsLoading } = useA2AAgents();
  const { data: topicsData, isLoading: topicsLoading } = useA2ATopics();
  const { data: locksData, isLoading: locksLoading } = useActiveLocks();

  const agentColumns = [
    { header: "Agent Name", accessorKey: "name" },
    { header: "Role", accessorKey: "role" },
    { header: "Consensus Weight", accessorKey: "consensus_weight" },
    { header: "Status", accessorKey: "status" },
    { header: "Mailbox Size", accessorKey: "mailbox_size" },
  ];

  const lockColumns = [
    { header: "Resource ID", accessorKey: "resource" },
    { header: "Owner Agent", accessorKey: "owner" },
    { header: "TTL Remaining (s)", accessorKey: "ttl_remaining" },
  ];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            A2A Multi-Agent Swarm Monitor
          </h1>
          <p className="text-sm text-slate-400">
            Real-time topology, topics, locks, and consensus tracking across 14 Swarm Agents
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Active Swarm Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-400">
              {agentsLoading ? "..." : agentsData?.count ?? 0}
            </div>
            <p className="text-xs text-slate-400">Registered across Swarm Runtime</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active PubSub Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-sky-400">
              {topicsLoading ? "..." : topicsData?.count ?? 0}
            </div>
            <p className="text-xs text-slate-400">Event distribution channels</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Distributed Resource Locks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-400">
              {locksLoading ? "..." : locksData?.count ?? 0}
            </div>
            <p className="text-xs text-slate-400">Active mutex resource locks</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>14 Canonical Swarm Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              data={(agentsData?.agents ?? []) as any}
              columns={agentColumns}
              isLoading={agentsLoading}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Distributed Locks</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              data={(locksData?.locks ?? []) as any}
              columns={lockColumns}
              isLoading={locksLoading}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function A2AMonitorDashboard() {
  return (
    <QueryClientProvider client={queryClient}>
      <A2AMonitorContent />
    </QueryClientProvider>
  );
}

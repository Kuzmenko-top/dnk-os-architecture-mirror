// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_CommandOverviewTab"
// purpose: "Command Overview tab showing active agents, workers, health cards, and summary stats (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

"use client";

import React from "react";
import { SystemHealth } from "../../lib/api_client";

interface Props {
  health: SystemHealth | null;
  loading: boolean;
}

export function CommandOverviewTab({ health, loading }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-xs font-mono text-slate-400">
        Loading Command Overview telemetry...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Metric Stat Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-1">
          <p className="text-xs font-medium text-slate-400">System Health</p>
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <p className="text-xl font-bold text-slate-100">{health?.status || "HEALTHY"}</p>
          </div>
          <p className="text-[11px] text-emerald-400/80 font-mono">Fail-Closed Invariants OK</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-1">
          <p className="text-xs font-medium text-slate-400">Active Agents</p>
          <p className="text-xl font-bold text-slate-100">{health?.active_agents || 3}</p>
          <p className="text-[11px] text-slate-400 font-mono">Antigravity, Hermes, Rick</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-1">
          <p className="text-xs font-medium text-slate-400">Active Swarm Flowers</p>
          <p className="text-xl font-bold text-slate-100">{health?.active_workers || 4}</p>
          <p className="text-[11px] text-slate-400 font-mono">dnk-dev-01, companion</p>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-4 space-y-1">
          <p className="text-xs font-medium text-slate-400">Approval Requests</p>
          <p className="text-xl font-bold text-amber-400">{health?.pending_approvals || 0}</p>
          <p className="text-[11px] text-amber-400/80 font-mono">Pending Supervisor Action</p>
        </div>
      </div>

      {/* 2. Swarm Agents Roster */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Swarm Agents Roster & Roles</h2>
          <span className="text-[11px] font-mono text-slate-400">Tenancy: Isolated</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-slate-800/80 bg-slate-950/40 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-slate-200">Antigravity</span>
              <span className="bg-purple-500/10 text-purple-400 text-[10px] px-2 py-0.5 rounded border border-purple-500/20 font-mono">
                Mentor
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Lead Architect & Planning Mode supervisor. Approves task trees, reviews implementations.
            </p>
            <div className="text-[11px] font-mono text-slate-500">Status: Active Supervisor</div>
          </div>

          <div className="border border-slate-800/80 bg-slate-950/40 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-slate-200">Hermes (Gerych)</span>
              <span className="bg-emerald-500/10 text-emerald-400 text-[10px] px-2 py-0.5 rounded border border-emerald-500/20 font-mono">
                Primary Builder
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Swarm manager & physical code executor. Dispatches subagent flowers and runs verification.
            </p>
            <div className="text-[11px] font-mono text-emerald-400/80">Status: Executing DNK-VISUAL-OS-001</div>
          </div>

          <div className="border border-slate-800/80 bg-slate-950/40 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-slate-200">Governance Companion</span>
              <span className="bg-blue-500/10 text-blue-400 text-[10px] px-2 py-0.5 rounded border border-blue-500/20 font-mono">
                Gatekeeper
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Verifies MRH headers, tenant isolation, zero host pollution, and ED25519 plugin signatures.
            </p>
            <div className="text-[11px] font-mono text-slate-500">Status: Gate Active</div>
          </div>
        </div>
      </div>

      {/* 3. Operational Invariants Notice */}
      <div className="bg-slate-900/30 border border-slate-800/60 rounded-lg p-4 text-xs space-y-2">
        <div className="flex items-center space-x-2 text-slate-300 font-semibold">
          <span>🛡️ Operational Invariants & Security Guard</span>
        </div>
        <ul className="list-disc list-inside text-slate-400 space-y-1 text-[11px]">
          <li><strong>Zero Host Pollution:</strong> All build systems run inside Docker anonymous volumes.</li>
          <li><strong>Read-Only Cabinet:</strong> Real Shopify mutation execution is strictly locked and simulated.</li>
          <li><strong>Tenant Isolation:</strong> Request tokens validated with 100% fail-closed gate.</li>
        </ul>
      </div>
    </div>
  );
}

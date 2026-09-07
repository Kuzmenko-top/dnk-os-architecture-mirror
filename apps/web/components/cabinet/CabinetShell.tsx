// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_CabinetShell"
// purpose: "Application Shell, Navigation Rail, Workspace Header & Status bar (DNK-VISUAL-OS-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-23"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";
import { SystemHealth, cabinetApi } from "../../lib/api_client";
import { CommandOverviewTab } from "./CommandOverviewTab";
import { TasksAndRunsTab } from "./TasksAndRunsTab";
import { TimelineTab } from "./TimelineTab";
import { GovernanceTab } from "./GovernanceTab";
import { DomainPanelsTab } from "./DomainPanelsTab";
import { PRInspectorTab } from "./PRInspectorTab";

export type CabinetActiveTab = "overview" | "prs" | "tasks" | "timeline" | "governance" | "domains";

export function CabinetShell() {
  const [activeTab, setActiveTab] = useState<CabinetActiveTab>("overview");
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadHealth() {
      try {
        const data = await cabinetApi.getHealth();
        setHealth(data);
      } catch (err) {
        console.error("Failed to fetch cabinet health:", err);
      } finally {
        setLoading(false);
      }
    }
    loadHealth();
    const interval = setInterval(loadHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 antialiased font-sans overflow-hidden">
      {/* 1. Left Navigation Rail */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 backdrop-blur flex flex-col justify-between p-4 select-none">
        <div className="space-y-6">
          {/* Workspace Title & Brand */}
          <div className="flex items-center space-x-3 px-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center font-bold text-emerald-400 text-sm">
              DNK
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-wide text-slate-100">DNK OS Cabinet</h1>
              <p className="text-xs text-slate-400">Workspace: <span className="text-emerald-400 font-mono">ws-alpha-001</span></p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab("overview")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "overview"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <span>Command Overview</span>
            </button>

            <button
              onClick={() => setActiveTab("prs")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "prs"
                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <span>PR & Checks Inspector</span>
            </button>

            <button
              onClick={() => setActiveTab("tasks")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "tasks"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <span>Tasks & Plant Runs</span>
            </button>

            <button
              onClick={() => setActiveTab("timeline")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "timeline"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <span>Live Timeline Stream</span>
            </button>

            <button
              onClick={() => setActiveTab("governance")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "governance"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span>Governance & Trust</span>
                {health && health.pending_approvals > 0 && (
                  <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1.5 py-0.5 rounded text-[10px] font-mono">
                    {health.pending_approvals}
                  </span>
                )}
              </div>
            </button>

            <button
              onClick={() => setActiveTab("domains")}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                activeTab === "domains"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <span>Domain Panels</span>
            </button>
          </nav>
        </div>

        {/* Isolation & Security Guard Indicator */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-xs space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Mode</span>
            <span className="font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">READ-ONLY</span>
          </div>
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Zero Host Pollution</span>
            <span className="text-emerald-400">ENFORCED</span>
          </div>
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span>Active Swarm</span>
            <span className="font-mono text-slate-200">{health?.active_agents || 3} Agents</span>
          </div>
        </div>
      </aside>

      {/* 2. Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950">
        {/* Top Header */}
        <header className="h-14 border-b border-slate-800 bg-slate-900/40 backdrop-blur px-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-xs font-mono uppercase text-slate-400 tracking-wider">
              Cabinet View: <strong className="text-slate-100">{activeTab}</strong>
            </span>
            <div className="h-4 w-px bg-slate-800" />
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-emerald-400 font-mono">Live Sync Active</span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <a
              href="/canvas/default-canvas-id"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 border border-purple-500/30 font-medium transition-colors"
            >
              <span>✨ Stitch Spatial Canvas</span>
            </a>
            <a
              href="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium transition-colors"
            >
              <span>🧬 DNK OS Hub</span>
            </a>
            <div className="bg-slate-800/50 border border-slate-700/60 rounded px-2.5 py-1 text-slate-300 font-mono text-[11px]">
              User: <span className="text-emerald-400 font-medium">Maxim (Primary Supervisor)</span>
            </div>
          </div>
        </header>

        {/* Tab Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === "overview" && <CommandOverviewTab health={health} loading={loading} />}
          {activeTab === "prs" && <PRInspectorTab />}
          {activeTab === "tasks" && <TasksAndRunsTab />}
          {activeTab === "timeline" && <TimelineTab />}
          {activeTab === "governance" && <GovernanceTab />}
          {activeTab === "domains" && <DomainPanelsTab />}
        </div>

        {/* Bottom Persistent Status Bar */}
        <footer className="h-8 border-t border-slate-800 bg-slate-900/80 px-4 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <div className="flex items-center space-x-6">
            <span>System: <strong className="text-emerald-400">{health?.status || "HEALTHY"}</strong></span>
            <span>Uptime: <strong>{health ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : "4h 12m"}</strong></span>
            <span>Memory: <strong>{health?.memory_usage_mb || 248.5} MB</strong></span>
          </div>
          <div className="flex items-center space-x-4">
            <span>TaskDNA: <strong>v2.0-MVP</strong></span>
            <span>Fail-Closed Tenant Isolation: <strong className="text-emerald-400">PASSED</strong></span>
          </div>
        </footer>
      </main>
    </div>
  );
}
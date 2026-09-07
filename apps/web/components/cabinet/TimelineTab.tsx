// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_cabinet_TimelineTab"
// purpose: "Live Event Timeline stream view for system, adapters & swarm audit events (DNK-UX-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.1.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Filter,
  RefreshCw,
  GitBranch,
  ShoppingBag,
  Cpu,
  Shield,
  Database
} from "lucide-react";
import { cabinetApi, TimelineEnvelope } from "../../lib/api_client";

export function TimelineTab() {
  const [selectedSource, setSelectedSource] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [timelineData, setTimelineData] = useState<TimelineEnvelope>({
    data: [],
    total_count: 0,
    data_source: "live",
    stale: false,
    fetched_at: "",
    expires_at: ""
  });
  const [loading, setLoading] = useState<boolean>(true);

  const loadTimeline = async () => {
    try {
      const res = await cabinetApi.getTimelineStream(selectedSource, selectedCategory);
      if (res && res.data) {
        setTimelineData(res);
      }
    } catch (err) {
      console.error("Failed to fetch timeline:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
    const interval = setInterval(loadTimeline, 5000);
    return () => clearInterval(interval);
  }, [selectedSource, selectedCategory]);

  const sources = [
    { id: "all", label: "All Sources", icon: Activity },
    { id: "github", label: "GitHub", icon: GitBranch },
    { id: "shopify", label: "Shopify", icon: ShoppingBag },
    { id: "system", label: "System", icon: Cpu },
    { id: "swarm", label: "Swarm", icon: Shield }
  ];

  const categories = [
    { id: "all", label: "All Categories" },
    { id: "adapter", label: "Adapters" },
    { id: "quality_gate", label: "Quality Gate" },
    { id: "governance", label: "Governance" },
    { id: "security", label: "Security" }
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-5">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">Live Audit & Event Stream</h2>
            <p className="text-xs text-slate-400">
              Real-time telemetry & events from GitHub, Shopify Adapters, Swarm & Security Gate
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">Source:</span>
            <span className="font-semibold uppercase text-emerald-400 font-mono">
              {timelineData.data_source}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-mono font-semibold text-emerald-400">Connected</span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
        {/* Source Pills */}
        <div className="flex flex-wrap gap-1.5">
          {sources.map((src) => {
            const Icon = src.icon;
            const isActive = selectedSource === src.id;
            return (
              <button
                key={src.id}
                onClick={() => setSelectedSource(src.id)}
                className={`flex items-center space-x-1.5 text-xs font-medium px-2.5 py-1 rounded-md transition ${
                  isActive
                    ? "bg-blue-600 text-white font-semibold shadow-sm"
                    : "bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{src.label}</span>
              </button>
            );
          })}
        </div>

        {/* Category Dropdown */}
        <div className="flex items-center space-x-2 self-end sm:self-auto">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs bg-slate-900 text-slate-300 border border-slate-800 rounded-md px-2.5 py-1 focus:outline-none focus:border-blue-500 font-mono"
          >
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.label}
              </option>
            ))}
          </select>

          <button
            onClick={loadTimeline}
            disabled={loading}
            className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-md border border-slate-800"
            title="Refresh stream"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Stream List */}
      {loading && timelineData.data.length === 0 ? (
        <div className="flex items-center justify-center h-48 text-xs font-mono text-slate-400 space-x-2">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
          <span>Loading Event Timeline...</span>
        </div>
      ) : timelineData.data.length === 0 ? (
        <div className="p-8 text-center bg-slate-950/60 border border-slate-800/80 rounded-lg text-slate-400 text-xs font-mono">
          No events match the selected filter criteria.
        </div>
      ) : (
        <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
          {timelineData.data.map((evt) => (
            <div
              key={evt.id}
              className="flex items-start space-x-3 p-3.5 rounded-lg border border-slate-800/80 bg-slate-950/60 text-xs hover:border-slate-700/80 transition"
            >
              <div className="pt-0.5">
                <span
                  className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                    evt.level === "SECURITY"
                      ? "bg-purple-500/20 text-purple-400 border border-purple-500/40"
                      : evt.level === "ERROR"
                      ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                      : evt.level === "WARNING"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                      : evt.level === "SUCCESS"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                      : "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                  }`}
                >
                  {evt.level}
                </span>
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-mono">
                    <span className="font-bold text-slate-200 uppercase text-[11px]">
                      [{evt.source}]
                    </span>
                    <span className="text-[10px] text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                      {evt.category}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <h4 className="font-semibold text-slate-200">{evt.title || evt.summary}</h4>
                {evt.summary && evt.title && (
                  <p className="text-slate-400 text-[11px] leading-relaxed">{evt.summary}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

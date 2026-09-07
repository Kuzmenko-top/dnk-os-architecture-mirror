// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_platform_multi_region_dashboard"
// purpose: "Main Dashboard Component for Multi-Region Deployment, GSLB, Edge Routing & Telemetry (DNK-PLATFORM-SCALE-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useEffect, useState } from "react";
import {
  RegionConfig,
  GSLBConfig,
  EdgeRoutingRule,
  ReplicationStatusStream,
  fetchRegions,
  fetchGSLBConfig,
  fetchEdgeRoutingRules,
  fetchReplicationStatus,
} from "../../lib/api/platform_regions_client";
import { GSLBConfigCard } from "./GSLBConfigCard";
import { EdgeRoutingRulesTable } from "./EdgeRoutingRulesTable";
import { RegionHealthMonitor } from "./RegionHealthMonitor";

export const MultiRegionDashboard: React.FC = () => {
  const [regions, setRegions] = useState<RegionConfig[]>([]);
  const [gslbConfig, setGslbConfig] = useState<GSLBConfig | null>(null);
  const [edgeRules, setEdgeRules] = useState<EdgeRoutingRule[]>([]);
  const [streams, setStreams] = useState<ReplicationStatusStream[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [regData, gslbData, edgeData, streamData] = await Promise.all([
          fetchRegions(),
          fetchGSLBConfig(),
          fetchEdgeRoutingRules(),
          fetchReplicationStatus(),
        ]);
        setRegions(regData);
        setGslbConfig(gslbData);
        setEdgeRules(edgeData);
        setStreams(streamData);
      } catch (e) {
        console.error("Failed to load multi-region telemetry", e);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="p-8 text-center text-slate-400 bg-slate-950 min-h-screen">
        Loading Multi-Region Platform Control Plane...
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-950 min-h-screen text-slate-100">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">🌐 Multi-Region Platform & Edge Routing Control Plane</h1>
          <p className="text-sm text-slate-400">
            AWS + GCP Multi-Region EKS/GKE | Edge Routing | GSLB Failover | PostgreSQL Replication
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-emerald-400 font-mono font-medium">SYSTEM HEALTH: 100% OPERATIONAL</span>
        </div>
      </div>

      <GSLBConfigCard config={gslbConfig} onUpdate={(updated) => setGslbConfig(updated)} />
      <RegionHealthMonitor regions={regions} streams={streams} />
      <EdgeRoutingRulesTable rules={edgeRules} />
    </div>
  );
};

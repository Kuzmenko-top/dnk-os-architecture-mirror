// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_lib_api_platform_regions_client"
// purpose: "API Client for Multi-Region Deployment, GSLB Config, Edge Routing & Replication (DNK-PLATFORM-SCALE-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import { useState, useEffect } from "react";

export interface RegionConfig {
  id: string;
  region_name: string;
  cloud_provider: string;
  is_primary: boolean;
  is_active: boolean;
  health_check_endpoint: string;
  failover_priority: number;
}

export interface GSLBConfig {
  dns_provider: string;
  routing_policy: string;
  health_check_interval_seconds: number;
  failover_threshold: number;
  ttl_seconds: number;
}

export interface EdgeRoutingRule {
  id: string;
  rule_name: string;
  geo_match_type: string;
  geo_values: string[];
  target_region: string;
  priority: number;
  enabled: boolean;
}

export interface ReplicationStatusStream {
  id: string;
  source_region: string;
  target_region: string;
  replication_type: string;
  lag_seconds: number;
  status: "healthy" | "lagging" | "broken";
}

const API_BASE = "/api/v1/platform";

export async function fetchRegions(): Promise<RegionConfig[]> {
  const res = await fetch(`${API_BASE}/regions`);
  if (!res.ok) throw new Error("Failed to fetch regions");
  const json = await res.json();
  return json.regions || [];
}

export async function fetchGSLBConfig(): Promise<GSLBConfig> {
  const res = await fetch(`${API_BASE}/gslb/config`);
  if (!res.ok) throw new Error("Failed to fetch GSLB config");
  const json = await res.json();
  return json.config;
}

export async function updateGSLBConfig(updates: Partial<GSLBConfig>): Promise<GSLBConfig> {
  const res = await fetch(`${API_BASE}/gslb/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update GSLB config");
  const json = await res.json();
  return json.config;
}

export async function fetchEdgeRoutingRules(): Promise<EdgeRoutingRule[]> {
  const res = await fetch(`${API_BASE}/edge-routing/rules`);
  if (!res.ok) throw new Error("Failed to fetch edge routing rules");
  const json = await res.json();
  return json.rules || [];
}

export async function fetchReplicationStatus(): Promise<ReplicationStatusStream[]> {
  const res = await fetch(`${API_BASE}/replication/status`);
  if (!res.ok) throw new Error("Failed to fetch replication status");
  const json = await res.json();
  return json.streams || [];
}

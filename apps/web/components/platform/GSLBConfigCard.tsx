// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_platform_gslb_config_card"
// purpose: "React Component for Managing Global Load Balancer Configuration (DNK-PLATFORM-SCALE-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from "react";
import { GSLBConfig, updateGSLBConfig } from "../../lib/api/platform_regions_client";

interface Props {
  config: GSLBConfig | null;
  onUpdate: (updated: GSLBConfig) => void;
}

export const GSLBConfigCard: React.FC<Props> = ({ config, onUpdate }) => {
  const [dnsProvider, setDnsProvider] = useState(config?.dns_provider || "route53");
  const [routingPolicy, setRoutingPolicy] = useState(config?.routing_policy || "latency");
  const [ttl, setTtl] = useState(config?.ttl_seconds || 60);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await updateGSLBConfig({
        dns_provider: dnsProvider,
        routing_policy: routingPolicy,
        ttl_seconds: ttl,
      });
      onUpdate(updated);
    } catch (e) {
      console.error("GSLB update failed", e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 shadow-sm">
      <h3 className="text-lg font-semibold mb-4 text-emerald-400">🌐 Global Load Balancer (GSLB)</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">DNS Provider</label>
          <select
            value={dnsProvider}
            onChange={(e) => setDnsProvider(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200"
          >
            <option value="route53">AWS Route53</option>
            <option value="cloud_dns">GCP Cloud DNS</option>
            <option value="cloudflare">CloudFlare DNS</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Routing Policy</label>
          <select
            value={routingPolicy}
            onChange={(e) => setRoutingPolicy(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200"
          >
            <option value="latency">Latency-based (P95)</option>
            <option value="geolocation">Geolocation Matching</option>
            <option value="weighted">Weighted Round-Robin</option>
            <option value="failover">Active-Passive Failover</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">TTL (seconds)</label>
          <input
            type="number"
            value={ttl}
            onChange={(e) => setTtl(Number(e.target.value))}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200"
          />
        </div>
      </div>
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm font-medium transition-colors"
      >
        {isSaving ? "Saving..." : "Save GSLB Config"}
      </button>
    </div>
  );
};

// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_platform_region_health_monitor"
// purpose: "React Component for Real-Time Multi-Region Liveness & Cross-Region Replication Status (DNK-PLATFORM-SCALE-003)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from "react";
import { RegionConfig, ReplicationStatusStream } from "../../lib/api/platform_regions_client";

interface Props {
  regions: RegionConfig[];
  streams: ReplicationStatusStream[];
}

export const RegionHealthMonitor: React.FC<Props> = ({ regions, streams }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
      {/* Regions Status Card */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 shadow-sm">
        <h3 className="text-lg font-semibold mb-3 text-indigo-400">🌍 Active Regions (Multi-Cloud EKS/GKE)</h3>
        <div className="space-y-3">
          {regions.map((reg) => (
            <div
              key={reg.id}
              className="flex items-center justify-between p-3 bg-slate-800/60 rounded border border-slate-700/50"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-slate-200">{reg.region_name}</span>
                  <span className="text-xs uppercase px-1.5 py-0.5 bg-slate-700 text-slate-300 rounded font-mono">
                    {reg.cloud_provider}
                  </span>
                  {reg.is_primary && (
                    <span className="text-xs px-1.5 py-0.5 bg-amber-950 text-amber-300 border border-amber-800 rounded">
                      PRIMARY
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-400 truncate max-w-xs">{reg.health_check_endpoint}</div>
              </div>
              <div className="text-right">
                {reg.is_active ? (
                  <span className="text-xs font-semibold text-emerald-400 bg-emerald-950 px-2 py-1 rounded border border-emerald-800">
                    ONLINE
                  </span>
                ) : (
                  <span className="text-xs font-semibold text-rose-400 bg-rose-950 px-2 py-1 rounded border border-rose-800">
                    OFFLINE
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Replication Status Card */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 shadow-sm">
        <h3 className="text-lg font-semibold mb-3 text-purple-400">🔄 Cross-Region Database Replication</h3>
        <div className="space-y-3">
          {streams.map((stream) => (
            <div
              key={stream.id}
              className="flex items-center justify-between p-3 bg-slate-800/60 rounded border border-slate-700/50"
            >
              <div>
                <div className="font-mono text-xs text-slate-300">
                  {stream.source_region} ➔ {stream.target_region}
                </div>
                <div className="text-xs text-slate-400">
                  Type: <span className="font-mono text-slate-300">{stream.replication_type}</span> | Lag:{" "}
                  <span className="font-mono text-amber-300">{stream.lag_seconds}s</span>
                </div>
              </div>
              <div>
                {stream.status === "healthy" ? (
                  <span className="text-xs font-semibold text-emerald-400 bg-emerald-950 px-2 py-1 rounded border border-emerald-800">
                    HEALTHY
                  </span>
                ) : stream.status === "lagging" ? (
                  <span className="text-xs font-semibold text-amber-400 bg-amber-950 px-2 py-1 rounded border border-amber-800">
                    LAGGING
                  </span>
                ) : (
                  <span className="text-xs font-semibold text-rose-400 bg-rose-950 px-2 py-1 rounded border border-rose-800">
                    BROKEN
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

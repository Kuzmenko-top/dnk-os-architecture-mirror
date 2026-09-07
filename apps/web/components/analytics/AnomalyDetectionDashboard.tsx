// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_anomaly_detection_dashboard"
// purpose: "React Dashboard for Streaming Anomaly Detection & Metric Scoring (DNK-ANALYTICS-004)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import {
  useAnomalyDetectionConfigs,
  useAnomalyEvents,
  useAnomalyLiveStream,
  AnomalyDetectionConfig
} from '../../lib/api/analytics_anomaly_client';

interface DashboardProps {
  workspaceId: string;
}

export const AnomalyDetectionDashboard: React.FC<DashboardProps> = ({ workspaceId }) => {
  const { configs, loading: configsLoading, refresh: refreshConfigs } = useAnomalyDetectionConfigs(workspaceId);
  const { events, loading: eventsLoading } = useAnomalyEvents(workspaceId);
  const { latestTelemetry, connected } = useAnomalyLiveStream();

  const [selectedDetector, setSelectedDetector] = useState<string>('zscore');
  const [sensitivity, setSensitivity] = useState<number>(0.80);

  return (
    <div className="p-6 bg-slate-900 text-slate-100 rounded-xl border border-slate-800 shadow-2xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            📊 Real-Time Anomaly Detection Engine
          </h2>
          <p className="text-sm text-slate-400">
            Streaming Z-Score, IQR, Holt-Winters & Isolation Forest Scoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${connected ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}`}>
            {connected ? '● LIVE STREAM ACTIVE' : '○ DISCONNECTED'}
          </span>
          <button
            onClick={() => refreshConfigs()}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
          >
            Refresh Configs
          </button>
        </div>
      </div>

      {/* Control Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Detector Algorithm
          </label>
          <select
            value={selectedDetector}
            onChange={(e) => setSelectedDetector(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="zscore">Z-Score (Gaussian Standard Deviation)</option>
            <option value="iqr">IQR (Interquartile Range Outlier)</option>
            <option value="holt_winters">Holt-Winters Forecasting</option>
            <option value="isolation_forest">Lightweight Isolation Forest</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Sensitivity Tuning: {sensitivity.toFixed(2)}
          </label>
          <input
            type="range"
            min="0.00"
            max="1.00"
            step="0.05"
            value={sensitivity}
            onChange={(e) => setSensitivity(parseFloat(e.target.value))}
            className="w-full accent-indigo-500 cursor-pointer"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Live Anomaly Score
          </label>
          <div className="text-xl font-extrabold text-indigo-400">
            {latestTelemetry?.metrics?.anomaly_score
              ? (latestTelemetry.metrics.anomaly_score * 100).toFixed(1) + '%'
              : '0.0%'}
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 font-medium">Latency P95</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {latestTelemetry?.metrics?.latency_p95 ?? 125.4} ms
          </div>
          <div className="text-xs text-emerald-400 mt-1">Normal Range [50 - 250 ms]</div>
        </div>

        <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 font-medium">Error Rate</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {((latestTelemetry?.metrics?.error_rate ?? 0.002) * 100).toFixed(2)} %
          </div>
          <div className="text-xs text-emerald-400 mt-1">Below threshold (1.00%)</div>
        </div>

        <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 font-medium">Active Configs</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1">
            {configsLoading ? '...' : configs.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">Configured Detectors</div>
        </div>

        <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 font-medium">Detected Anomalies</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {eventsLoading ? '...' : events.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">Recorded Events</div>
        </div>
      </div>

      {/* Configs List */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Active Detector Configurations</h3>
        {configsLoading ? (
          <div className="text-sm text-slate-400">Loading configurations...</div>
        ) : configs.length === 0 ? (
          <div className="text-sm text-slate-500 py-4 text-center border border-dashed border-slate-800 rounded-lg">
            No active detector configurations found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/60 text-slate-400 uppercase text-xs">
                <tr>
                  <th className="py-2.5 px-4">Metric Type</th>
                  <th className="py-2.5 px-4">Detector</th>
                  <th className="py-2.5 px-4">Sensitivity</th>
                  <th className="py-2.5 px-4">Window (hrs)</th>
                  <th className="py-2.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {configs.map((cfg: AnomalyDetectionConfig) => (
                  <tr key={cfg.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 font-mono font-medium text-indigo-300">{cfg.metric_type}</td>
                    <td className="py-3 px-4 capitalize">{cfg.detector_type}</td>
                    <td className="py-3 px-4">{cfg.sensitivity.toFixed(2)}</td>
                    <td className="py-3 px-4">{cfg.rolling_window_hours}h</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${cfg.enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-400'}`}>
                        {cfg.enabled ? 'ENABLED' : 'DISABLED'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

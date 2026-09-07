// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_alert_rules_config_card"
// purpose: "React Component for Managing Composite Advanced Alert Rules (DNK-ANALYTICS-004)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';
import { useAdvancedAlertRules, AdvancedAlertRule } from '../../lib/api/analytics_anomaly_client';

interface AlertRulesConfigCardProps {
  workspaceId: string;
}

export const AlertRulesConfigCard: React.FC<AlertRulesConfigCardProps> = ({ workspaceId }) => {
  const { rules, loading, refresh } = useAdvancedAlertRules(workspaceId);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'warning':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      default:
        return 'bg-sky-500/20 text-sky-300 border-sky-500/30';
    }
  };

  return (
    <div className="p-6 bg-slate-900 text-slate-100 rounded-xl border border-slate-800 shadow-xl">
      <div className="flex justify-between items-center mb-5">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            ⚙️ Advanced Composite Alert Rules
          </h3>
          <p className="text-xs text-slate-400">
            Multi-metric AND/OR rule evaluation & cooldown deduplication
          </p>
        </div>
        <button
          onClick={() => refresh()}
          className="px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition font-medium"
        >
          Refresh Rules
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-slate-400 py-4">Loading rules...</div>
      ) : rules.length === 0 ? (
        <div className="text-sm text-slate-500 py-6 text-center border border-dashed border-slate-800 rounded-lg">
          No composite alert rules defined for this workspace.
        </div>
      ) : (
        <div className="space-y-4">
          {rules.map((rule: AdvancedAlertRule) => (
            <div
              key={rule.id}
              className="p-4 bg-slate-800/60 rounded-lg border border-slate-700/60 flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-100 text-base">{rule.rule_name}</span>
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${getSeverityBadge(rule.severity)}`}>
                    {rule.severity.toUpperCase()}
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-400 bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800 max-w-xl truncate">
                  {JSON.stringify(rule.composite_logic)}
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-400">
                <div>
                  Cooldown: <span className="font-mono text-slate-200">{rule.cooldown_seconds}s</span>
                </div>
                <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${rule.enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-400'}`}>
                  {rule.enabled ? 'ACTIVE' : 'MUTED'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

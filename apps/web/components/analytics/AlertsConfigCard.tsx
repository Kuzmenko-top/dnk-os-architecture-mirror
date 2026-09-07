// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_alerts_config_card"
// purpose: "React component for configuring threshold & composite alert rules, viewing audit events, and resolving alerts"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';

export interface AlertRule {
  id: string;
  workspace_id: string;
  name: string;
  metric_type: string;
  operator: string;
  threshold_value: number;
  window_seconds: number;
  severity: 'info' | 'warning' | 'critical';
  enabled: boolean;
  composite_logic?: any;
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  rule_name: string;
  metric_type: string;
  metric_value: number;
  threshold_value: number;
  severity: string;
  triggered_at: string;
  resolved_at?: string | null;
  resolution_note?: string | null;
}

interface AlertsConfigCardProps {
  workspaceId: string;
  rules: AlertRule[];
  events: AlertEvent[];
  onCreateRule?: (rule: Partial<AlertRule>) => Promise<void>;
  onToggleRule?: (ruleId: string, enabled: boolean) => Promise<void>;
  onDeleteRule?: (ruleId: string) => Promise<void>;
  onResolveEvent?: (eventId: string, note: string) => Promise<void>;
}

export const AlertsConfigCard: React.FC<AlertsConfigCardProps> = ({
  workspaceId,
  rules = [],
  events = [],
  onCreateRule,
  onToggleRule,
  onDeleteRule,
  onResolveEvent,
}) => {
  const [name, setName] = useState('');
  const [metricType, setMetricType] = useState('error_rate');
  const [operator, setOperator] = useState('gt');
  const [threshold, setThreshold] = useState<number>(0.05);
  const [severity, setSeverity] = useState<'info' | 'warning' | 'critical'>('warning');
  const [activeTab, setActiveTab] = useState<'rules' | 'events'>('rules');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    if (onCreateRule) {
      await onCreateRule({
        workspace_id: workspaceId,
        name,
        metric_type: metricType,
        operator,
        threshold_value: threshold,
        severity,
        enabled: true,
        window_seconds: 300,
      });
      setName('');
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-amber-500 animate-pulse" />
            Alerting & Audit Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure threshold rules, composite conditions (AND/OR), and track immutable alert events.
          </p>
        </div>
        <div className="flex bg-slate-800 rounded-lg p-1 text-xs">
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              activeTab === 'rules' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Rules ({rules.length})
          </button>
          <button
            onClick={() => setActiveTab('events')}
            className={`px-3 py-1.5 rounded-md font-medium transition ${
              activeTab === 'events' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Triggered Events ({events.filter((e) => !e.resolved_at).length})
          </button>
        </div>
      </div>

      {activeTab === 'rules' ? (
        <div className="space-y-6">
          {/* Create Rule Form */}
          <form onSubmit={handleCreate} className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 space-y-4">
            <div className="text-sm font-semibold text-slate-200">New Alert Rule</div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              <input
                type="text"
                placeholder="Rule Name (e.g., High Error Rate)"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none col-span-2"
                required
              />
              <select
                value={metricType}
                onChange={(e) => setMetricType(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="error_rate">Error Rate (%)</option>
                <option value="latency_p95">Latency p95 (ms)</option>
                <option value="inactivity">Inactivity (s)</option>
                <option value="resource_usage">Resource Usage (%)</option>
              </select>
              <select
                value={operator}
                onChange={(e) => setOperator(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
              >
                <option value="gt">&gt; (Greater than)</option>
                <option value="gte">&gt;= (Greater or eq)</option>
                <option value="lt">&lt; (Less than)</option>
                <option value="lte">&lt;= (Less or eq)</option>
                <option value="eq">== (Equal)</option>
              </select>
              <input
                type="number"
                step="any"
                placeholder="Threshold"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value) || 0)}
                className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs focus:outline-none"
                required
              />
            </div>
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-400">Severity:</span>
                {(['info', 'warning', 'critical'] as const).map((sev) => (
                  <label key={sev} className="flex items-center gap-1 cursor-pointer">
                    <input
                      type="radio"
                      name="severity"
                      value={sev}
                      checked={severity === sev}
                      onChange={() => setSeverity(sev)}
                      className="text-indigo-600 focus:ring-indigo-500"
                    />
                    <span
                      className={`capitalize ${
                        sev === 'critical'
                          ? 'text-rose-400'
                          : sev === 'warning'
                          ? 'text-amber-400'
                          : 'text-sky-400'
                      }`}
                    >
                      {sev}
                    </span>
                  </label>
                ))}
              </div>
              <button
                type="submit"
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow transition"
              >
                + Add Rule
              </button>
            </div>
          </form>

          {/* Rules List */}
          <div className="space-y-2">
            {rules.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs">No alert rules configured yet.</div>
            ) : (
              rules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between p-3.5 bg-slate-950/40 border border-slate-800 rounded-lg hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        rule.severity === 'critical'
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
                          : rule.severity === 'warning'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                          : 'bg-sky-950/80 text-sky-300 border border-sky-800/60'
                      }`}
                    >
                      {rule.severity}
                    </span>
                    <div>
                      <div className="text-xs font-semibold text-white">{rule.name}</div>
                      <div className="text-[11px] text-slate-400">
                        {rule.metric_type} {rule.operator} {rule.threshold_value} (window: {rule.window_seconds}s)
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => onToggleRule && onToggleRule(rule.id, !rule.enabled)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                        rule.enabled
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                    {onDeleteRule && (
                      <button
                        onClick={() => onDeleteRule(rule.id)}
                        className="text-slate-500 hover:text-rose-400 text-xs px-2 py-1 transition"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        /* Events Log */
        <div className="space-y-3">
          {events.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">No alert events recorded.</div>
          ) : (
            events.map((event) => (
              <div
                key={event.id}
                className={`p-3.5 rounded-lg border flex items-center justify-between text-xs ${
                  event.resolved_at
                    ? 'bg-slate-950/30 border-slate-800/60 opacity-60'
                    : 'bg-rose-950/20 border-rose-900/60'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{event.rule_name}</span>
                    <span className="text-[10px] text-slate-400">
                      {new Date(event.triggered_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-300 mt-0.5">
                    Trigger value: <span className="text-rose-300 font-mono">{event.metric_value}</span> (Threshold:{' '}
                    {event.threshold_value})
                  </div>
                  {event.resolved_at && (
                    <div className="text-[10px] text-emerald-400 mt-1">
                      ✓ Resolved: {event.resolution_note || 'Resolved'}
                    </div>
                  )}
                </div>
                {!event.resolved_at && onResolveEvent && (
                  <button
                    onClick={() => onResolveEvent(event.id, 'Resolved via dashboard')}
                    className="px-3 py-1 bg-slate-800 hover:bg-emerald-700 text-slate-200 hover:text-white rounded text-xs font-medium border border-slate-700 transition"
                  >
                    Resolve
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

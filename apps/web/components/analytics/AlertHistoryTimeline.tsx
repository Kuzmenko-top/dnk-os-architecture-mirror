// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_analytics_alert_history_timeline"
// purpose: "React Component for Alert Event History, Multi-Channel Delivery Status & Resolution (DNK-ANALYTICS-004)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState, useEffect } from 'react';
import { AdvancedAlertEvent } from '../../lib/api/analytics_anomaly_client';

interface AlertHistoryTimelineProps {
  workspaceId: string;
}

export const AlertHistoryTimeline: React.FC<AlertHistoryTimelineProps> = ({ workspaceId }) => {
  const [events, setEvents] = useState<AdvancedAlertEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchAlertEvents = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/alerts/events/advanced?workspace_id=${workspaceId}`);
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertEvents();
  }, [workspaceId]);

  const handleResolve = async (eventId: string) => {
    try {
      const res = await fetch(`/api/v1/alerts/events/advanced/${eventId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: 'Resolved from UI Dashboard' }),
      });
      if (res.ok) {
        fetchAlertEvents();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 bg-slate-900 text-slate-100 rounded-xl border border-slate-800 shadow-xl">
      <div className="flex justify-between items-center mb-5">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            🔔 Alert Event History & Delivery Status
          </h3>
          <p className="text-xs text-slate-400">
            Audit log of triggered alerts across Telegram, Slack, PagerDuty & Email
          </p>
        </div>
        <button
          onClick={fetchAlertEvents}
          className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
        >
          Refresh Timeline
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-slate-400 py-4">Loading timeline events...</div>
      ) : events.length === 0 ? (
        <div className="text-sm text-slate-500 py-6 text-center border border-dashed border-slate-800 rounded-lg">
          No alert events recorded in timeline.
        </div>
      ) : (
        <div className="relative border-l-2 border-slate-800 ml-4 space-y-6 pl-6 py-2">
          {events.map((evt: AdvancedAlertEvent) => (
            <div key={evt.id} className="relative group">
              {/* Timeline marker node */}
              <div
                className={`absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full border-2 ${
                  evt.resolved_at
                    ? 'bg-emerald-500 border-emerald-300'
                    : evt.severity === 'critical'
                    ? 'bg-rose-500 border-rose-300 animate-pulse'
                    : 'bg-amber-500 border-amber-300'
                }`}
              />

              <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700/50">
                <div className="flex flex-wrap justify-between items-center gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100">{evt.rule_id}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-indigo-300 border border-slate-800">
                      {evt.severity.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">{evt.triggered_at}</span>
                </div>

                <div className="flex flex-wrap items-center gap-2 my-2">
                  <span className="text-xs text-slate-400">Channels Delivered:</span>
                  {evt.channels_delivered.map((ch) => (
                    <span
                      key={ch}
                      className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 capitalize"
                    >
                      {ch} ({evt.delivery_status[ch] ?? 'sent'})
                    </span>
                  ))}
                </div>

                <div className="flex justify-between items-center mt-3 pt-2 border-t border-slate-800">
                  {evt.resolved_at ? (
                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                      ✓ Resolved at {evt.resolved_at} ({evt.resolution_note})
                    </span>
                  ) : (
                    <button
                      onClick={() => handleResolve(evt.id)}
                      className="px-2.5 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium transition"
                    >
                      Mark Resolved
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

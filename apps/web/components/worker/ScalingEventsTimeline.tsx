// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_worker_ScalingEventsTimeline"
// purpose: "React Component for Scaling Events Audit Log Timeline (DNK-PLATFORM-SCALE-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React from 'react';

export interface ScalingEvent {
  id: string;
  pool_id: string;
  event_type: 'scale_up' | 'scale_down' | 'drain' | 'emergency_stop';
  worker_count_before: number;
  worker_count_after: number;
  trigger_reason: string;
  triggered_at: string;
}

export interface ScalingEventsTimelineProps {
  events?: ScalingEvent[];
}

export const ScalingEventsTimeline: React.FC<ScalingEventsTimelineProps> = ({ events = [] }) => {
  const sampleEvents: ScalingEvent[] = events.length > 0 ? events : [
    {
      id: 'evt-1',
      pool_id: 'pool-alpha',
      event_type: 'scale_up',
      worker_count_before: 1,
      worker_count_after: 3,
      trigger_reason: 'queue depth 120 >= threshold 80',
      triggered_at: '2026-08-28T11:45:00Z',
    },
    {
      id: 'evt-2',
      pool_id: 'pool-alpha',
      event_type: 'scale_down',
      worker_count_before: 3,
      worker_count_after: 1,
      trigger_reason: 'idle timeout 300s >= threshold 300s',
      triggered_at: '2026-08-28T11:55:00Z',
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <h3 className="text-lg font-bold mb-4">Scaling Events Audit Log</h3>
      <div className="space-y-3 font-mono text-xs">
        {sampleEvents.map((evt) => (
          <div key={evt.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 flex items-center justify-between">
            <div>
              <span className={`px-2 py-0.5 rounded font-bold uppercase mr-2 ${
                evt.event_type === 'scale_up' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'
              }`}>
                {evt.event_type}
              </span>
              <span className="text-slate-300">{evt.trigger_reason}</span>
            </div>
            <div className="text-slate-500">
              {evt.worker_count_before} → <span className="text-slate-200 font-bold">{evt.worker_count_after} Workers</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

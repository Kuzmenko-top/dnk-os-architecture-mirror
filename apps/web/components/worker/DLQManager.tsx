// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_worker_DLQManager"
// purpose: "React Component for Dead Letter Queue Management (DNK-PLATFORM-SCALE-002)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-28"
// --- END DNK-MRH-HEADER ---

import React, { useState } from 'react';
import { DLQEntry } from '../../lib/api/worker_client';

export interface DLQManagerProps {
  initialEntries?: DLQEntry[];
}

export const DLQManager: React.FC<DLQManagerProps> = ({ initialEntries = [] }) => {
  const [entries, setEntries] = useState<DLQEntry[]>(
    initialEntries.length > 0
      ? initialEntries
      : [
          {
            id: 'dlq-1',
            original_task_id: 'task-poison-99',
            error_message: 'Max retries exceeded: ConnectionTimeout to downstream microservice',
            retry_count: 3,
            max_retries: 3,
            status: 'failed',
          },
        ]
  );

  const handleRetry = async (id: string) => {
    try {
      await fetch(`/api/v1/worker/dlq/${id}/retry`, { method: 'POST' });
      setEntries((prev) =>
        prev.map((e) => (e.id === id ? { ...e, retry_count: e.retry_count + 1, status: 'retrying' } : e))
      );
    } catch {
      // Ignore in demo
    }
  };

  const handlePurge = async (id: string) => {
    try {
      await fetch(`/api/v1/worker/dlq/${id}`, { method: 'DELETE' });
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // Ignore in demo
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-xl">
      <h3 className="text-lg font-bold mb-4 flex items-center justify-between">
        <span>Dead Letter Queue (DLQ)</span>
        <span className="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-mono">
          {entries.length} Poison Tasks
        </span>
      </h3>

      {entries.length === 0 ? (
        <div className="text-slate-500 text-sm py-4 text-center">DLQ is empty. All workers healthy.</div>
      ) : (
        <div className="space-y-3 font-mono text-xs">
          {entries.map((item) => (
            <div key={item.id} className="bg-slate-950 p-4 rounded-lg border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
              <div>
                <div className="text-slate-200 font-bold">{item.original_task_id}</div>
                <div className="text-rose-400 mt-1">{item.error_message}</div>
                <div className="text-slate-500 text-[10px] mt-1">
                  Retries: {item.retry_count}/{item.max_retries} • Status: {item.status}
                </div>
              </div>
              <div className="flex gap-2 w-full md:w-auto">
                <button
                  onClick={() => handleRetry(item.id)}
                  className="px-3 py-1.5 bg-indigo-900/60 hover:bg-indigo-800/80 text-indigo-300 rounded font-medium transition"
                >
                  Retry Task
                </button>
                <button
                  onClick={() => handlePurge(item.id)}
                  className="px-3 py-1.5 bg-rose-900/60 hover:bg-rose-800/80 text-rose-300 rounded font-medium transition"
                >
                  Purge Entry
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

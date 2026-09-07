// --- DNK-MRH-HEADER ---
// mrh_id: "apps_web_components_StreamViewer"
// purpose: "SSE Streaming component for real-time task and plant execution events (DNK-USER-CABINET-001)"
// author: "DNK-e.com Maksym"
// license: "DNK-INTERNAL"
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-08-27"
// --- END DNK-MRH-HEADER ---

'use client';

import React, { useEffect, useState, useRef } from 'react';

interface StreamEvent {
  step: number;
  message: string;
  timestamp: string;
}

interface StreamViewerProps {
  endpoint: string;
  autoStart?: boolean;
}

export default function StreamViewer({ endpoint, autoStart = false }: StreamViewerProps) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (autoStart) {
      startStream();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [autoStart, endpoint]);

  const startStream = () => {
    setEvents([]);
    setError(null);
    setConnected(true);

    const eventSource = new EventSource(endpoint);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setEvents((prev) => [
          ...prev,
          {
            step: data.step ?? prev.length + 1,
            message: data.message ?? event.data,
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch {
        setEvents((prev) => [
          ...prev,
          {
            step: prev.length + 1,
            message: event.data,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    eventSource.onerror = () => {
      setError('Connection lost');
      setConnected(false);
      eventSource.close();
    };

    eventSource.onopen = () => {
      setConnected(true);
    };
  };

  const stopStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setConnected(false);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-lg p-6 text-slate-100">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-slate-100">Stream Viewer</h2>
        <div className="flex gap-2">
          {!connected ? (
            <button
              onClick={startStream}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition cursor-pointer"
            >
              Start
            </button>
          ) : (
            <button
              onClick={stopStream}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-medium transition cursor-pointer"
            >
              Stop
            </button>
          )}
        </div>
      </div>

      <div className="mb-4 flex items-center">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            connected
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
          }`}
        >
          {connected ? 'Connected' : 'Disconnected'}
        </span>
        {error && <span className="ml-2 text-rose-400 text-xs font-medium">{error}</span>}
      </div>

      <div className="border border-slate-800 rounded-lg p-4 h-64 overflow-y-auto bg-slate-950 font-mono text-sm">
        {events.length === 0 ? (
          <p className="text-slate-500">No events yet. Click &quot;Start&quot; to begin streaming.</p>
        ) : (
          events.map((event, index) => (
            <div key={index} className="mb-2 border-b border-slate-800/80 pb-2 last:border-b-0">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span className="font-semibold text-emerald-400">Step {event.step}</span>
                <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="text-slate-200">{event.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// --- DNK-MRH-HEADER ---
// mrh_id: "scripts/load_test/ws_load_test.js"
// purpose: "k6 WebSocket load test for DNK OS Swarm Event Streaming."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import ws from 'k6/ws';
import { check } from 'k6';

export let options = {
  vus: 50,
  duration: '60s',
};

export default function () {
  const wsUrl = __ENV.WS_URL || 'ws://localhost:8000/ws/telemetry';
  const res = ws.connect(wsUrl, {}, function (socket) {
    socket.on('open', () => {
      socket.send(JSON.stringify({ type: 'ping' }));
    });
    socket.on('message', (data) => {
      check(data, { 'message received': (d) => d.length > 0 });
      socket.close();
    });
  });

  check(res, { 'status is 101': (r) => r && r.status === 101 });
}

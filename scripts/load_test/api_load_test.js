// --- DNK-MRH-HEADER ---
// mrh_id: "scripts/load_test/api_load_test.js"
// purpose: "k6 API load testing script simulating concurrent user requests and task operations."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-05"
// author: "DNK-e.com Maksym"
// --- END DNK-MRH-HEADER ---

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '30s', target: 100 },   // Ramp up to 100 users
    { duration: '5m', target: 100 },    // Stay at 100 users
    { duration: '30s', target: 0 },     // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p95<1000'],    // 95% of requests should be below 1s
    errors: ['rate<0.01'],              // Error rate should be < 1%
  },
};

export default function () {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';

  // Health check
  let res = http.get(`${baseUrl}/health`);
  check(res, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 100ms': (r) => r.timings.duration < 100,
  });
  errorRate.add(res.status !== 200);
  sleep(1);

  // Task creation
  res = http.post(`${baseUrl}/api/v3/tasks`, JSON.stringify({
    title: 'Load Test Task',
    description: 'Testing system under load',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  check(res, {
    'task creation status is 201 or 200': (r) => r.status === 201 || r.status === 200,
    'task creation response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(res.status !== 201 && res.status !== 200);
  sleep(1);

  // Task list
  res = http.get(`${baseUrl}/api/v3/tasks`);
  check(res, {
    'task list status is 200': (r) => r.status === 200,
    'task list response time < 300ms': (r) => r.timings.duration < 300,
  });
  errorRate.add(res.status !== 200);
  sleep(1);
}

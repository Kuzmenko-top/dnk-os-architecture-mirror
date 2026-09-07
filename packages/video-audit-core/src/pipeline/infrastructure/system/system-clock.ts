/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/system/system-clock.ts"
# purpose: "Production System Clock Implementation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { Clock } from '../../ports/clock.js';

export class SystemClock implements Clock {
  now(): Date {
    return new Date();
  }

  nowIso(): string {
    return new Date().toISOString();
  }

  nowMs(): number {
    return Date.now();
  }
}

export class FixedClock implements Clock {
  private currentTimeMs: number;

  constructor(initialIsoOrMs: string | number = '2026-09-02T12:00:00.000Z') {
    this.currentTimeMs =
      typeof initialIsoOrMs === 'string'
        ? new Date(initialIsoOrMs).getTime()
        : initialIsoOrMs;
  }

  now(): Date {
    return new Date(this.currentTimeMs);
  }

  nowIso(): string {
    return new Date(this.currentTimeMs).toISOString();
  }

  nowMs(): number {
    return this.currentTimeMs;
  }

  advanceMs(ms: number): void {
    this.currentTimeMs += ms;
  }

  setTime(isoOrMs: string | number): void {
    this.currentTimeMs =
      typeof isoOrMs === 'string'
        ? new Date(isoOrMs).getTime()
        : isoOrMs;
  }
}

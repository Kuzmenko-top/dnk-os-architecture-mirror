/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/runtime-adapter.ts"
// purpose: "Browser Runtime Adapter (Wake Lock, Vibration Feedback, Secure Context) implementing RuntimePort."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type { RuntimePort } from './ports';

export class BrowserRuntimeAdapter implements RuntimePort {
  private wakeLockSentinel: unknown = null;

  async requestWakeLock(): Promise<boolean> {
    if (typeof navigator === 'undefined' || !('wakeLock' in navigator)) {
      return false;
    }

    try {
      const wakeLock = (navigator as unknown as { wakeLock: { request: (type: string) => Promise<unknown> } }).wakeLock;
      this.wakeLockSentinel = await wakeLock.request('screen');
      return true;
    } catch {
      return false;
    }
  }

  async releaseWakeLock(): Promise<void> {
    if (this.wakeLockSentinel) {
      try {
        const sentinel = this.wakeLockSentinel as { release: () => Promise<void> };
        await sentinel.release();
      } catch {
        // ignore
      }
      this.wakeLockSentinel = null;
    }
  }

  isSecureContext(): boolean {
    if (typeof window === 'undefined') return false;
    return !!window.isSecureContext;
  }

  vibrate(pattern: number | number[]): void {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      try {
        navigator.vibrate(pattern);
      } catch {
        // ignore vibration failure
      }
    }
  }
}

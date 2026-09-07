/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/capabilities.ts"
// purpose: "Browser Capability Probe for Teleprompter PWA Runtime."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type { WebCapabilities, CapabilityCheckResult } from './ports';

export class BrowserCapabilitiesProbe {
  static probe(): CapabilityCheckResult {
    const isBrowser = typeof window !== 'undefined' && typeof navigator !== 'undefined';
    
    if (!isBrowser) {
      return {
        capabilities: {
          camera: false,
          microphone: false,
          mediaRecorder: false,
          speechRecognition: false,
          indexedDb: false,
          secureContext: false,
          wakeLock: false,
        },
        allEssentialSupported: false,
        warnings: ['Running in a non-browser environment.'],
        errors: ['Window/Navigator API not available.'],
      };
    }

    const secureContext = window.isSecureContext ?? false;
    const hasMediaDevices = !!(navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function');
    const mediaRecorder = typeof window.MediaRecorder !== 'undefined';
    const speechRecognition = !!(
      (window as unknown as { SpeechRecognition?: unknown }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition
    );
    const indexedDb = typeof window.indexedDB !== 'undefined';
    const wakeLock = !!(navigator && 'wakeLock' in navigator);

    const capabilities: WebCapabilities = {
      camera: hasMediaDevices,
      microphone: hasMediaDevices,
      mediaRecorder,
      speechRecognition,
      indexedDb,
      secureContext,
      wakeLock,
    };

    const warnings: string[] = [];
    const errors: string[] = [];

    if (!secureContext) {
      warnings.push('Not running in a Secure Context (HTTPS or localhost). Camera and microphone permissions may be restricted.');
    }

    if (!speechRecognition) {
      warnings.push('Web Speech API is not natively supported in this browser. Fallback simulation mode will be used for ASR alignment.');
    }

    if (!mediaRecorder) {
      warnings.push('MediaRecorder API is not available. Video recording is disabled; prompter will run in display-only mode.');
    }

    if (!hasMediaDevices) {
      warnings.push('MediaDevices API not found. Camera preview and microphone are unavailable.');
    }

    if (!indexedDb) {
      errors.push('IndexedDB is not supported. Session history and offline recovery cannot be saved.');
    }

    // Essential for basic prompter usage: IndexedDB must work, basic window must exist
    const allEssentialSupported = indexedDb;

    return {
      capabilities,
      allEssentialSupported,
      warnings,
      errors,
    };
  }
}

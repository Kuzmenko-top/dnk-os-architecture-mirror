/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/ports.ts"
// purpose: "Browser Runtime Adapter Interfaces and Capabilities Contracts for Teleprompter PWA."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import type { TeleprompterSession } from '@dnk/teleprompter-core';

export interface WebCapabilities {
  camera: boolean;
  microphone: boolean;
  mediaRecorder: boolean;
  speechRecognition: boolean;
  indexedDb: boolean;
  secureContext: boolean;
  wakeLock: boolean;
}

export interface CapabilityCheckResult {
  capabilities: WebCapabilities;
  allEssentialSupported: boolean;
  warnings: string[];
  errors: string[];
}

export interface MediaRecorderPort {
  start(stream: MediaStream): Promise<void>;
  stop(): Promise<Blob>;
  pause(): void;
  resume(): void;
  isRecording(): boolean;
  getMimeType(): string;
  getRecordedBlob(): Blob | null;
}

export interface RuntimePort {
  isSecureContext(): boolean;
  requestWakeLock(): Promise<boolean>;
  releaseWakeLock(): Promise<void>;
  vibrate(pattern: number | number[]): void;
}

export interface SessionStorePort {
  saveSession(session: TeleprompterSession): Promise<void>;
  getSession(sessionId: string): Promise<TeleprompterSession | null>;
  listSessions(): Promise<TeleprompterSession[]>;
  deleteSession(sessionId: string): Promise<void>;
}

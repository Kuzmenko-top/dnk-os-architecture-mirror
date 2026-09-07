/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/tests/integration/teleprompter-web-adapters.test.ts"
# purpose: "Integration Verification of Web Adapters, Capabilities, Mock Speech Provider, MediaRecorder, and IndexedDB Store."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach, vi } from 'vitest';

import { BrowserCapabilitiesProbe } from '../../../../apps/web/src/adapters/teleprompter/capabilities.js';
import {
  WebSpeechProvider,
  MockASRStreamProvider,
} from '../../../../apps/web/src/adapters/teleprompter/web-speech-provider.js';
import { WebMediaRecorderAdapter } from '../../../../apps/web/src/adapters/teleprompter/media-recorder-adapter.js';
import { IndexedDbSessionStore } from '../../../../apps/web/src/adapters/teleprompter/indexed-db-session-store.js';
import { BrowserRuntimeAdapter } from '../../../../apps/web/src/adapters/teleprompter/runtime-adapter.js';

import { reburnReferenceFixture } from '../../../video-audit-core/src/fixtures/reburn-reference.js';
import { TeleprompterRuntime } from '../../src/state/session-machine.js';
import { ASRHypothesis } from '../../src/ports/asr.js';

describe('TELEPROMPTER-WEB-001 Integration & Browser Adapters Verification', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('1. Browser Capabilities & Probe', () => {
    it('BrowserCapabilitiesProbe safely detects capabilities in synthetic/Node environment without crashing', () => {
      const probe = BrowserCapabilitiesProbe.probe();
      expect(probe).toBeDefined();
      expect(typeof probe.capabilities.camera).toBe('boolean');
      expect(typeof probe.capabilities.microphone).toBe('boolean');
      expect(typeof probe.capabilities.secureContext).toBe('boolean');
      expect(typeof probe.capabilities.indexedDb).toBe('boolean');
      expect(typeof probe.capabilities.mediaRecorder).toBe('boolean');
      expect(typeof probe.capabilities.speechRecognition).toBe('boolean');
      expect(typeof probe.capabilities.wakeLock).toBe('boolean');
      expect(Array.isArray(probe.warnings)).toBe(true);
      expect(Array.isArray(probe.errors)).toBe(true);
    });
  });

  describe('2. ASRProviderPort Lifecycle, Monotonic Sequence & Order Handling', () => {
    it('WebSpeechProvider exposes expected capabilities and handles language config', () => {
      const provider = new WebSpeechProvider({ language: 'uk-UA' });
      expect(provider.id).toBe('web-speech-api');
      expect(provider.capabilities.language).toBe('uk-UA');
      expect(provider.capabilities.supportsInterimResults).toBe(true);
      expect(provider.capabilities.supportsConfidence).toBe(true);
    });

    it('MockASRStreamProvider adheres to ASRProviderPort lifecycle: subscribe, step, emit, unsubscribe, stop', async () => {
      const runtime = new TeleprompterRuntime(
        reburnReferenceFixture.script,
        reburnReferenceFixture.prosody,
        { targetWpm: 130 }
      );
      const tokens = runtime.getTokens();

      const mockProvider = new MockASRStreamProvider({
        scriptTokens: tokens,
        targetWpm: 180,
        enableInterim: true,
      });

      const receivedHypotheses: ASRHypothesis[] = [];
      const unsubscribe = mockProvider.subscribe((hyp) => {
        receivedHypotheses.push(hyp);
      });

      await mockProvider.start();

      // Step 4 tokens deterministically
      await mockProvider.step(4);

      expect(receivedHypotheses.length).toBe(4);
      // Strictly monotonic sequences
      for (let i = 1; i < receivedHypotheses.length; i++) {
        expect(receivedHypotheses[i].sequence).toBeGreaterThan(
          receivedHypotheses[i - 1].sequence
        );
      }

      unsubscribe();
      await mockProvider.stop();
    });

    it('Runtime gracefully handles monotonic, duplicate, and out-of-order hypotheses', () => {
      const runtime = new TeleprompterRuntime(
        reburnReferenceFixture.script,
        reburnReferenceFixture.prosody,
        { targetWpm: 130 }
      );
      runtime.start();

      const tokens = runtime.getTokens();
      expect(tokens.length).toBeGreaterThan(2);

      const firstTokenWord = tokens[0].normalizedWord;
      const secondTokenWord = tokens[1].normalizedWord;

      // 1. Valid sequence 1
      const hyp1: ASRHypothesis = {
        sequence: 1,
        text: firstTokenWord,
        words: [{ word: firstTokenWord, startMs: 0, endMs: 250, confidence: 0.95 }],
        isFinal: true,
        startedAtMs: 0,
        endedAtMs: 250,
        confidence: 0.95,
      };
      const res1 = runtime.processHypothesis(hyp1);
      expect(res1.nextConfirmedIndex).toBeGreaterThanOrEqual(1);

      // 2. Duplicate sequence 1 (should be ignored and not corrupt or regress state)
      const resDuplicate = runtime.processHypothesis(hyp1);
      expect(resDuplicate.nextConfirmedIndex).toBe(res1.nextConfirmedIndex);
      expect(resDuplicate.matchedTokenIndexes).toHaveLength(0);

      // 3. Forward progression sequence 2
      const hyp2: ASRHypothesis = {
        sequence: 2,
        text: secondTokenWord,
        words: [{ word: secondTokenWord, startMs: 250, endMs: 500, confidence: 0.95 }],
        isFinal: true,
        startedAtMs: 250,
        endedAtMs: 500,
        confidence: 0.95,
      };
      const res2 = runtime.processHypothesis(hyp2);
      expect(res2.nextConfirmedIndex).toBeGreaterThanOrEqual(res1.nextConfirmedIndex);

      // 4. Out-of-order / stale hypothesis with sequence 1 arriving after sequence 2
      const resStale = runtime.processHypothesis(hyp1);
      expect(resStale.nextConfirmedIndex).toBe(res2.nextConfirmedIndex);
      expect(resStale.matchedTokenIndexes).toHaveLength(0);
    });
  });

  describe('3. IndexedDB Storage & In-Memory Fallback', () => {
    it('IndexedDbSessionStore correctly persists, retrieves, lists, and deletes sessions with fallback', async () => {
      const store = new IndexedDbSessionStore();

      const runtime = new TeleprompterRuntime(
        reburnReferenceFixture.script,
        reburnReferenceFixture.prosody,
        { targetWpm: 130 }
      );

      runtime.start();
      const session = runtime.getSession();

      await store.saveSession(session);

      const retrieved = await store.getSession(session.sessionId);
      expect(retrieved).not.toBeNull();
      expect(retrieved?.sessionId).toBe(session.sessionId);
      expect(retrieved?.scriptId).toBe(reburnReferenceFixture.script.id);

      const list = await store.listSessions();
      expect(list.length).toBeGreaterThanOrEqual(1);

      await store.deleteSession(session.sessionId);
      const deleted = await store.getSession(session.sessionId);
      expect(deleted).toBeNull();
    });
  });

  describe('4. MediaRecorderPort Lifecycle & MIME Fallback', () => {
    it('WebMediaRecorderAdapter exposes safe contract and tracks recording states', () => {
      const recorder = new WebMediaRecorderAdapter();
      expect(recorder.isRecording()).toBe(false);
      expect(recorder.getRecordedBlob()).toBeNull();
      expect(typeof recorder.getMimeType()).toBe('string');

      // Pause / resume on inactive recorder should not throw
      expect(() => recorder.pause()).not.toThrow();
      expect(() => recorder.resume()).not.toThrow();
    });
  });

  describe('5. BrowserRuntimeAdapter Degradation (Wake Lock & Vibration)', () => {
    it('gracefully degrades when Wake Lock and Vibration APIs are absent or rejected', async () => {
      const adapter = new BrowserRuntimeAdapter();
      expect(typeof adapter.isSecureContext()).toBe('boolean');

      const wakeLockResult = await adapter.requestWakeLock();
      expect(typeof wakeLockResult).toBe('boolean');

      await expect(adapter.releaseWakeLock()).resolves.not.toThrow();
      expect(() => adapter.vibrate(200)).not.toThrow();
      expect(() => adapter.vibrate([100, 50, 100])).not.toThrow();
    });
  });
});

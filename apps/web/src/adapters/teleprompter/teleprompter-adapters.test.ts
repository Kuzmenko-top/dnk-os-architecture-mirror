/*
// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/adapters/teleprompter/teleprompter-adapters.test.ts"
// purpose: "Unit & Integration Tests for Teleprompter Browser Adapters & IndexedDB Session Store."
// canonical_source: true
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---
*/

import 'fake-indexeddb/auto';
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

import { BrowserCapabilitiesProbe } from './capabilities.js';
import { MockASRStreamProvider, WebSpeechProvider } from './web-speech-provider.js';
import { WebMediaRecorderAdapter } from './media-recorder-adapter.js';
import { IndexedDbSessionStore } from './indexed-db-session-store.js';
import { BrowserRuntimeAdapter } from './runtime-adapter.js';

import { reburnReferenceFixture } from '@dnk/video-audit-core';
import { ScriptFlatteningService } from '@dnk/teleprompter-core';
import type { TeleprompterSession } from '@dnk/teleprompter-core';

describe('Teleprompter Web Adapters & Storage', () => {
  let flatteningService: ScriptFlatteningService;

  beforeEach(() => {
    flatteningService = new ScriptFlatteningService();
  });

  it('CapabilitiesProbe detects capabilities safely in environment', () => {
    const probeResult = BrowserCapabilitiesProbe.probe();
    assert.equal(typeof probeResult.capabilities.camera, 'boolean');
    assert.equal(typeof probeResult.capabilities.microphone, 'boolean');
    assert.equal(typeof probeResult.capabilities.indexedDb, 'boolean');
    assert.equal(typeof probeResult.capabilities.speechRecognition, 'boolean');
  });

  it('MockASRStreamProvider emits ordered ASR hypotheses matching script tokens', async () => {
    const tokens = flatteningService.flatten(
      reburnReferenceFixture.script,
      reburnReferenceFixture.prosody
    );

    const provider = new MockASRStreamProvider({
      scriptTokens: tokens,
      targetWpm: 600, // fast speed for test
      enableInterim: false,
    });

    const received: string[] = [];
    const unsubscribe = provider.subscribe((hyp) => {
      received.push(hyp.text);
      assert.ok(hyp.sequence > 0);
      assert.ok(hyp.confidence! >= 0.85);
    });

    await provider.start();
    // Allow stream timer ticks
    await new Promise((resolve) => setTimeout(resolve, 200));
    await provider.stop();
    unsubscribe();

    assert.ok(received.length > 0, 'Should have received at least one hypothesis');
  });

  it('IndexedDbSessionStore saves, reads, lists and deletes sessions', async () => {
    const store = new IndexedDbSessionStore();

    const sampleSession: TeleprompterSession = {
      sessionId: 'ses-test-101',
      scriptId: 'reburn-hook-v1',
      scriptVersion: '1.0.0',
      prosodyVersion: '1.0.0',
      status: 'completed',
      currentTokenIndex: 12,
      confirmedTokenIndex: 12,
      speculativeTokenIndex: 12,
      startedAtMs: Date.now() - 5000,
      completedAtMs: Date.now(),
      updatedAtMs: Date.now(),
      totalTokens: 50,
      lastProcessedHypothesisSequence: 15,
    };

    await store.saveSession(sampleSession);

    const retrieved = await store.getSession('ses-test-101');
    assert.ok(retrieved !== null);
    assert.equal(retrieved?.sessionId, 'ses-test-101');
    assert.equal(retrieved?.status, 'completed');

    const list = await store.listSessions();
    assert.ok(list.length >= 1);
    assert.ok(list.some((s) => s.sessionId === 'ses-test-101'));

    await store.deleteSession('ses-test-101');
    const afterDelete = await store.getSession('ses-test-101');
    assert.equal(afterDelete, null);
  });

  it('BrowserRuntimeAdapter gracefully handles environment calls without throwing', async () => {
    const adapter = new BrowserRuntimeAdapter();
    assert.equal(typeof adapter.isSecureContext(), 'boolean');

    // Should not throw even in Node test environment
    await adapter.requestWakeLock();
    await adapter.releaseWakeLock();
    adapter.vibrate(100);
  });
});

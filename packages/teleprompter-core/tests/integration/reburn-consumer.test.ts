/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/tests/integration/reburn-consumer.test.ts"
# purpose: "Mandatory End-to-End Consumer Contract Test: Video Audit -> Teleprompter Runtime -> Analytics."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { reburnReferenceFixture } from '@dnk/video-audit-core';
import { TeleprompterRuntime } from '../../src/state/session-machine.js';
import { ASRHypothesis } from '../../src/ports/asr.js';
import { ContractVersionMismatchError } from '../../src/errors/errors.js';
import { TeleprompterEvent } from '../../src/domain/events.js';

describe('VideoAudit to Teleprompter Integration: reburn-reference consumer flow', () => {
  const scriptDoc = reburnReferenceFixture.script;
  const prosodyDoc = reburnReferenceFixture.prosody;

  it('should ingest valid AdaptationResult script & prosody and flatten into runtime tokens with prosody cues', () => {
    const runtime = new TeleprompterRuntime(scriptDoc, prosodyDoc, {
      targetWpm: 130,
    });

    const tokens = runtime.getTokens();
    const session = runtime.getSession();

    expect(tokens.length).toBeGreaterThan(15);
    expect(session.scriptId).toBe(scriptDoc.id);
    expect(session.scriptVersion).toBe('script.v1');
    expect(session.prosodyVersion).toBe('prosody.v1');
    expect(session.status).toBe('idle');

    // Check prosody mapping on first words
    const firstToken = tokens[0];
    expect(firstToken.sceneRole).toBe('hook');
    expect(firstToken.prosody).toBeDefined();
    expect(firstToken.prosody?.emphasis).toBe('punch');
    expect(firstToken.prosody?.pauseAfterMs).toBe(100);
    expect(firstToken.prosody?.gesture).toBe('hand_raise');
  });

  it('should execute full ASR streaming session with pause, skip, stumble and manual reset', () => {
    const runtime = new TeleprompterRuntime(scriptDoc, prosodyDoc, {
      targetWpm: 130,
    });

    const emittedEvents: TeleprompterEvent[] = [];
    runtime.onEvent((evt) => {
      emittedEvents.push(evt);
    });

    const startTime = 1725280000000;
    runtime.start(startTime);
    expect(runtime.getSession().status).toBe('running');

    const tokens = runtime.getTokens();

    // 1. First spoken phrase (interim then final)
    const hyp1Interim: ASRHypothesis = {
      sequence: 1,
      text: `${tokens[0].word} ${tokens[1].word}`,
      isFinal: false,
      startedAtMs: startTime,
      endedAtMs: startTime + 800,
    };
    runtime.processHypothesis(hyp1Interim, startTime + 800);

    // Interim hypothesis marks tokens speculative
    expect(tokens[0].status).toBe('speculative');
    expect(tokens[1].status).toBe('speculative');

    const hyp1Final: ASRHypothesis = {
      sequence: 2,
      text: `${tokens[0].word} ${tokens[1].word}`,
      isFinal: true,
      startedAtMs: startTime,
      endedAtMs: startTime + 1000,
    };
    runtime.processHypothesis(hyp1Final, startTime + 1000);

    // Final hypothesis marks tokens completed/confirmed
    expect(tokens[0].status).toBe('completed');
    expect(tokens[1].status).toBe('confirmed');
    expect(runtime.getSession().confirmedTokenIndex).toBe(2);

    // 2. Next phrase with a skip (speaker skips token 2 and speaks tokens 3 & 4)
    const hyp2Skip: ASRHypothesis = {
      sequence: 3,
      text: `${tokens[3].word} ${tokens[4].word}`,
      isFinal: true,
      startedAtMs: startTime + 1200,
      endedAtMs: startTime + 2000,
    };
    const skipResult = runtime.processHypothesis(hyp2Skip, startTime + 2000);

    expect(skipResult.skippedTokenIndexes).toContain(2);
    expect(tokens[1].status).toBe('completed');
    expect(tokens[2].status).toBe('skipped');
    expect(tokens[3].status).toBe('completed');
    expect(tokens[4].status).toBe('confirmed');

    // 3. User performs manual reset (taps word at index 1 to re-read)
    runtime.resetToToken(1, startTime + 2500);
    expect(runtime.getSession().confirmedTokenIndex).toBe(1);
    expect(tokens[1].status).toBe('upcoming');
    expect(tokens[3].status).toBe('upcoming');

    // Verify manual reset event was recorded
    const resetEvents = emittedEvents.filter((e) => e.type === 'MANUAL_RESET');
    expect(resetEvents.length).toBe(1);

    // 4. Continue speaking and finish remaining script
    let currentSeq = 4;
    for (let i = 1; i < tokens.length; i += 3) {
      const chunk = tokens.slice(i, i + 3).map((t) => t.word).join(' ');
      const hyp: ASRHypothesis = {
        sequence: ++currentSeq,
        text: chunk,
        isFinal: true,
        startedAtMs: startTime + 3000 + i * 300,
        endedAtMs: startTime + 3000 + (i + 3) * 300,
      };
      runtime.processHypothesis(hyp, startTime + 3000 + (i + 3) * 300);
    }

    // 5. Complete session
    const finalAnalytics = runtime.finish(startTime + 15000);

    expect(finalAnalytics.sessionId).toBe(runtime.getSession().sessionId);
    expect(finalAnalytics.scriptId).toBe(scriptDoc.id);
    expect(finalAnalytics.scriptWordCount).toBe(tokens.length);
    expect(finalAnalytics.manualResetCount).toBe(1);
    expect(finalAnalytics.adherenceScore).toBeGreaterThan(0.7);
    expect(finalAnalytics.adherenceNote).toContain('script fidelity');
  });

  it('should reject incompatible script schema versions', () => {
    const incompatibleScript = {
      ...scriptDoc,
      schemaVersion: 'script.v999' as any,
    };

    expect(
      () => new TeleprompterRuntime(incompatibleScript, prosodyDoc)
    ).toThrow(ContractVersionMismatchError);
  });
});

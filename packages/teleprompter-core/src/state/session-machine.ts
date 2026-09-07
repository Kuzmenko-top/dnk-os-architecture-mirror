/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/state/session-machine.ts"
# purpose: "Teleprompter Runtime Session Orchestrator and State Coordinator."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ScriptDocument, ProsodyDocument } from '@dnk/video-audit-core';
import { RuntimeToken, ScriptFlatteningService } from '../domain/tokens.js';
import { TeleprompterSession, SessionStatus } from '../domain/session.js';
import {
  TeleprompterEvent,
  ManualResetEvent,
  SessionStateChangedEvent,
  SessionCompletedEvent,
  PacingDriftEvent,
} from '../domain/events.js';
import { AlignmentEngine, AlignmentConfig, AlignmentResult } from '../alignment/engine.js';
import { WPMController, PacingMetrics } from '../pacing/wpm.js';
import { SessionAnalyticsCollector, SessionAnalytics } from '../analytics/collector.js';
import { TextNormalizerPort, DefaultTextNormalizer } from '../ports/normalizer.js';
import { ASRHypothesis } from '../ports/asr.js';
import {
  InvalidStateTransitionError,
  TokenIndexOutOfBoundsError,
} from '../errors/errors.js';
import { TokenStateMachine } from './token-state.js';

export interface TeleprompterRuntimeOptions {
  sessionId?: string;
  targetWpm?: number;
  alignmentConfig?: Partial<AlignmentConfig>;
  normalizer?: TextNormalizerPort;
}

export class TeleprompterRuntime {
  private readonly session: TeleprompterSession;
  private readonly tokens: RuntimeToken[];
  private readonly alignmentEngine: AlignmentEngine;
  private readonly wpmController: WPMController;
  private readonly analyticsCollector: SessionAnalyticsCollector;
  private readonly stateMachine: TokenStateMachine;
  private readonly listeners = new Set<(event: TeleprompterEvent) => void>();

  constructor(
    script: ScriptDocument,
    prosody?: ProsodyDocument,
    options?: TeleprompterRuntimeOptions
  ) {
    const normalizer = options?.normalizer || new DefaultTextNormalizer();
    const flatteningService = new ScriptFlatteningService(normalizer);
    const targetWpm =
      options?.targetWpm || prosody?.globalPacing?.targetWpm || 140;

    this.tokens = flatteningService.flatten(script, prosody, {
      targetWpm,
      normalizer,
    });

    const sessionId = options?.sessionId || `tp-sess-${Date.now()}`;
    const now = Date.now();

    this.session = {
      sessionId,
      scriptId: script.id,
      scriptVersion: script.schemaVersion,
      prosodyVersion: prosody ? prosody.schemaVersion : 'prosody.none',
      status: 'idle',
      currentTokenIndex: 0,
      confirmedTokenIndex: 0,
      speculativeTokenIndex: undefined,
      updatedAtMs: now,
      totalTokens: this.tokens.length,
      lastProcessedHypothesisSequence: 0,
    };

    this.alignmentEngine = new AlignmentEngine(
      options?.alignmentConfig,
      normalizer
    );
    this.wpmController = new WPMController(targetWpm);
    this.analyticsCollector = new SessionAnalyticsCollector();
    this.stateMachine = new TokenStateMachine();
  }

  onEvent(listener: (event: TeleprompterEvent) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit(event: TeleprompterEvent): void {
    this.analyticsCollector.recordEvent(event);
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (err) {
        // Defensive: prevent listener errors from crashing runtime
        console.error('Teleprompter listener error:', err);
      }
    }
  }

  private transitionSessionStatus(
    newStatus: SessionStatus,
    nowMs: number
  ): void {
    const prevStatus = this.session.status;
    this.session.status = newStatus;
    this.session.updatedAtMs = nowMs;

    this.emit({
      type: 'SESSION_STATE_CHANGED',
      previousStatus: prevStatus,
      newStatus,
      timestampMs: nowMs,
    } as SessionStateChangedEvent);
  }

  start(nowMs = Date.now()): void {
    if (this.session.status !== 'idle' && this.session.status !== 'paused') {
      throw new InvalidStateTransitionError(
        this.session.status,
        'running',
        'Session start/resume'
      );
    }

    if (!this.session.startedAtMs) {
      this.session.startedAtMs = nowMs;
    }
    this.transitionSessionStatus('running', nowMs);
  }

  pause(nowMs = Date.now()): void {
    if (this.session.status !== 'running') {
      throw new InvalidStateTransitionError(
        this.session.status,
        'paused',
        'Session pause'
      );
    }
    this.session.pausedAtMs = nowMs;
    this.transitionSessionStatus('paused', nowMs);
  }

  resume(nowMs = Date.now()): void {
    this.start(nowMs);
  }

  finish(nowMs = Date.now()): SessionAnalytics {
    if (this.session.status === 'completed') {
      return this.getAnalytics(nowMs);
    }

    this.session.completedAtMs = nowMs;
    this.transitionSessionStatus('completed', nowMs);

    const analytics = this.getAnalytics(nowMs);
    this.emit({
      type: 'SESSION_COMPLETED',
      durationMs: analytics.totalDurationMs,
      spokenWordsCount: analytics.spokenWordCount,
      totalTokensCount: analytics.scriptWordCount,
      adherenceScore: analytics.adherenceScore,
      timestampMs: nowMs,
    } as SessionCompletedEvent);

    return analytics;
  }

  stop(nowMs = Date.now()): SessionAnalytics {
    return this.finish(nowMs);
  }

  /**
   * High-priority manual reset: user taps on a word to rewind/fast-forward
   */
  resetToToken(targetIndex: number, nowMs = Date.now()): void {
    if (targetIndex < 0 || targetIndex >= this.tokens.length) {
      throw new TokenIndexOutOfBoundsError(targetIndex, this.tokens.length);
    }

    const previousIndex = this.session.confirmedTokenIndex;

    // Reset status of tokens accordingly
    for (let i = 0; i < this.tokens.length; i++) {
      const t = this.tokens[i];
      if (i < targetIndex) {
        if (t.status !== 'completed') {
          this.stateMachine.transition(t, 'completed');
        }
      } else if (i === targetIndex) {
        this.stateMachine.transition(t, 'upcoming');
      } else {
        if (t.status !== 'upcoming') {
          this.stateMachine.transition(t, 'upcoming');
        }
      }
    }

    this.session.confirmedTokenIndex = targetIndex;
    this.session.currentTokenIndex = targetIndex;
    this.session.speculativeTokenIndex = undefined;
    this.session.updatedAtMs = nowMs;

    this.emit({
      type: 'MANUAL_RESET',
      previousIndex,
      targetIndex,
      reason: 'User manual repositioning',
      timestampMs: nowMs,
    } as ManualResetEvent);
  }

  processHypothesis(
    hypothesis: ASRHypothesis,
    nowMs = Date.now()
  ): AlignmentResult {
    if (this.session.status !== 'running') {
      return {
        nextConfirmedIndex: this.session.confirmedTokenIndex,
        nextSpeculativeIndex: this.session.speculativeTokenIndex,
        matchedTokenIndexes: [],
        skippedTokenIndexes: [],
        confidence: 0,
        recovery: 'none',
        events: [],
      };
    }

    const result = this.alignmentEngine.align(
      hypothesis,
      this.tokens,
      this.session,
      nowMs
    );

    // Update session pointers
    this.session.lastProcessedHypothesisSequence = Math.max(
      this.session.lastProcessedHypothesisSequence,
      hypothesis.sequence
    );
    this.session.confirmedTokenIndex = result.nextConfirmedIndex;
    this.session.currentTokenIndex = result.nextConfirmedIndex;
    this.session.speculativeTokenIndex = result.nextSpeculativeIndex;
    this.session.updatedAtMs = nowMs;

    // Emit all internal alignment events
    for (const evt of result.events) {
      this.emit(evt);
    }

    // Check for pacing drift periodically
    const elapsed = this.session.startedAtMs
      ? nowMs - this.session.startedAtMs
      : 0;
    const pacing = this.wpmController.computePacingMetrics(
      this.tokens,
      this.session.confirmedTokenIndex,
      elapsed
    );

    if (Math.abs(pacing.driftPercentage) > 20) {
      this.emit({
        type: 'PACING_DRIFT',
        actualWpm: pacing.actualWpm,
        targetWpm: pacing.targetWpm,
        driftPercentage: pacing.driftPercentage,
        estimatedRemainingMs: pacing.estimatedRemainingMs,
        timestampMs: nowMs,
      } as PacingDriftEvent);
    }

    // Auto-complete if all tokens have been confirmed
    if (this.session.confirmedTokenIndex >= this.tokens.length) {
      this.finish(nowMs);
    }

    return result;
  }

  getSession(): Readonly<TeleprompterSession> {
    return { ...this.session };
  }

  getTokens(): Readonly<RuntimeToken[]> {
    return this.tokens;
  }

  getPacingMetrics(nowMs = Date.now()): PacingMetrics {
    const elapsed = this.session.startedAtMs
      ? nowMs - this.session.startedAtMs
      : 0;
    return this.wpmController.computePacingMetrics(
      this.tokens,
      this.session.confirmedTokenIndex,
      elapsed
    );
  }

  getAnalytics(nowMs = Date.now()): SessionAnalytics {
    return this.analyticsCollector.compile(
      this.session,
      this.tokens,
      this.wpmController.getEffectiveTargetWpm(),
      nowMs
    );
  }
}

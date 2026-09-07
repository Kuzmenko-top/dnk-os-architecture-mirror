/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/alignment/engine.ts"
# purpose: "Dynamic ASR Word Alignment Engine with Recovery Strategies."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RuntimeToken } from '../domain/tokens.js';
import { TeleprompterSession } from '../domain/session.js';
import {
  TeleprompterEvent,
  AlignmentMatchedEvent,
  AlignmentSkippedEvent,
  AlignmentRecoveryEvent,
  TokenStatusChangedEvent,
} from '../domain/events.js';
import { ASRHypothesis } from '../ports/asr.js';
import { TextNormalizerPort, DefaultTextNormalizer } from '../ports/normalizer.js';
import { WordMatcher } from './matcher.js';
import { TokenStateMachine } from '../state/token-state.js';

export type RecoveryStrategy =
  | 'none'
  | 'local'
  | 'forward_jump'
  | 'manual_required';

export interface AlignmentConfig {
  forwardWindowTokens: number;
  backwardWindowTokens: number;
  minSpeculativeConfidence: number;
  minConfirmedConfidence: number;
  maxSkipTokens: number;
  repeatedHypothesisLimit: number;
}

export const DEFAULT_ALIGNMENT_CONFIG: AlignmentConfig = {
  forwardWindowTokens: 8,
  backwardWindowTokens: 2,
  minSpeculativeConfidence: 0.55,
  minConfirmedConfidence: 0.75,
  maxSkipTokens: 4,
  repeatedHypothesisLimit: 3,
};

export interface AlignmentResult {
  nextConfirmedIndex: number;
  nextSpeculativeIndex?: number;
  matchedTokenIndexes: number[];
  skippedTokenIndexes: number[];
  confidence: number;
  recovery: RecoveryStrategy;
  events: TeleprompterEvent[];
}

export class AlignmentEngine {
  private readonly config: AlignmentConfig;
  private readonly normalizer: TextNormalizerPort;
  private readonly matcher: WordMatcher;
  private readonly stateMachine: TokenStateMachine;

  constructor(
    config?: Partial<AlignmentConfig>,
    normalizer?: TextNormalizerPort
  ) {
    this.config = { ...DEFAULT_ALIGNMENT_CONFIG, ...config };
    this.normalizer = normalizer || new DefaultTextNormalizer();
    this.matcher = new WordMatcher(this.normalizer);
    this.stateMachine = new TokenStateMachine();
  }

  /**
   * Aligns incoming ASR Hypothesis against script tokens
   */
  align(
    hypothesis: ASRHypothesis,
    tokens: RuntimeToken[],
    session: TeleprompterSession,
    nowMs: number = Date.now()
  ): AlignmentResult {
    // 1. Monotonic sequence check: ignore stale or duplicate hypotheses
    if (hypothesis.sequence <= session.lastProcessedHypothesisSequence) {
      return {
        nextConfirmedIndex: session.confirmedTokenIndex,
        nextSpeculativeIndex: session.speculativeTokenIndex,
        matchedTokenIndexes: [],
        skippedTokenIndexes: [],
        confidence: 1.0,
        recovery: 'none',
        events: [],
      };
    }

    const events: TeleprompterEvent[] = [];
    const spokenWords = this.normalizer.tokenize(hypothesis.text);

    if (spokenWords.length === 0 || tokens.length === 0) {
      return {
        nextConfirmedIndex: session.confirmedTokenIndex,
        nextSpeculativeIndex: session.speculativeTokenIndex,
        matchedTokenIndexes: [],
        skippedTokenIndexes: [],
        confidence: 0.0,
        recovery: 'none',
        events,
      };
    }

    // 2. Define search window
    const startIndex = Math.max(
      0,
      session.confirmedTokenIndex - this.config.backwardWindowTokens
    );
    const endIndex = Math.min(
      tokens.length,
      session.confirmedTokenIndex + this.config.forwardWindowTokens + spokenWords.length
    );

    const windowTokens = tokens.slice(startIndex, endIndex);
    const matchedTokenIndexes: number[] = [];
    const skippedTokenIndexes: number[] = [];
    let currentSearchCursor = session.confirmedTokenIndex;
    let totalScore = 0;
    let matchCount = 0;

    for (const spokenWord of spokenWords) {
      const remainingWindow = windowTokens.filter(
        (t) => t.index >= currentSearchCursor
      );
      if (remainingWindow.length === 0) break;

      const best = this.matcher.findBestMatchInWindow(
        remainingWindow,
        spokenWord,
        hypothesis.isFinal
          ? this.config.minConfirmedConfidence
          : this.config.minSpeculativeConfidence
      );

      if (best) {
        // If match skipped ahead
        if (best.tokenIndex > currentSearchCursor) {
          const skipCount = best.tokenIndex - currentSearchCursor;
          if (skipCount <= this.config.maxSkipTokens) {
            for (let i = currentSearchCursor; i < best.tokenIndex; i++) {
              if (!skippedTokenIndexes.includes(i) && !matchedTokenIndexes.includes(i)) {
                skippedTokenIndexes.push(i);
              }
            }
          }
        }

        matchedTokenIndexes.push(best.tokenIndex);
        currentSearchCursor = best.tokenIndex + 1;
        totalScore += best.similarity;
        matchCount++;
      }
    }

    const avgConfidence = matchCount > 0 ? totalScore / matchCount : 0.0;
    let recovery: RecoveryStrategy = 'none';

    if (matchedTokenIndexes.length === 0) {
      recovery = 'manual_required';
      return {
        nextConfirmedIndex: session.confirmedTokenIndex,
        nextSpeculativeIndex: session.speculativeTokenIndex,
        matchedTokenIndexes: [],
        skippedTokenIndexes: [],
        confidence: 0.0,
        recovery,
        events,
      };
    }

    const highestMatchedIndex = Math.max(...matchedTokenIndexes);

    // Determine recovery mode
    if (skippedTokenIndexes.length > 0) {
      recovery = 'forward_jump';
      events.push({
        type: 'ALIGNMENT_SKIPPED',
        skippedTokenIndexes: [...skippedTokenIndexes],
        jumpTargetIndex: highestMatchedIndex,
        hypothesisSequence: hypothesis.sequence,
        timestampMs: nowMs,
      } as AlignmentSkippedEvent);
    } else if (highestMatchedIndex > session.confirmedTokenIndex) {
      recovery = 'local';
    }

    // 3. Process Final vs Interim hypothesis state transitions
    if (hypothesis.isFinal) {
      // Mark skipped tokens as skipped
      for (const idx of skippedTokenIndexes) {
        const token = tokens[idx];
        if (token && token.status !== 'skipped' && token.status !== 'completed') {
          const prevStatus = token.status;
          this.stateMachine.transition(token, 'skipped');
          events.push({
            type: 'TOKEN_STATUS_CHANGED',
            tokenIndex: token.index,
            previousStatus: prevStatus,
            newStatus: 'skipped',
            reason: 'Jumped ahead in speech',
            timestampMs: nowMs,
          } as TokenStatusChangedEvent);
        }
      }

      // Mark previously confirmed and newly matched tokens up to highest as completed / confirmed
      for (let i = 0; i <= highestMatchedIndex; i++) {
        const token = tokens[i];
        if (!token) continue;

        if (i < highestMatchedIndex) {
          if (token.status !== 'completed' && token.status !== 'skipped') {
            const prevStatus = token.status;
            this.stateMachine.transition(token, 'completed');
            events.push({
              type: 'TOKEN_STATUS_CHANGED',
              tokenIndex: token.index,
              previousStatus: prevStatus,
              newStatus: 'completed',
              timestampMs: nowMs,
            } as TokenStatusChangedEvent);
          }
        } else if (i === highestMatchedIndex) {
          const prevStatus = token.status;
          this.stateMachine.transition(token, 'confirmed');
          token.actualEndMs = hypothesis.endedAtMs;
          token.matchedHypothesisSeq = hypothesis.sequence;
          events.push({
            type: 'TOKEN_STATUS_CHANGED',
            tokenIndex: token.index,
            previousStatus: prevStatus,
            newStatus: 'confirmed',
            timestampMs: nowMs,
          } as TokenStatusChangedEvent);
        }
      }

      events.push({
        type: 'ALIGNMENT_MATCHED',
        matchedTokenIndexes: [...matchedTokenIndexes],
        confidence: avgConfidence,
        recovery,
        hypothesisSequence: hypothesis.sequence,
        isFinal: true,
        timestampMs: nowMs,
      } as AlignmentMatchedEvent);

      return {
        nextConfirmedIndex: highestMatchedIndex + 1,
        nextSpeculativeIndex: undefined,
        matchedTokenIndexes,
        skippedTokenIndexes,
        confidence: avgConfidence,
        recovery,
        events,
      };
    } else {
      // Interim hypothesis: mark upcoming tokens as speculative
      for (const idx of matchedTokenIndexes) {
        const token = tokens[idx];
        if (token && token.status === 'upcoming') {
          const prevStatus = token.status;
          this.stateMachine.transition(token, 'speculative');
          events.push({
            type: 'TOKEN_STATUS_CHANGED',
            tokenIndex: token.index,
            previousStatus: prevStatus,
            newStatus: 'speculative',
            timestampMs: nowMs,
          } as TokenStatusChangedEvent);
        }
      }

      events.push({
        type: 'ALIGNMENT_MATCHED',
        matchedTokenIndexes: [...matchedTokenIndexes],
        confidence: avgConfidence,
        recovery,
        hypothesisSequence: hypothesis.sequence,
        isFinal: false,
        timestampMs: nowMs,
      } as AlignmentMatchedEvent);

      return {
        nextConfirmedIndex: session.confirmedTokenIndex,
        nextSpeculativeIndex: highestMatchedIndex,
        matchedTokenIndexes,
        skippedTokenIndexes,
        confidence: avgConfidence,
        recovery,
        events,
      };
    }
  }
}

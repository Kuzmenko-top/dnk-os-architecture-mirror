/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/domain/events.ts"
# purpose: "Typed Event Contracts for Teleprompter Execution Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { TokenStatus } from './tokens.js';

export type EventType =
  | 'TOKEN_STATUS_CHANGED'
  | 'ALIGNMENT_MATCHED'
  | 'ALIGNMENT_SKIPPED'
  | 'ALIGNMENT_RECOVERY'
  | 'PACING_DRIFT'
  | 'MANUAL_RESET'
  | 'SESSION_STATE_CHANGED'
  | 'SESSION_COMPLETED';

export interface BaseTeleprompterEvent {
  type: EventType;
  timestampMs: number;
}

export interface TokenStatusChangedEvent extends BaseTeleprompterEvent {
  type: 'TOKEN_STATUS_CHANGED';
  tokenIndex: number;
  previousStatus: TokenStatus;
  newStatus: TokenStatus;
  reason?: string;
}

export interface AlignmentMatchedEvent extends BaseTeleprompterEvent {
  type: 'ALIGNMENT_MATCHED';
  matchedTokenIndexes: number[];
  confidence: number;
  recovery: 'none' | 'local' | 'forward_jump' | 'manual_required';
  hypothesisSequence: number;
  isFinal: boolean;
}

export interface AlignmentSkippedEvent extends BaseTeleprompterEvent {
  type: 'ALIGNMENT_SKIPPED';
  skippedTokenIndexes: number[];
  jumpTargetIndex: number;
  hypothesisSequence: number;
}

export interface AlignmentRecoveryEvent extends BaseTeleprompterEvent {
  type: 'ALIGNMENT_RECOVERY';
  strategy: 'none' | 'local' | 'forward_jump' | 'manual_required';
  fromTokenIndex: number;
  toTokenIndex: number;
  reason: string;
}

export interface PacingDriftEvent extends BaseTeleprompterEvent {
  type: 'PACING_DRIFT';
  actualWpm: number;
  targetWpm: number;
  driftPercentage: number;
  estimatedRemainingMs: number;
}

export interface ManualResetEvent extends BaseTeleprompterEvent {
  type: 'MANUAL_RESET';
  previousIndex: number;
  targetIndex: number;
  reason?: string;
}

export interface SessionStateChangedEvent extends BaseTeleprompterEvent {
  type: 'SESSION_STATE_CHANGED';
  previousStatus: string;
  newStatus: string;
}

export interface SessionCompletedEvent extends BaseTeleprompterEvent {
  type: 'SESSION_COMPLETED';
  durationMs: number;
  spokenWordsCount: number;
  totalTokensCount: number;
  adherenceScore: number;
}

export type TeleprompterEvent =
  | TokenStatusChangedEvent
  | AlignmentMatchedEvent
  | AlignmentSkippedEvent
  | AlignmentRecoveryEvent
  | PacingDriftEvent
  | ManualResetEvent
  | SessionStateChangedEvent
  | SessionCompletedEvent;

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/domain/session.ts"
# purpose: "Teleprompter Session State Models and Contracts."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export type SessionStatus =
  | 'idle'
  | 'running'
  | 'paused'
  | 'completed'
  | 'error';

export interface TeleprompterSession {
  sessionId: string;
  scriptId: string;
  scriptVersion: string;
  prosodyVersion: string;
  status: SessionStatus;
  currentTokenIndex: number;
  confirmedTokenIndex: number;
  speculativeTokenIndex?: number;
  startedAtMs?: number;
  pausedAtMs?: number;
  completedAtMs?: number;
  updatedAtMs: number;
  totalTokens: number;
  lastProcessedHypothesisSequence: number;
}

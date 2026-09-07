/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/state/token-state.ts"
# purpose: "Deterministic Word Token State Machine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RuntimeToken, TokenStatus } from '../domain/tokens.js';
import { InvalidStateTransitionError } from '../errors/errors.js';

const VALID_TRANSITIONS: Record<TokenStatus, Set<TokenStatus>> = {
  upcoming: new Set(['speculative', 'confirmed', 'completed', 'skipped', 'manual_reset']),
  speculative: new Set(['upcoming', 'confirmed', 'completed', 'skipped', 'manual_reset']),
  confirmed: new Set(['completed', 'upcoming', 'manual_reset', 'skipped']),
  completed: new Set(['upcoming', 'manual_reset']),
  skipped: new Set(['upcoming', 'speculative', 'confirmed', 'manual_reset']),
  manual_reset: new Set(['upcoming', 'speculative', 'confirmed']),
};

export class TokenStateMachine {
  /**
   * Validates if transition is allowed
   */
  canTransition(currentStatus: TokenStatus, nextStatus: TokenStatus): boolean {
    if (currentStatus === nextStatus) return true;
    const allowed = VALID_TRANSITIONS[currentStatus];
    return allowed ? allowed.has(nextStatus) : false;
  }

  /**
   * Applies transition to a RuntimeToken with strict verification
   */
  transition(token: RuntimeToken, nextStatus: TokenStatus): RuntimeToken {
    if (token.status === nextStatus) return token;

    if (!this.canTransition(token.status, nextStatus)) {
      throw new InvalidStateTransitionError(
        token.status,
        nextStatus,
        `Token index ${token.index} (${token.word})`
      );
    }

    token.status = nextStatus;
    return token;
  }
}

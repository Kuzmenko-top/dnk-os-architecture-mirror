/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/pacing/wpm.ts"
# purpose: "WPM Controller, Prosody Pause Compensation, and Pacing Calculator."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RuntimeToken } from '../domain/tokens.js';

export interface PacingMetrics {
  targetWpm: number;
  actualWpm: number;
  targetDurationMs: number;
  adjustedDurationMs: number;
  elapsedMs: number;
  estimatedRemainingMs: number;
  driftPercentage: number;
  totalPauseCompensationMs: number;
}

export class WPMController {
  private targetWpm: number;
  private manualSpeedMultiplier = 1.0;

  constructor(targetWpm = 140) {
    this.targetWpm = targetWpm;
  }

  setTargetWpm(wpm: number): void {
    if (wpm > 0) this.targetWpm = wpm;
  }

  setManualMultiplier(multiplier: number): void {
    if (multiplier > 0.1 && multiplier < 5.0) {
      this.manualSpeedMultiplier = multiplier;
    }
  }

  getEffectiveTargetWpm(): number {
    return Math.round(this.targetWpm * this.manualSpeedMultiplier);
  }

  /**
   * Computes estimated target and adjusted duration with pause/hold compensation
   */
  calculateTargetDurations(tokens: RuntimeToken[]): {
    targetDurationMs: number;
    adjustedDurationMs: number;
    totalPauseCompensationMs: number;
  } {
    const wordCount = tokens.length;
    const effectiveWpm = this.getEffectiveTargetWpm();
    const baseDurationMs = Math.round((wordCount / effectiveWpm) * 60000);

    let totalPauseCompensationMs = 0;
    for (const token of tokens) {
      if (token.prosody?.pauseAfterMs) {
        totalPauseCompensationMs += token.prosody.pauseAfterMs;
      }
      if (token.prosody?.emphasis === 'hold' || token.prosody?.emphasis === 'stretched') {
        totalPauseCompensationMs += 300; // 300ms hold/stretched emphasis bonus
      }
    }

    return {
      targetDurationMs: baseDurationMs,
      adjustedDurationMs: baseDurationMs + totalPauseCompensationMs,
      totalPauseCompensationMs,
    };
  }

  /**
   * Computes current pacing metrics based on elapsed time and confirmed tokens
   */
  computePacingMetrics(
    tokens: RuntimeToken[],
    confirmedTokenIndex: number,
    elapsedMs: number
  ): PacingMetrics {
    const durations = this.calculateTargetDurations(tokens);
    const spokenWords = Math.min(confirmedTokenIndex, tokens.length);
    const effectiveWpm = this.getEffectiveTargetWpm();

    let actualWpm = effectiveWpm;
    if (elapsedMs > 2000 && spokenWords > 0) {
      actualWpm = Math.round((spokenWords / elapsedMs) * 60000);
    }

    const driftPercentage =
      effectiveWpm > 0
        ? Math.round(((actualWpm - effectiveWpm) / effectiveWpm) * 100)
        : 0;

    const remainingTokens = tokens.slice(confirmedTokenIndex);
    const remainingDurations = this.calculateTargetDurations(remainingTokens);

    let estimatedRemainingMs = remainingDurations.adjustedDurationMs;
    if (actualWpm > 0 && remainingTokens.length > 0) {
      estimatedRemainingMs = Math.round(
        (remainingTokens.length / actualWpm) * 60000 +
          remainingDurations.totalPauseCompensationMs
      );
    }

    return {
      targetWpm: effectiveWpm,
      actualWpm,
      targetDurationMs: durations.targetDurationMs,
      adjustedDurationMs: durations.adjustedDurationMs,
      elapsedMs,
      estimatedRemainingMs,
      driftPercentage,
      totalPauseCompensationMs: durations.totalPauseCompensationMs,
    };
  }
}

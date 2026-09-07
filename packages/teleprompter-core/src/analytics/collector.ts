/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/analytics/collector.ts"
# purpose: "Session Analytics Collector and Adherence Score Aggregator."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RuntimeToken } from '../domain/tokens.js';
import { TeleprompterSession } from '../domain/session.js';
import { TeleprompterEvent } from '../domain/events.js';

export interface SessionAnalytics {
  sessionId: string;
  scriptId: string;
  scriptVersion: string;
  prosodyVersion: string;
  totalDurationMs: number;
  spokenWordCount: number;
  scriptWordCount: number;
  actualWpm: number;
  targetWpm: number;
  adherenceScore: number;
  adherenceNote: string;
  alignmentConfidence: number;
  skippedTokenCount: number;
  recoveryCount: number;
  manualResetCount: number;
  pauseCount: number;
  longestPauseMs: number;
  completedAtIso: string;
}

export class SessionAnalyticsCollector {
  private manualResetCount = 0;
  private recoveryCount = 0;
  private confidenceSamples: number[] = [];
  private pauseTimestamps: { startMs: number; durationMs: number }[] = [];
  private lastSpokenTimestampMs?: number;

  recordEvent(event: TeleprompterEvent): void {
    if (event.type === 'MANUAL_RESET') {
      this.manualResetCount++;
    } else if (
      event.type === 'ALIGNMENT_RECOVERY' ||
      (event.type === 'ALIGNMENT_MATCHED' && event.recovery !== 'none')
    ) {
      this.recoveryCount++;
    } else if (event.type === 'ALIGNMENT_MATCHED') {
      this.confidenceSamples.push(event.confidence);

      if (this.lastSpokenTimestampMs) {
        const gapMs = event.timestampMs - this.lastSpokenTimestampMs;
        if (gapMs > 1200) {
          // Pause detected (> 1.2s silence/gap)
          this.pauseTimestamps.push({
            startMs: this.lastSpokenTimestampMs,
            durationMs: gapMs,
          });
        }
      }
      this.lastSpokenTimestampMs = event.timestampMs;
    }
  }

  compile(
    session: TeleprompterSession,
    tokens: RuntimeToken[],
    targetWpm: number,
    nowMs: number = Date.now()
  ): SessionAnalytics {
    const startedAtMs = session.startedAtMs || nowMs;
    const completedAtMs = session.completedAtMs || nowMs;
    const totalDurationMs = Math.max(1000, completedAtMs - startedAtMs);

    let completedCount = 0;
    let skippedCount = 0;

    for (const t of tokens) {
      if (t.status === 'completed' || t.status === 'confirmed') {
        completedCount++;
      } else if (t.status === 'skipped') {
        skippedCount++;
      }
    }

    const scriptWordCount = tokens.length;
    const spokenWordCount = completedCount;

    // Adherence score: measures script fidelity / exact tracking (not speech eloquence)
    const adherenceScore =
      scriptWordCount > 0
        ? Number(
            Math.max(
              0,
              Math.min(1.0, (spokenWordCount - skippedCount * 0.5) / scriptWordCount)
            ).toFixed(3)
          )
        : 1.0;

    const actualWpm =
      totalDurationMs > 0
        ? Math.round((spokenWordCount / totalDurationMs) * 60000)
        : targetWpm;

    const avgConfidence =
      this.confidenceSamples.length > 0
        ? Number(
            (
              this.confidenceSamples.reduce((a, b) => a + b, 0) /
              this.confidenceSamples.length
            ).toFixed(3)
          )
        : 1.0;

    const longestPauseMs =
      this.pauseTimestamps.length > 0
        ? Math.max(...this.pauseTimestamps.map((p) => p.durationMs))
        : 0;

    return {
      sessionId: session.sessionId,
      scriptId: session.scriptId,
      scriptVersion: session.scriptVersion,
      prosodyVersion: session.prosodyVersion,
      totalDurationMs,
      spokenWordCount,
      scriptWordCount,
      actualWpm,
      targetWpm,
      adherenceScore,
      adherenceNote:
        'Adherence score measures script fidelity and prompt tracking, not rhetorical or speech performance quality.',
      alignmentConfidence: avgConfidence,
      skippedTokenCount: skippedCount,
      recoveryCount: this.recoveryCount,
      manualResetCount: this.manualResetCount,
      pauseCount: this.pauseTimestamps.length,
      longestPauseMs,
      completedAtIso: new Date(completedAtMs).toISOString(),
    };
  }
}

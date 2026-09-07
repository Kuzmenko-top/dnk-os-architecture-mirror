import { describe, it, expect } from 'vitest';
import { WPMController } from '../../src/pacing/wpm.js';
import { SessionAnalyticsCollector } from '../../src/analytics/collector.js';
import { RuntimeToken } from '../../src/domain/tokens.js';
import { TeleprompterSession } from '../../src/domain/session.js';

describe('WPMController', () => {
  const controller = new WPMController(120);

  it('should calculate adjusted duration with pause and hold emphasis compensation', () => {
    const tokens: RuntimeToken[] = [
      {
        index: 0,
        word: 'Слово1',
        normalizedWord: 'слово1',
        sceneId: 's1',
        paragraphId: 'p1',
        status: 'upcoming',
        estimatedStartMs: 0,
        estimatedEndMs: 500,
        prosody: { pauseAfterMs: 500, emphasis: 'none' },
      },
      {
        index: 1,
        word: 'Слово2',
        normalizedWord: 'слово2',
        sceneId: 's1',
        paragraphId: 'p1',
        status: 'upcoming',
        estimatedStartMs: 500,
        estimatedEndMs: 1000,
        prosody: { emphasis: 'hold' },
      },
    ];

    const durations = controller.calculateTargetDurations(tokens);
    // Base duration for 2 words at 120 WPM = (2 / 120) * 60000 = 1000ms
    expect(durations.targetDurationMs).toBe(1000);
    // Pause compensation: 500ms + 300ms (hold) = 800ms
    expect(durations.totalPauseCompensationMs).toBe(800);
    expect(durations.adjustedDurationMs).toBe(1800);
  });
});

describe('SessionAnalyticsCollector', () => {
  it('should compile session analytics with adherence score', () => {
    const collector = new SessionAnalyticsCollector();
    const session: TeleprompterSession = {
      sessionId: 'sess-test',
      scriptId: 'scr-1',
      scriptVersion: 'script.v1',
      prosodyVersion: 'prosody.v1',
      status: 'completed',
      currentTokenIndex: 10,
      confirmedTokenIndex: 10,
      startedAtMs: 10000,
      completedAtMs: 16000, // 6 seconds
      updatedAtMs: 16000,
      totalTokens: 10,
      lastProcessedHypothesisSequence: 10,
    };

    const tokens: RuntimeToken[] = Array.from({ length: 10 }).map((_, i) => ({
      index: i,
      word: `w${i}`,
      normalizedWord: `w${i}`,
      sceneId: 's1',
      paragraphId: 'p1',
      status: i === 5 ? 'skipped' : 'completed',
      estimatedStartMs: i * 500,
      estimatedEndMs: (i + 1) * 500,
    }));

    const analytics = collector.compile(session, tokens, 100, 16000);
    expect(analytics.sessionId).toBe('sess-test');
    expect(analytics.scriptWordCount).toBe(10);
    expect(analytics.spokenWordCount).toBe(9);
    expect(analytics.skippedTokenCount).toBe(1);
    expect(analytics.adherenceScore).toBeGreaterThan(0.8);
    expect(analytics.adherenceNote).toContain('Adherence score measures script fidelity');
  });
});

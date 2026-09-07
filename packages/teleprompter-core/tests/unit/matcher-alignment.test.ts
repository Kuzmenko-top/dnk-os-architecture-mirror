import { describe, it, expect } from 'vitest';
import { WordMatcher } from '../../src/alignment/matcher.js';
import { AlignmentEngine } from '../../src/alignment/engine.js';
import { RuntimeToken } from '../../src/domain/tokens.js';
import { TeleprompterSession } from '../../src/domain/session.js';
import { ASRHypothesis } from '../../src/ports/asr.js';

describe('WordMatcher', () => {
  const matcher = new WordMatcher();

  it('should match identical words with 1.0 score', () => {
    const token: RuntimeToken = {
      index: 0,
      word: 'Відео',
      normalizedWord: 'відео',
      sceneId: 's1',
      paragraphId: 'p1',
      status: 'upcoming',
      estimatedStartMs: 0,
      estimatedEndMs: 500,
    };

    const match = matcher.matchTokenWithWord(token, 'відео');
    expect(match.isMatch).toBe(true);
    expect(match.score).toBe(1.0);
  });
});

describe('AlignmentEngine', () => {
  const engine = new AlignmentEngine();

  const makeTokens = (words: string[]): RuntimeToken[] =>
    words.map((w, idx) => ({
      index: idx,
      word: w,
      normalizedWord: w.toLowerCase().replace(/[^a-zа-яіїєґ0-9']/gi, ''),
      sceneId: 's1',
      paragraphId: 'p1',
      status: 'upcoming',
      estimatedStartMs: idx * 400,
      estimatedEndMs: (idx + 1) * 400,
    }));

  it('should update speculative status on interim hypotheses and confirm on final', () => {
    const tokens = makeTokens(['привіт', 'сьогодні', 'ми', 'говоримо', 'про', 'ai']);
    const session: TeleprompterSession = {
      sessionId: 'sess-1',
      scriptId: 'scr-1',
      scriptVersion: 'script.v1',
      prosodyVersion: 'prosody.v1',
      status: 'running',
      currentTokenIndex: 0,
      confirmedTokenIndex: 0,
      updatedAtMs: 1000,
      totalTokens: tokens.length,
      lastProcessedHypothesisSequence: 0,
    };

    // Interim hypothesis
    const interimHyp: ASRHypothesis = {
      sequence: 1,
      text: 'привіт сьогодні',
      isFinal: false,
      startedAtMs: 1000,
      endedAtMs: 1800,
    };

    const interimResult = engine.align(interimHyp, tokens, session, 1800);
    expect(interimResult.matchedTokenIndexes).toContain(0);
    expect(interimResult.matchedTokenIndexes).toContain(1);
    expect(tokens[0].status).toBe('speculative');
    expect(tokens[1].status).toBe('speculative');

    // Final hypothesis
    const finalHyp: ASRHypothesis = {
      sequence: 2,
      text: 'привіт сьогодні',
      isFinal: true,
      startedAtMs: 1000,
      endedAtMs: 2000,
    };

    const finalResult = engine.align(finalHyp, tokens, session, 2000);
    expect(finalResult.matchedTokenIndexes).toContain(0);
    expect(finalResult.matchedTokenIndexes).toContain(1);
    expect(tokens[0].status).toBe('completed');
    expect(tokens[1].status).toBe('confirmed');
    expect(finalResult.nextConfirmedIndex).toBe(2);
  });

  it('should ignore duplicate or out-of-order hypothesis sequence', () => {
    const tokens = makeTokens(['один', 'два', 'три']);
    const session: TeleprompterSession = {
      sessionId: 'sess-1',
      scriptId: 'scr-1',
      scriptVersion: 'script.v1',
      prosodyVersion: 'prosody.v1',
      status: 'running',
      currentTokenIndex: 0,
      confirmedTokenIndex: 0,
      updatedAtMs: 1000,
      totalTokens: tokens.length,
      lastProcessedHypothesisSequence: 5,
    };

    const staleHyp: ASRHypothesis = {
      sequence: 4, // Stale!
      text: 'один',
      isFinal: true,
      startedAtMs: 1000,
      endedAtMs: 1500,
    };

    const result = engine.align(staleHyp, tokens, session, 1500);
    expect(result.matchedTokenIndexes.length).toBe(0);
    expect(tokens[0].status).toBe('upcoming');
  });
});

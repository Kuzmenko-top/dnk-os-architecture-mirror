/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/alignment/matcher.ts"
# purpose: "Word & Phrase Matcher with Ukrainian & Multi-lingual Tolerance."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RuntimeToken } from '../domain/tokens.js';
import { DefaultTextNormalizer, TextNormalizerPort } from '../ports/normalizer.js';

export interface MatchScore {
  tokenIndex: number;
  similarity: number;
  isExact: boolean;
  matchedHypothesisWord: string;
}

export class WordMatcher {
  private readonly normalizer: TextNormalizerPort;

  constructor(normalizer?: TextNormalizerPort) {
    this.normalizer = normalizer || new DefaultTextNormalizer();
  }

  /**
   * Evaluates match between a script token and a single candidate spoken word
   */
  evaluateWordMatch(token: RuntimeToken, spokenWord: string): MatchScore {
    const normSpoken = this.normalizer.normalize(spokenWord);
    const normToken = token.normalizedWord;

    if (normToken === normSpoken) {
      return {
        tokenIndex: token.index,
        similarity: 1.0,
        isExact: true,
        matchedHypothesisWord: spokenWord,
      };
    }

    const similarity = this.normalizer.similarityScore(normToken, normSpoken);
    return {
      tokenIndex: token.index,
      similarity,
      isExact: similarity >= 0.99,
      matchedHypothesisWord: spokenWord,
    };
  }

  /**
   * Finds the best matching candidate inside a window of tokens for a spoken word
   */
  matchTokenWithWord(token: RuntimeToken, spokenWord: string, threshold = 0.7): { isMatch: boolean; score: number } {
    const evaluated = this.evaluateWordMatch(token, spokenWord);
    return {
      isMatch: evaluated.similarity >= threshold,
      score: evaluated.similarity,
    };
  }

  findBestMatchInWindow(
    tokens: RuntimeToken[],
    spokenWord: string,
    minThreshold = 0.7
  ): MatchScore | null {
    let bestScore: MatchScore | null = null;

    for (const token of tokens) {
      const score = this.evaluateWordMatch(token, spokenWord);
      if (score.similarity >= minThreshold) {
        if (!bestScore || score.similarity > bestScore.similarity) {
          bestScore = score;
          if (score.isExact) break; // early exit on exact match
        }
      }
    }

    return bestScore;
  }
}

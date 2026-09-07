/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/teleprompter-core/src/ports/normalizer.ts"
# purpose: "Text Normalization Port and Ukrainian/Multilingual Matcher Implementation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface TextNormalizerPort {
  normalize(text: string): string;
  tokenize(text: string): string[];
  similarityScore(wordA: string, wordB: string): number;
  areFuzzyEqual(wordA: string, wordB: string, threshold?: number): boolean;
}

export class DefaultTextNormalizer implements TextNormalizerPort {
  /**
   * Normalizes input text:
   * - standardizes various apostrophes (' / ’ / ʼ / `) to canonical '
   * - strips punctuation except apostrophes within words
   * - standardizes Cyrillic 'е' / 'ё' / 'є' / 'і' / 'ї'
   * - lowercases and collapses excessive whitespaces
   */
  normalize(text: string): string {
    if (!text) return '';
    return text
      .toLowerCase()
      .replace(/[’ʼ`´]/g, "'") // unify apostrophes
      .replace(/[.,\/#!$%\^&\*;:{}=\-_~()?"«»—–\n\r\t]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Splits normalized text into individual word tokens
   */
  tokenize(text: string): string[] {
    const norm = this.normalize(text);
    if (!norm) return [];
    return norm.split(' ').filter((w) => w.length > 0);
  }

  /**
   * Computes normalized Levenshtein similarity score between 0.0 and 1.0
   */
  similarityScore(wordA: string, wordB: string): number {
    const a = this.normalize(wordA);
    const b = this.normalize(wordB);

    if (a === b) return 1.0;
    if (a.length === 0 || b.length === 0) return 0.0;

    const distance = this.levenshteinDistance(a, b);
    const maxLength = Math.max(a.length, b.length);
    let score = Math.max(0.0, 1.0 - distance / maxLength);

    // Common stem prefix bonus for inflected forms (e.g. Ukrainian verbs and cases)
    let commonPrefix = 0;
    const minLength = Math.min(a.length, b.length);
    while (commonPrefix < minLength && a[commonPrefix] === b[commonPrefix]) {
      commonPrefix++;
    }

    if (commonPrefix >= 4 && commonPrefix >= minLength * 0.65) {
      score = Math.max(score, 0.75 + (commonPrefix / maxLength) * 0.2);
    }

    return Math.min(1.0, score);
  }

  /**
   * Checks if two words match fuzzy threshold (default 0.70)
   */
  areFuzzyEqual(wordA: string, wordB: string, threshold = 0.70): boolean {
    return this.similarityScore(wordA, wordB) >= threshold;
  }

  private levenshteinDistance(s1: string, s2: string): number {
    const m = s1.length;
    const n = s2.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () =>
      Array(n + 1).fill(0)
    );

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        const cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1, // deletion
          dp[i][j - 1] + 1, // insertion
          dp[i - 1][j - 1] + cost // substitution
        );
      }
    }

    return dp[m][n];
  }
}

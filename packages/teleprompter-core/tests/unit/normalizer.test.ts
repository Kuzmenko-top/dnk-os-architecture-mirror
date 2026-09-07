import { describe, it, expect } from 'vitest';
import { DefaultTextNormalizer } from '../../src/ports/normalizer.js';

describe('DefaultTextNormalizer', () => {
  const normalizer = new DefaultTextNormalizer();

  it('should normalize punctuation, cases and whitespace', () => {
    const text = '  Привіт, світе! Як твої справи? -- Добре...  ';
    const normalized = normalizer.normalize(text);
    expect(normalized).toBe('привіт світе як твої справи добре');
  });

  it('should unify different Ukrainian apostrophe characters', () => {
    const text1 = "п'ять";
    const text2 = 'п’ять';
    const text3 = 'пʼять';
    const text4 = 'п`ять';

    expect(normalizer.normalize(text1)).toBe("п'ять");
    expect(normalizer.normalize(text2)).toBe("п'ять");
    expect(normalizer.normalize(text3)).toBe("п'ять");
    expect(normalizer.normalize(text4)).toBe("п'ять");
  });

  it('should compute Levenshtein similarity score accurately', () => {
    expect(normalizer.similarityScore('телефон', 'телефон')).toBe(1.0);
    expect(normalizer.similarityScore('суфлер', 'суфлером')).toBeGreaterThan(0.7);
    expect(normalizer.similarityScore('привіт', 'допобачення')).toBeLessThan(0.3);
  });

  it('should evaluate fuzzy equality', () => {
    expect(normalizer.areFuzzyEqual('суфлер', 'суфлер!')).toBe(true);
    expect(normalizer.areFuzzyEqual('зливають', 'зливає')).toBe(true);
    expect(normalizer.areFuzzyEqual('камера', 'мікрофон')).toBe(false);
  });
});

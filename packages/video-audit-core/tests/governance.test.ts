/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/governance.test.ts"
# purpose: "Unit Tests for Evidence Classification & Similarity Risk Policy Governance."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  evaluateSimilarityRisk,
  createEvidenceItem,
  validateEvidenceConfidence,
} from '../src/index.js';

describe('Similarity Risk Governance Policy', () => {
  it('should allow high structural similarity without flagging plagiarism', () => {
    const report = evaluateSimilarityRisk({
      lexical: 0.05,
      structural: 0.92, // high structural transfer intended
      visual: 0.1,
      audio: 0.0,
      brand: 0.0,
    });

    expect(report.overallRisk).toBe('low');
    expect(report.notes.some(n => n.includes('Structural storytelling mechanism preserved'))).toBe(true);
  });

  it('should escalate to critical_plagiarism when lexical similarity is too high', () => {
    const report = evaluateSimilarityRisk({
      lexical: 0.88,
      structural: 0.90,
      visual: 0.2,
      audio: 0.0,
      brand: 0.0,
    });

    expect(report.overallRisk).toBe('critical_plagiarism');
  });

  it('should flag high brand element overlap as high risk', () => {
    const report = evaluateSimilarityRisk({
      lexical: 0.1,
      structural: 0.5,
      visual: 0.1,
      audio: 0.0,
      brand: 0.45,
    });

    expect(report.overallRisk).toBe('high');
  });
});

describe('Evidence Governance & Classification', () => {
  it('should classify deterministic measurements as observed', () => {
    const item = createEvidenceItem({
      id: 'ev-test-1',
      claim: 'Hook duration is 3.0s',
      confidence: 0.95,
      source: 'whisperx',
    });

    expect(item.type).toBe('observed');
  });

  it('should enforce confidence bounds validation', () => {
    expect(() => validateEvidenceConfidence(1.5)).toThrow();
    expect(() => validateEvidenceConfidence(-0.1)).toThrow();
    expect(validateEvidenceConfidence(0.85)).toBe(0.85);
  });
});

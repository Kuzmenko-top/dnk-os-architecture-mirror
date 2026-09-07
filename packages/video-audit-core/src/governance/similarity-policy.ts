/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/governance/similarity-policy.ts"
# purpose: "Similarity Risk Calculation and Governance Policy Engine."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { SimilarityReport, OverallSimilarityRisk } from '../schemas/similarity.js';

export interface SimilarityScores {
  lexical: number;
  structural: number;
  visual: number;
  audio: number;
  brand: number;
  notes?: string[];
}

export function evaluateSimilarityRisk(scores: SimilarityScores): SimilarityReport {
  const lexical = Math.max(0, Math.min(1, scores.lexical));
  const structural = Math.max(0, Math.min(1, scores.structural));
  const visual = Math.max(0, Math.min(1, scores.visual));
  const audio = Math.max(0, Math.min(1, scores.audio));
  const brand = Math.max(0, Math.min(1, scores.brand));

  const notes: string[] = [...(scores.notes || [])];

  let overallRisk: OverallSimilarityRisk = 'low';

  // Rule 1: High structural similarity is intended for format mechanism transfer
  if (structural > 0.7) {
    notes.push('Structural storytelling mechanism preserved from reference.');
  }

  // Rule 2: Lexical risk evaluation
  if (lexical >= 0.85) {
    overallRisk = 'critical_plagiarism';
    notes.push('CRITICAL: High lexical overlap detected. Verbatim script copying forbidden.');
  } else if (lexical >= 0.6) {
    overallRisk = 'high';
    notes.push('HIGH: Significant phrasing similarity. Paraphrasing required.');
  } else if (lexical >= 0.35) {
    if (overallRisk === 'low') overallRisk = 'medium';
    notes.push('MEDIUM: Moderate text similarity.');
  }

  // Rule 3: Brand infringement risk
  if (brand >= 0.3) {
    if (overallRisk !== 'critical_plagiarism') overallRisk = 'high';
    notes.push('HIGH: Trademark or brand element similarity detected.');
  }

  // Rule 4: Visual / Audio risk
  if (visual >= 0.8 || audio >= 0.8) {
    if (overallRisk !== 'critical_plagiarism') overallRisk = 'high';
    notes.push('HIGH: Direct visual frame sequence or audio track reuse detected.');
  } else if ((visual >= 0.5 || audio >= 0.5) && overallRisk === 'low') {
    overallRisk = 'medium';
  }

  return {
    overallRisk,
    lexical,
    structural,
    visual,
    audio,
    brand,
    notes,
  };
}

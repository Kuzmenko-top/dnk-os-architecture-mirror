/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/similarity.ts"
# purpose: "Similarity Report & Copyright/Plagiarism Risk Zod Schemas."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const OverallSimilarityRiskSchema = z.enum(['low', 'medium', 'high', 'critical_plagiarism']);
export type OverallSimilarityRisk = z.infer<typeof OverallSimilarityRiskSchema>;

export const SimilarityReportSchema = z.object({
  overallRisk: OverallSimilarityRiskSchema,
  lexical: z.number().min(0).max(1),
  structural: z.number().min(0).max(1),
  visual: z.number().min(0).max(1),
  audio: z.number().min(0).max(1),
  brand: z.number().min(0).max(1),
  notes: z.array(z.string()).default([]),
});

export type SimilarityReport = z.infer<typeof SimilarityReportSchema>;

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/adaptation.ts"
# purpose: "Niche Adaptation Request, Result (adaptation.v1) and Compliance Contracts."
# canonical_source: true
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { EvidenceItemSchema } from './audit.js';
import { ScriptDocumentSchema } from './script.js';
import { ProsodyDocumentSchema } from './prosody.js';
import { ShotListSchema } from './shotlist.js';
import { SimilarityReportSchema } from './similarity.js';
import { BrandComplianceReportSchema } from './brand.js';

export const AdaptationStatusSchema = z.enum([
  'accepted',
  'manual_review',
  'rejected',
]);

export type AdaptationStatus = z.infer<typeof AdaptationStatusSchema>;

export const AdaptationRequestSchema = z.object({
  schemaVersion: z.literal('adaptation-request.v1').default('adaptation-request.v1'),
  sourceAuditId: z.string().min(1),
  brandId: z.string().min(1),
  niche: z.string().min(1),
  audience: z.string().min(1),
  language: z.string().default('uk'),
  targetDurationMs: z.number().positive(),
  tone: z.string().default('professional_expert'),
  desiredMechanisms: z.array(z.string()).default([]),
  ctaType: z.string().optional(),
  forbiddenElements: z.array(z.string()).default([]),
  approvedFactIds: z.array(z.string()).default([]),
});

export type AdaptationRequest = z.infer<typeof AdaptationRequestSchema>;

export const AdaptationResultSchema = z.object({
  schemaVersion: z.literal('adaptation.v1'),
  id: z.string(),
  sourceAuditId: z.string(),
  requestId: z.string().default('req-default'),
  createdAt: z.string().default(() => new Date().toISOString()),
  script: ScriptDocumentSchema,
  prosody: ProsodyDocumentSchema,
  shotList: ShotListSchema,
  preservedMechanisms: z.array(z.string()).default([]),
  changedElements: z.array(z.string()).default([]),
  similarity: SimilarityReportSchema,
  brandCompliance: BrandComplianceReportSchema.default({
    status: 'compliant',
    usedFactIds: [],
    unverifiedClaims: [],
    forbiddenViolations: [],
    commercialViolations: [],
    toneScore: 1.0,
    notes: [],
  }),
  status: AdaptationStatusSchema.default('accepted'),
  warnings: z.array(z.string()).default([]),
  adaptationRationale: z.string().optional(),
  evidence: z.array(EvidenceItemSchema).default([]),
});

export type AdaptationResult = z.infer<typeof AdaptationResultSchema>;

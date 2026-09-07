/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn/types.ts"
# purpose: "Type definitions and Zod schemas for versioned ReBurn Audit Fixtures & Manifests."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { ReferenceAssetSchema } from '../../schemas/reference.js';
export type ReferenceAsset = z.infer<typeof ReferenceAssetSchema>;
import { MultimodalAuditResult } from '../../schemas/multimodal-audit.js';
import { TranscriptDocument } from '../../pipeline/domain/transcription/transcript.js';
import { SceneDocument } from '../../pipeline/domain/analyzers/scenes.js';
import { OCRDocument } from '../../pipeline/domain/analyzers/ocr.js';
import { AudioFeaturesDocument } from '../../pipeline/domain/analyzers/audio-features.js';
import { MultimodalEvidenceDocument } from '../../pipeline/domain/analyzers/multimodal-evidence.js';

export const FixtureCategorySchema = z.enum([
  'product_demo',
  'workshop_talking_head',
  'before_after',
  'educational_listicle',
  'founder_story',
  'technical_explainer',
  'offer_cta',
  'no_audio',
  'no_ocr',
  'fast_paced_short',
  'manual_review'
]);

export type FixtureCategory = z.infer<typeof FixtureCategorySchema>;

export const FixtureCoverageTypeSchema = z.enum(['full', 'partial', 'degraded', 'manual_review']);
export type FixtureCoverageType = z.infer<typeof FixtureCoverageTypeSchema>;

export const ExpectedClaimAssertionSchema = z.object({
  id: z.string(),
  textSnippet: z.string(),
  role: z.enum(['hook', 'core', 'cta', 'technical', 'retention']),
  classification: z.enum(['observed', 'inferred', 'hypothesized']),
  requiresEvidenceRefs: z.boolean().default(true)
});

export type ExpectedClaimAssertion = z.infer<typeof ExpectedClaimAssertionSchema>;

export const ReBurnFixtureManifestSchema = z.object({
  fixtureId: z.string(),
  version: z.string().default('v1.0'),
  category: FixtureCategorySchema,
  title: z.string(),
  language: z.literal('uk-UA').default('uk-UA'),
  durationMs: z.number().positive(),
  coverageType: FixtureCoverageTypeSchema,
  expectedScenes: z.number().int().nonnegative(),
  expectedOcrTerms: z.array(z.string()).default([]),
  expectedTechnicalTerms: z.array(z.string()).default([]),
  expectedClaims: z.array(ExpectedClaimAssertionSchema).default([]),
  knownUncertainties: z.array(z.string()).default([]),
  expectedAggregateStatus: z.enum(['READY', 'DEGRADED', 'NEEDS_REVIEW']),
  invariants: z.object({
    hookMustStartNearZero: z.boolean().default(true),
    viralityNeverObservedWithoutEngagement: z.boolean().default(true),
    noHallucinatedIds: z.boolean().default(true),
    allowEmptyTranscript: z.boolean().default(false),
    allowEmptyOcr: z.boolean().default(false)
  })
});

export type ReBurnFixtureManifest = z.infer<typeof ReBurnFixtureManifestSchema>;

export interface ReBurnFixtureData {
  manifest: ReBurnFixtureManifest;
  referenceAsset: ReferenceAsset;
  transcript?: TranscriptDocument;
  scenes?: SceneDocument;
  ocr?: OCRDocument;
  audioFeatures?: AudioFeaturesDocument;
  multimodalEvidence?: MultimodalEvidenceDocument;
  multimodalAudit: MultimodalAuditResult;
}

export interface SemanticAssertionViolation {
  code: string;
  message: string;
  context?: Record<string, unknown>;
}

export interface SemanticAssertionResult {
  valid: boolean;
  fixtureId: string;
  violations: SemanticAssertionViolation[];
}

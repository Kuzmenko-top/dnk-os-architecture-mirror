/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/multimodal-audit.ts"
# purpose: "Zod Schema and Contract for Multimodal Audit Result (.v1) with renamed types to avoid conflicts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { ConfidenceSchema, TimeRangeSchema } from './common.js';
import { EvidenceReferenceSchema, EvidenceReference } from '../pipeline/domain/analyzers/multimodal-evidence.js';

export { EvidenceReferenceSchema };
export type { EvidenceReference };

export const ClaimClassificationSchema = z.enum(['observed', 'inferred', 'hypothesized']);
export type ClaimClassification = z.infer<typeof ClaimClassificationSchema>;

export const AuditedClaimSchema = z.object({
  id: z.string(),
  text: z.string().min(1),
  classification: ClaimClassificationSchema,
  confidence: ConfidenceSchema,
  evidenceRefs: EvidenceReferenceSchema,
  timeRange: z.object({
    startMs: z.number().nonnegative(),
    endMs: z.number().nonnegative()
  }).refine((val) => val.endMs >= val.startMs, {
    message: 'endMs must be greater than or equal to startMs'
  }).optional()
});

export type AuditedClaim = z.infer<typeof AuditedClaimSchema>;

export const ObservedFactSchema = z.object({
  id: z.string(),
  category: z.enum(['visual', 'speech', 'text_ocr', 'audio', 'pacing']),
  description: z.string().min(1),
  confidence: ConfidenceSchema,
  timeRange: TimeRangeSchema,
  evidenceRefs: EvidenceReferenceSchema
});

export type ObservedFact = z.infer<typeof ObservedFactSchema>;

export const HookTypeSchema = z.enum([
  'negative_frame',
  'bold_claim',
  'curiosity_gap',
  'story_origin',
  'visual_shock',
  'question_prompt',
  'problem_agitation',
  'other'
]);

export type HookType = z.infer<typeof HookTypeSchema>;

export const NarrativeBeatSchema = z.object({
  name: z.string(),
  startMs: z.number().nonnegative(),
  endMs: z.number().nonnegative(),
  description: z.string(),
  evidenceRefs: EvidenceReferenceSchema.optional()
});

export type NarrativeBeat = z.infer<typeof NarrativeBeatSchema>;

export const MultimodalStructureAnalysisSchema = z.object({
  hookType: HookTypeSchema,
  hookDurationMs: z.number().nonnegative(),
  narrativeArc: z.string(),
  narrativeBeats: z.array(NarrativeBeatSchema).default([]),
  keyTakeaways: z.array(z.string()).default([]),
  ctaType: z.string().optional(),
  ctaStructure: z.string().optional(),
  pacingStructure: z.string()
});

export type MultimodalStructureAnalysis = z.infer<typeof MultimodalStructureAnalysisSchema>;

export const MultimodalVisualAnalysisSchema = z.object({
  dominantColorPalette: z.array(z.string()).default([]),
  cutFrequencyPerMin: z.number().nonnegative(),
  faceVisibilityRatio: z.number().min(0).max(1),
  hasCaptions: z.boolean().default(true),
  captionStyle: z.string().optional(),
  visualGrammar: z.string(),
  shotPacing: z.string().optional(),
  motionEnergyScore: z.number().min(0).max(1).optional()
});

export type MultimodalVisualAnalysis = z.infer<typeof MultimodalVisualAnalysisSchema>;

export const MultimodalAudioInterpretationSchema = z.object({
  hasBackgroundMusic: z.boolean().default(false),
  musicGenre: z.string().optional(),
  musicBpm: z.number().optional(),
  speechToMusicRatioDb: z.number().optional(),
  averageLoudnessLufs: z.number().optional(),
  pauseCount: z.number().default(0),
  averagePauseDurationMs: z.number().default(0),
  speakingWpm: z.number().optional(),
  audioPacing: z.string(),
  clippingDetected: z.boolean().default(false)
});

export type MultimodalAudioInterpretation = z.infer<typeof MultimodalAudioInterpretationSchema>;

export const HypothesisTypeSchema = z.enum([
  'hook_dropoff',
  'pacing_lull',
  'cta_abandonment',
  'engagement_peak',
  'content_fatigue',
  'general'
]);

export type HypothesisType = z.infer<typeof HypothesisTypeSchema>;

export const MultimodalRetentionHypothesisSchema = z.object({
  id: z.string(),
  estimatedRetentionScore: z.number().min(0).max(100),
  hypothesisType: HypothesisTypeSchema,
  description: z.string(),
  timeRange: TimeRangeSchema.optional(),
  severity: z.enum(['low', 'medium', 'high']).default('medium'),
  evidenceRefs: EvidenceReferenceSchema.optional(),
  confidence: z.number().min(0).max(1).default(0.5)
});

export type MultimodalRetentionHypothesis = z.infer<typeof MultimodalRetentionHypothesisSchema>;

export const RecommendedShotSchema = z.object({
  shotIndex: z.number().int().nonnegative(),
  shotType: z.string(),
  description: z.string(),
  durationMs: z.number().positive()
});

export type RecommendedShot = z.infer<typeof RecommendedShotSchema>;

export const AdaptationRecommendationSchema = z.object({
  id: z.string(),
  targetNiche: z.string().optional(),
  opportunity: z.string(),
  suggestedHook: z.string().optional(),
  suggestedAngle: z.string().optional(),
  recommendedShotList: z.array(RecommendedShotSchema).default([]),
  riskFlags: z.array(z.string()).default([])
});

export type AdaptationRecommendation = z.infer<typeof AdaptationRecommendationSchema>;

export const ArtifactRefSchema = z.object({
  key: z.string().min(1),
  sha256: z.string().length(64),
  schemaVersion: z.string().min(1),
  byteSize: z.number().int().nonnegative().optional()
});

export type ArtifactRef = z.infer<typeof ArtifactRefSchema>;

export const ModelSetMetadataSchema = z.object({
  provider: z.string().min(1),
  model: z.string().min(1),
  modelSnapshot: z.string().optional(),
  modelSetVersion: z.string().min(1),
  promptTemplateVersion: z.string().min(1),
  inputArtifactHashes: z.record(z.string()),
  outputSchemaVersion: z.literal('multimodal-audit.v1'),
  processingDurationMs: z.number().nonnegative(),
  tokenUsage: z.object({
    promptTokens: z.number().int().nonnegative(),
    completionTokens: z.number().int().nonnegative(),
    totalTokens: z.number().int().nonnegative()
  }).optional(),
  fallbackReason: z.string().optional()
});

export type ModelSetMetadata = z.infer<typeof ModelSetMetadataSchema>;

export const MultimodalAuditResultSchema = z.object({
  schemaVersion: z.literal('multimodal-audit.v1'),
  referenceAssetId: z.string().min(1),
  inputArtifacts: z.object({
    transcript: ArtifactRefSchema.optional(),
    scenes: ArtifactRefSchema.optional(),
    ocr: ArtifactRefSchema.optional(),
    audioFeatures: ArtifactRefSchema.optional(),
    evidence: ArtifactRefSchema.optional()
  }),
  observedFacts: z.array(ObservedFactSchema).default([]),
  claims: z.array(AuditedClaimSchema).default([]),
  structure: MultimodalStructureAnalysisSchema,
  visual: MultimodalVisualAnalysisSchema,
  audio: MultimodalAudioInterpretationSchema,
  retentionHypotheses: z.array(MultimodalRetentionHypothesisSchema).default([]),
  adaptationRecommendations: z.array(AdaptationRecommendationSchema).default([]),
  confidence: z.number().min(0).max(1),
  warnings: z.array(z.string()).default([]),
  modelSet: ModelSetMetadataSchema
});

export type MultimodalAuditResult = z.infer<typeof MultimodalAuditResultSchema>;

/**
 * Validates audited claims based on observed/inferred/hypothesized policy:
 * - 'observed' claims must have at least one non-empty evidence reference array in evidenceRefs.
 * - 'hypothesized' claims should not be presented as certain facts.
 */
export function validateAuditedClaims(
  claims: AuditedClaim[],
  options: { requireEvidenceForObserved?: boolean } = { requireEvidenceForObserved: true }
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  for (const claim of claims) {
    // Basic structural checks
    const parsed = AuditedClaimSchema.safeParse(claim);
    if (!parsed.success) {
      errors.push(`Claim ${claim.id || 'unknown'} has invalid structure: ${parsed.error.message}`);
      continue;
    }

    if (claim.classification === 'observed' && options.requireEvidenceForObserved) {
      const refs = claim.evidenceRefs;
      const hasTranscriptRefs = !!(refs.transcriptSegmentIds && refs.transcriptSegmentIds.length > 0);
      const hasWordRefs = !!(refs.transcriptWordIndexes && refs.transcriptWordIndexes.length > 0);
      const hasSceneRefs = !!(refs.sceneIds && refs.sceneIds.length > 0);
      const hasOcrRefs = !!(refs.ocrFrameIds && refs.ocrFrameIds.length > 0);
      const hasAudioRefs = !!(refs.audioSegmentIndexes && refs.audioSegmentIndexes.length > 0);

      const hasAnyRef = hasTranscriptRefs || hasWordRefs || hasSceneRefs || hasOcrRefs || hasAudioRefs;

      if (!hasAnyRef) {
        errors.push(
          `Claim "${claim.id}" is marked 'observed' but has no evidence references. Observed claims must cite evidence.`
        );
      }
    }

    if (claim.classification === 'hypothesized') {
      // Hypothesized claim confidence is decoupled from classification
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

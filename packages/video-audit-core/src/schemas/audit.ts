/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/audit.ts"
# purpose: "Multimodal Video Audit, Transcript, Scene, Structural Analysis & Evidence Zod Schemas."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { ConfidenceSchema, TimeRangeSchema } from './common.js';
import { ReferenceAssetSchema } from './reference.js';

export const TranscriptWordSchema = z.object({
  word: z.string(),
  startMs: z.number().nonnegative(),
  endMs: z.number().nonnegative(),
  confidence: ConfidenceSchema.default(0.9),
  speakerTag: z.string().optional(),
});

export type TranscriptWord = z.infer<typeof TranscriptWordSchema>;

export const TranscriptSegmentSchema = z.object({
  id: z.string(),
  startMs: z.number().nonnegative(),
  endMs: z.number().nonnegative(),
  text: z.string(),
  words: z.array(TranscriptWordSchema).default([]),
  speakerTag: z.string().optional(),
});

export type TranscriptSegment = z.infer<typeof TranscriptSegmentSchema>;

export const TranscriptDocumentSchema = z.object({
  language: z.string().default('uk'),
  fullText: z.string(),
  segments: z.array(TranscriptSegmentSchema).default([]),
  overallConfidence: ConfidenceSchema.default(0.9),
});

export type TranscriptDocument = z.infer<typeof TranscriptDocumentSchema>;

export const ShotSchema = z.object({
  id: z.string(),
  timeRange: TimeRangeSchema,
  shotType: z.enum([
    'close_up',
    'medium_shot',
    'wide_shot',
    'b_roll',
    'screen_recording',
    'text_graphic',
    'overlay',
  ]),
  description: z.string(),
  hasTextOnScreen: z.boolean().default(false),
  textOnScreen: z.string().optional(),
  visualPacingWpm: z.number().optional(),
});

export type Shot = z.infer<typeof ShotSchema>;

export const SceneRoleSchema = z.enum([
  'hook',
  'problem_statement',
  'core_value',
  'demonstration',
  'social_proof',
  'call_to_action',
  'outro',
]);

export type SceneRole = z.infer<typeof SceneRoleSchema>;

export const SceneSchema = z.object({
  id: z.string(),
  title: z.string(),
  role: SceneRoleSchema,
  timeRange: TimeRangeSchema,
  summary: z.string(),
  shots: z.array(ShotSchema).default([]),
});

export type Scene = z.infer<typeof SceneSchema>;

export const AudioFeatureSetSchema = z.object({
  hasBackgroundMusic: z.boolean().default(false),
  musicGenre: z.string().optional(),
  musicBpm: z.number().optional(),
  speechToMusicRatioDb: z.number().optional(),
  averageLoudnessLufs: z.number().optional(),
  pauseCount: z.number().default(0),
  averagePauseDurationMs: z.number().default(0),
  speakingWpm: z.number().optional(),
});

export type AudioFeatureSet = z.infer<typeof AudioFeatureSetSchema>;

export const StructureAnalysisSchema = z.object({
  hookType: z.enum([
    'negative_frame',
    'bold_claim',
    'curiosity_gap',
    'story_origin',
    'visual_shock',
    'question_prompt',
  ]),
  hookDurationMs: z.number().nonnegative(),
  narrativeArc: z.string(),
  keyTakeaways: z.array(z.string()).default([]),
  ctaType: z.string().optional(),
  pacingStructure: z.string(),
});

export type StructureAnalysis = z.infer<typeof StructureAnalysisSchema>;

export const VisualAnalysisSchema = z.object({
  dominantColorPalette: z.array(z.string()).default([]),
  cutFrequencyPerMin: z.number().nonnegative(),
  faceVisibilityRatio: z.number().min(0).max(1),
  hasCaptions: z.boolean().default(true),
  captionStyle: z.string().optional(),
});

export type VisualAnalysis = z.infer<typeof VisualAnalysisSchema>;

export const RetentionHypothesisSchema = z.object({
  estimatedRetentionScore: z.number().min(0).max(100),
  dropoffRisks: z
    .array(
      z.object({
        timeRange: TimeRangeSchema,
        reason: z.string(),
        severity: z.enum(['low', 'medium', 'high']),
      })
    )
    .default([]),
  engagementDrivers: z
    .array(
      z.object({
        timeRange: TimeRangeSchema,
        driver: z.string(),
      })
    )
    .default([]),
});

export type RetentionHypothesis = z.infer<typeof RetentionHypothesisSchema>;

export const EvidenceTypeSchema = z.enum(['observed', 'inferred', 'hypothesized']);

export type EvidenceType = z.infer<typeof EvidenceTypeSchema>;

export const EvidenceItemSchema = z.object({
  id: z.string(),
  type: EvidenceTypeSchema,
  claim: z.string(),
  confidence: ConfidenceSchema,
  source: z.string(),
  timeRange: TimeRangeSchema.optional(),
  modelVersion: z.string().optional(),
  evidenceRefs: z.array(z.string()).default([]),
});

export type EvidenceItem = z.infer<typeof EvidenceItemSchema>;

export const AuditStatusSchema = z.enum([
  'RECEIVED',
  'VALIDATING',
  'INGESTING',
  'TRANSCRIBING',
  'EXTRACTING_FRAMES',
  'ANALYZING_AUDIO',
  'ANALYZING_VISUALS',
  'ANALYZING_STRUCTURE',
  'GENERATING_REPORT',
  'READY',
  'FAILED',
]);

export type AuditStatus = z.infer<typeof AuditStatusSchema>;

export const VideoAuditReportSchema = z.object({
  schemaVersion: z.literal('video-audit.v1'),
  id: z.string(),
  status: AuditStatusSchema,
  createdAt: z.string().default(() => new Date().toISOString()),
  referenceAsset: ReferenceAssetSchema,
  transcript: TranscriptDocumentSchema,
  scenes: z.array(SceneSchema).default([]),
  audioFeatures: AudioFeatureSetSchema,
  structure: StructureAnalysisSchema,
  visuals: VisualAnalysisSchema,
  retention: RetentionHypothesisSchema,
  evidence: z.array(EvidenceItemSchema).default([]),
});

export type VideoAuditReport = z.infer<typeof VideoAuditReportSchema>;

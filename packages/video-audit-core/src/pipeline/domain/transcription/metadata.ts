/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/transcription/metadata.ts"
# purpose: "Transcription Execution Metadata Zod Schema and Quality Flags."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const TranscriptionQualityFlagsSchema = z.object({
  hasAudio: z.boolean().default(true),
  hasBackgroundMusic: z.boolean().default(false),
  isMultiSpeaker: z.boolean().default(false),
  hasHighNoise: z.boolean().default(false),
  hasOverlappingSpeech: z.boolean().default(false),
  wordTimestampCoverage: z.number().min(0).max(1).default(1.0),
  segmentTimestampCoverage: z.number().min(0).max(1).default(1.0),
  technicalTermAccuracy: z.number().min(0).max(1).optional(),
});

export type TranscriptionQualityFlags = z.infer<typeof TranscriptionQualityFlagsSchema>;

export const TranscriptionProcessingMetadataSchema = z.object({
  provider: z.string(),
  modelVersion: z.string(),
  alignmentModelVersion: z.string().optional(),
  languageRequested: z.string().optional(),
  languageDetected: z.string(),
  device: z.enum(['cpu', 'cuda', 'mps', 'fake']).default('fake'),
  computeMode: z.string().default('fp16'),
  processingDurationMs: z.number().nonnegative(),
  audioDurationMs: z.number().nonnegative(),
  realTimeFactor: z.number().nonnegative(),
  wordCount: z.number().int().nonnegative(),
  segmentCount: z.number().int().nonnegative(),
  qualityFlags: TranscriptionQualityFlagsSchema.default({}),
});

export type TranscriptionProcessingMetadata = z.infer<typeof TranscriptionProcessingMetadataSchema>;

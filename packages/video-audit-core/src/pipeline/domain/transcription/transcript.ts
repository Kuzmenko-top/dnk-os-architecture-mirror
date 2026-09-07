/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/transcription/transcript.ts"
# purpose: "Canonical transcript.v1 Domain Schema with Segment and Word Level Timestamps."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const TranscriptWordSchema = z.object({
  ordinal: z.number().int().nonnegative(),
  text: z.string().min(1),
  startMs: z.number().int().nonnegative(),
  endMs: z.number().int().nonnegative(),
  confidence: z.number().min(0).max(1).optional(),
  punctuation: z.string().optional(),
  speakerId: z.string().optional()
}).refine(data => data.endMs >= data.startMs, {
  message: 'Word endMs must be >= startMs'
});

export type TranscriptWord = z.infer<typeof TranscriptWordSchema>;

export const TranscriptSegmentSchema = z.object({
  id: z.string(),
  ordinal: z.number().int().nonnegative(),
  startMs: z.number().int().nonnegative(),
  endMs: z.number().int().nonnegative(),
  text: z.string(),
  confidence: z.number().min(0).max(1).optional(),
  speakerId: z.string().optional(),
  words: z.array(TranscriptWordSchema).default([])
}).refine(data => data.endMs >= data.startMs, {
  message: 'Segment endMs must be >= startMs'
}).refine(data => {
  for (const w of data.words) {
    if (w.startMs < data.startMs || w.endMs > data.endMs) {
      return false;
    }
  }
  return true;
}, {
  message: 'All word timestamp intervals must fit inside segment interval bounds'
});

export type TranscriptSegment = z.infer<typeof TranscriptSegmentSchema>;

export const TranscriptStatusSchema = z.enum(['completed', 'partial', 'degraded']);
export type TranscriptStatus = z.infer<typeof TranscriptStatusSchema>;

export const TranscriptDocumentSchema = z.object({
  schemaVersion: z.literal('transcript.v1').default('transcript.v1'),
  id: z.string(),
  referenceAssetId: z.string(),
  language: z.string().min(2),
  provider: z.string(),
  modelVersion: z.string(),
  alignmentModelVersion: z.string().optional(),
  segments: z.array(TranscriptSegmentSchema).default([]),
  durationMs: z.number().int().nonnegative(),
  confidence: z.number().min(0).max(1).default(0.95),
  status: TranscriptStatusSchema,
  warnings: z.array(z.string()).default([])
}).refine(data => {
  if (data.status === 'completed' && data.segments.length === 0) {
    return false;
  }
  return true;
}, {
  message: "Empty transcript document cannot have status 'completed'"
}).refine(data => {
  const maxEndMs = data.segments.reduce((max, seg) => Math.max(max, seg.endMs), 0);
  return data.durationMs >= maxEndMs;
}, {
  message: 'durationMs must be >= maximum timestamp of any segment'
});

export type TranscriptDocument = z.infer<typeof TranscriptDocumentSchema>;

// Aliasing for unambiguous package-level re-exports
export const TranscriptDocumentV1Schema = TranscriptDocumentSchema;
export type TranscriptDocumentV1 = TranscriptDocument;
export const TranscriptSegmentV1Schema = TranscriptSegmentSchema;
export type TranscriptSegmentV1 = TranscriptSegment;
export const TranscriptWordV1Schema = TranscriptWordSchema;
export type TranscriptWordV1 = TranscriptWord;

export function createTranscriptDocument(input: Partial<TranscriptDocument> & {
  id: string;
  referenceAssetId: string;
  language: string;
  provider: string;
  modelVersion: string;
  durationMs: number;
  status: TranscriptStatus;
}): TranscriptDocument {
  const raw: TranscriptDocument = {
    schemaVersion: 'transcript.v1',
    id: input.id,
    referenceAssetId: input.referenceAssetId,
    language: input.language.toLowerCase().trim(),
    provider: input.provider,
    modelVersion: input.modelVersion,
    alignmentModelVersion: input.alignmentModelVersion,
    segments: input.segments ?? [],
    durationMs: input.durationMs,
    confidence: input.confidence ?? 0.95,
    status: input.status,
    warnings: input.warnings ?? []
  };

  return TranscriptDocumentSchema.parse(raw);
}

export function validateTranscriptDocument(data: unknown): TranscriptDocument {
  return TranscriptDocumentSchema.parse(data);
}

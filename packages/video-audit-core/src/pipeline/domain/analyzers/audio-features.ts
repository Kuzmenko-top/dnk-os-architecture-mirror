/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analyzers/audio-features.ts"
# purpose: "Canonical audio-features.v1 Schema, Observable Acoustic Metrics, RMS, Silence, and Degradation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const AudioFeatureSegmentSchema = z
  .object({
    startMs: z.number().int().nonnegative(),
    endMs: z.number().int().positive(),
    rmsDb: z.number().optional(),
    peakDb: z.number().optional(),
    speechProbability: z.number().min(0).max(1).optional(),
    silence: z.boolean().default(false),
    musicProbability: z.number().min(0).max(1).optional(),
    noiseScore: z.number().min(0).max(1).optional(),
    clippingDetected: z.boolean().default(false)
  })
  .refine((seg) => seg.endMs > seg.startMs, {
    message: 'AudioFeatureSegment endMs must be strictly greater than startMs'
  });

export type AudioFeatureSegment = z.infer<typeof AudioFeatureSegmentSchema>;

export const AudioFeaturesDocumentSchema = z
  .object({
    schemaVersion: z.literal('audio-features.v1'),
    referenceAssetId: z.string().min(1),
    sampleRate: z.number().int().positive().default(44100),
    durationMs: z.number().int().nonnegative(),
    provider: z.string().min(1),
    hasAudioTrack: z.boolean().default(true),
    isDegraded: z.boolean().default(false),
    features: z.array(AudioFeatureSegmentSchema),
    warnings: z.array(z.string()).default([])
  })
  .superRefine((doc, ctx) => {
    if (!doc.hasAudioTrack && doc.features.length > 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Degraded audio document with hasAudioTrack=false must not contain feature segments',
        path: ['features']
      });
    }

    for (let i = 1; i < doc.features.length; i++) {
      const prev = doc.features[i - 1];
      const curr = doc.features[i];
      if (curr.startMs < prev.endMs) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `AudioFeatureSegment[${i}] (${curr.startMs}ms) overlaps with segment[${i - 1}] (${prev.endMs}ms)`,
          path: ['features', i, 'startMs']
        });
      }
    }
  });

export type AudioFeaturesDocument = z.infer<typeof AudioFeaturesDocumentSchema>;

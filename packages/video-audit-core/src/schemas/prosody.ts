/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/prosody.ts"
# purpose: "Prosody Document Zod Schema (prosody.v1) for Vocal Teleprompter HUD Cues."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const ProsodyEmphasisSchema = z.enum([
  'none',
  'punch',
  'soft',
  'whisper',
  'stretched',
]);

export type ProsodyEmphasis = z.infer<typeof ProsodyEmphasisSchema>;

export const ProsodyPitchSchema = z.enum(['low', 'normal', 'high']);

export type ProsodyPitch = z.infer<typeof ProsodyPitchSchema>;

export const ProsodyGestureSchema = z.enum([
  'none',
  'hand_raise',
  'finger_point',
  'head_nod',
  'head_shake',
  'eyebrow_raise',
  'smile',
  'lean_forward',
  'palms_up',
]);

export type ProsodyGesture = z.infer<typeof ProsodyGestureSchema>;

export const ProsodyTokenSchema = z.object({
  id: z.string(),
  word: z.string(),
  sceneId: z.string(),
  paragraphId: z.string(),
  emphasis: ProsodyEmphasisSchema.default('none'),
  pitchShift: ProsodyPitchSchema.default('normal'),
  pauseAfterMs: z.number().default(0),
  gesture: ProsodyGestureSchema.default('none'),
  customHint: z.string().optional(),
});

export type ProsodyToken = z.infer<typeof ProsodyTokenSchema>;

export const ProsodyGlobalPacingSchema = z.object({
  targetWpm: z.number().positive().optional(),
  targetDurationMs: z.number().positive().optional(),
});

export type ProsodyGlobalPacing = z.infer<typeof ProsodyGlobalPacingSchema>;

export const ProsodyDocumentSchema = z.object({
  schemaVersion: z.literal('prosody.v1'),
  scriptId: z.string(),
  globalPacing: ProsodyGlobalPacingSchema.default({}),
  tokens: z.array(ProsodyTokenSchema).default([]),
});

export type ProsodyDocument = z.infer<typeof ProsodyDocumentSchema>;

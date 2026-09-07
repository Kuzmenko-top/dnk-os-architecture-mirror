/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analyzers/scenes.ts"
# purpose: "Canonical scenes.v1 Schema, Scene Boundaries, Keyframes, and Extraction Policy Contracts."
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

export const ShotTypeSchema = z.enum([
  'talking_head',
  'close_up',
  'wide',
  'product',
  'screen',
  'unknown'
]);

export type ShotType = z.infer<typeof ShotTypeSchema>;

export const SceneSchema = z.object({
  id: z.string().min(1),
  ordinal: z.number().int().min(0),
  startMs: z.number().min(0),
  endMs: z.number().min(0),
  durationMs: z.number().min(0),
  boundaryConfidence: z.number().min(0).max(1),
  keyframeArtifactKey: z.string().optional(),
  visualChangeScore: z.number().min(0).max(1).optional(),
  shotType: ShotTypeSchema.optional()
}).refine((data) => data.endMs > data.startMs, {
  message: 'Scene endMs must be strictly greater than startMs'
}).refine((data) => Math.abs(data.durationMs - (data.endMs - data.startMs)) < 1, {
  message: 'Scene durationMs must equal endMs - startMs'
});

export type Scene = z.infer<typeof SceneSchema>;

export const SceneExtractionPolicySchema = z.object({
  threshold: z.number().min(0).max(1),
  minSceneDurationMs: z.number().min(0),
  maxSceneDurationMs: z.number().min(0).optional(),
  keyframeStrategy: z.enum(['first', 'middle', 'both']),
  maxScenes: z.number().int().min(1)
});

export type SceneExtractionPolicy = z.infer<typeof SceneExtractionPolicySchema>;

export function validateScenesNonOverlapping(scenes: Scene[]): boolean {
  for (let i = 1; i < scenes.length; i++) {
    if (scenes[i].startMs < scenes[i - 1].endMs) {
      return false;
    }
  }
  return true;
}

export const SceneDocumentSchema = z.object({
  schemaVersion: z.literal('scenes.v1'),
  referenceAssetId: z.string().min(1),
  extractor: z.object({
    provider: z.string().min(1),
    version: z.string().min(1),
    method: z.string().min(1)
  }),
  scenes: z.array(SceneSchema),
  durationMs: z.number().min(0),
  warnings: z.array(z.string()).optional()
}).refine((doc) => validateScenesNonOverlapping(doc.scenes), {
  message: 'Scenes must be non-overlapping and sorted chronologically'
}).refine((doc) => {
  return doc.scenes.every(s => s.endMs <= doc.durationMs);
}, {
  message: 'Scenes must not exceed media total durationMs'
});

export type SceneDocument = z.infer<typeof SceneDocumentSchema>;

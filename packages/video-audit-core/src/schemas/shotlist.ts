/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/shotlist.ts"
# purpose: "ShotList Zod Schema (shot-list.v1) for Recording and Remotion Visual Cues."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const ShotInstructionSchema = z.object({
  id: z.string(),
  sceneId: z.string(),
  shotType: z.enum([
    'close_up',
    'medium_shot',
    'wide_shot',
    'b_roll',
    'screen_recording',
    'text_graphic',
    'overlay',
  ]),
  visualPrompt: z.string(),
  estimatedDurationMs: z.number().positive(),
  cameraAngle: z.string().optional(),
  textOverlay: z.string().optional(),
  bRollKeywords: z.array(z.string()).default([]),
});

export type ShotInstruction = z.infer<typeof ShotInstructionSchema>;

export const ShotListSchema = z.object({
  schemaVersion: z.literal('shot-list.v1'),
  scriptId: z.string(),
  shots: z.array(ShotInstructionSchema).default([]),
});

export type ShotList = z.infer<typeof ShotListSchema>;

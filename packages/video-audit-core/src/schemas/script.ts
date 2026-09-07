/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/script.ts"
# purpose: "Script Document Zod Schema (script.v1) for Teleprompter and Content Pipelines."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { TimeRangeSchema } from './common.js';
import { SceneRoleSchema } from './audit.js';

export const ScriptParagraphSchema = z.object({
  id: z.string(),
  text: z.string(),
  speakerRole: z.string().default('main_speaker'),
  estimatedDurationMs: z.number().nonnegative(),
});

export type ScriptParagraph = z.infer<typeof ScriptParagraphSchema>;

export const ScriptSceneSchema = z.object({
  id: z.string(),
  title: z.string(),
  role: SceneRoleSchema,
  targetTimeRange: TimeRangeSchema.optional(),
  paragraphs: z.array(ScriptParagraphSchema).default([]),
});

export type ScriptScene = z.infer<typeof ScriptSceneSchema>;

export const ScriptSourceSchema = z.object({
  type: z.enum(['original', 'adapted']),
  auditId: z.string().optional(),
  adaptationId: z.string().optional(),
});

export type ScriptSource = z.infer<typeof ScriptSourceSchema>;

export const ScriptDocumentSchema = z.object({
  schemaVersion: z.literal('script.v1'),
  id: z.string(),
  language: z.string().default('uk'),
  title: z.string().optional(),
  estimatedDurationMs: z.number().nonnegative(),
  source: ScriptSourceSchema,
  scenes: z.array(ScriptSceneSchema).default([]),
  metadata: z.record(z.unknown()).optional(),
});

export type ScriptDocument = z.infer<typeof ScriptDocumentSchema>;

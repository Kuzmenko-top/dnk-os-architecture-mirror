/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/common.ts"
# purpose: "Common Zod Primitive Schemas, TimeRanges and Confidence Bounds for Video Intelligence."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const TimeRangeSchema = z.object({
  startMs: z.number().min(0, 'startMs must be non-negative'),
  endMs: z.number().min(0, 'endMs must be non-negative'),
}).refine(data => data.endMs >= data.startMs, {
  message: 'endMs must be greater than or equal to startMs',
  path: ['endMs'],
});

export type TimeRange = z.infer<typeof TimeRangeSchema>;

export const ConfidenceSchema = z.number().min(0).max(1);
export type Confidence = z.infer<typeof ConfidenceSchema>;

export const SchemaVersionSchema = z.string().regex(/^[a-z0-9-]+.v[0-9]+$/, 'Invalid schemaVersion format (e.g. script.v1)');

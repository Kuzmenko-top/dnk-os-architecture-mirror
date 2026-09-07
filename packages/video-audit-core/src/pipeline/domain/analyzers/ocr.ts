/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analyzers/ocr.ts"
# purpose: "Canonical ocr.v1 Schema, Visual Text Overlays, Normalized Bounding Boxes and Frames."
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

export const BoundingBoxSchema = z
  .object({
    x: z.number().min(0).max(1),
    y: z.number().min(0).max(1),
    width: z.number().positive().max(1),
    height: z.number().positive().max(1)
  })
  .refine((box) => box.x + box.width <= 1.001, {
    message: 'Bounding box (x + width) cannot exceed 1.0'
  })
  .refine((box) => box.y + box.height <= 1.001, {
    message: 'Bounding box (y + height) cannot exceed 1.0'
  });

export type BoundingBox = z.infer<typeof BoundingBoxSchema>;

export const OCRRegionSchema = z.object({
  text: z.string(),
  confidence: z.number().min(0).max(1),
  boundingBox: BoundingBoxSchema,
  normalizedText: z.string(),
  language: z.string().optional()
});

export type OCRRegion = z.infer<typeof OCRRegionSchema>;

export const OCRFrameSchema = z.object({
  frameId: z.string().min(1),
  timestampMs: z.number().int().nonnegative(),
  width: z.number().int().positive(),
  height: z.number().int().positive(),
  regions: z.array(OCRRegionSchema)
});

export type OCRFrame = z.infer<typeof OCRFrameSchema>;

export const OCRDocumentSchema = z
  .object({
    schemaVersion: z.literal('ocr.v1'),
    referenceAssetId: z.string().min(1),
    provider: z.string().min(1),
    modelVersion: z.string().min(1),
    frames: z.array(OCRFrameSchema),
    languageHints: z.array(z.string()).default(['uk', 'en']),
    warnings: z.array(z.string()).default([])
  })
  .superRefine((doc, ctx) => {
    for (let i = 1; i < doc.frames.length; i++) {
      if (doc.frames[i].timestampMs < doc.frames[i - 1].timestampMs) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `OCRFrame[${i}] timestamp (${doc.frames[i].timestampMs}ms) is earlier than frame[${i - 1}] (${doc.frames[i - 1].timestampMs}ms)`,
          path: ['frames', i, 'timestampMs']
        });
      }
    }
  });

export type OCRDocument = z.infer<typeof OCRDocumentSchema>;

/**
 * Text normalization and duplicate suppression helper
 */
export function normalizeOCRText(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/\r\n/g, '\n')
    .replace(/\n+/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .trim();
}

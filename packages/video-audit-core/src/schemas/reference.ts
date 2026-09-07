/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/reference.ts"
# purpose: "Legacy Reference Asset and Media Metadata Zod Contracts."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const MediaMetadataSchema = z.object({
  durationMs: z.number().nonnegative(),
  width: z.number().positive(),
  height: z.number().positive(),
  fps: z.number().positive(),
  aspectRatio: z.string().default('9:16'),
  bitrateKbps: z.number().optional(),
  codec: z.string().optional(),
});

export type MediaMetadata = z.infer<typeof MediaMetadataSchema>;

export const PlatformMetadataSchema = z.object({
  authorHandle: z.string().optional(),
  viewsCount: z.number().nonnegative().optional(),
  likesCount: z.number().nonnegative().optional(),
  sharesCount: z.number().nonnegative().optional(),
  postedAt: z.string().optional(),
  caption: z.string().optional(),
  hashtags: z.array(z.string()).default([]),
});

export type PlatformMetadata = z.infer<typeof PlatformMetadataSchema>;

export const SourceTypeSchema = z.enum([
  'url_tiktok',
  'url_youtube',
  'url_instagram',
  'telegram_file',
  'direct_upload',
]);

export type SourceType = z.infer<typeof SourceTypeSchema>;

export const LegacyReferenceAssetSchema = z.object({
  id: z.string(),
  sourceType: SourceTypeSchema,
  url: z.string().url().optional(),
  storagePath: z.string().optional(),
  mediaMetadata: MediaMetadataSchema,
  platformMetadata: PlatformMetadataSchema.default({ hashtags: [] }),
  createdAt: z.string().default(() => new Date().toISOString()),
});

export type LegacyReferenceAsset = z.infer<typeof LegacyReferenceAssetSchema>;
export const ReferenceAssetSchema = LegacyReferenceAssetSchema;
export type ReferenceAsset = z.infer<typeof ReferenceAssetSchema>;


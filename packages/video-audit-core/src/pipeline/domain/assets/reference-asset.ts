/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/assets/reference-asset.ts"
# purpose: "Canonical ReferenceAsset Domain Model, Rights Metadata, Probing Schemas and Capabilities."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const RightsStatusSchema = z.enum([
  'unknown',
  'user_owned',
  'licensed',
  'user_confirmed'
]);
export type RightsStatus = z.infer<typeof RightsStatusSchema>;

export const UsageIntentSchema = z.enum([
  'private_analysis',
  'internal',
  'commercial_adaptation'
]);
export type UsageIntent = z.infer<typeof UsageIntentSchema>;

export const RightsMetadataSchema = z.object({
  status: RightsStatusSchema,
  confirmedAt: z.string().datetime().optional(),
  confirmedBy: z.string().min(1).optional(),
  sourcePlatform: z.string().min(1).optional(),
  usageIntent: UsageIntentSchema
});
export type RightsMetadata = z.infer<typeof RightsMetadataSchema>;

export const MediaContainerSchema = z.enum(['mp4', 'mov', 'webm', 'mkv', 'unknown']);
export type MediaContainer = z.infer<typeof MediaContainerSchema>;

export const MediaProbeResultSchema = z.object({
  mimeType: z.string().min(1),
  container: MediaContainerSchema,
  durationMs: z.number().nonnegative(),
  width: z.number().int().positive().optional(),
  height: z.number().int().positive().optional(),
  frameRate: z.number().positive().optional(),
  videoCodec: z.string().optional(),
  audioCodec: z.string().optional(),
  hasVideo: z.boolean(),
  hasAudio: z.boolean(),
  byteSize: z.number().int().nonnegative(),
  sha256: z.string().length(64),
  isCorrupted: z.boolean().default(false),
  corruptionReason: z.string().optional()
});
export type MediaProbeResult = z.infer<typeof MediaProbeResultSchema>;

export const MediaCapabilitySchema = z.enum([
  'video',
  'audio',
  'transcription',
  'scene_extraction',
  'ocr',
  'audio_analysis',
  'multimodal_audit',
  'adaptation'
]);
export type MediaCapability = z.infer<typeof MediaCapabilitySchema>;

export const SourcePlatformSchema = z.enum([
  'direct_upload',
  'telegram',
  'youtube',
  'tiktok',
  'instagram',
  'manual_fallback',
  'custom_url'
]);
export type SourcePlatform = z.infer<typeof SourcePlatformSchema>;

export const ReferenceAssetSchema = z.object({
  id: z.string().min(1),
  sourcePlatform: SourcePlatformSchema,
  sourceUrl: z.string().url().optional(),
  telegramFileId: z.string().min(1).optional(),
  telegramFileUniqueId: z.string().min(1).optional(),
  originalFilename: z.string().optional(),
  sanitizedFilename: z.string().min(1),
  contentHash: z.string().length(64),
  storageKey: z.string().min(1),
  rightsMetadata: RightsMetadataSchema,
  probeResult: MediaProbeResultSchema,
  capabilities: z.array(MediaCapabilitySchema),
  degradationWarnings: z.array(z.string()),
  schemaVersion: z.literal('reference-asset.v1'),
  createdAt: z.string().datetime(),
  createdBy: z.string().min(1)
});
export type ReferenceAsset = z.infer<typeof ReferenceAssetSchema>;

/**
 * Calculates domain capabilities and degradation warnings based on media probe results and rights.
 */
export function deriveMediaCapabilities(
  probe: MediaProbeResult,
  rights: RightsMetadata
): { capabilities: MediaCapability[]; degradationWarnings: string[] } {
  const capabilities: MediaCapability[] = [];
  const degradationWarnings: string[] = [];

  if (probe.hasVideo) {
    capabilities.push('video');
    capabilities.push('scene_extraction');
    capabilities.push('ocr');
    capabilities.push('multimodal_audit');
  } else {
    degradationWarnings.push('No video stream detected; visual and OCR inspection unavailable.');
  }

  if (probe.hasAudio) {
    capabilities.push('audio');
    capabilities.push('transcription');
    capabilities.push('audio_analysis');
  } else {
    degradationWarnings.push('No audio stream detected; audio analysis and transcription unavailable. Running in degraded visual-only mode.');
  }

  if (rights.status === 'user_owned' || rights.status === 'licensed' || rights.status === 'user_confirmed') {
    capabilities.push('adaptation');
  } else {
    if (rights.usageIntent === 'commercial_adaptation') {
      degradationWarnings.push('Rights status is unconfirmed/unknown. Commercial adaptation requires explicit rights confirmation.');
    }
  }

  return { capabilities, degradationWarnings };
}

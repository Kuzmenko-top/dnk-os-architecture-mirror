/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/ingestion/input.ts"
# purpose: "Canonical Ingestion Input Abstractions for Direct Upload, Telegram Files, and URLs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { RightsMetadata } from '../assets/reference-asset.js';

export interface DirectFileUploadInput {
  type: 'file_upload';
  buffer: Uint8Array;
  originalFilename?: string;
  declaredMimeType?: string;
  actorId: string;
  rightsMetadata?: Partial<RightsMetadata>;
  correlationId?: string;
}

export interface TelegramFileInput {
  type: 'telegram_file';
  buffer: Uint8Array;
  updateId: number;
  fileId: string;
  fileUniqueId: string;
  chatId: string | number;
  userId: string | number;
  originalFilename?: string;
  declaredMimeType?: string;
  fileSize?: number;
  actorId: string;
  rightsMetadata?: Partial<RightsMetadata>;
  correlationId?: string;
}

export interface UrlReferenceInput {
  type: 'url_reference';
  url: string;
  actorId: string;
  rightsMetadata?: Partial<RightsMetadata>;
  correlationId?: string;
}

export interface ManualFallbackInput {
  type: 'manual_fallback';
  transcriptText?: string;
  screenshotBuffers?: Uint8Array[];
  originalFilename?: string;
  actorId: string;
  rightsMetadata?: Partial<RightsMetadata>;
  correlationId?: string;
}

export type MediaInput =
  | DirectFileUploadInput
  | TelegramFileInput
  | UrlReferenceInput
  | ManualFallbackInput;

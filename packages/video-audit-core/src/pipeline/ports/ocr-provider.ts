/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/ocr-provider.ts"
# purpose: "Provider-Agnostic Optical Character Recognition (OCR) Port and DTO Contracts."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { OCRDocument } from '../domain/analyzers/ocr.js';

export interface OCRFrameInput {
  frameId: string;
  timestampMs: number;
  imageBuffer: Buffer;
  width: number;
  height: number;
}

export interface OCRInput {
  referenceAssetId: string;
  frames: OCRFrameInput[];
  languageHints?: string[];
}

export interface OCRResult {
  document: OCRDocument;
}

export interface OCRProviderPort {
  extractOCR(input: OCRInput): Promise<OCRResult>;
}

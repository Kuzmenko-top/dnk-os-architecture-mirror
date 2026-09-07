/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/transcription-provider.ts"
# purpose: "Provider-Agnostic Transcription Port & Interface Definitions."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { TranscriptDocument } from '../domain/transcription/transcript.js';
import { TranscriptionProcessingMetadata } from '../domain/transcription/metadata.js';

export interface TranscriptionCapabilities {
  wordTimestamps: boolean;
  speakerDiarization: boolean;
  languageDetection: boolean;
  streaming: boolean;
  offline: boolean;
}

export interface TranscriptionInput {
  artifactKey: string;
  mimeType: string;
  languageHint?: string;
  durationMs?: number;
  referenceAssetId?: string;
  audioBuffer?: Buffer;
}

export interface TranscriptionContext {
  jobId: string;
  traceId?: string;
  workerId?: string;
}

export interface TranscriptionResult {
  transcript: TranscriptDocument;
  metadata: TranscriptionProcessingMetadata;
}

export interface TranscriptionProviderPort {
  readonly providerId: string;
  readonly capabilities: TranscriptionCapabilities;

  transcribe(
    input: TranscriptionInput,
    context: TranscriptionContext
  ): Promise<TranscriptionResult>;
}

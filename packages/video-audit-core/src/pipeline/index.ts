/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/index.ts"
# purpose: "Public Barrel File Exporting Domain Models, Ports, Infrastructure, Ingestion, Transcription & 001D Analyzer Services."
# canonical_source: true
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

// Domain
export * from './domain/jobs/job.js';
export * from './domain/jobs/state-machine.js';
export * from './domain/artifacts/artifact.js';
export * from './domain/idempotency/key.js';
export * from './domain/retry-policy.js';
export * from './domain/events/events.js';
export * from './domain/assets/reference-asset.js';
export * from './domain/ingestion/input.js';
export * from './domain/ingestion/security.js';
export type {
  TranscriptDocumentV1,
  TranscriptSegmentV1,
  TranscriptWordV1,
  TranscriptStatus,
  TranscriptDocumentV1 as PipelineTranscriptDocument
} from './domain/transcription/transcript.js';

export {
  TranscriptDocumentV1Schema,
  TranscriptSegmentV1Schema,
  TranscriptWordV1Schema,
  TranscriptStatusSchema,
  createTranscriptDocument,
  validateTranscriptDocument,
  TranscriptDocumentV1Schema as PipelineTranscriptDocumentSchema
} from './domain/transcription/transcript.js';
export * from './domain/transcription/metadata.js';
export * from './domain/transcription/compatibility.js';

// Analyzers Domain (001D)
export * from './domain/analyzers/scenes.js';
export * from './domain/analyzers/ocr.js';
export * from './domain/analyzers/audio-features.js';
export * from './domain/analyzers/aggregate-status.js';
export * from './domain/analyzers/multimodal-evidence.js';

// DTO
export * from './dto/mappers.js';

// Ports
export * from './ports/job-repository.js';
export * from './ports/artifact-store.js';
export * from './ports/event-bus.js';
export * from './ports/clock.js';
export * from './ports/id-generator.js';
export * from './ports/reference-asset-repository.js';
export * from './ports/media-probe.js';
export * from './ports/telegram-update-tracker.js';
export * from './ports/url-validator.js';
export * from './ports/transcription-provider.js';
export * from './ports/scene-extraction-provider.js';
export * from './ports/ocr-provider.js';
export * from './ports/audio-feature-provider.js';
export * from './ports/multimodal-audit-provider.js';

// Infrastructure
export * from './infrastructure/system/system-clock.js';
export * from './infrastructure/system/uuid-id-generator.js';
export * from './infrastructure/in-memory/in-memory-job-repository.js';
export * from './infrastructure/in-memory/in-memory-artifact-store.js';
export * from './infrastructure/in-memory/in-memory-event-bus.js';
export * from './infrastructure/in-memory/in-memory-reference-asset-repository.js';
export {
  InMemoryTelegramUpdateTracker,
  InMemoryTelegramUpdateTracker as InMemoryTelegramTracker
} from './infrastructure/in-memory/in-memory-telegram-tracker.js';
export * from './infrastructure/media-probe/deterministic-media-probe.js';
export * from './infrastructure/security/ssrf-url-validator.js';
export * from './infrastructure/fake-worker/deterministic-fake-worker.js';
export * from './infrastructure/contracts/postgres-contract.js';
export * from './infrastructure/contracts/redis-contract.js';
export * from './infrastructure/contracts/object-storage-contract.js';
export * from './infrastructure/transcription/deterministic-transcription-provider.js';
export * from './infrastructure/transcription/whisperx-transcription-adapter.js';
export * from './infrastructure/analyzers/deterministic-scene-provider.js';
export * from './infrastructure/analyzers/deterministic-ocr-provider.js';
export * from './infrastructure/analyzers/deterministic-audio-feature-provider.js';
export * from './infrastructure/analyzers/ffmpeg-scene-adapter.js';
export * from './infrastructure/analyzers/ocr-cli-adapter.js';
export * from './infrastructure/analyzers/ffmpeg-audio-feature-adapter.js';
export * from './infrastructure/prompt/index.js';

// Application
export * from './application/orchestrator.js';
export * from './application/ingestion-service.js';
export * from './application/transcription-worker.js';
export * from './application/scene-extraction-worker.js';
export * from './application/ocr-worker.js';
export * from './application/audio-feature-worker.js';
export * from './application/run-leased-analyzer-job.js';
export * from './application/spend-guard.js';
export * from './application/telemetry.js';

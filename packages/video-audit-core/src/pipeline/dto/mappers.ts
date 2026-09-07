/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/dto/mappers.ts"
# purpose: "DTO Mappers and Strict Version Guards for Video Audit Pipeline Entities."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditJob, VideoAuditJobSchema } from '../domain/jobs/job.js';
import { ArtifactManifest, ArtifactManifestSchema } from '../domain/artifacts/artifact.js';
import { AuditEvent, AuditEventSchema } from '../domain/events/events.js';
import { SchemaVersionMismatchError } from '../../validation/errors.js';

export function assertJobSchemaVersion(job: VideoAuditJob | Record<string, unknown>): void {
  const version = (job as any).schemaVersion || (job as any).schema_version;
  if (version !== 'audit-job.v1') {
    throw new SchemaVersionMismatchError('audit-job.v1', version || 'unknown');
  }
}

export function assertArtifactManifestSchemaVersion(manifest: ArtifactManifest | Record<string, unknown>): void {
  const version = (manifest as any).schemaVersion || (manifest as any).schema_version;
  if (version !== 'artifact-manifest.v1') {
    throw new SchemaVersionMismatchError('artifact-manifest.v1', version || 'unknown');
  }
}

export interface JobDto {
  id: string;
  reference_asset_id: string;
  type: string;
  status: string;
  attempt: number;
  max_attempts: number;
  idempotency_key: string;
  input_artifact_keys: string[];
  output_artifact_keys: string[];
  schema_version: string;
  created_at: string;
  available_at: string;
  leased_until?: string;
  started_at?: string;
  finished_at?: string;
  last_error?: {
    code: string;
    message: string;
    classification: string;
    occurred_at: string;
    details?: Record<string, unknown>;
  };
}

export function mapJobToDto(job: VideoAuditJob): JobDto {
  assertJobSchemaVersion(job);
  return {
    id: job.id,
    reference_asset_id: job.referenceAssetId,
    type: job.type,
    status: job.status,
    attempt: job.attempt,
    max_attempts: job.maxAttempts,
    idempotency_key: job.idempotencyKey,
    input_artifact_keys: [...job.inputArtifactKeys],
    output_artifact_keys: [...job.outputArtifactKeys],
    schema_version: job.schemaVersion,
    created_at: job.createdAt,
    available_at: job.availableAt,
    leased_until: job.leasedUntil,
    started_at: job.startedAt,
    finished_at: job.finishedAt,
    last_error: job.lastError
      ? {
          code: job.lastError.code,
          message: job.lastError.message,
          classification: job.lastError.classification,
          occurred_at: job.lastError.occurredAt,
          details: job.lastError.details
        }
      : undefined
  };
}

export function mapDtoToJob(dto: any): VideoAuditJob {
  assertJobSchemaVersion(dto);

  const raw = {
    id: dto.id,
    referenceAssetId: dto.referenceAssetId || dto.reference_asset_id,
    type: dto.type,
    status: dto.status,
    attempt: dto.attempt,
    maxAttempts: dto.maxAttempts || dto.max_attempts,
    idempotencyKey: dto.idempotencyKey || dto.idempotency_key,
    inputArtifactKeys: dto.inputArtifactKeys || dto.input_artifact_keys || [],
    outputArtifactKeys: dto.outputArtifactKeys || dto.output_artifact_keys || [],
    schemaVersion: dto.schemaVersion || dto.schema_version,
    createdAt: dto.createdAt || dto.created_at,
    availableAt: dto.availableAt || dto.available_at,
    leasedUntil: dto.leasedUntil || dto.leased_until,
    startedAt: dto.startedAt || dto.started_at,
    finishedAt: dto.finishedAt || dto.finished_at,
    lastError: (dto.lastError || dto.last_error)
      ? {
          code: (dto.lastError || dto.last_error).code,
          message: (dto.lastError || dto.last_error).message,
          classification: (dto.lastError || dto.last_error).classification,
          occurredAt: (dto.lastError || dto.last_error).occurredAt || (dto.lastError || dto.last_error).occurred_at,
          details: (dto.lastError || dto.last_error).details
        }
      : undefined
  };

  return VideoAuditJobSchema.parse(raw);
}

export function toDomainJob(raw: any): VideoAuditJob {
  return mapDtoToJob(raw);
}

export function toDomainArtifactManifest(raw: any): ArtifactManifest {
  assertArtifactManifestSchemaVersion(raw);
  const parsed = ArtifactManifestSchema.parse(raw);
  return parsed;
}

export function parseAndValidateArtifactManifest(data: unknown): ArtifactManifest {
  return toDomainArtifactManifest(data);
}

export function parseAndValidateAuditEvent(data: unknown): AuditEvent {
  return AuditEventSchema.parse(data);
}

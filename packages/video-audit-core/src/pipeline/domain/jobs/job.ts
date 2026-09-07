/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/jobs/job.ts"
# purpose: "Canonical VideoAuditJob Entity, Job Status, Types, Payload and Error Classification Domain Model."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const AuditJobTypeSchema = z.enum([
  'ingestion',
  'transcription',
  'scene_extraction',
  'ocr',
  'visual_detection',
  'audio_analysis',
  'report_generation'
]);

export type AuditJobType = z.infer<typeof AuditJobTypeSchema>;

export const AuditJobStatusSchema = z.enum([
  'queued',
  'leased',
  'running',
  'succeeded',
  'retryable_error',
  'permanent_error',
  'cancelled'
]);

export type AuditJobStatus = z.infer<typeof AuditJobStatusSchema>;

export const JobErrorClassification = z.enum([
  'retryable',
  'permanent',
  'manual_review'
]);

export type JobErrorClassification = z.infer<typeof JobErrorClassification>;

export const JobErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  classification: JobErrorClassification,
  occurredAt: z.string(),
  details: z.record(z.unknown()).optional()
});

export type JobError = z.infer<typeof JobErrorSchema>;

export const VideoAuditJobSchema = z.object({
  id: z.string(),
  referenceAssetId: z.string(),
  type: AuditJobTypeSchema,
  status: AuditJobStatusSchema,
  attempt: z.number().int().min(1),
  maxAttempts: z.number().int().min(1),
  idempotencyKey: z.string(),
  inputArtifactKeys: z.array(z.string()),
  outputArtifactKeys: z.array(z.string()),
  schemaVersion: z.string(),
  createdAt: z.string(),
  availableAt: z.string(),
  leasedUntil: z.string().optional(),
  leasedBy: z.string().optional(),
  leaseToken: z.string().optional(),
  startedAt: z.string().optional(),
  finishedAt: z.string().optional(),
  payload: z.record(z.unknown()).optional(),
  lastError: JobErrorSchema.optional()
});

export type VideoAuditJob = z.infer<typeof VideoAuditJobSchema>;

export interface SubmitAuditJobInput {
  referenceAssetId: string;
  type: AuditJobType;
  inputVersion?: string;
  processorVersion?: string;
  idempotencyKey?: string;
  maxAttempts?: number;
  correlationId?: string;
  inputArtifactKeys?: string[];
  actorId?: string;
  payload?: Record<string, unknown>;
}

export function createAuditJob(input: SubmitAuditJobInput, nowIso?: string): VideoAuditJob {
  const ts = nowIso ?? new Date().toISOString();
  const inputVersion = input.inputVersion ?? 'v1';
  const processorVersion = input.processorVersion ?? 'default-v1';
  const key =
    input.idempotencyKey ??
    `${input.referenceAssetId}:${input.type}:${inputVersion}:${processorVersion}`;
  const id = `job_${key.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

  return {
    id,
    referenceAssetId: input.referenceAssetId,
    type: input.type,
    status: 'queued',
    attempt: 1,
    maxAttempts: input.maxAttempts ?? 4,
    idempotencyKey: key,
    inputArtifactKeys: input.inputArtifactKeys ?? [],
    outputArtifactKeys: [],
    schemaVersion: 'audit-job.v1',
    createdAt: ts,
    availableAt: ts,
    payload: input.payload
  };
}

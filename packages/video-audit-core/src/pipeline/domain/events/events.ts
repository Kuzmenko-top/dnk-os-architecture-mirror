/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/events/events.ts"
# purpose: "Canonical Versioned Event Schemas, Envelopes and Factories for Video Audit Pipeline."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';
import { AuditJobTypeSchema, JobErrorSchema } from '../jobs/job.js';
import { ArtifactManifestSchema } from '../artifacts/artifact.js';

export const AuditEventTypeSchema = z.enum([
  'ReferenceCreated.v1',
  'AuditJobCreated.v1',
  'AuditJobLeased.v1',
  'AuditJobRunning.v1',
  'AuditJobSucceeded.v1',
  'AuditJobRetryScheduled.v1',
  'AuditJobFailed.v1',
  'AuditJobCancelled.v1',
  'ArtifactCreated.v1',
  'AuditReportCreated.v1'
]);

export type AuditEventType = z.infer<typeof AuditEventTypeSchema>;

export const BaseAuditEventSchema = z.object({
  eventId: z.string().min(1),
  eventType: AuditEventTypeSchema,
  timestamp: z.string().datetime(),
  correlationId: z.string().min(1),
  actorId: z.string().min(1)
});

export const ReferenceCreatedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('ReferenceCreated.v1'),
  payload: z.object({
    referenceAssetId: z.string().min(1),
    title: z.string(),
    sourceUrl: z.string().optional(),
    platform: z.string().optional(),
    rawSha256: z.string().min(1),
    durationSeconds: z.number().positive()
  })
});
export type ReferenceCreatedEvent = z.infer<typeof ReferenceCreatedEventSchema>;

export const AuditJobCreatedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobCreated.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    idempotencyKey: z.string().min(1),
    attempt: z.number().int().min(1),
    maxAttempts: z.number().int().min(1),
    availableAt: z.string().datetime()
  })
});
export type AuditJobCreatedEvent = z.infer<typeof AuditJobCreatedEventSchema>;

export const AuditJobLeasedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobLeased.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    workerId: z.string().min(1),
    leasedUntil: z.string().datetime(),
    attempt: z.number().int().min(1)
  })
});
export type AuditJobLeasedEvent = z.infer<typeof AuditJobLeasedEventSchema>;

export const AuditJobRunningEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobRunning.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    workerId: z.string().min(1),
    startedAt: z.string().datetime(),
    attempt: z.number().int().min(1)
  })
});
export type AuditJobRunningEvent = z.infer<typeof AuditJobRunningEventSchema>;

export const AuditJobSucceededEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobSucceeded.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    workerId: z.string().min(1),
    outputArtifactKeys: z.array(z.string()),
    finishedAt: z.string().datetime(),
    attempt: z.number().int().min(1)
  })
});
export type AuditJobSucceededEvent = z.infer<typeof AuditJobSucceededEventSchema>;

export const AuditJobRetryScheduledEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobRetryScheduled.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    attempt: z.number().int().min(1),
    nextAttempt: z.number().int().min(1),
    availableAt: z.string().datetime(),
    error: JobErrorSchema
  })
});
export type AuditJobRetryScheduledEvent = z.infer<typeof AuditJobRetryScheduledEventSchema>;

export const AuditJobFailedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobFailed.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    attempt: z.number().int().min(1),
    error: JobErrorSchema,
    finishedAt: z.string().datetime()
  })
});
export type AuditJobFailedEvent = z.infer<typeof AuditJobFailedEventSchema>;

export const AuditJobCancelledEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditJobCancelled.v1'),
  payload: z.object({
    jobId: z.string().min(1),
    referenceAssetId: z.string().min(1),
    jobType: AuditJobTypeSchema,
    reason: z.string().optional(),
    cancelledAt: z.string().datetime()
  })
});
export type AuditJobCancelledEvent = z.infer<typeof AuditJobCancelledEventSchema>;

export const ArtifactCreatedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('ArtifactCreated.v1'),
  payload: z.object({
    manifest: ArtifactManifestSchema
  })
});
export type ArtifactCreatedEvent = z.infer<typeof ArtifactCreatedEventSchema>;

export const AuditReportCreatedEventSchema = BaseAuditEventSchema.extend({
  eventType: z.literal('AuditReportCreated.v1'),
  payload: z.object({
    referenceAssetId: z.string().min(1),
    reportId: z.string().min(1),
    reportKey: z.string().min(1),
    aggregateStatus: z.string().min(1),
    sha256: z.string().min(1),
    createdAt: z.string().datetime(),
    metadata: z.record(z.unknown()).optional()
  })
});
export type AuditReportCreatedEvent = z.infer<typeof AuditReportCreatedEventSchema>;

export const AuditEventSchema = z.discriminatedUnion('eventType', [
  ReferenceCreatedEventSchema,
  AuditJobCreatedEventSchema,
  AuditJobLeasedEventSchema,
  AuditJobRunningEventSchema,
  AuditJobSucceededEventSchema,
  AuditJobRetryScheduledEventSchema,
  AuditJobFailedEventSchema,
  AuditJobCancelledEventSchema,
  ArtifactCreatedEventSchema,
  AuditReportCreatedEventSchema
]);

export type AuditEvent = z.infer<typeof AuditEventSchema>;

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/idempotency/key.ts"
# purpose: "Deterministic Idempotency Key Builder and Parser for Video Audit Jobs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AuditJobType, AuditJobTypeSchema } from '../jobs/job.js';

export interface IdempotencyComponents {
  referenceAssetId: string;
  jobType: AuditJobType;
  inputVersion: string;
  processorVersion: string;
}

export function buildIdempotencyKey(components: IdempotencyComponents): string {
  const { referenceAssetId, jobType, inputVersion, processorVersion } = components;
  if (!referenceAssetId || !jobType || !inputVersion || !processorVersion) {
    throw new Error('All idempotency components (referenceAssetId, jobType, inputVersion, processorVersion) must be non-empty strings.');
  }
  return `${referenceAssetId}:${jobType}:${inputVersion}:${processorVersion}`;
}

export const generateIdempotencyKey = buildIdempotencyKey;

export function parseIdempotencyKey(key: string): IdempotencyComponents {
  const parts = key.split(':');
  if (parts.length < 4) {
    throw new Error(`Invalid idempotency key format: '${key}'. Expected '{referenceAssetId}:{jobType}:{inputVersion}:{processorVersion}'`);
  }
  const referenceAssetId = parts[0];
  const jobTypeParsed = AuditJobTypeSchema.safeParse(parts[1]);
  if (!jobTypeParsed.success) {
    throw new Error(`Invalid job type '${parts[1]}' in idempotency key '${key}'`);
  }
  const inputVersion = parts[2];
  const processorVersion = parts.slice(3).join(':'); // handles versions with colons if any

  return {
    referenceAssetId,
    jobType: jobTypeParsed.data,
    inputVersion,
    processorVersion
  };
}

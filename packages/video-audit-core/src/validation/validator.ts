/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/validation/validator.ts"
# purpose: "Runtime Schema Validator for Video Intelligence Contracts."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReportSchema, VideoAuditReport } from '../schemas/audit.js';
import { ScriptDocumentSchema, ScriptDocument } from '../schemas/script.js';
import { ProsodyDocumentSchema, ProsodyDocument } from '../schemas/prosody.js';
import { ShotListSchema, ShotList } from '../schemas/shotlist.js';
import { AdaptationResultSchema, AdaptationResult } from '../schemas/adaptation.js';
import { ContractValidationError, SchemaVersionMismatchError } from './errors.js';

export function validateVideoAuditReport(data: unknown): VideoAuditReport {
  if (typeof data === 'object' && data !== null && 'schemaVersion' in data) {
    const sv = (data as { schemaVersion?: unknown }).schemaVersion;
    if (sv !== 'video-audit.v1') {
      throw new SchemaVersionMismatchError('video-audit.v1', String(sv));
    }
  }

  const result = VideoAuditReportSchema.safeParse(data);
  if (!result.success) {
    throw new ContractValidationError(
      'Invalid VideoAuditReport contract payload',
      result.error.errors
    );
  }
  return result.data;
}

export function validateScriptDocument(data: unknown): ScriptDocument {
  if (typeof data === 'object' && data !== null && 'schemaVersion' in data) {
    const sv = (data as { schemaVersion?: unknown }).schemaVersion;
    if (sv !== 'script.v1') {
      throw new SchemaVersionMismatchError('script.v1', String(sv));
    }
  }

  const result = ScriptDocumentSchema.safeParse(data);
  if (!result.success) {
    throw new ContractValidationError(
      'Invalid ScriptDocument contract payload',
      result.error.errors
    );
  }
  return result.data;
}

export function validateProsodyDocument(data: unknown): ProsodyDocument {
  if (typeof data === 'object' && data !== null && 'schemaVersion' in data) {
    const sv = (data as { schemaVersion?: unknown }).schemaVersion;
    if (sv !== 'prosody.v1') {
      throw new SchemaVersionMismatchError('prosody.v1', String(sv));
    }
  }

  const result = ProsodyDocumentSchema.safeParse(data);
  if (!result.success) {
    throw new ContractValidationError(
      'Invalid ProsodyDocument contract payload',
      result.error.errors
    );
  }
  return result.data;
}

export function validateShotList(data: unknown): ShotList {
  if (typeof data === 'object' && data !== null && 'schemaVersion' in data) {
    const sv = (data as { schemaVersion?: unknown }).schemaVersion;
    if (sv !== 'shot-list.v1') {
      throw new SchemaVersionMismatchError('shot-list.v1', String(sv));
    }
  }

  const result = ShotListSchema.safeParse(data);
  if (!result.success) {
    throw new ContractValidationError(
      'Invalid ShotList contract payload',
      result.error.errors
    );
  }
  return result.data;
}

export function validateAdaptationResult(data: unknown): AdaptationResult {
  if (typeof data === 'object' && data !== null && 'schemaVersion' in data) {
    const sv = (data as { schemaVersion?: unknown }).schemaVersion;
    if (sv !== 'adaptation.v1') {
      throw new SchemaVersionMismatchError('adaptation.v1', String(sv));
    }
  }

  const result = AdaptationResultSchema.safeParse(data);
  if (!result.success) {
    throw new ContractValidationError(
      'Invalid AdaptationResult contract payload',
      result.error.errors
    );
  }
  return result.data;
}

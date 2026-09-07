/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/serializers/json.ts"
# purpose: "Pure JSON Serializers for Video Intelligence & Adaptation Contracts."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReport } from '../schemas/audit.js';
import { ScriptDocument } from '../schemas/script.js';
import { ProsodyDocument } from '../schemas/prosody.js';
import { ShotList } from '../schemas/shotlist.js';
import { AdaptationResult } from '../schemas/adaptation.js';
import {
  validateVideoAuditReport,
  validateScriptDocument,
  validateProsodyDocument,
  validateShotList,
  validateAdaptationResult
} from '../validation/validator.js';

export function serializeContract<T>(data: T): string {
  return JSON.stringify(data, null, 2);
}

export function deserializeVideoAuditReport(jsonString: string): VideoAuditReport {
  const parsed = JSON.parse(jsonString);
  return validateVideoAuditReport(parsed);
}

export function deserializeScriptDocument(jsonString: string): ScriptDocument {
  const parsed = JSON.parse(jsonString);
  return validateScriptDocument(parsed);
}

export function deserializeProsodyDocument(jsonString: string): ProsodyDocument {
  const parsed = JSON.parse(jsonString);
  return validateProsodyDocument(parsed);
}

export function deserializeShotList(jsonString: string): ShotList {
  const parsed = JSON.parse(jsonString);
  return validateShotList(parsed);
}

export function deserializeAdaptationResult(jsonString: string): AdaptationResult {
  const parsed = JSON.parse(jsonString);
  return validateAdaptationResult(parsed);
}

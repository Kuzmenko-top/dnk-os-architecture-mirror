/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/ports/adaptation-repository.ts"
# purpose: "Port interface for Immutable and Idempotent Adaptation Storage."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AdaptationResult, AdaptationRequest } from '../../schemas/adaptation.js';

export interface AdaptationStorageVersions {
  promptVersion: string;
  adaptationPolicyVersion: string;
}

export interface AdaptationRepository {
  getById(id: string): Promise<AdaptationResult | null>;
  findByKey(idempotencyKey: string): Promise<AdaptationResult | null>;
  save(idempotencyKey: string, result: AdaptationResult): Promise<void>;
  generateKey(request: AdaptationRequest, versions: AdaptationStorageVersions): string;
}

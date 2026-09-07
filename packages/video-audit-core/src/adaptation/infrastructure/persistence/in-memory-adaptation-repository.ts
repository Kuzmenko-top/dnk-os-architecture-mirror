/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/infrastructure/persistence/in-memory-adaptation-repository.ts"
# purpose: "In-memory Idempotent & Immutable Adaptation Repository."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import crypto from 'crypto';
import { AdaptationResult, AdaptationRequest } from '../../../schemas/adaptation.js';
import { AdaptationRepository, AdaptationStorageVersions } from '../../ports/adaptation-repository.js';

export class InMemoryAdaptationRepository implements AdaptationRepository {
  private readonly storage = new Map<string, AdaptationResult>();
  private readonly idIndex = new Map<string, string>(); // id -> idempotencyKey

  public generateKey(request: AdaptationRequest, versions: AdaptationStorageVersions): string {
    const rawContent = JSON.stringify({
      sourceAuditId: request.sourceAuditId,
      brandId: request.brandId,
      niche: request.niche,
      audience: request.audience,
      language: request.language,
      targetDurationMs: request.targetDurationMs,
      tone: request.tone,
      desiredMechanisms: [...request.desiredMechanisms].sort(),
      forbiddenElements: [...request.forbiddenElements].sort(),
      approvedFactIds: [...request.approvedFactIds].sort(),
      promptVersion: versions.promptVersion,
      adaptationPolicyVersion: versions.adaptationPolicyVersion,
    });

    const hash = crypto.createHash('sha256').update(rawContent).digest('hex');
    return `adapt:${request.brandId}:${request.sourceAuditId}:${hash}`;
  }

  public async getById(id: string): Promise<AdaptationResult | null> {
    const key = this.idIndex.get(id);
    if (!key) return null;
    return this.findByKey(key);
  }

  public async findByKey(idempotencyKey: string): Promise<AdaptationResult | null> {
    const item = this.storage.get(idempotencyKey);
    if (!item) return null;
    // Return structured clone to guarantee immutability
    return structuredClone(item);
  }

  public async save(idempotencyKey: string, result: AdaptationResult): Promise<void> {
    if (this.storage.has(idempotencyKey)) {
      // Immutable invariant: do not overwrite
      return;
    }
    const cloned = structuredClone(result);
    this.storage.set(idempotencyKey, cloned);
    this.idIndex.set(result.id, idempotencyKey);
  }

  public clear(): void {
    this.storage.clear();
    this.idIndex.clear();
  }
}

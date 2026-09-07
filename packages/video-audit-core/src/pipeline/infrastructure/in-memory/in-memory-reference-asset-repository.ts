/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/in-memory/in-memory-reference-asset-repository.ts"
# purpose: "In-Memory Thread-Safe ReferenceAsset Repository with Content-Hash and Telegram Unique-ID Indexes."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import {
  ReferenceAssetRepository,
  ReferenceAssetFilter
} from '../../ports/reference-asset-repository.js';
import { ReferenceAsset } from '../../domain/assets/reference-asset.js';

export class InMemoryReferenceAssetRepository implements ReferenceAssetRepository {
  private readonly assetsById = new Map<string, ReferenceAsset>();
  private readonly assetsByHash = new Map<string, string>(); // SHA-256 -> id
  private readonly assetsByTelegramUniqueId = new Map<string, string>(); // telegramFileUniqueId -> id

  async getById(id: string): Promise<ReferenceAsset | null> {
    const asset = this.assetsById.get(id);
    return asset ? { ...asset } : null;
  }

  async getByContentHash(contentHash: string): Promise<ReferenceAsset | null> {
    const id = this.assetsByHash.get(contentHash);
    if (!id) return null;
    return this.getById(id);
  }

  async getByTelegramFileUniqueId(fileUniqueId: string): Promise<ReferenceAsset | null> {
    const id = this.assetsByTelegramUniqueId.get(fileUniqueId);
    if (!id) return null;
    return this.getById(id);
  }

  async create(asset: ReferenceAsset): Promise<ReferenceAsset> {
    if (this.assetsById.has(asset.id)) {
      throw new Error(`ReferenceAsset with ID '${asset.id}' already exists.`);
    }

    const copy = JSON.parse(JSON.stringify(asset)) as ReferenceAsset;
    this.assetsById.set(copy.id, copy);
    this.assetsByHash.set(copy.contentHash, copy.id);

    if (copy.telegramFileUniqueId) {
      this.assetsByTelegramUniqueId.set(copy.telegramFileUniqueId, copy.id);
    }

    return { ...copy };
  }

  async update(asset: ReferenceAsset): Promise<ReferenceAsset> {
    if (!this.assetsById.has(asset.id)) {
      throw new Error(`ReferenceAsset with ID '${asset.id}' does not exist.`);
    }

    const copy = JSON.parse(JSON.stringify(asset)) as ReferenceAsset;
    this.assetsById.set(copy.id, copy);
    this.assetsByHash.set(copy.contentHash, copy.id);

    if (copy.telegramFileUniqueId) {
      this.assetsByTelegramUniqueId.set(copy.telegramFileUniqueId, copy.id);
    }

    return { ...copy };
  }

  async list(filter?: ReferenceAssetFilter): Promise<ReferenceAsset[]> {
    let list = Array.from(this.assetsById.values());

    if (filter?.sourcePlatform) {
      list = list.filter((a) => a.sourcePlatform === filter.sourcePlatform);
    }

    if (filter?.createdBy) {
      list = list.filter((a) => a.createdBy === filter.createdBy);
    }

    const offset = filter?.offset ?? 0;
    const limit = filter?.limit ?? list.length;

    return list.slice(offset, offset + limit).map((a) => ({ ...a }));
  }

  async clear(): Promise<void> {
    this.assetsById.clear();
    this.assetsByHash.clear();
    this.assetsByTelegramUniqueId.clear();
  }
}

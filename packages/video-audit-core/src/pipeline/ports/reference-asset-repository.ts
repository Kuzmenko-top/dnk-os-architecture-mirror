/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/reference-asset-repository.ts"
# purpose: "Port Interface for ReferenceAsset Persistence and Hash/Telegram Indexes."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ReferenceAsset, SourcePlatform } from '../domain/assets/reference-asset.js';

export interface ReferenceAssetFilter {
  sourcePlatform?: SourcePlatform;
  createdBy?: string;
  limit?: number;
  offset?: number;
}

export interface ReferenceAssetRepository {
  getById(id: string): Promise<ReferenceAsset | null>;
  getByContentHash(contentHash: string): Promise<ReferenceAsset | null>;
  getByTelegramFileUniqueId(fileUniqueId: string): Promise<ReferenceAsset | null>;
  create(asset: ReferenceAsset): Promise<ReferenceAsset>;
  update(asset: ReferenceAsset): Promise<ReferenceAsset>;
  list(filter?: ReferenceAssetFilter): Promise<ReferenceAsset[]>;
}

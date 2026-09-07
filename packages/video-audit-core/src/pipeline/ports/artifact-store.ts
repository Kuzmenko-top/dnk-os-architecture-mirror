/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/artifact-store.ts"
# purpose: "Port Interface for Versioned Binary Artifact Storage and Manifest Retrieval."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ArtifactInput, ArtifactManifest } from '../domain/artifacts/artifact.js';

export interface ArtifactStore {
  put(input: ArtifactInput): Promise<ArtifactManifest>;
  get(key: string): Promise<Buffer | Uint8Array>;
  getText(key: string): Promise<string>;
  getJson<T = unknown>(key: string): Promise<T>;
  exists(key: string): Promise<boolean>;
  delete(key: string): Promise<void>;
  getManifest(key: string): Promise<ArtifactManifest | null>;
  listManifests(referenceAssetId: string): Promise<ArtifactManifest[]>;
}

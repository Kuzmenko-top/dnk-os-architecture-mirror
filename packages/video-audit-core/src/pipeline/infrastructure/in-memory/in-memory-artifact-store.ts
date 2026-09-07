/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/in-memory/in-memory-artifact-store.ts"
# purpose: "In-Memory Artifact Store with SHA-256 Checksums and Manifest Indexing."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { createHash } from 'node:crypto';
import { ArtifactInput, ArtifactManifest, ArtifactManifestSchema } from '../../domain/artifacts/artifact.js';
import { ArtifactStore } from '../../ports/artifact-store.js';

export class InMemoryArtifactStore implements ArtifactStore {
  private storage = new Map<string, Buffer>();
  private manifests = new Map<string, ArtifactManifest>();

  async put(input: ArtifactInput): Promise<ArtifactManifest> {
    let buffer: Buffer;
    if (Buffer.isBuffer(input.data)) {
      buffer = input.data;
    } else if (input.data instanceof Uint8Array) {
      buffer = Buffer.from(input.data.buffer, input.data.byteOffset, input.data.byteLength);
    } else if (typeof input.data === 'string') {
      buffer = Buffer.from(input.data, 'utf-8');
    } else {
      buffer = Buffer.from(JSON.stringify(input.data), 'utf-8');
    }

    const sha256 = createHash('sha256').update(buffer).digest('hex');
    const byteSize = buffer.byteLength;
    const createdAt = new Date().toISOString();

    const manifest: ArtifactManifest = {
      key: input.key,
      referenceAssetId: input.referenceAssetId,
      jobId: input.jobId,
      jobType: input.jobType,
      sha256,
      byteSize,
      mimeType: input.mimeType,
      schemaVersion: 'artifact-manifest.v1',
      createdAt,
      metadata: input.metadata ? { ...input.metadata } : undefined
    };

    ArtifactManifestSchema.parse(manifest);

    this.storage.set(input.key, buffer);
    this.manifests.set(input.key, manifest);

    return { ...manifest };
  }

  async get(key: string): Promise<Buffer> {
    const data = this.storage.get(key);
    if (!data) {
      throw new Error(`Artifact not found for key: ${key}`);
    }
    return Buffer.from(data);
  }

  async getText(key: string): Promise<string> {
    const buf = await this.get(key);
    return buf.toString('utf-8');
  }

  async getJson<T = unknown>(key: string): Promise<T> {
    const text = await this.getText(key);
    return JSON.parse(text) as T;
  }

  async exists(key: string): Promise<boolean> {
    return this.storage.has(key);
  }

  async delete(key: string): Promise<void> {
    this.storage.delete(key);
    this.manifests.delete(key);
  }

  async getManifest(key: string): Promise<ArtifactManifest | null> {
    const m = this.manifests.get(key);
    return m ? { ...m } : null;
  }

  async listManifests(referenceAssetId: string): Promise<ArtifactManifest[]> {
    const results: ArtifactManifest[] = [];
    for (const m of this.manifests.values()) {
      if (m.referenceAssetId === referenceAssetId) {
        results.push({ ...m });
      }
    }
    return results;
  }
}

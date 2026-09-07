/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/index.ts"
# purpose: "Public entry point for @dnk/video-audit-core module."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export * from './schemas/adaptation.js';
export * from './schemas/audit.js';
export * from './schemas/multimodal-audit.js';
export * from './schemas/common.js';
export * from './schemas/prosody.js';
export * from './schemas/reference.js';
export * from './schemas/script.js';
export * from './schemas/shotlist.js';
export * from './schemas/similarity.js';
export * from './schemas/brand.js';

export * from './validation/errors.js';
export * from './validation/validator.js';

export * from './governance/evidence.js';
export * from './governance/similarity-policy.js';

export * from './serializers/json.js';

export * from './adaptation/application/adaptation-pipeline.js';
export * from './adaptation/domain/mechanism-extractor.js';
export * from './adaptation/domain/brand/reburn-profile.js';
export * from './adaptation/domain/script-writer/script-writer.js';
export * from './adaptation/domain/script-writer/live-llm-script-writer.js';
export * from './adaptation/domain/guards/brand-guard.js';
export * from './adaptation/domain/guards/similarity-guard.js';
export * from './adaptation/domain/guards/human-review-policy.js';
export * from './adaptation/domain/transformers/prosody-transformer.js';
export * from './adaptation/domain/transformers/shotlist-generator.js';

export * from './fixtures/educational-short.js';
export * from './fixtures/product-demo.js';
export * from './fixtures/reburn-reference.js';
export * from './fixtures/talking-head.js';

export * from './pipeline/index.js';

// Explicit re-exports to resolve TS2308 ambiguity
export type { Scene } from './schemas/audit.js';
export { SceneSchema } from './schemas/audit.js';
export { ReferenceAssetSchema, type ReferenceAsset } from './schemas/reference.js';

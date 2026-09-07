/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/id-generator.ts"
# purpose: "Port Interface for ID Generation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

export interface IdGenerator {
  generate(prefix?: string): string;
}

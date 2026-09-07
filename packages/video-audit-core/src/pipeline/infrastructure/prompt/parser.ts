/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/parser.ts"
# purpose: "Safe JSON Extraction, JsonRepairPolicy & SchemaValidator for LLM outputs."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditResultSchema, MultimodalAuditResult } from '../../../schemas/multimodal-audit.js';

export class JsonRepairPolicy {
  /**
   * Safely repair JSON without changing semantics.
   * Only allows structural cleanup like removing fences, trimming surrounding prose, and stripping trailing commas.
   */
  repair(raw: string): string {
    let cleaned = raw.trim();

    // 1. Remove markdown code blocks if present
    const markdownFenceRegex = /```(?:json)?\s*([\s\S]*?)\s*```/;
    const fenceMatch = cleaned.match(markdownFenceRegex);
    if (fenceMatch) {
      cleaned = fenceMatch[1].trim();
    }

    // 2. Extract JSON object/array bounds to ignore extra prose around it
    const firstBrace = cleaned.indexOf('{');
    const lastBrace = cleaned.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
      cleaned = cleaned.substring(firstBrace, lastBrace + 1);
    }

    // 3. Remove trailing commas (e.g. ,} or ,] )
    cleaned = cleaned.replace(/,(\s*[}\]])/g, '$1');

    return cleaned;
  }
}

export class SchemaValidator {
  validate(parsed: unknown): MultimodalAuditResult {
    // Perform robust Zod validation
    const result = MultimodalAuditResultSchema.safeParse(parsed);
    if (!result.success) {
      const errorMsg = result.error.errors.map(e => `${e.path.join('.')}: ${e.message}`).join(', ');
      throw new Error(`Schema validation failed: ${errorMsg}`);
    }

    // Explicitly reject if schemaVersion is wrong
    if (result.data.schemaVersion !== 'multimodal-audit.v1') {
      throw new Error(`Wrong schemaVersion: Expected 'multimodal-audit.v1' but got '${result.data.schemaVersion}'`);
    }

    return result.data;
  }
}

export class LLMResponseParser {
  private repairPolicy = new JsonRepairPolicy();
  private validator = new SchemaValidator();

  parse(raw: string): MultimodalAuditResult {
    // Try simple parse first
    try {
      const parsed = JSON.parse(raw);
      return this.validator.validate(parsed);
    } catch (err) {
      // If fails, apply repair policy and try again once
      try {
        const repaired = this.repairPolicy.repair(raw);
        const parsedRepaired = JSON.parse(repaired);
        return this.validator.validate(parsedRepaired);
      } catch (repairErr: any) {
        throw new Error(`Failed to parse response JSON even after repair: ${repairErr.message || repairErr}`);
      }
    }
  }
}

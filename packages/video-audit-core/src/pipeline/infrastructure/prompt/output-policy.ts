/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/prompt/output-policy.ts"
# purpose: "Audit Output Policy to govern raw response acceptance, errors, and manual review routing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MultimodalAuditResult } from '../../../schemas/multimodal-audit.js';
import { MultimodalAuditInput } from '../../ports/multimodal-audit-provider.js';
import { LLMResponseParser } from './parser.js';
import { EvidenceClaimValidator, ValidationIssue } from './claim-validator.js';

export interface PolicyCheckResult {
  status: 'accepted' | 'rejected' | 'manual_review';
  result?: MultimodalAuditResult;
  warnings: string[];
  errors: string[];
}

export class AuditOutputPolicy {
  private parser = new LLMResponseParser();
  private claimValidator = new EvidenceClaimValidator();
  private maxResponseChars = 1048576; // 1MB size limit

  apply(
    rawResponse: string,
    input: MultimodalAuditInput,
    inputWarnings: string[] = []
  ): PolicyCheckResult {
    const warnings: string[] = [...inputWarnings];
    const errors: string[] = [];

    // 1. Check for oversized output
    if (rawResponse.length > this.maxResponseChars) {
      errors.push(`Response oversized: ${rawResponse.length} characters exceeds limit of ${this.maxResponseChars}`);
      return {
        status: 'rejected',
        warnings,
        errors
      };
    }

    // 2. Parse and validate JSON Schema
    let parsedResult: MultimodalAuditResult;
    try {
      parsedResult = this.parser.parse(rawResponse);
    } catch (err: any) {
      errors.push(err.message || String(err));
      return {
        status: 'rejected',
        warnings,
        errors
      };
    }

    // 3. Apply Evidence Governance and Claim validation rules
    const validationIssues = this.claimValidator.validate(parsedResult, input);

    for (const issue of validationIssues) {
      if (issue.type === 'error') {
        errors.push(issue.message);
      } else {
        warnings.push(issue.message);
      }
    }

    // Check for contradictory claims or critical errors that route to manual review
    let status: 'accepted' | 'rejected' | 'manual_review' = 'accepted';

    if (errors.length > 0) {
      // If there are semantic errors like hallucinated IDs, invalid timeRange, or missing evidence refs,
      // we route them to manual_review instead of a silent outright failure if needed, or outright reject.
      // The prompt contract states:
      // "Invalid output has controlled retry/manual-review path."
      // Let's mark as 'rejected' for critical parser/schema failures, but 'manual_review' for policy/governance errors
      const hasSchemaFailure = errors.some(e => e.includes('Schema validation failed') || e.includes('Failed to parse'));
      if (hasSchemaFailure) {
        status = 'rejected';
      } else {
        status = 'manual_review';
      }
    }

    // Merge warnings into the final parsed result warnings array
    if (status === 'accepted' || status === 'manual_review') {
      parsedResult.warnings = Array.from(new Set([
        ...(parsedResult.warnings ?? []),
        ...warnings
      ]));
    }

    return {
      status,
      result: parsedResult,
      warnings,
      errors
    };
  }
}

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/url-validator.ts"
# purpose: "Port Interface for SSRF URL Security Validation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { UrlValidationResult } from '../domain/ingestion/security.js';

export interface UrlSecurityValidatorPort {
  validateUrl(url: string): Promise<UrlValidationResult>;
}

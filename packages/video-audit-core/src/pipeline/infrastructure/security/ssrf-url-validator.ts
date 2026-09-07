/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/security/ssrf-url-validator.ts"
# purpose: "SSRF URL Security Validator Implementation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { UrlSecurityValidatorPort } from '../../ports/url-validator.js';
import { validateUrlForSsrf, UrlValidationResult } from '../../domain/ingestion/security.js';

export class SsrfUrlValidator implements UrlSecurityValidatorPort {
  async validateUrl(url: string): Promise<UrlValidationResult> {
    return validateUrlForSsrf(url);
  }
}

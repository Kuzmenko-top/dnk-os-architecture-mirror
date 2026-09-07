/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/ingestion/security-ssrf.test.ts"
# purpose: "Security Unit Tests for SSRF Prevention, IP Range Restrictions, and Safe URL Resolver."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { validateUrlForSsrf } from '../../../src/pipeline/domain/ingestion/security.js';
import { SsrfUrlValidator } from '../../../src/pipeline/infrastructure/security/ssrf-url-validator.js';

describe('SSRF Security Policy & URL Resolver', () => {
  const validator = new SsrfUrlValidator();

  it('allows safe HTTPS URLs', async () => {
    const res = await validator.validateUrl('https://cdn.example.com/assets/sample_video.mp4');
    expect(res.valid).toBe(true);
    expect(res.sanitizedUrl).toBe('https://cdn.example.com/assets/sample_video.mp4');
  });

  it('rejects non-HTTPS schemes (http, ftp, file, gopher)', async () => {
    const httpRes = validateUrlForSsrf('http://cdn.example.com/video.mp4');
    expect(httpRes.valid).toBe(false);
    expect(httpRes.reason).toMatch(/HTTPS scheme/i);

    const fileRes = validateUrlForSsrf('file:///etc/passwd');
    expect(fileRes.valid).toBe(false);
    expect(fileRes.reason).toMatch(/HTTPS scheme/i);
  });

  it('rejects loopback and localhost addresses', async () => {
    const urls = [
      'https://localhost/video.mp4',
      'https://127.0.0.1/video.mp4',
      'https://0.0.0.0/video.mp4',
      'https://[::1]/video.mp4'
    ];

    for (const url of urls) {
      const res = validateUrlForSsrf(url);
      expect(res.valid).toBe(false);
      expect(res.reason).toMatch(/Loopback|localhost/i);
    }
  });

  it('rejects RFC1918 private IP addresses', async () => {
    const privateUrls = [
      'https://10.0.0.1/video.mp4',
      'https://172.16.0.5/video.mp4',
      'https://192.168.1.1/video.mp4'
    ];

    for (const url of privateUrls) {
      const res = validateUrlForSsrf(url);
      expect(res.valid).toBe(false);
      expect(res.reason).toMatch(/Private IP/i);
    }
  });

  it('rejects AWS and Cloud Metadata endpoints', async () => {
    const metadataUrls = [
      'https://169.254.169.254/latest/meta-data/',
      'https://metadata.google.internal/computeMetadata/v1/'
    ];

    for (const url of metadataUrls) {
      const res = validateUrlForSsrf(url);
      expect(res.valid).toBe(false);
      expect(res.reason).toMatch(/Metadata endpoint|Private IP/i);
    }
  });

  it('rejects URLs with embedded credentials', async () => {
    const res = validateUrlForSsrf('https://admin:secret@cdn.example.com/video.mp4');
    expect(res.valid).toBe(false);
    expect(res.reason).toMatch(/embedded credentials/i);
  });
});

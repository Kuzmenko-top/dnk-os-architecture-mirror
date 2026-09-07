/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/ingestion/security.ts"
# purpose: "Ingestion Security Protocols: Path Traversal, Magic Byte Sniffing, Resource Limits, and SSRF Security."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MediaProbeResult } from '../assets/reference-asset.js';

export interface IngestionSecurityPolicy {
  maxByteSize: number; // default 500MB
  maxDurationMs: number; // default 600,000 ms (10 minutes)
  allowedContainers: Array<'mp4' | 'mov' | 'webm' | 'mkv'>;
  allowedMimes: string[];
}

export const DefaultIngestionSecurityPolicy: IngestionSecurityPolicy = {
  maxByteSize: 524_288_000,
  maxDurationMs: 600_000,
  allowedContainers: ['mp4', 'mov', 'webm', 'mkv'],
  allowedMimes: ['video/mp4', 'video/quicktime', 'video/webm', 'video/x-matroska']
};

export class IngestionSecurityError extends Error {
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'IngestionSecurityError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Sanitizes an incoming filename to prevent path traversal, null-byte injections,
 * and dangerous shell characters.
 */
export function sanitizeFilename(rawFilename?: string): string {
  if (!rawFilename || typeof rawFilename !== 'string' || !rawFilename.trim()) {
    return 'unnamed_asset.mp4';
  }

  // 1. Remove null bytes and control characters
  let clean = rawFilename.replace(/[\x00-\x1F\x7F]/g, '');

  // 2. Strip directory path traversal components (e.g. ../, ..\, /etc/passwd)
  clean = clean.replace(/^.*[\\/]/, '');

  // 3. Keep alphanumeric, dots, hyphens, underscores, spaces
  clean = clean.replace(/[^a-zA-Z0-9._\- ]/g, '_');

  // 4. Prevent hidden files or leading dots
  clean = clean.replace(/^\.+/, '');

  // 5. Truncate long filenames to safe length (max 128 chars)
  if (clean.length > 128) {
    const extIdx = clean.lastIndexOf('.');
    if (extIdx > 0 && extIdx > clean.length - 10) {
      const ext = clean.substring(extIdx);
      clean = clean.substring(0, 118) + ext;
    } else {
      clean = clean.substring(0, 128);
    }
  }

  return clean.trim() || 'unnamed_asset.mp4';
}

export interface SniffedMediaHeader {
  container: 'mp4' | 'mov' | 'webm' | 'mkv' | 'unknown';
  mimeType: string;
  isRecognized: boolean;
  isSpoofed: boolean;
  spoofReason?: string;
}

/**
 * Sniffs the magic bytes of the file buffer to accurately identify real container & prevent MIME spoofing.
 */
export function sniffMediaHeader(buffer: Uint8Array): SniffedMediaHeader {
  // 1. Check executable / script / archive signatures first regardless of length (min 4 bytes)
  if (buffer.length >= 4) {
    // Check ELF binary (\x7fELF)
    if (buffer[0] === 0x7f && buffer[1] === 0x45 && buffer[2] === 0x4c && buffer[3] === 0x46) {
      return {
        container: 'unknown',
        mimeType: 'application/x-executable',
        isRecognized: false,
        isSpoofed: true,
        spoofReason: 'Executable binary disguised as video'
      };
    }

    // Check Windows PE binary (MZ)
    if (buffer[0] === 0x4d && buffer[1] === 0x5a) {
      return {
        container: 'unknown',
        mimeType: 'application/x-dsexecutable',
        isRecognized: false,
        isSpoofed: true,
        spoofReason: 'Executable binary disguised as video'
      };
    }

    // Check Zip archive (PK\x03\x04)
    if (buffer[0] === 0x50 && buffer[1] === 0x4b && buffer[2] === 0x03 && buffer[3] === 0x04) {
      return {
        container: 'unknown',
        mimeType: 'application/zip',
        isRecognized: false,
        isSpoofed: true,
        spoofReason: 'Zip archive disguised as video'
      };
    }
  }

  const headerUtf8 = new TextDecoder('utf-8', { fatal: false }).decode(buffer.subarray(0, 64)).toLowerCase();
  if (
    headerUtf8.includes('<!doctype html') ||
    headerUtf8.includes('<html') ||
    headerUtf8.includes('<?xml') ||
    headerUtf8.includes('<script')
  ) {
    return {
      container: 'unknown',
      mimeType: 'text/html',
      isRecognized: false,
      isSpoofed: true,
      spoofReason: 'MIME spoofing detected: HTML / script content masquerading as video'
    };
  }

  if (buffer.length < 12) {
    return {
      container: 'unknown',
      mimeType: 'application/octet-stream',
      isRecognized: false,
      isSpoofed: true,
      spoofReason: 'Buffer too small for media container header'
    };
  }

  // 2. MP4 / MOV Check (ftyp box at byte 4-8)
  if (buffer[4] === 0x66 && buffer[5] === 0x74 && buffer[6] === 0x79 && buffer[7] === 0x70) {
    const brand = String.fromCharCode(buffer[8], buffer[9], buffer[10], buffer[11]);
    if (['qt  ', 'moov', 'mdat'].includes(brand)) {
      return {
        container: 'mov',
        mimeType: 'video/quicktime',
        isRecognized: true,
        isSpoofed: false
      };
    }
    return {
      container: 'mp4',
      mimeType: 'video/mp4',
      isRecognized: true,
      isSpoofed: false
    };
  }

  // 3. WebM / MKV Check (EBML header ID: 0x1A 0x45 0xDF 0xA3)
  if (buffer[0] === 0x1a && buffer[1] === 0x45 && buffer[2] === 0xdf && buffer[3] === 0xa3) {
    const subUtf8 = new TextDecoder('utf-8', { fatal: false }).decode(buffer.subarray(0, 100));
    if (subUtf8.includes('webm')) {
      return {
        container: 'webm',
        mimeType: 'video/webm',
        isRecognized: true,
        isSpoofed: false
      };
    }
    return {
      container: 'mkv',
      mimeType: 'video/x-matroska',
      isRecognized: true,
      isSpoofed: false
    };
  }

  return {
    container: 'unknown',
    mimeType: 'application/octet-stream',
    isRecognized: false,
    isSpoofed: true,
    spoofReason: 'Unrecognized or unsupported media container magic bytes'
  };
}

export function validateMediaPolicy(
  probe: MediaProbeResult,
  policy: IngestionSecurityPolicy = DefaultIngestionSecurityPolicy
): void {
  if (probe.isCorrupted) {
    throw new IngestionSecurityError(
      'CORRUPT_MEDIA',
      `Media container is corrupted or unparseable: ${probe.corruptionReason ?? 'Unknown error'}`,
      { probe }
    );
  }

  if (probe.byteSize > policy.maxByteSize) {
    throw new IngestionSecurityError(
      'FILE_TOO_LARGE',
      `File byte size (${probe.byteSize} bytes) exceeds maximum permitted limit (${policy.maxByteSize} bytes)`,
      { byteSize: probe.byteSize, maxByteSize: policy.maxByteSize }
    );
  }

  if (probe.durationMs > policy.maxDurationMs) {
    throw new IngestionSecurityError(
      'DURATION_TOO_LONG',
      `Media duration (${probe.durationMs} ms) exceeds maximum permitted limit (${policy.maxDurationMs} ms)`,
      { durationMs: probe.durationMs, maxDurationMs: policy.maxDurationMs }
    );
  }

  if (!policy.allowedContainers.includes(probe.container as any)) {
    throw new IngestionSecurityError(
      'UNSUPPORTED_CONTAINER',
      `Container format '${probe.container}' is not allowed by policy. Allowed: [${policy.allowedContainers.join(', ')}]`,
      { container: probe.container }
    );
  }
}

export interface UrlValidationResult {
  isValid: boolean;
  valid: boolean;
  url: string;
  sanitizedUrl?: string;
  rejectionReason?: string;
  reason?: string;
}

/**
 * Validates URLs against SSRF (Server-Side Request Forgery) attacks:
 * - Scheme MUST be https:
 * - Blocks localhost / 127.0.0.1 / ::1
 * - Blocks RFC 1918 Private IPv4 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
 * - Blocks Link-Local IPv4 (169.254.0.0/16)
 * - Blocks Cloud metadata IP (169.254.169.254) and metadata endpoints
 * - Blocks URLs with user credentials
 */
export function validateUrlForSsrf(urlString: string): UrlValidationResult {
  let parsed: URL;
  try {
    parsed = new URL(urlString);
  } catch {
    const msg = 'Invalid URL format';
    return {
      isValid: false,
      valid: false,
      url: urlString,
      rejectionReason: msg,
      reason: msg
    };
  }

  // 1. Strict scheme check
  if (parsed.protocol !== 'https:') {
    const msg = `Insecure or disallowed protocol: '${parsed.protocol}'. Only HTTPS scheme is permitted.`;
    return {
      isValid: false,
      valid: false,
      url: urlString,
      rejectionReason: msg,
      reason: msg
    };
  }

  // 2. Disallow embedded credentials
  if (parsed.username || parsed.password) {
    const msg = 'URLs containing embedded credentials are strictly forbidden.';
    return {
      isValid: false,
      valid: false,
      url: urlString,
      rejectionReason: msg,
      reason: msg
    };
  }

  const hostname = parsed.hostname.toLowerCase();

  // 3. Block localhost, loopback, metadata hostnames
  if (
    hostname === 'localhost' ||
    hostname.endsWith('.localhost') ||
    hostname === '127.0.0.1' ||
    hostname === '0.0.0.0' ||
    hostname === '::1' ||
    hostname === '[::1]' ||
    hostname === 'metadata.google.internal' ||
    hostname.includes('metadata') ||
    hostname === 'instance-data'
  ) {
    const msg = `Disallowed host target '${hostname}'. Localhost, loopback, and Metadata endpoint endpoints are blocked (Private IP / Metadata endpoint).`;
    return {
      isValid: false,
      valid: false,
      url: urlString,
      rejectionReason: msg,
      reason: msg
    };
  }

  // 4. Private IPv4 Range Checks
  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
  const match = hostname.match(ipv4Regex);
  if (match) {
    const p1 = parseInt(match[1], 10);
    const p2 = parseInt(match[2], 10);

    // 10.0.0.0/8
    if (p1 === 10) {
      const msg = `Private IP network range '10.0.0.0/8' is blocked for SSRF security.`;
      return { isValid: false, valid: false, url: urlString, rejectionReason: msg, reason: msg };
    }

    // 172.16.0.0/12
    if (p1 === 172 && p2 >= 16 && p2 <= 31) {
      const msg = `Private IP network range '172.16.0.0/12' is blocked for SSRF security.`;
      return { isValid: false, valid: false, url: urlString, rejectionReason: msg, reason: msg };
    }

    // 192.168.0.0/16
    if (p1 === 192 && p2 === 168) {
      const msg = `Private IP network range '192.168.0.0/16' is blocked for SSRF security.`;
      return { isValid: false, valid: false, url: urlString, rejectionReason: msg, reason: msg };
    }

    // 169.254.0.0/16 (Link Local & AWS/GCP Metadata)
    if (p1 === 169 && p2 === 254) {
      const msg = `Metadata endpoint & Link-Local Private IP range '169.254.0.0/16' is strictly blocked.`;
      return { isValid: false, valid: false, url: urlString, rejectionReason: msg, reason: msg };
    }

    // 127.0.0.0/8
    if (p1 === 127) {
      const msg = `Loopback Private IP range '127.0.0.0/8' is blocked.`;
      return { isValid: false, valid: false, url: urlString, rejectionReason: msg, reason: msg };
    }
  }

  return {
    isValid: true,
    valid: true,
    url: urlString,
    sanitizedUrl: parsed.toString()
  };
}

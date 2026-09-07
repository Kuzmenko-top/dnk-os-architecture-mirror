/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/infrastructure/media-probe/deterministic-media-probe.ts"
# purpose: "Deterministic Media Probe Implementation with Magic-Byte Inspection, Hash Computation, and Corruption Checking."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import createHash from 'crypto';
import { MediaProbePort } from '../../ports/media-probe.js';
import { MediaProbeResult } from '../../domain/assets/reference-asset.js';
import {
  sniffMediaHeader,
  validateMediaPolicy,
  DefaultIngestionSecurityPolicy,
  IngestionSecurityPolicy,
  IngestionSecurityError
} from '../../domain/ingestion/security.js';

export interface DeterministicProbeOptions {
  overrideDurationMs?: number;
  overrideWidth?: number;
  overrideHeight?: number;
  overrideFrameRate?: number;
  overrideHasAudio?: boolean;
  overrideHasVideo?: boolean;
  overrideVideoCodec?: string;
  overrideAudioCodec?: string;
  simulateCorrupted?: boolean;
  corruptionReason?: string;
  maxByteSize?: number;
  maxDurationMs?: number;
  policy?: IngestionSecurityPolicy;
}

export class DeterministicMediaProbe implements MediaProbePort {
  constructor(private readonly defaultOptions: DeterministicProbeOptions = {}) {}

  async probeBuffer(
    buffer: Uint8Array,
    options?: { filename?: string; declaredMime?: string } & DeterministicProbeOptions
  ): Promise<MediaProbeResult> {
    const opts = { ...this.defaultOptions, ...options };

    const effectivePolicy: IngestionSecurityPolicy = {
      ...DefaultIngestionSecurityPolicy,
      ...opts.policy,
      ...(opts.maxByteSize !== undefined ? { maxByteSize: opts.maxByteSize } : {}),
      ...(opts.maxDurationMs !== undefined ? { maxDurationMs: opts.maxDurationMs } : {})
    };

    // 1. Calculate SHA-256 Hash
    const hash = createHash.createHash('sha256').update(buffer).digest('hex');

    // 2. Sniff Magic Header
    const sniffed = sniffMediaHeader(buffer);
    if (sniffed.isSpoofed) {
      throw new IngestionSecurityError(
        'MIME_SPOOFING',
        `Media probe failed: ${sniffed.spoofReason ?? 'Spoofed media header'}`
      );
    }

    const bufferStr = new TextDecoder('utf-8', { fatal: false }).decode(buffer);

    // 3. Handle corrupt buffers
    const isCorrupt =
      opts.simulateCorrupted ||
      bufferStr.includes('CORRUPTED') ||
      bufferStr.includes('CORRUPTED_STREAM_FLAG');

    if (isCorrupt) {
      const corruptResult: MediaProbeResult = {
        mimeType: sniffed.mimeType,
        container: sniffed.container,
        durationMs: 0,
        hasVideo: false,
        hasAudio: false,
        byteSize: buffer.length,
        sha256: hash,
        isCorrupted: true,
        corruptionReason: opts.corruptionReason ?? 'Stream header is corrupted or unparseable'
      };
      validateMediaPolicy(corruptResult, effectivePolicy);
      return corruptResult;
    }

    // 4. Derive flags from options or buffer string
    const isOverDuration = bufferStr.includes('DURATION_OVER_LIMIT_FLAG');
    const isNoAudio =
      bufferStr.includes('NO_AUDIO_FLAG') ||
      bufferStr.includes('NO_AUDIO_STREAM') ||
      opts.overrideHasAudio === false;

    const durationMs = opts.overrideDurationMs ?? (isOverDuration ? 3_600_000 : 30_000);
    const hasAudio = !isNoAudio;
    const hasVideo = opts.overrideHasVideo ?? true;

    const probeResult: MediaProbeResult = {
      mimeType: sniffed.mimeType,
      container: sniffed.container,
      durationMs,
      width: hasVideo ? (opts.overrideWidth ?? 1080) : undefined,
      height: hasVideo ? (opts.overrideHeight ?? 1920) : undefined,
      frameRate: hasVideo ? (opts.overrideFrameRate ?? 30) : undefined,
      videoCodec: hasVideo ? (opts.overrideVideoCodec ?? 'h264') : undefined,
      audioCodec: hasAudio ? (opts.overrideAudioCodec ?? 'aac') : undefined,
      hasVideo,
      hasAudio,
      byteSize: buffer.length,
      sha256: hash,
      isCorrupted: false
    };

    // 5. Validate against Security Policy
    validateMediaPolicy(probeResult, effectivePolicy);

    return probeResult;
  }
}

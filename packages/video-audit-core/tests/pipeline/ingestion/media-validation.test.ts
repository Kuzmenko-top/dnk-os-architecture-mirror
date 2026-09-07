/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/ingestion/media-validation.test.ts"
# purpose: "Unit Tests for Media Validation, Path Traversal Sanitization, MIME Spoofing, and Resource Limits."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import {
  sanitizeFilename,
  IngestionSecurityError,
  DefaultIngestionSecurityPolicy
} from '../../../src/pipeline/domain/ingestion/security.js';
import { DeterministicMediaProbe } from '../../../src/pipeline/infrastructure/media-probe/deterministic-media-probe.js';
import { deriveMediaCapabilities } from '../../../src/pipeline/domain/assets/reference-asset.js';

describe('Media Validation & Ingestion Security', () => {
  const probe = new DeterministicMediaProbe();

  it('sanitizes dangerous filenames and prevents path traversal', () => {
    expect(sanitizeFilename('../../../etc/passwd')).toBe('passwd');
    expect(sanitizeFilename('normal_video.mp4')).toBe('normal_video.mp4');
    expect(sanitizeFilename('evil\x00_file.mp4')).toBe('evil_file.mp4');
    expect(sanitizeFilename('   ')).toBe('unnamed_asset.mp4');
  });

  it('detects MIME spoofing when HTML is disguised as video', async () => {
    const htmlBuffer = new TextEncoder().encode('<!DOCTYPE html><html><body>Spoofed</body></html>');
    await expect(probe.probeBuffer(htmlBuffer)).rejects.toThrow(IngestionSecurityError);
    await expect(probe.probeBuffer(htmlBuffer)).rejects.toThrow(/MIME spoofing/i);
  });

  it('detects MIME spoofing when ELF binary is disguised as video', async () => {
    const elfBuffer = new Uint8Array([0x7f, 0x45, 0x4c, 0x46, 0x01, 0x01, 0x01]);
    await expect(probe.probeBuffer(elfBuffer)).rejects.toThrow(IngestionSecurityError);
    await expect(probe.probeBuffer(elfBuffer)).rejects.toThrow(/Executable binary/i);
  });

  it('rejects corrupt media stream buffers', async () => {
    const corruptBuffer = new TextEncoder().encode('....ftypisom....CORRUPTED_STREAM_FLAG....');
    await expect(probe.probeBuffer(corruptBuffer)).rejects.toThrow(IngestionSecurityError);
    await expect(probe.probeBuffer(corruptBuffer)).rejects.toThrow(/corrupted/i);
  });

  it('enforces maximum file byte size limit', async () => {
    const customProbe = new DeterministicMediaProbe({
      maxByteSize: 100
    });

    const oversizedBuffer = new Uint8Array(200);
    // Add MP4 header bytes
    oversizedBuffer.set([0, 0, 0, 20, 0x66, 0x74, 0x79, 0x70, 0x69, 0x73, 0x6f, 0x6d]);

    await expect(customProbe.probeBuffer(oversizedBuffer)).rejects.toThrow(/exceeds maximum permitted limit/i);
  });

  it('enforces maximum video duration limit', async () => {
    const customProbe = new DeterministicMediaProbe({
      maxDurationMs: 10000 // 10s limit
    });

    const longBuffer = new TextEncoder().encode('....ftypisom....DURATION_OVER_LIMIT_FLAG....');
    await expect(customProbe.probeBuffer(longBuffer)).rejects.toThrow(/exceeds maximum permitted limit/i);
  });

  it('derives degraded capabilities when audio stream is absent', async () => {
    const noAudioBuffer = new TextEncoder().encode('....ftypisom....NO_AUDIO_STREAM....');
    const result = await probe.probeBuffer(noAudioBuffer);

    expect(result.hasVideo).toBe(true);
    expect(result.hasAudio).toBe(false);

    const { capabilities, degradationWarnings } = deriveMediaCapabilities(result, {
      status: 'user_owned',
      usageIntent: 'private_analysis'
    });

    expect(capabilities).not.toContain('transcription');
    expect(capabilities).toContain('multimodal_audit');
    expect(degradationWarnings.length).toBeGreaterThan(0);
  });
});

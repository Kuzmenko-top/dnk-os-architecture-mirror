/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/ports/media-probe.ts"
# purpose: "Port Interface for Media Probing, Stream Inspection, and Integrity Checks."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { MediaProbeResult } from '../domain/assets/reference-asset.js';

export interface MediaProbeOptions {
  filename?: string;
  declaredMimeType?: string;
  enforceLimits?: boolean;
}

export interface MediaProbePort {
  probeBuffer(buffer: Uint8Array, options?: MediaProbeOptions): Promise<MediaProbeResult>;
}

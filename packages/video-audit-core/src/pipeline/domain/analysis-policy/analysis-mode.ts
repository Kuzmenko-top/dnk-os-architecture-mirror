/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/pipeline/domain/analysis-policy/analysis-mode.ts"
# purpose: "Define VideoAnalysisMode types, schema and helper mapping parameters."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export type VideoAnalysisMode = 'quick' | 'standard' | 'deep';

export const VideoAnalysisModeSchema = z.enum(['quick', 'standard', 'deep']);

export interface AnalysisModeConfig {
  mode: VideoAnalysisMode;
  frameDensityFps: number; // e.g., 0.5 (1 frame every 2s), 1, 2
  ocrFrequencySeconds: number; // e.g., 5, 2, 1
  audioResolutionKbps: number; // e.g., 64, 128, 256
  multimodalContextBudgetTokens: number; // e.g., 20000, 50000, 100000
  expectedLatencyMs: number;
  estimatedCostUsd: number;
}

export const ANALYSIS_MODE_PRESETS: Record<VideoAnalysisMode, AnalysisModeConfig> = {
  quick: {
    mode: 'quick',
    frameDensityFps: 0.2, // 1 frame every 5 seconds
    ocrFrequencySeconds: 10,
    audioResolutionKbps: 64,
    multimodalContextBudgetTokens: 15000,
    expectedLatencyMs: 3000,
    estimatedCostUsd: 0.005,
  },
  standard: {
    mode: 'standard',
    frameDensityFps: 1.0, // 1 frame every second
    ocrFrequencySeconds: 5,
    audioResolutionKbps: 128,
    multimodalContextBudgetTokens: 40000,
    expectedLatencyMs: 8000,
    estimatedCostUsd: 0.02,
  },
  deep: {
    mode: 'deep',
    frameDensityFps: 3.0, // 3 frames every second
    ocrFrequencySeconds: 1,
    audioResolutionKbps: 256,
    multimodalContextBudgetTokens: 100000,
    expectedLatencyMs: 25000,
    estimatedCostUsd: 0.08,
  },
};

export function getAnalysisModeConfig(mode: VideoAnalysisMode): AnalysisModeConfig {
  return ANALYSIS_MODE_PRESETS[mode] || ANALYSIS_MODE_PRESETS.standard;
}

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/pipeline/analyzers/video-analysis-mode.test.ts"
# purpose: "Unit tests for VideoAnalysisMode presets, validation, and configurations."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect } from 'vitest';
import { getAnalysisModeConfig, ANALYSIS_MODE_PRESETS, VideoAnalysisModeSchema } from '../../../src/pipeline/domain/analysis-policy/analysis-mode.js';

describe('VideoAnalysisMode Configuration and Presets', () => {
  it('defines valid schemas for quick, standard, and deep modes', () => {
    expect(VideoAnalysisModeSchema.safeParse('quick').success).toBe(true);
    expect(VideoAnalysisModeSchema.safeParse('standard').success).toBe(true);
    expect(VideoAnalysisModeSchema.safeParse('deep').success).toBe(true);
    expect(VideoAnalysisModeSchema.safeParse('invalid_mode').success).toBe(false);
  });

  it('correctly maps quick mode parameters', () => {
    const quickConfig = getAnalysisModeConfig('quick');
    expect(quickConfig.mode).toBe('quick');
    expect(quickConfig.frameDensityFps).toBe(0.2);
    expect(quickConfig.ocrFrequencySeconds).toBe(10);
    expect(quickConfig.audioResolutionKbps).toBe(64);
    expect(quickConfig.multimodalContextBudgetTokens).toBe(15000);
  });

  it('correctly maps standard mode parameters', () => {
    const standardConfig = getAnalysisModeConfig('standard');
    expect(standardConfig.mode).toBe('standard');
    expect(standardConfig.frameDensityFps).toBe(1.0);
    expect(standardConfig.ocrFrequencySeconds).toBe(5);
    expect(standardConfig.audioResolutionKbps).toBe(128);
    expect(standardConfig.multimodalContextBudgetTokens).toBe(40000);
  });

  it('correctly maps deep mode parameters', () => {
    const deepConfig = getAnalysisModeConfig('deep');
    expect(deepConfig.mode).toBe('deep');
    expect(deepConfig.frameDensityFps).toBe(3.0);
    expect(deepConfig.ocrFrequencySeconds).toBe(1);
    expect(deepConfig.audioResolutionKbps).toBe(256);
    expect(deepConfig.multimodalContextBudgetTokens).toBe(100000);
  });

  it('falls back to standard mode config for unrecognized modes', () => {
    const fallbackConfig = getAnalysisModeConfig('invalid_mode' as any);
    expect(fallbackConfig.mode).toBe('standard');
    expect(fallbackConfig.frameDensityFps).toBe(1.0);
  });
});

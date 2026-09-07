/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/educational-short.ts"
# purpose: "Educational Short Reference Asset and Audit Fixture."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReport } from '../schemas/audit.js';
import { LegacyReferenceAsset } from '../schemas/reference.js';

export const EducationalShortAssetFixture: LegacyReferenceAsset = {
  id: 'ref-edu-001',
  sourceType: 'url_youtube',
  url: 'https://youtube.com/shorts/edu_demo_123',
  createdAt: '2026-09-02T10:00:00Z',
  mediaMetadata: {
    durationMs: 45000,
    width: 1080,
    height: 1920,
    fps: 30,
    aspectRatio: '9:16',
  },
  platformMetadata: {
    authorHandle: '@tech_explainer',
    viewsCount: 450000,
    likesCount: 38000,
    hashtags: ['#ai', '#tech', '#education'],
    caption: '3 AI Tools that feel illegal to know',
  },
};

export const EducationalShortAuditFixture: VideoAuditReport = {
  schemaVersion: 'video-audit.v1',
  id: 'audit-educational-short-001',
  status: 'READY',
  createdAt: '2026-09-02T10:05:00Z',
  referenceAsset: EducationalShortAssetFixture,
  transcript: {
    language: 'en',
    fullText:
      '3 AI tools that feel illegal to know. First, Perplexity for instant research. Second, Claude for long document analysis. Third, Midjourney for photorealistic visuals.',
    overallConfidence: 0.96,
    segments: [
      {
        id: 'seg-1',
        startMs: 0,
        endMs: 3000,
        text: '3 AI tools that feel illegal to know.',
        words: [],
      },
    ],
  },
  scenes: [
    {
      id: 'sc-1',
      title: 'Hook Statement',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 3000 },
      summary: 'Bold claim hook calling out 3 tools.',
      shots: [],
    },
  ],
  audioFeatures: {
    hasBackgroundMusic: true,
    musicGenre: 'lofi_hiphop',
    pauseCount: 2,
    averagePauseDurationMs: 300,
  },
  structure: {
    hookType: 'bold_claim',
    hookDurationMs: 3000,
    narrativeArc: 'Listicle format (3 items in fast succession)',
    keyTakeaways: ['Perplexity', 'Claude', 'Midjourney'],
    pacingStructure: 'Fast listicle',
  },
  visuals: {
    dominantColorPalette: ['#000000', '#00FF88'],
    cutFrequencyPerMin: 20,
    faceVisibilityRatio: 0.8,
    hasCaptions: true,
  },
  retention: {
    estimatedRetentionScore: 88,
    dropoffRisks: [],
    engagementDrivers: [
      {
        timeRange: { startMs: 0, endMs: 3000 },
        driver: 'Curiosity gap in hook',
      },
    ],
  },
  evidence: [
    {
      id: 'ev-1',
      type: 'inferred',
      claim: 'Hook uses bold claim listicle formula',
      confidence: 0.92,
      source: 'claude_structural',
      evidenceRefs: ['seg-1'],
    },
  ],
};

export const educationalShortAuditFixture = EducationalShortAuditFixture;

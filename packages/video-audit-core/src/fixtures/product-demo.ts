/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/product-demo.ts"
# purpose: "Product Demo Reference Asset and Audit Fixture."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReport } from '../schemas/audit.js';
import { LegacyReferenceAsset } from '../schemas/reference.js';

export const ProductDemoAssetFixture: LegacyReferenceAsset = {
  id: 'ref-prod-001',
  sourceType: 'url_instagram',
  url: 'https://instagram.com/reel/demo_456',
  createdAt: '2026-09-02T11:00:00Z',
  mediaMetadata: {
    durationMs: 30000,
    width: 1080,
    height: 1920,
    fps: 60,
    aspectRatio: '9:16',
  },
  platformMetadata: {
    authorHandle: '@gadget_reviews',
    viewsCount: 120000,
    likesCount: 9500,
    hashtags: ['#gadgets', '#tech', '#unboxing'],
  },
};

export const ProductDemoAuditFixture: VideoAuditReport = {
  schemaVersion: 'video-audit.v1',
  id: 'audit-product-demo-001',
  status: 'READY',
  createdAt: '2026-09-02T11:05:00Z',
  referenceAsset: ProductDemoAssetFixture,
  transcript: {
    language: 'uk',
    fullText:
      'Цей гаджет повністю змінив мій робочий стіл. Подивіться як це працює в реальному житті.',
    overallConfidence: 0.94,
    segments: [],
  },
  scenes: [
    {
      id: 'sc-1',
      title: 'Visual Shock Hook',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 2500 },
      summary: 'Close up product transformation',
      shots: [],
    },
  ],
  audioFeatures: {
    hasBackgroundMusic: true,
    pauseCount: 1,
    averagePauseDurationMs: 200,
  },
  structure: {
    hookType: 'visual_shock',
    hookDurationMs: 2500,
    narrativeArc: 'Problem -> Solution -> Live Demo',
    keyTakeaways: ['Desk organization', 'Wireless charging'],
    pacingStructure: 'Dynamic visual presentation',
  },
  visuals: {
    dominantColorPalette: ['#FFFFFF', '#333333'],
    cutFrequencyPerMin: 24,
    faceVisibilityRatio: 0.3,
    hasCaptions: true,
  },
  retention: {
    estimatedRetentionScore: 82,
    dropoffRisks: [],
    engagementDrivers: [],
  },
  evidence: [
    {
      id: 'ev-1',
      type: 'observed',
      claim: 'First cut occurs at 2500ms',
      confidence: 1.0,
      source: 'ffmpeg',
      evidenceRefs: ['shot-1'],
    },
  ],
};

export const productDemoAuditFixture = ProductDemoAuditFixture;

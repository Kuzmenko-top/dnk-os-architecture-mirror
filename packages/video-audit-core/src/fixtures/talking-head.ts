/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/talking-head.ts"
# purpose: "Talking Head Reference Asset and Audit Fixture."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { VideoAuditReport } from '../schemas/audit.js';
import { LegacyReferenceAsset } from '../schemas/reference.js';

export const TalkingHeadAssetFixture: LegacyReferenceAsset = {
  id: 'ref-talk-001',
  sourceType: 'url_tiktok',
  url: 'https://tiktok.com/@creator/video/123456',
  createdAt: '2026-09-02T08:00:00Z',
  mediaMetadata: {
    durationMs: 35000,
    width: 1080,
    height: 1920,
    fps: 30,
    aspectRatio: '9:16',
  },
  platformMetadata: {
    authorHandle: '@business_coach',
    viewsCount: 250000,
    likesCount: 18000,
    hashtags: ['#business', '#marketing'],
  },
};

export const TalkingHeadAuditFixture: VideoAuditReport = {
  schemaVersion: 'video-audit.v1',
  id: 'audit-talking-head-001',
  status: 'READY',
  createdAt: '2026-09-02T08:05:00Z',
  referenceAsset: TalkingHeadAssetFixture,
  transcript: {
    language: 'uk',
    fullText: 'Більшість підприємців роблять одну і ту саму помилку в рекламі...',
    overallConfidence: 0.98,
    segments: [
      {
        id: 'seg-talk-1',
        startMs: 0,
        endMs: 3500,
        text: 'Більшість підприємців роблять одну і ту саму помилку в рекламі...',
        words: [],
      },
    ],
  },
  scenes: [
    {
      id: 'sc-1',
      title: 'Negative Frame Hook',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 3500 },
      summary: 'Creator speaks directly into camera identifying a common mistake.',
      shots: [],
    },
  ],
  audioFeatures: {
    hasBackgroundMusic: false,
    pauseCount: 3,
    averagePauseDurationMs: 400,
  },
  structure: {
    hookType: 'negative_frame',
    hookDurationMs: 3500,
    narrativeArc: 'Mistake -> Consequence -> Correct Approach',
    keyTakeaways: ['Focus on value proposition', 'A/B test hooks'],
    pacingStructure: 'Direct conversational pace',
  },
  visuals: {
    dominantColorPalette: ['#1A1A1A', '#FF9900'],
    cutFrequencyPerMin: 12,
    faceVisibilityRatio: 0.95,
    hasCaptions: true,
  },
  retention: {
    estimatedRetentionScore: 85,
    dropoffRisks: [],
    engagementDrivers: [],
  },
  evidence: [],
};

export const talkingHeadAuditFixture = TalkingHeadAuditFixture;

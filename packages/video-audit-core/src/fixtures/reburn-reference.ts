/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn-reference.ts"
# purpose: "ReBurn Reference Full End-to-End Adaptation Result Fixture."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { AdaptationResult } from '../schemas/adaptation.js';

export const ReBurnAdaptationResultFixture: AdaptationResult = {
  schemaVersion: 'adaptation.v1',
  id: 'adapt-reburn-001',
  sourceAuditId: 'audit-talk-001',
  requestId: 'req-audit-talk-001',
  createdAt: '2026-09-02T12:00:00Z',
  status: 'accepted',
  warnings: [],
  brandCompliance: {
    status: 'compliant',
    usedFactIds: ['reburn-fact-mat-001'],
    unverifiedClaims: [],
    forbiddenViolations: [],
    commercialViolations: [],
    toneScore: 1.0,
    notes: ['Сценарій повністю відповідає бренду.'],
  },
  script: {
    schemaVersion: 'script.v1',
    id: 'script-reburn-001',
    language: 'uk',
    title: 'Помилка при виборі суфлера для відео',
    estimatedDurationMs: 32000,
    source: {
      type: 'adapted',
      auditId: 'audit-talk-001',
      adaptationId: 'adapt-reburn-001',
    },
    scenes: [
      {
        id: 'sc-1',
        title: 'Негативний гачок',
        role: 'hook',
        targetTimeRange: { startMs: 0, endMs: 3500 },
        paragraphs: [
          {
            id: 'p-1',
            text: 'Більшість авторів зливають 80 відсотків переглядів через застиглий погляд у суфлер.',
            speakerRole: 'main_speaker',
            estimatedDurationMs: 3500,
          },
        ],
      },
      {
        id: 'sc-2',
        title: 'Суть рішення',
        role: 'core_value',
        targetTimeRange: { startMs: 3500, endMs: 25000 },
        paragraphs: [
          {
            id: 'p-2',
            text: 'Новий ройовий суфлер DNK OS підлаштовується під твій темп мовлення в реальному часі.',
            speakerRole: 'main_speaker',
            estimatedDurationMs: 21500,
          },
        ],
      },
      {
        id: 'sc-3',
        title: 'Заклик до дії',
        role: 'call_to_action',
        targetTimeRange: { startMs: 25000, endMs: 32000 },
        paragraphs: [
          {
            id: 'p-3',
            text: 'Спробуй безкоштовно в Telegram Mini App зараз!',
            speakerRole: 'main_speaker',
            estimatedDurationMs: 7000,
          },
        ],
      },
    ],
  },
  prosody: {
    schemaVersion: 'prosody.v1',
    scriptId: 'script-reburn-001',
    globalPacing: {
      targetWpm: 140,
      targetDurationMs: 32000,
    },
    tokens: [
      {
        id: 'tok-1',
        word: 'Більшість',
        sceneId: 'sc-1',
        paragraphId: 'p-1',
        emphasis: 'punch',
        pitchShift: 'high',
        pauseAfterMs: 100,
        gesture: 'hand_raise',
      },
      {
        id: 'tok-2',
        word: 'авторів',
        sceneId: 'sc-1',
        paragraphId: 'p-1',
        emphasis: 'none',
        pitchShift: 'normal',
        pauseAfterMs: 0,
        gesture: 'none',
      },
      {
        id: 'tok-3',
        word: 'зливають',
        sceneId: 'sc-1',
        paragraphId: 'p-1',
        emphasis: 'punch',
        pitchShift: 'low',
        pauseAfterMs: 200,
        gesture: 'finger_point',
      },
    ],
  },
  shotList: {
    schemaVersion: 'shot-list.v1',
    scriptId: 'script-reburn-001',
    shots: [
      {
        id: 'shot-1',
        sceneId: 'sc-1',
        shotType: 'close_up',
        visualPrompt: 'Крупний план спікера, прямий погляд у камеру, контрастне світло.',
        estimatedDurationMs: 3500,
        cameraAngle: 'eye_level',
        textOverlay: '80% зливають перегляди!',
        bRollKeywords: ['teleprompter', 'camera_glance'],
      },
      {
        id: 'shot-2',
        sceneId: 'sc-2',
        shotType: 'medium_shot',
        visualPrompt: 'Cередній план з показом смартфона з інтерфейсом суфлера.',
        estimatedDurationMs: 21500,
        bRollKeywords: ['phone_screen', 'voice_wave'],
      },
    ],
  },
  preservedMechanisms: [
    'Negative framing hook pattern',
    'Problem -> Tech Solution -> Action structure',
    'Emphatic punch pause rhythm',
  ],
  changedElements: [
    'Original generic advertising mistake replaced with teleprompter glance issue',
    'Niche adapted to Content Creators & Solo Business',
  ],
  similarity: {
    overallRisk: 'low',
    lexical: 0.05,
    structural: 0.85,
    visual: 0.2,
    audio: 0.0,
    brand: 0.0,
    notes: [
      'Structural storytelling mechanism preserved from reference video (intended format transfer).',
      'Lexical similarity is safely under 30% threshold.',
    ],
  },
  evidence: [
    {
      id: 'ev-1',
      type: 'observed',
      claim: 'Reference hook duration was 3500ms',
      confidence: 0.98,
      source: 'whisperx',
      timeRange: { startMs: 0, endMs: 3500 },
      evidenceRefs: ['sc-1'],
    },
    {
      id: 'ev-2',
      type: 'inferred',
      claim: 'Negative frame hook drives 85% higher retention in early 5s window',
      confidence: 0.88,
      source: 'claude_structural',
      evidenceRefs: ['sc-1'],
    },
  ],
};

export const reburnAdaptationFixture = ReBurnAdaptationResultFixture;
export const reburnReferenceFixture = ReBurnAdaptationResultFixture;

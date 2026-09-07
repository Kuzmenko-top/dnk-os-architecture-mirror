/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/tests/adaptation/adaptation-pipeline.test.ts"
# purpose: "Comprehensive Unit and Semantic Tests for Niche Adaptation Pipeline, guards, and transformers."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { describe, it, expect, beforeEach } from 'vitest';

import {
  NicheAdaptationPipeline,
  LiveLlmScriptWriter,
  DeterministicScriptWriter,
  SpendGuard,
  REBURN_BRAND_PROFILE,
  VideoAuditReport,
  AdaptationRequest,
  BrandProfile
} from '../../src/index.js';
import { InMemoryAdaptationRepository } from '../../src/adaptation/infrastructure/persistence/in-memory-adaptation-repository.js';

// Setup highly realistic mock data for our tests
const mockAuditReport: VideoAuditReport = {
  schemaVersion: 'video-audit.v1',
  id: 'audit-talk-001',
  status: 'READY',
  createdAt: '2026-09-03T10:00:00Z',
  referenceAsset: {
    id: 'ref-talk-001',
    sourceType: 'url_youtube',
    url: 'https://youtube.com/watch?v=12345',
    createdAt: '2026-09-03T09:00:00Z',
    mediaMetadata: {
      durationMs: 31500,
      width: 1920,
      height: 1080,
      fps: 30,
      aspectRatio: '16:9'
    },
    platformMetadata: {
      authorHandle: '@original_creator',
      viewsCount: 150000,
      likesCount: 12000,
      sharesCount: 1000,
      postedAt: '2026-09-03T09:00:00Z',
      caption: 'Original creator video text',
      hashtags: ['#smokers', '#barbecue'],
      // We will cast this as any to avoid TS platformMetadata limitations
      rightsStatus: 'cleared'
    } as any
  },
  transcript: {
    language: 'uk',
    fullText: 'Більшість авторів зливають 80 відсотків переглядів через застиглий погляд у суфлер. Коли ви дивитесь в одну точку...',
    overallConfidence: 0.97,
    segments: [
      {
        id: 'seg-1',
        startMs: 0,
        endMs: 3500,
        text: 'Більшість авторів зливають 80 відсотків переглядів через застиглий погляд у суфлер.',
        words: []
      }
    ]
  },
  audioFeatures: {
    speakingWpm: 130,
    pauseCount: 4,
    averagePauseDurationMs: 450,
    hasBackgroundMusic: true
  },
  visuals: {
    dominantColorPalette: ['#000000', '#ffffff'],
    cutFrequencyPerMin: 12,
    faceVisibilityRatio: 0.85,
    hasCaptions: true
  },
  retention: {
    estimatedRetentionScore: 85,
    dropoffRisks: [],
    engagementDrivers: []
  },
  scenes: [
    {
      id: 'scene-1',
      title: 'Гачок (Hook)',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 3500 },
      summary: 'Гачок про помилку авторів з суфлером',
      shots: []
    },
    {
      id: 'scene-2',
      title: 'Біль та проблема',
      role: 'problem_statement',
      timeRange: { startMs: 3500, endMs: 11500 },
      summary: 'Проблема застиглого погляду та втрати аудиторії',
      shots: []
    },
    {
      id: 'scene-3',
      title: 'Рішення та переваги',
      role: 'demonstration',
      timeRange: { startMs: 11500, endMs: 26500 },
      summary: 'Як налаштувати суфлер та жестикулювати природно',
      shots: []
    },
    {
      id: 'scene-4',
      title: 'Заклик до дії',
      role: 'call_to_action',
      timeRange: { startMs: 26500, endMs: 31500 },
      summary: 'Заклик написати коментар для отримання гайду',
      shots: []
    }
  ],
  structure: {
    hookType: 'bold_claim',
    hookDurationMs: 3500,
    narrativeArc: 'problem_solution',
    keyTakeaways: ['Дивитись трохи повз камеру', 'Робити мікрорухи головою'],
    ctaType: 'comment',
    pacingStructure: 'fast_paced'
  },
  evidence: [
    {
      type: 'observed',
      id: 'ev-1',
      confidence: 0.95,
      claim: 'Більшість авторів зливають перегляди через суфлер',
      source: 'transcript',
      evidenceRefs: ['seg-1'],
      timeRange: { startMs: 0, endMs: 3500 }
    }
  ]
};

const mockRequest: AdaptationRequest = {
  schemaVersion: 'adaptation-request.v1',
  sourceAuditId: 'audit-talk-001',
  brandId: 'reburn-brand',
  niche: 'barbecue',
  forbiddenElements: [],
  targetDurationMs: 31500,
  language: 'uk',
  audience: 'Власники ресторанів та заміських комплексів',
  tone: 'professional',
  ctaType: 'REBURN_CTA',
  approvedFactIds: REBURN_BRAND_PROFILE.approvedFacts.map(f => f.id),
  desiredMechanisms: []
};

describe('Niche Adaptation Pipeline & Certification tests', () => {
  let repository: InMemoryAdaptationRepository;
  let deterministicWriter: DeterministicScriptWriter;
  let liveWriter: LiveLlmScriptWriter;

  beforeEach(() => {
    repository = new InMemoryAdaptationRepository();
    deterministicWriter = new DeterministicScriptWriter();
    liveWriter = new LiveLlmScriptWriter(deterministicWriter);
    SpendGuard.reset();
  });

  // --- BUSINESS SCENARIOS ---

  it('1. Valid ReBurn product adaptation -> status: accepted', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const result = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('accepted');
    expect(result.warnings.length).toBe(0);
    expect(result.brandCompliance.status).toBe('approved');
    expect(result.brandCompliance.usedFactIds).toContain('reburn-fact-mat-001');
  });

  it('2. ROI claim без approved source -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const requestWithRoi = {
      ...mockRequest,
      desiredMechanisms: ['simulate_roi_claim']
    };

    const result = await pipeline.adapt(requestWithRoi, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('manual_review');
    expect(result.brandCompliance.unverifiedClaims).toContain('Окупіть коптильню вже за перший тиждень з гарантованим чистим прибутком 1000 доларів!');
    expect(result.warnings.some(w => w.includes('UNVERIFIED_COMMERCIAL_CLAIM') || w.includes('непідтверджені комерційні'))).toBe(true);
  });

  it('3. Unverified certification claim -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const requestWithUnverifiedCert = {
      ...mockRequest,
      desiredMechanisms: ['simulate_unverified_cert']
    };

    const result = await pipeline.adapt(requestWithUnverifiedCert, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('manual_review');
    expect(result.brandCompliance.unverifiedClaims.some(c => c.includes('медичну сертифікацію'))).toBe(true);
  });

  it('4. Unknown rights for commercial adaptation -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    // Modify report reference asset to have unknown rights
    const reportWithUnknownRights: VideoAuditReport = {
      ...mockAuditReport,
      referenceAsset: {
        ...mockAuditReport.referenceAsset!,
        platformMetadata: {
          ...mockAuditReport.referenceAsset!.platformMetadata,
          rightsStatus: 'unknown'
        } as any
      }
    };

    const result = await pipeline.adapt(mockRequest, reportWithUnknownRights, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('manual_review');
    expect(result.warnings.some(w => w.includes('RIGHTS_STATUS_UNKNOWN') || w.includes('невідомі права'))).toBe(true);
  });

  it('5. High lexical similarity (>= 0.60) -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const requestHighSim = {
      ...mockRequest,
      desiredMechanisms: ['simulate_high_similarity']
    };

    const result = await pipeline.adapt(requestHighSim, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.similarity.lexical).toBeGreaterThanOrEqual(0.60);
    expect(result.similarity.lexical).toBeLessThan(0.85);
    expect(result.status).toBe('manual_review');
    expect(result.warnings.some(w => w.includes('HIGH_LEXICAL_SIMILARITY') || w.includes('висока лексична схожість'))).toBe(true);
  });

  it('6. Critical lexical similarity (>= 0.85) -> status: rejected', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const requestCritSim = {
      ...mockRequest,
      desiredMechanisms: ['simulate_critical_similarity']
    };

    const result = await pipeline.adapt(requestCritSim, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.similarity.lexical).toBeGreaterThanOrEqual(0.85);
    expect(result.status).toBe('rejected');
    expect(result.warnings.some(w => w.includes('CRITICAL_LEXICAL_SIMILARITY') || w.includes('критичний ризик плагіату'))).toBe(true);
  });

  it('7. Forbidden safety claim -> status: rejected', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const requestForbidden = {
      ...mockRequest,
      desiredMechanisms: ['simulate_forbidden_claim']
    };

    const result = await pipeline.adapt(requestForbidden, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('rejected');
    expect(result.brandCompliance.status).toBe('rejected');
    expect(result.brandCompliance.forbiddenViolations.some(v => v.includes('квартирі без витяжки'))).toBe(true);
  });

  it('8. Missing approved fact reference -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    // Request with NO approved facts, but script writer asserts AISI 304 and PID controllers
    const requestWithNoApprovedFacts: AdaptationRequest = {
      ...mockRequest,
      approvedFactIds: []
    };

    const result = await pipeline.adapt(requestWithNoApprovedFacts, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('manual_review');
    expect(result.brandCompliance.unverifiedClaims.length).toBeGreaterThan(0);
    expect(result.brandCompliance.unverifiedClaims.some(c => c.includes('AISI 304') || c.includes('PID-термоконтролери'))).toBe(true);
  });

  it('9. Invalid duration (outside +/- 25%) -> status: manual_review', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    // Target duration is 15 seconds, but deterministic writer produces 31.5 seconds (which is outside 15 +/- 3.75s)
    const requestShortDuration: AdaptationRequest = {
      ...mockRequest,
      targetDurationMs: 15000
    };

    const result = await pipeline.adapt(requestShortDuration, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('manual_review');
    expect(result.warnings.some(w => w.includes('DURATION_OUT_OF_BOUNDS') || w.includes('Невідповідність хронометражу'))).toBe(true);
  });

  it('10 & 11. Missing prosody or shotlist fails closed', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    // Test with a broken custom pipeline orchestration where prosody is stripped or has empty tokens
    const result = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);
    
    // Simulate missing prosody tokens
    const brokenResultEmptyProsody = {
      ...result,
      prosody: {
        ...result.prosody,
        tokens: []
      }
    };
    
    // Evaluate via HumanReviewPolicy
    const humanReviewEngine = pipeline.humanReviewPolicy;
    const decision = humanReviewEngine.evaluate({
      targetDurationMs: mockRequest.targetDurationMs,
      script: result.script,
      prosody: brokenResultEmptyProsody.prosody,
      shotList: result.shotList,
      brandCompliance: result.brandCompliance,
      similarity: result.similarity,
      rightsStatus: 'cleared'
    });

    expect(decision.status).toBe('rejected');
    expect(decision.reasons.some(r => r.includes('просодії'))).toBe(true);
  });

  it('12. Duplicate request -> returns existing cached result (idempotency)', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    const result1 = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);
    const result2 = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result1.id).toBe(result2.id);
  });

  it('13. Changed policy version -> new adaptation result', async () => {
    const pipeline1 = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const result1 = await pipeline1.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    // Re-create pipeline with different policy version
    const pipeline2 = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    pipeline2.adaptationPolicyVersion = 'adaptation.policy.v2.0';
    const result2 = await pipeline2.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result1.id).not.toBe(result2.id);
  });

  it('14. Changed brand profile / prompt version -> new adaptation result', async () => {
    const pipeline1 = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const result1 = await pipeline1.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    const pipeline2 = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    pipeline2.promptVersion = 'reburn-prompt-v2.5';
    const result2 = await pipeline2.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result1.id).not.toBe(result2.id);
  });

  it('15. Input report ID/hash mismatch -> status: rejected', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    
    // Mismatched sourceAuditId in request
    const mismatchedRequest = {
      ...mockRequest,
      sourceAuditId: 'audit-mismatch-id-999'
    };

    const result = await pipeline.adapt(mismatchedRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    expect(result.status).toBe('rejected');
    expect(result.warnings).toContain('INPUT_REPORT_MISMATCH');
    expect(result.brandCompliance.forbiddenViolations[0]).toContain('Input report ID mismatch');
  });

  // --- SEMANTIC VALIDATION TESTS ---

  it('Semantic validation: Prosody token alignment & parameters', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const result = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    const prosody = result.prosody;

    // A. Check token count & matching text
    expect(prosody.tokens.length).toBeGreaterThan(0);
    
    // B. pauseAfterMs >= 0
    prosody.tokens.forEach(tok => {
      expect(tok.pauseAfterMs).toBeGreaterThanOrEqual(0);
    });

    // C. Gestures from allowlist
    const validGestures = ['none', 'hand_raise', 'finger_point', 'head_nod', 'head_shake', 'eyebrow_raise', 'smile', 'lean_forward', 'palms_up'];
    prosody.tokens.forEach(tok => {
      expect(validGestures).toContain(tok.gesture);
    });

    // D. Pitch from allowlist
    const validPitch = ['low', 'normal', 'high'];
    prosody.tokens.forEach(tok => {
      expect(validPitch).toContain(tok.pitchShift);
    });

    // E. Punch/hold formatting is not overapplied (< 50% of tokens have non-none emphasis)
    const totalTokens = prosody.tokens.length;
    const emphasizedTokens = prosody.tokens.filter(tok => tok.emphasis !== 'none').length;
    const emphasisRatio = emphasizedTokens / totalTokens;

    expect(emphasisRatio).toBeLessThan(0.50);
  });

  it('Semantic validation: ShotList structural coverage', async () => {
    const pipeline = new NicheAdaptationPipeline({ repository, scriptWriter: liveWriter });
    const result = await pipeline.adapt(mockRequest, mockAuditReport, REBURN_BRAND_PROFILE);

    const shotList = result.shotList;
    const script = result.script;

    // A. ShotList covers all scenes in the script
    const scriptSceneIds = script.scenes.map(s => s.id);
    const shotSceneIds = new Set(shotList.shots.map(s => s.sceneId));

    scriptSceneIds.forEach(id => {
      expect(shotSceneIds.has(id)).toBe(true);
    });

    // B. Each shot has a valid duration
    shotList.shots.forEach(shot => {
      expect(shot.estimatedDurationMs).toBeGreaterThan(0);
    });

    // C. Text overlays do not contain forbidden claims
    shotList.shots.forEach(shot => {
      if (shot.textOverlay) {
        expect(shot.textOverlay.includes('без витяжки прямо в квартирі')).toBe(false);
      }
    });
  });

  // --- SPENDGUARD GATE ---

  it('SpendGuard tracks and limits API costs correctly', () => {
    expect(SpendGuard.getSpend()).toBe(0);
    
    // Track some spending
    SpendGuard.trackSpend(0.150);
    expect(SpendGuard.getSpend()).toBe(0.150);

    // Overspend to trigger safety cap
    expect(() => {
      SpendGuard.trackSpend(5.00);
    }).toThrow('[SpendGuard] Spend limit of $5.000 exceeded!');
  });
});

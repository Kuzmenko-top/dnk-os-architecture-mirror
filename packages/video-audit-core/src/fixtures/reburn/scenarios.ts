/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/fixtures/reburn/scenarios.ts"
# purpose: "Modular Registry of 11 Business-Realistic ReBurn Audit Fixtures & Calibrated Manifests."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { ReBurnFixtureData, ReBurnFixtureManifest } from './types.js';
import {
  buildReferenceAsset,
  buildTranscriptDoc,
  buildSceneDoc,
  buildOcrDoc,
  buildAudioFeaturesDoc,
  buildEvidenceDoc,
  buildMultimodalAuditResult
} from './fixture-builder.js';
import { AuditedClaim } from '../../schemas/multimodal-audit.js';

export const reburnScenarios: Record<string, ReBurnFixtureData> = {};

// Helper to generate a standardized scenario
function registerScenario(opts: {
  id: string;
  category: ReBurnFixtureManifest['category'];
  title: string;
  durationMs: number;
  expectedScenesCount: number;
  expectedOcrTerms: string[];
  expectedTechnicalTerms: string[];
  expectedClaims: ReBurnFixtureManifest['expectedClaims'];
  knownUncertainties: string[];
  expectedAggregateStatus: ReBurnFixtureManifest['expectedAggregateStatus'];
  coverageType: ReBurnFixtureManifest['coverageType'];
  invariants?: ReBurnFixtureManifest['invariants'];
  
  // Custom document overrides
  transcriptSegments: Array<{ text: string; startMs: number; endMs: number }>;
  scenes: Array<{ sceneNumber: number; startMs: number; endMs: number; visualDescription: string }>;
  ocrFrames: Array<{ timestampMs: number; text: string }>;
  audioSegments?: Array<{ startMs: number; endMs: number; speechProb: number; musicProb: number; silence?: boolean }>;
  claims: Array<{
    id: string;
    classification: 'observed' | 'inferred' | 'hypothesized';
    textSnippet?: string;
    text?: string;
    role?: string;
    timeRange?: { startMs: number; endMs: number };
    evidenceRefs?: {
      transcriptSegmentIds?: string[];
      transcriptWordIndexes?: number[];
      sceneIds?: string[];
      ocrFrameIds?: string[];
      audioFeatureIds?: string[];
    };
    confidence?: number;
  }>;
}) {
  const manifest: ReBurnFixtureManifest = {
    fixtureId: opts.id,
    version: '1.0.0',
    category: opts.category,
    title: opts.title,
    language: 'uk-UA',
    durationMs: opts.durationMs,
    coverageType: opts.coverageType,
    expectedScenes: opts.expectedScenesCount,
    expectedOcrTerms: opts.expectedOcrTerms,
    expectedTechnicalTerms: opts.expectedTechnicalTerms,
    expectedClaims: opts.expectedClaims,
    knownUncertainties: opts.knownUncertainties,
    expectedAggregateStatus: opts.expectedAggregateStatus,
    invariants: opts.invariants ?? {
      hookMustStartNearZero: true,
      viralityNeverObservedWithoutEngagement: true,
      noHallucinatedIds: true,
      allowEmptyTranscript: opts.coverageType === 'degraded',
      allowEmptyOcr: opts.category === 'no_ocr'
    }
  };

  const referenceAsset = buildReferenceAsset({
    id: opts.id,
    durationMs: opts.durationMs,
    sourceUrl: `https://reburn-assets.dnk-e.com/fixtures/${opts.id}.mp4`
  });

  const transcript = buildTranscriptDoc({
    referenceAssetId: opts.id,
    durationMs: opts.durationMs,
    segments: opts.transcriptSegments.map((seg, idx) => ({
      id: `tr_seg_${idx + 1}`,
      ordinal: idx + 1,
      startMs: seg.startMs,
      endMs: seg.endMs,
      text: seg.text,
      words: seg.text.split(' ').map((w, wIdx) => ({
        ordinal: wIdx + 1,
        word: w.replace(/[.,\/#!$%^&*;:{}=\-_`~()]/g, ''),
        startMs: seg.startMs + wIdx * 200,
        endMs: seg.startMs + (wIdx + 1) * 200,
        confidence: 0.95
      }))
    }))
  });

  const scenes = buildSceneDoc({
    referenceAssetId: opts.id,
    scenes: opts.scenes.map((sc, idx) => ({
      id: `sc_scene_${idx + 1}`,
      startMs: sc.startMs,
      endMs: sc.endMs,
      description: sc.visualDescription
    }))
  });

  const ocr = buildOcrDoc({
    referenceAssetId: opts.id,
    frames: opts.ocrFrames.map((f, idx) => ({
      frameId: `ocr_frame_${idx + 1}`,
      timestampMs: f.timestampMs,
      regions: [{ text: f.text, x: 100, y: 100, width: 200, height: 50, confidence: 0.96 }]
    }))
  });

  const audioFeatures = buildAudioFeaturesDoc({
    referenceAssetId: opts.id,
    durationMs: opts.durationMs,
    hasAudioTrack: opts.category !== 'no_audio',
    segments: opts.audioSegments ?? [
      { startMs: 0, endMs: opts.durationMs, speechProb: 0.92, musicProb: 0.45, silence: false }
    ]
  });

  const multimodalEvidence = buildEvidenceDoc({
    referenceAssetId: opts.id,
    durationMs: opts.durationMs,
    aggregateStatus: opts.coverageType === 'degraded' ? 'partial' : 'completed'
  });

  // Inject inputArtifactHashes
  const mappedClaims = opts.claims.map(c => ({
    id: c.id,
    classification: c.classification as 'observed' | 'inferred' | 'hypothesized',
    text: c.text ?? c.textSnippet ?? '',
    confidence: c.confidence ?? 0.95,
    evidenceRefs: c.evidenceRefs
  })) as AuditedClaim[];

  const multimodalAudit = buildMultimodalAuditResult({
    referenceAssetId: opts.id,
    durationMs: opts.durationMs,
    claims: mappedClaims,
    inputArtifacts: {
      transcript: { schemaVersion: 'artifact.v1', key: `transcript_${opts.id}`, sha256: 'mock_sha_tr' },
      scenes: { schemaVersion: 'artifact.v1', key: `scenes_${opts.id}`, sha256: 'mock_sha_sc' },
      ocr: { schemaVersion: 'artifact.v1', key: `ocr_${opts.id}`, sha256: 'mock_sha_ocr' },
      audioFeatures: { schemaVersion: 'artifact.v1', key: `audio_${opts.id}`, sha256: 'mock_sha_audio' },
      evidence: { schemaVersion: 'artifact.v1', key: `evidence_${opts.id}`, sha256: 'mock_sha_ev' }
    }
  });

  reburnScenarios[opts.id] = {
    manifest,
    referenceAsset,
    transcript,
    scenes,
    ocr,
    audioFeatures,
    multimodalEvidence,
    multimodalAudit
  };
}

// ==========================================
// 1. PRODUCT DEMO FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-product-demo-001',
  category: 'product_demo',
  title: 'Огляд професійної коптильні ReBurn з димогенератором',
  durationMs: 18400,
  expectedScenesCount: 4,
  expectedOcrTerms: ['ReBurn', 'нержавіюча сталь', 'AISI 304'],
  expectedTechnicalTerms: ['коптильна камера', 'димогенератор', 'нержавіюча сталь'],
  expectedClaims: [
    { id: 'cl_dem_01', textSnippet: 'коптильна камера ReBurn повністю виготовлена з харчової нержавіючої сталі AISI 304', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_dem_02', textSnippet: 'димогенератор забезпечує до 8 годин автономної роботи', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_dem_03', textSnippet: 'ви отримаєте ідеальний золотистий колір без гіркоти', role: 'core', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_dem_04', textSnippet: 'замовляйте консультацію інженера за посиланням', role: 'cta', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_dem_05', textSnippet: 'збільшить ваші продажі копченого м’яса вдвічі', role: 'retention', classification: 'hypothesized', requiresEvidenceRefs: false }
  ],
  knownUncertainties: ['Вплив на об’єм продажів є припущенням'],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 4000, text: 'Шукаєте надійне обладнання? Наша коптильна камера ReBurn повністю виготовлена з харчової нержавіючої сталі AISI 304.' },
    { startMs: 4100, endMs: 9000, text: 'Цей потужний димогенератор забезпечує до 8 годин автономної роботи на одній закладці тріски.' },
    { startMs: 9100, endMs: 14000, text: 'Завдяки унікальній системі очищення диму ви отримаєте ідеальний золотистий колір без гіркоти.' },
    { startMs: 14100, endMs: 18400, text: 'Переходьте за посиланням та замовляйте консультацію інженера прямо зараз.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 4000, visualDescription: 'Загальний план коптильні ReBurn, блискуча нержавіюча сталь' },
    { sceneNumber: 2, startMs: 4000, endMs: 9000, visualDescription: 'Макро зварних швів та димогенератора з щепою' },
    { sceneNumber: 3, startMs: 9000, endMs: 14000, visualDescription: 'Апетитне золотисте м’ясо дістають з камери' },
    { sceneNumber: 4, startMs: 14000, endMs: 18400, visualDescription: 'Титр з сайтом та заклик до дії' }
  ],
  ocrFrames: [
    { timestampMs: 2000, text: 'ReBurn: Коптильні з нержавіючої сталі AISI 304' },
    { timestampMs: 7000, text: 'Димогенератор: 8 годин автономності' },
    { timestampMs: 16000, text: 'Консультація інженера: dnk-e.com' }
  ],
  claims: [
    {
      id: 'cl_dem_01',
      textSnippet: 'коптильна камера ReBurn повністю виготовлена з харчової нержавіючої сталі AISI 304',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 4000 },
      evidenceRefs: {
        transcriptSegmentIds: ['tr_seg_1'],
        sceneIds: ['sc_scene_1'],
        ocrFrameIds: ['ocr_frame_1']
      },
      confidence: 0.98
    },
    {
      id: 'cl_dem_02',
      textSnippet: 'димогенератор забезпечує до 8 годин автономної роботи',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 4100, endMs: 9000 },
      evidenceRefs: {
        transcriptSegmentIds: ['tr_seg_2'],
        sceneIds: ['sc_scene_2'],
        ocrFrameIds: ['ocr_frame_2']
      },
      confidence: 0.95
    },
    {
      id: 'cl_dem_03',
      textSnippet: 'ви отримаєте ідеальний золотистий колір без гіркоти',
      classification: 'observed',
      role: 'core',
      timeRange: { startMs: 9100, endMs: 14000 },
      evidenceRefs: {
        transcriptSegmentIds: ['tr_seg_3'],
        sceneIds: ['sc_scene_3']
      },
      confidence: 0.91
    },
    {
      id: 'cl_dem_04',
      textSnippet: 'замовляйте консультацію інженера за посиланням',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 14100, endMs: 18400 },
      evidenceRefs: {
        transcriptSegmentIds: ['tr_seg_4'],
        sceneIds: ['sc_scene_4'],
        ocrFrameIds: ['ocr_frame_3']
      },
      confidence: 0.99
    },
    {
      id: 'cl_dem_05',
      textSnippet: 'збільшить ваші продажі копченого м’яса вдвічі',
      classification: 'hypothesized',
      role: 'retention',
      timeRange: { startMs: 9100, endMs: 14000 },
      evidenceRefs: {},
      confidence: 0.60
    }
  ]
});

// ==========================================
// 2. WORKSHOP TALKING-HEAD FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-workshop-talking-head-001',
  category: 'workshop_talking_head',
  title: 'Чому гіркне м’ясо при копченні та як це виправити',
  durationMs: 28000,
  expectedScenesCount: 3,
  expectedOcrTerms: ['ReBurn', 'конденсатовідвідник'],
  expectedTechnicalTerms: ['конденсатовідвідник', 'холодне копчення', 'тріска'],
  expectedClaims: [
    { id: 'cl_th_01', textSnippet: 'головна проблема гіркоти — це важкий конденсат', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_th_02', textSnippet: 'наш конденсатовідвідник повністю вловлює смоли', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_th_03', textSnippet: 'залишіть заявку на розрахунок комплектації', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 6000, text: 'Часто стикаєтеся з кислим або гірким смаком? Головна проблема гіркоти — це важкий конденсат, який осідає на продукті.' },
    { startMs: 6100, endMs: 18000, text: 'У димогенераторах ReBurn наш конденсатовідвідник запатентованої конструкції повністю вловлює смоли та вологу.' },
    { startMs: 18100, endMs: 28000, text: 'Хочете коптити професійно? Залишіть заявку на розрахунок комплектації вашої майбутньої коптильні.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 6000, visualDescription: 'Майстер у цеху розповідає на камеру, тримаючи в руках закопчену деталь' },
    { sceneNumber: 2, startMs: 6000, endMs: 18000, visualDescription: 'Демонстрація конденсатовідвідника ReBurn у розрізі, витікання темної смоли' },
    { sceneNumber: 3, startMs: 18000, endMs: 28000, visualDescription: 'Майстер посміхається біля великої лінійки коптилень ReBurn' }
  ],
  ocrFrames: [
    { timestampMs: 3000, text: 'Проблема: Гіркота при копченні' },
    { timestampMs: 12000, text: 'Рішення: Конденсатовідвідник ReBurn' },
    { timestampMs: 22000, text: 'Заявка на розрахунок комплектації' }
  ],
  claims: [
    {
      id: 'cl_th_01',
      textSnippet: 'головна проблема гіркоти — це важкий конденсат',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 6000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.97
    },
    {
      id: 'cl_th_02',
      textSnippet: 'наш конденсатовідвідник повністю вловлює смоли',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 6100, endMs: 18000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.96
    },
    {
      id: 'cl_th_03',
      textSnippet: 'залишіть заявку на розрахунок комплектації',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 18100, endMs: 28000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.98
    }
  ]
});

// ==========================================
// 3. BEFORE / AFTER FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-before-after-001',
  category: 'before_after',
  title: 'Порівняння: Копчення у бочці vs у камері ReBurn',
  durationMs: 22000,
  expectedScenesCount: 3,
  expectedOcrTerms: ['До', 'Після', 'ReBurn'],
  expectedTechnicalTerms: ['коптильня', 'температура ядра', 'копчення'],
  expectedClaims: [
    { id: 'cl_ba_01', textSnippet: 'копчення у звичайній бочці дає нерівномірний колір', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_ba_02', textSnippet: 'автоматика ReBurn контролює температуру ядра', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_ba_03', textSnippet: 'дізнайтеся ціну готової коптильні під ваші потреби', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 7000, text: 'Порівняйте самі! Копчення у звичайній бочці дає нерівномірний колір, сажу та перегрів продукту.' },
    { startMs: 7100, endMs: 15000, text: 'А ось результат у ReBurn: розумна автоматика чітко контролює температуру ядра та подачу чистого диму.' },
    { startMs: 15100, endMs: 22000, text: 'Бажаєте такий самий ідеальний результат щоразу? Дізнайтеся ціну готової коптильні ReBurn.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 7000, visualDescription: 'Нерівномірно закопчене сало з чорними плямами сажі' },
    { sceneNumber: 2, startMs: 7000, endMs: 15000, visualDescription: 'Ідеальне бурштинове реберце, термощуп всередині м’яса' },
    { sceneNumber: 3, startMs: 15000, endMs: 22000, visualDescription: 'Логотип ReBurn, контакти та заклик дізнатися ціну' }
  ],
  ocrFrames: [
    { timestampMs: 3000, text: 'Звичайна бочка: Сажа та перегрів' },
    { timestampMs: 10000, text: 'Коптильня ReBurn: Рівномірний прогрів' },
    { timestampMs: 18000, text: 'Дізнатися ціну: reburn.com.ua' }
  ],
  claims: [
    {
      id: 'cl_ba_01',
      textSnippet: 'копчення у звичайній бочці дає нерівномірний колір',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 7000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.96
    },
    {
      id: 'cl_ba_02',
      textSnippet: 'автоматика ReBurn контролює температуру ядра',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 7100, endMs: 15000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.95
    },
    {
      id: 'cl_ba_03',
      textSnippet: 'дізнайтеся ціну готової коптильні під ваші потреби',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 15100, endMs: 22000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.97
    }
  ]
});

// ==========================================
// 4. EDUCATIONAL LISTICLE FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-educational-listicle-001',
  category: 'educational_listicle',
  title: '3 критичні помилки при виборі щепи для копчення',
  durationMs: 35000,
  expectedScenesCount: 4,
  expectedOcrTerms: ['3 помилки', 'щепа', 'ReBurn'],
  expectedTechnicalTerms: ['щепа', 'термоконтроль', 'гаряче копчення'],
  expectedClaims: [
    { id: 'cl_ed_01', textSnippet: 'три головні помилки при виборі щепи', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_ed_02', textSnippet: 'хвойні породи виділяють небезпечні смоли', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_ed_03', textSnippet: 'вологість щепи повинна бути не більше п’ятнадцяти відсотків', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_ed_04', textSnippet: 'переходьте за посиланням за детальною інструкцією', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 6000, text: 'Увага! Ось три головні помилки при виборі щепи, які зіпсують ваш дорогий продукт.' },
    { startMs: 6100, endMs: 15000, text: 'Помилка перша: використання хвойних порід. Вони виділяють небезпечні смоли, які роблять м’ясо чорним та гірким.' },
    { startMs: 15100, endMs: 25000, text: 'Помилка друга: надмірна вологість. Для димогенератора ReBurn вологість щепи повинна бути не більше п’ятнадцяти відсотків.' },
    { startMs: 25100, endMs: 35000, text: 'Бажаєте отримати повний гайд з підбору щепи? Переходьте за посиланням за детальною інструкцією.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 6000, visualDescription: 'Спікер стоїть біля столу з купою різної щепи та застерігає пальцем' },
    { sceneNumber: 2, startMs: 6000, endMs: 15000, visualDescription: 'Макро соснових гілок та темного диму' },
    { sceneNumber: 3, startMs: 15000, endMs: 25000, visualDescription: 'Вимірювання вологості вільхової тріски вологоміром' },
    { sceneNumber: 4, startMs: 25000, endMs: 35000, visualDescription: 'Посилання на безкоштовний PDF гайд на екрані' }
  ],
  ocrFrames: [
    { timestampMs: 3000, text: '3 Помилки при виборі щепи' },
    { timestampMs: 10000, text: '1. Хвойна тріска: Небезпечні смоли' },
    { timestampMs: 20000, text: '2. Вологість щепи > 15%' },
    { timestampMs: 30000, text: 'Завантажити Гайд з копчення' }
  ],
  claims: [
    {
      id: 'cl_ed_01',
      textSnippet: 'три головні помилки при виборі щепи',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 6000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.98
    },
    {
      id: 'cl_ed_02',
      textSnippet: 'хвойні породи виділяють небезпечні смоли',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 6100, endMs: 15000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.95
    },
    {
      id: 'cl_ed_03',
      textSnippet: 'вологість щепи повинна бути не більше п’ятнадцяти відсотків',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 15100, endMs: 25000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.94
    },
    {
      id: 'cl_ed_04',
      textSnippet: 'переходьте за посиланням за детальною інструкцією',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 25100, endMs: 35000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_4'], sceneIds: ['sc_scene_4'], ocrFrameIds: ['ocr_frame_4'] },
      confidence: 0.99
    }
  ]
});

// ==========================================
// 5. FOUNDER STORY FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-founder-story-001',
  category: 'founder_story',
  title: 'Історія створення ReBurn: від гаража до бренду №1',
  durationMs: 42000,
  expectedScenesCount: 4,
  expectedOcrTerms: ['ReBurn', 'Зроблено в Україні'],
  expectedTechnicalTerms: ['ReBurn', 'нержавіюча сталь', 'автоматика'],
  expectedClaims: [
    { id: 'cl_fs_01', textSnippet: 'чотири роки тому ми зварили першу коптильню', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_fs_02', textSnippet: 'сьогодні ReBurn — це повністю сертифіковане виробництво', role: 'core', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_fs_03', textSnippet: 'підтримайте українського виробника', role: 'cta', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_fs_04', textSnippet: 'наші коптильні стануть найвіруснішим товаром у вашому місті', role: 'retention', classification: 'hypothesized', requiresEvidenceRefs: false }
  ],
  knownUncertainties: ['Вірусний потенціал не підтверджено даними залученості'],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 8000, text: 'Привіт! Я засновник ReBurn. Чотири роки тому у звичайному гаражі ми зварили нашу першу коптильну камеру.' },
    { startMs: 8100, endMs: 25000, text: 'Сьогодні ReBurn — це сертифіковане виробництво, де професійні інженери виготовляють обладнання преміум якості для України та Європи.' },
    { startMs: 25100, endMs: 42000, text: 'Шукаєте надійний бізнес-інструмент? Обирайте ReBurn та підтримайте українського виробника.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 8000, visualDescription: 'Засновник показує старе чорно-біле фото маленького гаража' },
    { sceneNumber: 2, startMs: 8100, endMs: 25000, visualDescription: 'Сучасний просторий цех лазерної різки металу та професійні зварювальники' },
    { sceneNumber: 3, startMs: 25100, endMs: 42000, visualDescription: 'Ряд готових красивих коптилень ReBurn з синьо-жовтим прапором' }
  ],
  ocrFrames: [
    { timestampMs: 4000, text: 'Засновник ReBurn: З чого все починалося' },
    { timestampMs: 15000, text: 'ReBurn: Професійне обладнання преміум-класу' },
    { timestampMs: 35000, text: 'Зроблено в Україні: Купуй своє!' }
  ],
  claims: [
    {
      id: 'cl_fs_01',
      textSnippet: 'чотири роки тому ми зварили першу коптильню',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 8000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.98
    },
    {
      id: 'cl_fs_02',
      textSnippet: 'сьогодні ReBurn — це повністю сертифіковане виробництво',
      classification: 'observed',
      role: 'core',
      timeRange: { startMs: 8100, endMs: 25000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.97
    },
    {
      id: 'cl_fs_03',
      textSnippet: 'підтримайте українського виробника',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 25100, endMs: 42000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.99
    },
    {
      id: 'cl_fs_04',
      textSnippet: 'наші коптильні стануть найвіруснішим товаром у вашому місті',
      classification: 'hypothesized',
      role: 'retention',
      timeRange: { startMs: 25100, endMs: 42000 },
      evidenceRefs: {},
      confidence: 0.55
    }
  ]
});

// ==========================================
// 6. TECHNICAL EXPLAINER FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-technical-explainer-001',
  category: 'technical_explainer',
  title: 'Як працює система конвекції та термоконтролю ReBurn',
  durationMs: 31000,
  expectedScenesCount: 4,
  expectedOcrTerms: ['ReBurn', 'конвекція', 'PID терморегулятор'],
  expectedTechnicalTerms: ['конвекція', 'термоконтроль', 'терморегулятор', 'дефлектор', 'автоматика'],
  expectedClaims: [
    { id: 'cl_te_01', textSnippet: 'рівномірна температура — це секрет соковитого м’яса', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_te_02', textSnippet: 'дефлекторний вентилятор забезпечує ідеальну конвекцію', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_te_03', textSnippet: 'PID терморегулятор тримає задану температуру', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_te_04', textSnippet: 'замовте індивідуальне проектування коптильні під ваш бізнес', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 6000, text: 'Чи знали ви, що рівномірна температура в усьому об’ємі коптильні — це секрет соковитого м’яса без сухих країв?' },
    { startMs: 6100, endMs: 16000, text: 'У наших камерах дефлекторний вентилятор потужністю 120 ват забезпечує ідеальну примусову конвекцію.' },
    { startMs: 16100, endMs: 24000, text: 'Високоточний PID терморегулятор тримає задану температуру з похибкою не більше ніж пів градуса.' },
    { startMs: 24100, endMs: 31000, text: 'Залиште контакти та замовте індивідуальне проектування коптильні ReBurn під ваш бізнес.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 6000, visualDescription: 'Термознімок внутрішнього об’єму працюючої камери, рівномірно червоне тепло' },
    { sceneNumber: 2, startMs: 6100, endMs: 16000, visualDescription: 'Вентилятор конвекції та круговий ТЕН за дефлекторною панеллю' },
    { sceneNumber: 3, startMs: 16100, endMs: 24000, visualDescription: 'Крупний план блоку управління, цифри 75.0C стабільні на табло' },
    { sceneNumber: 4, startMs: 24100, endMs: 31000, visualDescription: 'Креслення індивідуального проекту на моніторі інженера' }
  ],
  ocrFrames: [
    { timestampMs: 3000, text: 'Рівномірний розподіл тепла: Секрет соковитості' },
    { timestampMs: 11000, text: 'Потужна Конвекція: Вентилятор 120W' },
    { timestampMs: 20000, text: 'PID Терморегулятор: Точність +/- 0.5C' },
    { timestampMs: 28000, text: 'Індивідуальне Проектування ReBurn' }
  ],
  claims: [
    {
      id: 'cl_te_01',
      textSnippet: 'рівномірна температура — це секрет соковитого м’яса',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 6000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.97
    },
    {
      id: 'cl_te_02',
      textSnippet: 'дефлекторний вентилятор забезпечує ідеальну конвекцію',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 6100, endMs: 16000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.98
    },
    {
      id: 'cl_te_03',
      textSnippet: 'PID терморегулятор тримає задану температуру',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 16100, endMs: 24000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.96
    },
    {
      id: 'cl_te_04',
      textSnippet: 'замовте індивідуальне проектування коптильні під ваш бізнес',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 24100, endMs: 31000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_4'], sceneIds: ['sc_scene_4'], ocrFrameIds: ['ocr_frame_4'] },
      confidence: 0.99
    }
  ]
});

// ==========================================
// 7. OFFER / CTA FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-offer-cta-001',
  category: 'offer_cta',
  title: 'Унікальна пропозиція: Коптильня ReBurn за спеціальною ціною',
  durationMs: 15000,
  expectedScenesCount: 3,
  expectedOcrTerms: ['ReBurn', 'Консультація', 'Розрахунок'],
  expectedTechnicalTerms: ['коптильна камера', 'ReBurn'],
  expectedClaims: [
    { id: 'cl_of_01', textSnippet: 'тільки до кінця тижня діє супер ціна', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_of_02', textSnippet: 'безкоштовна доставка та мішок тріски у подарунок', role: 'core', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_of_03', textSnippet: 'тисніть на кнопку та отримайте розрахунок окупності', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 5000, text: 'Увага! Тільки до кінця тижня діє супер ціна на найпопулярнішу модель ReBurn-150.' },
    { startMs: 5100, endMs: 10000, text: 'При замовленні зараз — безкоштовна доставка по всій Україні та мішок фірмової вільхової тріски у подарунок!' },
    { startMs: 10100, endMs: 15000, text: 'Не втрачайте вигоду! Тисніть на кнопку під відео та отримайте швидкий розрахунок окупності.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 5000, visualDescription: 'Велика червона плашка зі знижкою 15% на фоні коптильні ReBurn-150' },
    { sceneNumber: 2, startMs: 5100, endMs: 10000, visualDescription: 'Завантаження коптильні у фірмовий вантажний автомобіль та мішок щепи поруч' },
    { sceneNumber: 3, startMs: 10100, endMs: 15000, visualDescription: 'Телефон, де пальцем тиснуть на кнопку Замовити розрахунок' }
  ],
  ocrFrames: [
    { timestampMs: 2500, text: 'Акція: Спеціальна ціна ReBurn-150' },
    { timestampMs: 7500, text: 'Подарунок: Доставка + Вільхова тріска' },
    { timestampMs: 12500, text: 'Розрахунок Окупності: Клікни тут!' }
  ],
  claims: [
    {
      id: 'cl_of_01',
      textSnippet: 'тільки до кінця тижня діє супер ціна',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 5000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.98
    },
    {
      id: 'cl_of_02',
      textSnippet: 'безкоштовна доставка та мішок тріски у подарунок',
      classification: 'observed',
      role: 'core',
      timeRange: { startMs: 5100, endMs: 10000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.97
    },
    {
      id: 'cl_of_03',
      textSnippet: 'тисніть на кнопку та отримайте розрахунок окупності',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 10100, endMs: 15000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.99
    }
  ]
});

// ==========================================
// 8. NO-AUDIO VIDEO FIXTURE (DEGRADED MODE)
// ==========================================
registerScenario({
  id: 'reburn-no-audio-001',
  category: 'no_audio',
  title: 'Професійне обладнання ReBurn (Visual-only degraded mode)',
  durationMs: 14000,
  expectedScenesCount: 3,
  expectedOcrTerms: ['ReBurn', 'AISI 304'],
  expectedTechnicalTerms: ['нержавіюча сталь'],
  expectedClaims: [
    { id: 'cl_na_01', textSnippet: 'ReBurn AISI 304 нержавіюча сталь', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_na_02', textSnippet: 'dnk-e.com', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: ['Через відсутність аудіо аналіз заснований виключно на візуальних кадрах та OCR титрах'],
  expectedAggregateStatus: 'DEGRADED',
  coverageType: 'degraded',
  transcriptSegments: [], // Empty transcript
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 5000, visualDescription: 'Повільний проліт камери вздовж корпусу коптильні з дзеркальним відображенням' },
    { sceneNumber: 2, startMs: 5000, endMs: 10000, visualDescription: 'Крупно: панель з лазерним маркуванням AISI 304' },
    { sceneNumber: 3, startMs: 10000, endMs: 14000, visualDescription: 'Титр dnk-e.com на чорному тлі' }
  ],
  ocrFrames: [
    { timestampMs: 2500, text: 'ReBurn: Преміум якість' },
    { timestampMs: 7500, text: 'Харчова сталь AISI 304' },
    { timestampMs: 12000, text: 'Заходьте на dnk-e.com' }
  ],
  claims: [
    {
      id: 'cl_na_01',
      textSnippet: 'ReBurn AISI 304 нержавіюча сталь',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 10000 },
      evidenceRefs: { sceneIds: ['sc_scene_1', 'sc_scene_2'], ocrFrameIds: ['ocr_frame_1', 'ocr_frame_2'] },
      confidence: 0.94
    },
    {
      id: 'cl_na_02',
      textSnippet: 'dnk-e.com',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 10000, endMs: 14000 },
      evidenceRefs: { sceneIds: ['sc_scene_3'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.95
    }
  ]
});

// ==========================================
// 9. NO-OCR VIDEO FIXTURE (EMPTY OCR)
// ==========================================
registerScenario({
  id: 'reburn-no-ocr-001',
  category: 'no_ocr',
  title: 'Натуральне копчення домашніх ковбасок (No text/titles)',
  durationMs: 16000,
  expectedScenesCount: 3,
  expectedOcrTerms: [],
  expectedTechnicalTerms: ['коптильня', 'димогенератор'],
  expectedClaims: [
    { id: 'cl_no_01', textSnippet: 'ковбаски у коптильні ReBurn виходять надзвичайно соковитими', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_no_02', textSnippet: 'димогенератор подає чистий густий дим', role: 'technical', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: ['Через відсутність текстових накладень і титрів OCR розпізнавання порожнє'],
  expectedAggregateStatus: 'READY',
  coverageType: 'partial',
  transcriptSegments: [
    { startMs: 0, endMs: 6000, text: 'Подивіться, які красиві домашні ковбаски! У коптильні ReBurn вони виходять надзвичайно соковитими та ароматними.' },
    { startMs: 6100, endMs: 16000, text: 'Наш фірмовий димогенератор стабільно подає чистий та густий дим потрібної температури.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 6000, visualDescription: 'Красиві рум’яні ковбаски апетитно висять усередині камери' },
    { sceneNumber: 2, startMs: 6000, endMs: 11000, visualDescription: 'Дим красивою цівкою виходить з труби' },
    { sceneNumber: 3, startMs: 11000, endMs: 16000, visualDescription: 'Загальний план коптильні на подвір’ї, жодного тексту на екрані' }
  ],
  ocrFrames: [], // Empty OCR
  claims: [
    {
      id: 'cl_no_01',
      textSnippet: 'ковбаски у коптильні ReBurn виходять надзвичайно соковитими',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 6000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'] },
      confidence: 0.95
    },
    {
      id: 'cl_no_02',
      textSnippet: 'димогенератор подає чистий густий дим',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 6100, endMs: 16000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2'] },
      confidence: 0.96
    }
  ]
});

// ==========================================
// 10. FAST-PACED SHORT FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-fast-paced-short-001',
  category: 'fast_paced_short',
  title: 'Швидкий тест коптильні ReBurn за 12 секунд',
  durationMs: 12000,
  expectedScenesCount: 5,
  expectedOcrTerms: ['ReBurn', 'Шок', 'Результат'],
  expectedTechnicalTerms: ['димогенератор', 'тріска'],
  expectedClaims: [
    { id: 'cl_fp_01', textSnippet: 'шок результат за 12 секунд', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_fp_02', textSnippet: 'димогенератор ReBurn готовий за хвилину', role: 'technical', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_fp_03', textSnippet: 'хочеш так само переходь за посиланням', role: 'cta', classification: 'observed', requiresEvidenceRefs: true }
  ],
  knownUncertainties: [],
  expectedAggregateStatus: 'READY',
  coverageType: 'full',
  transcriptSegments: [
    { startMs: 0, endMs: 3000, text: 'Шок результат за дванадцять секунд! Дивись сюди.' },
    { startMs: 3100, endMs: 8000, text: 'Професійний димогенератор ReBurn готовий до роботи за одну хвилину на будь-якій трісці.' },
    { startMs: 8100, endMs: 12000, text: 'Хочеш коптити так само круто? Тисни за посиланням.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 2500, visualDescription: 'Блискавичний зум на димогенератор, дим валить клубами' },
    { sceneNumber: 2, startMs: 2500, endMs: 5000, visualDescription: 'Рука засипає тріску у димогенератор' },
    { sceneNumber: 3, startMs: 5000, endMs: 7500, visualDescription: 'Клацання тумблера включення автоматики' },
    { sceneNumber: 4, startMs: 7500, endMs: 10000, visualDescription: 'Апетитне м’ясо розрізають ножем, витікає прозорий сік' },
    { sceneNumber: 5, startMs: 10000, endMs: 12000, visualDescription: 'Екран телефону з кнопкою сайту ReBurn' }
  ],
  ocrFrames: [
    { timestampMs: 1500, text: 'ШОК-РЕЗУЛЬТАТ ЗА 12 СЕКУНД!' },
    { timestampMs: 4000, text: 'Запуск за 1 хвилину' },
    { timestampMs: 9000, text: 'ТИСНИ ПОСИЛАННЯ!' }
  ],
  claims: [
    {
      id: 'cl_fp_01',
      textSnippet: 'шок результат за 12 секунд',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 3000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.97
    },
    {
      id: 'cl_fp_02',
      textSnippet: 'димогенератор ReBurn готовий за хвилину',
      classification: 'observed',
      role: 'technical',
      timeRange: { startMs: 3100, endMs: 8000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_2'], sceneIds: ['sc_scene_2', 'sc_scene_3'], ocrFrameIds: ['ocr_frame_2'] },
      confidence: 0.95
    },
    {
      id: 'cl_fp_03',
      textSnippet: 'хочеш так само переходь за посиланням',
      classification: 'observed',
      role: 'cta',
      timeRange: { startMs: 8100, endMs: 12000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_3'], sceneIds: ['sc_scene_5'], ocrFrameIds: ['ocr_frame_3'] },
      confidence: 0.99
    }
  ]
});

// ==========================================
// 11. MANUAL REVIEW FIXTURE
// ==========================================
registerScenario({
  id: 'reburn-manual-review-001',
  category: 'manual_review',
  title: 'Нестандартні режими експлуатації коптильні (Conflicting statements)',
  durationMs: 25000,
  expectedScenesCount: 3,
  expectedOcrTerms: ['ReBurn'],
  expectedTechnicalTerms: ['коптильня'],
  expectedClaims: [
    { id: 'cl_mr_01', textSnippet: 'коптильня працює абсолютно без диму', role: 'hook', classification: 'observed', requiresEvidenceRefs: true },
    { id: 'cl_mr_02', textSnippet: 'наша автоматика гарантує стовідсотковий прибуток з першого дня', role: 'core', classification: 'hypothesized', requiresEvidenceRefs: false }
  ],
  knownUncertainties: ['Твердження про стовідсотковий прибуток з першого дня є комерційно спекулятивним та потребує ручної перевірки'],
  expectedAggregateStatus: 'NEEDS_REVIEW',
  coverageType: 'manual_review',
  transcriptSegments: [
    { startMs: 0, endMs: 8000, text: 'Унікальна розробка! Наша коптильня ReBurn працює абсолютно без диму та вогню, завдяки інноваційним ультразвуковим хвилям.' },
    { startMs: 8100, endMs: 25000, text: 'Високоточна автоматика ReBurn гарантує стовідсотковий прибуток з першого дня використання вашого нового бізнесу.' }
  ],
  scenes: [
    { sceneNumber: 1, startMs: 0, endMs: 8000, visualDescription: 'Незрозуміле дзижчання ультразвукової ванни з підключеними дротами до коптильні' },
    { sceneNumber: 2, startMs: 8100, endMs: 25000, visualDescription: 'Графіки стрімкого зростання продажів та посміхнені обличчя людей' }
  ],
  ocrFrames: [
    { timestampMs: 4000, text: 'Копчення ультразвуком: Без диму!' },
    { timestampMs: 15000, text: '100% Гарантований Прибуток!' }
  ],
  claims: [
    {
      id: 'cl_mr_01',
      textSnippet: 'коптильня працює абсолютно без диму',
      classification: 'observed',
      role: 'hook',
      timeRange: { startMs: 0, endMs: 8000 },
      evidenceRefs: { transcriptSegmentIds: ['tr_seg_1'], sceneIds: ['sc_scene_1'], ocrFrameIds: ['ocr_frame_1'] },
      confidence: 0.81
    },
    {
      id: 'cl_mr_02',
      textSnippet: 'наша автоматика гарантує стовідсотковий прибуток з першого дня',
      classification: 'hypothesized',
      role: 'core',
      timeRange: { startMs: 8100, endMs: 25000 },
      evidenceRefs: {},
      confidence: 0.40
    }
  ]
});

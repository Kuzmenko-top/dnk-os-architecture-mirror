/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/adaptation/domain/brand/reburn-profile.ts"
# purpose: "Canonical ReBurn Brand Profile with Versioned Approved Facts and Forbidden Claims."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { BrandProfile, ApprovedBrandFact } from '../../../schemas/brand.js';

export const REBURN_APPROVED_FACTS: ApprovedBrandFact[] = [
  {
    id: 'reburn-fact-mat-001',
    text: 'Коптильна камера та димогенератор ReBurn виготовлені з харчової нержавіючої сталі AISI 304 з аргонним TIG зварюванням.',
    category: 'material',
    source: 'reburn-spec-v2.1-sheet-aisi304',
    verifiedAt: '2026-08-15T10:00:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-proc-002',
    text: 'Примусова конвекція та дефлекторний блок забезпечують рівномірний розподіл диму та температури по всій камері з точністю ±1.5°C.',
    category: 'process',
    source: 'reburn-lab-test-thermal-convection-report-2026',
    verifiedAt: '2026-08-18T14:30:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-proc-003',
    text: 'Цифровий PID-термоконтролер з термощупом для вимірювання температури в середині продукту запобігає пересушуванню та забезпечує повторюваний результат.',
    category: 'process',
    source: 'reburn-tech-manual-pid-controller-v3',
    verifiedAt: '2026-08-20T09:15:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-prod-004',
    text: 'Універсальний комбінований цикл дозволяє виконувати холодне (18-25°C), напівгаряче та гаряче копчення (до 110°C) в одній установці.',
    category: 'product',
    source: 'reburn-cert-product-capabilities-eu-ukr-2026',
    verifiedAt: '2026-08-22T11:00:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-safe-005',
    text: 'Циклонний конденсатовідвідник та фільтр-охолоджувач диму очищають димову суміш від важких смол, дегтю та кислого конденсату.',
    category: 'safety',
    source: 'reburn-engineering-patent-tar-condenser-v1',
    verifiedAt: '2026-08-25T16:00:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-comm-006',
    text: 'Комплект під ключ постачається готовим до першого запуску: димогенератор, компресор-нагнітач, контролер, стартовий набір вільхової тріски та заводська гарантія 12 місяців.',
    category: 'commercial',
    source: 'reburn-commercial-sales-warranty-policy-2026',
    verifiedAt: '2026-08-28T12:00:00.000Z',
    status: 'approved',
  },
  {
    id: 'reburn-fact-proc-007',
    text: 'Використання сухої каліброваної тріски вільхи, бука та фруктових порід (яблуня, вишня) виключає гіркоту та дає рівномірний золотистий колір без сажі.',
    category: 'process',
    source: 'reburn-culinary-guide-wood-chips-calibration',
    verifiedAt: '2026-08-30T08:00:00.000Z',
    status: 'approved',
  },
];

export const REBURN_FORBIDDEN_CLAIMS: string[] = [
  'коптити в квартирі без витяжки',
  'безпечно для закритих житлових кімнат без вентиляції',
  '100% прибуток за 7 днів',
  'гарантована окупність за 3 дні',
  'лікує хвороби',
  'абсолютно бездимне копчення в спальні',
  'кустарна переробка електрики 380 вольт без заземлення',
];

export const REBURN_BRAND_PROFILE: BrandProfile = {
  id: 'brand-reburn-001',
  brandName: 'ReBurn',
  niche: 'smoking_equipment',
  toneGuidelines: [
    'Експертний, технічно виважений, але простий для розуміння тон.',
    'Повага до традицій копчення поєднана з сучасною інженерною точністю.',
    'Жодного агресивного "купи прямо зараз", фокус на вирішенні болю користувача (гіркота, конденсат, нерівномірність).',
  ],
  approvedFacts: REBURN_APPROVED_FACTS,
  forbiddenClaims: REBURN_FORBIDDEN_CLAIMS,
  defaultCtaPatterns: [
    'Пишіть у повідомлення "КОПТИЛЬНЯ" для детального розрахунку моделі під ваші обсяги.',
    'Замовляйте безкоштовну консультацію нашого інженера за посиланням у профілі.',
    'Дивіться повний огляд та характеристики обладнання на нашому сайті.',
  ],
};

/*
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/src/schemas/brand.ts"
# purpose: "Brand Profile, Versioned Approved Facts and Compliance Zod Schemas for Niche Adaptation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
*/

import { z } from 'zod';

export const ApprovedBrandFactCategorySchema = z.enum([
  'product',
  'material',
  'process',
  'safety',
  'commercial',
]);

export type ApprovedBrandFactCategory = z.infer<typeof ApprovedBrandFactCategorySchema>;

export const ApprovedBrandFactStatusSchema = z.enum([
  'approved',
  'draft',
  'deprecated',
]);

export type ApprovedBrandFactStatus = z.infer<typeof ApprovedBrandFactStatusSchema>;

export const ApprovedBrandFactSchema = z.object({
  id: z.string().min(1),
  text: z.string().min(1),
  category: ApprovedBrandFactCategorySchema,
  source: z.string().min(1),
  verifiedAt: z.string(),
  expiresAt: z.string().optional(),
  status: ApprovedBrandFactStatusSchema.default('approved'),
});

export type ApprovedBrandFact = z.infer<typeof ApprovedBrandFactSchema>;

export const BrandProfileSchema = z.object({
  id: z.string().min(1),
  brandName: z.string().min(1),
  niche: z.string().min(1),
  toneGuidelines: z.array(z.string()).default([]),
  approvedFacts: z.array(ApprovedBrandFactSchema).default([]),
  forbiddenClaims: z.array(z.string()).default([]),
  defaultCtaPatterns: z.array(z.string()).default([]),
});

export type BrandProfile = z.infer<typeof BrandProfileSchema>;

export const BrandComplianceStatusSchema = z.enum([
  'compliant',
  'approved',
  'flagged',
  'rejected',
]);

export type BrandComplianceStatus = z.infer<typeof BrandComplianceStatusSchema>;

export const BrandComplianceReportSchema = z.object({
  status: BrandComplianceStatusSchema,
  usedFactIds: z.array(z.string()).default([]),
  unverifiedClaims: z.array(z.string()).default([]),
  forbiddenViolations: z.array(z.string()).default([]),
  commercialViolations: z.array(z.string()).default([]),
  toneScore: z.number().min(0).max(1).default(1.0),
  notes: z.array(z.string()).default([]),
});

export type BrandComplianceReport = z.infer<typeof BrandComplianceReportSchema>;

/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/storage/schema.ts"
 * purpose: "Zod runtime schemas and IndexedDB store constants for DNK OS Canvas Storage."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import { z } from 'zod';
import type {
  CanvasState,
  CanvasAsset,
  CanvasMeta,
  NodeProperties,
  LayerState,
  ViewportState,
  CanvasDimensions,
} from './types/canvas.ts';
import type {
  CommandOperation,
  DifferentialSnapshot,
  Transaction,
  DraftRecord,
} from './types/history.ts';

export const CANVAS_DB_NAME = 'dnk_canvas_db';
export const CANVAS_DB_VERSION = 1;

export const CANVAS_STORES = {
  DRAFTS: 'drafts',
  HISTORY: 'history',
  ASSETS: 'assets',
  META: 'meta',
} as const;

export type CanvasStoreName = (typeof CANVAS_STORES)[keyof typeof CANVAS_STORES];

export const ViewportStateSchema = z.object({
  x: z.number(),
  y: z.number(),
  zoom: z.number().positive(),
});

export const CanvasDimensionsSchema = z.object({
  width: z.number().positive(),
  height: z.number().positive(),
});

export const NodePropertiesSchema = z.object({
  id: z.string(),
  type: z.string(),
  name: z.string().optional(),
  x: z.number(),
  y: z.number(),
  width: z.number(),
  height: z.number(),
  rotation: z.number().optional().default(0),
  scaleX: z.number().optional().default(1),
  scaleY: z.number().optional().default(1),
  opacity: z.number().optional().default(1),
  visible: z.boolean().optional().default(true),
  locked: z.boolean().optional().default(false),
  zIndex: z.number().optional().default(0),
  fill: z.string().optional(),
  stroke: z.string().optional(),
  strokeWidth: z.number().optional(),
  style: z.record(z.string(), z.unknown()).optional(),
  props: z.record(z.string(), z.unknown()).optional(),
  parentId: z.string().nullable().optional(),
  customData: z.record(z.string(), z.unknown()).optional(),
});

export const LayerStateSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  visible: z.boolean().default(true),
  locked: z.boolean().default(false),
  opacity: z.number().min(0).max(1).default(1),
  zIndex: z.number().default(0),
  nodes: z.array(NodePropertiesSchema).default([]),
  metadata: z.record(z.unknown()).optional(),
});

export const CanvasStateSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  version: z.number().int().nonnegative().default(1),
  viewport: ViewportStateSchema,
  dimensions: CanvasDimensionsSchema,
  layers: z.array(LayerStateSchema).default([]),
  activeLayerId: z.string().nullable().default(null),
  selectedNodeIds: z.array(z.string()).default([]),
  metadata: z.record(z.unknown()).default({}),
  createdAt: z.number().int().positive(),
  updatedAt: z.number().int().positive(),
});

export const CommandOperationSchema = z.object({
  op: z.enum(['add', 'remove', 'replace', 'move', 'copy', 'test']),
  path: z.string().min(1),
  value: z.unknown().optional(),
  from: z.string().optional(),
});

export const DifferentialSnapshotSchema = z.object({
  baseSnapshotId: z.string().min(1),
  targetSnapshotId: z.string().min(1),
  forwardPatches: z.array(CommandOperationSchema),
  inversePatches: z.array(CommandOperationSchema),
  timestamp: z.number().int().positive(),
  version: z.number().int().nonnegative(),
  checksum: z.string().optional(),
});

export const TransactionSchema = z.object({
  id: z.string().min(1),
  draftId: z.string().min(1),
  sequenceNumber: z.number().int().nonnegative(),
  timestamp: z.number().int().positive(),
  description: z.string().default(''),
  forwardPatches: z.array(CommandOperationSchema),
  inversePatches: z.array(CommandOperationSchema),
  metadata: z.record(z.unknown()).optional(),
});

export const DraftRecordSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  state: CanvasStateSchema,
  isDifferential: z.boolean().optional().default(false),
  baseDraftId: z.string().nullable().optional().default(null),
  differentialSnapshot: DifferentialSnapshotSchema.optional(),
  checksum: z.string().min(1),
  createdAt: z.number().int().positive(),
  updatedAt: z.number().int().positive(),
});

export const CanvasAssetSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  mimeType: z.string().min(1),
  size: z.number().nonnegative(),
  dataUrl: z.string().optional(),
  dataBase64: z.string().optional(),
  blob: z.any().optional(),
  metadata: z.record(z.unknown()).optional(),
  createdAt: z.number().int().positive(),
  updatedAt: z.number().int().positive(),
});

export const CanvasMetaSchema = z.object({
  id: z.string().min(1),
  currentDraftId: z.string().nullable().default(null),
  lastSavedAt: z.number().int().nonnegative().default(0),
  isDirty: z.boolean().default(false),
  isCrashed: z.boolean().default(false),
  activeSessionId: z.string().nullable().default(null),
  schemaVersion: z.number().int().positive().default(1),
  custom: z.record(z.unknown()).optional(),
});

export function validateCanvasState(data: unknown): CanvasState {
  return CanvasStateSchema.parse(data) as CanvasState;
}

export function validateTransaction(data: unknown): Transaction {
  return TransactionSchema.parse(data) as Transaction;
}

export function validateDraftRecord(data: unknown): DraftRecord {
  return DraftRecordSchema.parse(data) as DraftRecord;
}

export function validateCanvasAsset(data: unknown): CanvasAsset {
  return CanvasAssetSchema.parse(data) as CanvasAsset;
}

export function validateCanvasMeta(data: unknown): CanvasMeta {
  return CanvasMetaSchema.parse(data) as CanvasMeta;
}

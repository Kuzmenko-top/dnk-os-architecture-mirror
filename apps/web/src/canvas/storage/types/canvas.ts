/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/storage/types/canvas.ts"
 * purpose: "Core canvas domain types for DNK OS Canvas Engine storage, layers, nodes, and metadata."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

export interface ViewportState {
  x: number;
  y: number;
  zoom: number;
}

export interface CanvasDimensions {
  width: number;
  height: number;
}

export type NodeType =
  | 'shape'
  | 'text'
  | 'image'
  | 'group'
  | 'liquid_block'
  | 'connector'
  | 'frame'
  | 'component'
  | string;

export interface NodeProperties {
  id: string;
  type: NodeType;
  name?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation?: number;
  scaleX?: number;
  scaleY?: number;
  opacity?: number;
  visible?: boolean;
  locked?: boolean;
  zIndex?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  style?: Record<string, unknown>;
  props?: Record<string, unknown>;
  parentId?: string | null;
  customData?: Record<string, unknown>;
}

export interface LayerState {
  id: string;
  name: string;
  visible: boolean;
  locked: boolean;
  opacity: number;
  zIndex: number;
  nodes: NodeProperties[];
  metadata?: Record<string, unknown>;
}

export interface CanvasState {
  id: string;
  name: string;
  version: number;
  viewport: ViewportState;
  dimensions: CanvasDimensions;
  layers: LayerState[];
  activeLayerId: string | null;
  selectedNodeIds: string[];
  metadata: Record<string, unknown>;
  createdAt: number;
  updatedAt: number;
}

export interface CanvasAsset {
  id: string;
  name: string;
  mimeType: string;
  size: number;
  dataUrl?: string;
  dataBase64?: string;
  blob?: Blob | Uint8Array;
  metadata?: Record<string, unknown>;
  createdAt: number;
  updatedAt: number;
}

export interface CanvasMeta {
  id: string;
  currentDraftId: string | null;
  lastSavedAt: number;
  isDirty: boolean;
  isCrashed: boolean;
  activeSessionId: string | null;
  schemaVersion: number;
  custom?: Record<string, unknown>;
}

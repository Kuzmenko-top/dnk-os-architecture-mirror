/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/types.ts"
 * purpose: "Core types for Konva.js Stage, 3-Tier Layer architecture, viewport transforms, and grid snapping."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import type { ViewportState, CanvasDimensions, NodeProperties } from '../storage/types/canvas';

export type LayerTier = 'background' | 'content' | 'interaction';

export interface Point {
  x: number;
  y: number;
}

export interface RectBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface GridConfig {
  enabled: boolean;
  type: 'dots' | 'lines' | 'crosses';
  size: number;
  subdivisions?: number;
  color: string;
  subdivisionColor?: string;
  snapThreshold: number;
}

export interface SnapLine {
  orientation: 'horizontal' | 'vertical';
  position: number;
  start: number;
  end: number;
  type: 'grid' | 'node-edge' | 'node-center';
}

export interface SnapResult {
  x: number;
  y: number;
  snappedX: boolean;
  snappedY: boolean;
  lines: SnapLine[];
}

export interface MarqueeSelection {
  active: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

export interface StageConfig {
  container?: HTMLDivElement | string;
  width: number;
  height: number;
  viewport?: ViewportState;
  dimensions?: CanvasDimensions;
  grid?: Partial<GridConfig>;
  minZoom?: number;
  maxZoom?: number;
  pixelRatio?: number;
}

export interface NodeEventPayload {
  nodeId: string;
  nativeEvent: any;
  target?: any;
}

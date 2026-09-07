/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/layers/background-layer.ts"
 * purpose: "Tier 1 Background Layer: handles static canvas background, boundary frame, and responsive grid."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import Konva from 'konva';
import type { GridConfig, Point } from '../types';
import type { ViewportState, CanvasDimensions } from '../../storage/types/canvas';

function safeDraw(layer: Konva.Layer): void {
  if (!layer.getStage()) return;
  if (typeof window === 'undefined') {
    layer.draw();
  } else {
    layer.batchDraw();
  }
}

export const DEFAULT_GRID_CONFIG: GridConfig = {
  enabled: true,
  type: 'dots',
  size: 20,
  subdivisions: 5,
  color: 'rgba(203, 213, 225, 0.4)', // slate-300
  subdivisionColor: 'rgba(148, 163, 184, 0.6)', // slate-400
  snapThreshold: 6,
};

export class BackgroundLayer {
  public readonly layer: Konva.Layer;
  private backgroundRect: Konva.Rect;
  private canvasFrameRect: Konva.Rect;
  private gridGroup: Konva.Group;
  private gridConfig: GridConfig;
  private dimensions: CanvasDimensions;
  private viewport: ViewportState;

  constructor(
    dimensions: CanvasDimensions = { width: 1920, height: 1080 },
    viewport: ViewportState = { x: 0, y: 0, zoom: 1 },
    gridConfig: Partial<GridConfig> = {}
  ) {
    this.layer = new Konva.Layer({ id: 'dnk-tier-1-background', listening: false });
    this.dimensions = { ...dimensions };
    this.viewport = { ...viewport };
    this.gridConfig = { ...DEFAULT_GRID_CONFIG, ...gridConfig };

    this.backgroundRect = new Konva.Rect({
      name: 'infinite-backdrop',
      fill: '#0F172A', // slate-900 canvas ambient
      listening: false,
    });

    this.canvasFrameRect = new Konva.Rect({
      name: 'canvas-page-frame',
      x: 0,
      y: 0,
      width: this.dimensions.width,
      height: this.dimensions.height,
      fill: '#1E293B', // slate-800
      stroke: 'rgba(99, 102, 241, 0.5)', // indigo-500
      strokeWidth: 1,
      shadowColor: '#000000',
      shadowBlur: 20,
      shadowOpacity: 0.35,
      shadowOffset: { x: 0, y: 10 },
      listening: false,
    });

    this.gridGroup = new Konva.Group({ name: 'grid-group', listening: false });

    this.layer.add(this.backgroundRect);
    this.layer.add(this.canvasFrameRect);
    this.layer.add(this.gridGroup);
  }

  public updateDimensions(dimensions: CanvasDimensions): void {
    this.dimensions = { ...dimensions };
    this.canvasFrameRect.width(this.dimensions.width);
    this.canvasFrameRect.height(this.dimensions.height);
    this.render();
  }

  public updateViewport(viewport: ViewportState, stageWidth: number, stageHeight: number): void {
    this.viewport = { ...viewport };
    this.renderGrid(stageWidth, stageHeight);
  }

  public updateGridConfig(config: Partial<GridConfig>, stageWidth = 2000, stageHeight = 2000): void {
    this.gridConfig = { ...this.gridConfig, ...config };
    this.renderGrid(stageWidth, stageHeight);
  }

  public getGridConfig(): GridConfig {
    return { ...this.gridConfig };
  }

  public render(stageWidth = 2000, stageHeight = 2000): void {
    this.backgroundRect.width(Math.max(stageWidth * 4, 10000));
    this.backgroundRect.height(Math.max(stageHeight * 4, 10000));
    this.backgroundRect.position({
      x: -5000,
      y: -5000,
    });

    this.renderGrid(stageWidth, stageHeight);
    safeDraw(this.layer);
  }

  public renderGrid(stageWidth: number, stageHeight: number): void {
    this.gridGroup.destroyChildren();

    if (!this.gridConfig.enabled) {
      safeDraw(this.layer);
      return;
    }

    const { size, subdivisions, type, color, subdivisionColor } = this.gridConfig;
    const zoom = Math.max(this.viewport.zoom || 1, 0.01);
    
    // Level of detail (LOD) adaptive stepping so we never generate millions of shapes
    let effectiveStep = size;
    while (effectiveStep * zoom < 14 && effectiveStep < 200) {
      effectiveStep *= subdivisions || 5;
    }

    const subStep = effectiveStep / (subdivisions || 5);

    // Canvas space bounds visible in the viewport with bounded limits
    const visibleLeft = -this.viewport.x / zoom;
    const visibleTop = -this.viewport.y / zoom;
    const visibleRight = visibleLeft + stageWidth / zoom;
    const visibleBottom = visibleTop + stageHeight / zoom;

    const startX = Math.floor(visibleLeft / effectiveStep) * effectiveStep - effectiveStep;
    const endX = Math.ceil(visibleRight / effectiveStep) * effectiveStep + effectiveStep;
    const startY = Math.floor(visibleTop / effectiveStep) * effectiveStep - effectiveStep;
    const endY = Math.ceil(visibleBottom / effectiveStep) * effectiveStep + effectiveStep;

    // Safety cap on loop iterations for maximum performance
    const maxStepsPerAxis = 50;
    const stepCountX = Math.min(Math.ceil((endX - startX) / effectiveStep), maxStepsPerAxis);
    const stepCountY = Math.min(Math.ceil((endY - startY) / effectiveStep), maxStepsPerAxis);

    if (type === 'lines') {
      // Sub-grid lines (rendered only when sufficiently zoomed in)
      if (zoom > 1.2 && subdivisions > 1 && subStep * zoom >= 8) {
        for (let i = 0; i <= stepCountX * subdivisions; i++) {
          const x = startX + i * subStep;
          if (x % effectiveStep === 0) continue;
          this.gridGroup.add(
            new Konva.Line({
              points: [x, startY, x, startY + stepCountY * effectiveStep],
              stroke: subdivisionColor,
              strokeWidth: 0.5 / zoom,
              listening: false,
            })
          );
        }
        for (let j = 0; j <= stepCountY * subdivisions; j++) {
          const y = startY + j * subStep;
          if (y % effectiveStep === 0) continue;
          this.gridGroup.add(
            new Konva.Line({
              points: [startX, y, startX + stepCountX * effectiveStep, y],
              stroke: subdivisionColor,
              strokeWidth: 0.5 / zoom,
              listening: false,
            })
          );
        }
      }

      // Major grid lines
      for (let i = 0; i <= stepCountX; i++) {
        const x = startX + i * effectiveStep;
        this.gridGroup.add(
          new Konva.Line({
            points: [x, startY, x, startY + stepCountY * effectiveStep],
            stroke: color,
            strokeWidth: 1 / zoom,
            listening: false,
          })
        );
      }
      for (let j = 0; j <= stepCountY; j++) {
        const y = startY + j * effectiveStep;
        this.gridGroup.add(
          new Konva.Line({
            points: [startX, y, startX + stepCountX * effectiveStep, y],
            stroke: color,
            strokeWidth: 1 / zoom,
            listening: false,
          })
        );
      }
    } else {
      // Dots mode (high-performance LOD)
      for (let i = 0; i <= stepCountX; i++) {
        const x = startX + i * effectiveStep;
        for (let j = 0; j <= stepCountY; j++) {
          const y = startY + j * effectiveStep;
          this.gridGroup.add(
            new Konva.Circle({
              x,
              y,
              radius: Math.max(1 / zoom, 0.8),
              fill: color,
              listening: false,
            })
          );
        }
      }
    }

    safeDraw(this.layer);
  }

  public snapPoint(point: Point): Point {
    const threshold = this.gridConfig.snapThreshold;
    const step = this.gridConfig.size;

    const nearestX = Math.round(point.x / step) * step;
    const nearestY = Math.round(point.y / step) * step;

    return {
      x: Math.abs(point.x - nearestX) <= threshold ? nearestX : point.x,
      y: Math.abs(point.y - nearestY) <= threshold ? nearestY : point.y,
    };
  }
}

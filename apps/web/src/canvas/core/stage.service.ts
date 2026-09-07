/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/stage.service.ts"
 * purpose: "CanvasStageService: Orchestrates Konva.Stage, 3-Tier Layer isolation, viewport transforms, and 60 FPS render scheduler."
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
import { BackgroundLayer } from './layers/background-layer';
import { ContentLayer } from './layers/content-layer';
import { InteractionLayer } from './layers/interaction-layer';
import type { StageConfig, Point, RectBounds, SnapResult, SnapLine } from './types';
import type { ViewportState, CanvasDimensions, LayerState, NodeProperties } from '../storage/types/canvas';

export type ViewportChangeCallback = (viewport: ViewportState) => void;

export class CanvasStageService {
  public readonly stage: Konva.Stage;
  public readonly backgroundTier: BackgroundLayer;
  public readonly contentTier: ContentLayer;
  public readonly interactionTier: InteractionLayer;

  private minZoom: number;
  private maxZoom: number;
  private dimensions: CanvasDimensions;
  private viewportChangeListeners: Set<ViewportChangeCallback> = new Set();
  private destroyed = false;
  private rafTimer: any = null;

  constructor(config: StageConfig) {
    this.minZoom = config.minZoom ?? 0.05;
    this.maxZoom = config.maxZoom ?? 30.0;
    this.dimensions = config.dimensions ?? { width: 1920, height: 1080 };

    const initialViewport: ViewportState = config.viewport ?? { x: 0, y: 0, zoom: 1 };

    // Initialize Konva Stage
    this.stage = new Konva.Stage({
      container: (config.container as any) || (typeof document !== 'undefined' ? document.createElement('div') : undefined),
      width: config.width || 1200,
      height: config.height || 800,
      x: initialViewport.x,
      y: initialViewport.y,
      scaleX: initialViewport.zoom,
      scaleY: initialViewport.zoom,
    });

    // Initialize the 3 Isolated Tiers
    this.backgroundTier = new BackgroundLayer(this.dimensions, initialViewport, config.grid);
    this.contentTier = new ContentLayer();
    this.interactionTier = new InteractionLayer();

    // Attach layers in precise 3-tier visual hierarchy
    this.stage.add(this.backgroundTier.layer);
    this.stage.add(this.contentTier.layer);
    this.stage.add(this.interactionTier.layer);

    this.setupEventListeners();
  }

  // --- Viewport & Coordinate Transformation Math ---

  public getViewport(): ViewportState {
    return {
      x: this.stage.x(),
      y: this.stage.y(),
      zoom: this.stage.scaleX(),
    };
  }

  public setViewport(viewport: Partial<ViewportState>): void {
    const current = this.getViewport();
    const nextZoom = viewport.zoom !== undefined ? this.clampZoom(viewport.zoom) : current.zoom;
    const nextX = viewport.x !== undefined ? viewport.x : current.x;
    const nextY = viewport.y !== undefined ? viewport.y : current.y;

    this.stage.x(nextX);
    this.stage.y(nextY);
    this.stage.scaleX(nextZoom);
    this.stage.scaleY(nextZoom);

    const updated: ViewportState = { x: nextX, y: nextY, zoom: nextZoom };
    this.backgroundTier.updateViewport(updated, this.stage.width(), this.stage.height());

    this.requestRender();
    this.notifyViewportChange(updated);
  }

  public screenToCanvas(screenPoint: Point): Point {
    const scale = this.stage.scaleX() || 1;
    return {
      x: (screenPoint.x - this.stage.x()) / scale,
      y: (screenPoint.y - this.stage.y()) / scale,
    };
  }

  public canvasToScreen(canvasPoint: Point): Point {
    const scale = this.stage.scaleX() || 1;
    return {
      x: canvasPoint.x * scale + this.stage.x(),
      y: canvasPoint.y * scale + this.stage.y(),
    };
  }

  public zoomToPoint(targetZoom: number, screenPoint: Point): void {
    const oldZoom = this.stage.scaleX() || 1;
    const newZoom = this.clampZoom(targetZoom);
    if (Math.abs(oldZoom - newZoom) < 0.0001) return;

    // Canvas position under the cursor
    const mousePointTo = {
      x: (screenPoint.x - this.stage.x()) / oldZoom,
      y: (screenPoint.y - this.stage.y()) / oldZoom,
    };

    const newPos = {
      x: screenPoint.x - mousePointTo.x * newZoom,
      y: screenPoint.y - mousePointTo.y * newZoom,
    };

    this.setViewport({
      x: newPos.x,
      y: newPos.y,
      zoom: newZoom,
    });
  }

  public zoomBy(factor: number, centerScreenPoint?: Point): void {
    const center = centerScreenPoint || {
      x: this.stage.width() / 2,
      y: this.stage.height() / 2,
    };
    const currentZoom = this.stage.scaleX() || 1;
    this.zoomToPoint(currentZoom * factor, center);
  }

  public panBy(dx: number, dy: number): void {
    this.setViewport({
      x: this.stage.x() + dx,
      y: this.stage.y() + dy,
    });
  }

  public fitToScreen(padding = 50): void {
    const stageW = this.stage.width();
    const stageH = this.stage.height();

    const availableW = Math.max(stageW - padding * 2, 100);
    const availableH = Math.max(stageH - padding * 2, 100);

    const scaleX = availableW / this.dimensions.width;
    const scaleY = availableH / this.dimensions.height;
    const fitScale = this.clampZoom(Math.min(scaleX, scaleY));

    const x = (stageW - this.dimensions.width * fitScale) / 2;
    const y = (stageH - this.dimensions.height * fitScale) / 2;

    this.setViewport({ x, y, zoom: fitScale });
  }

  public resetZoom(): void {
    this.zoomToPoint(1, { x: this.stage.width() / 2, y: this.stage.height() / 2 });
  }

  // --- Resize & Lifecycle ---

  public setSize(width: number, height: number): void {
    this.stage.width(width);
    this.stage.height(height);
    this.backgroundTier.render(width, height);
    this.requestRender();
  }

  public setDimensions(dimensions: CanvasDimensions): void {
    this.dimensions = { ...dimensions };
    this.backgroundTier.updateDimensions(dimensions);
    this.requestRender();
  }

  public getDimensions(): CanvasDimensions {
    return { ...this.dimensions };
  }

  // --- Alignment & Snap Engine ---

  public calculateSnapping(activeNodeId: string, bounds: RectBounds, snapThreshold = 6): SnapResult {
    const lines: SnapLine[] = [];
    let snappedX = bounds.x;
    let snappedY = bounds.y;
    let didSnapX = false;
    let didSnapY = false;

    // 1. Grid Snapping
    const gridConfig = this.backgroundTier.getGridConfig();
    if (gridConfig.enabled) {
      const snappedPoint = this.backgroundTier.snapPoint({ x: bounds.x, y: bounds.y });
      if (snappedPoint.x !== bounds.x) {
        snappedX = snappedPoint.x;
        didSnapX = true;
      }
      if (snappedPoint.y !== bounds.y) {
        snappedY = snappedPoint.y;
        didSnapY = true;
      }
    }

    // 2. Node-to-Node Snapping against other content nodes
    const allNodes = this.contentTier.getAllNodes();
    const otherNodes = allNodes.filter((n) => n.id() !== activeNodeId && n.visible());

    const activeCenterX = bounds.x + bounds.width / 2;
    const activeCenterY = bounds.y + bounds.height / 2;
    const activeRight = bounds.x + bounds.width;
    const activeBottom = bounds.y + bounds.height;

    for (const other of otherNodes) {
      const ox = other.x();
      const oy = other.y();
      const ow = other.width();
      const oh = other.height();
      const oCenterX = ox + ow / 2;
      const oCenterY = oy + oh / 2;
      const oRight = ox + ow;
      const oBottom = oy + oh;

      // X-Axis Snapping (Left-to-Left, Center-to-Center, Right-to-Right)
      if (!didSnapX) {
        if (Math.abs(bounds.x - ox) <= snapThreshold) {
          snappedX = ox;
          didSnapX = true;
          lines.push({ orientation: 'vertical', position: ox, start: Math.min(bounds.y, oy), end: Math.max(activeBottom, oBottom), type: 'node-edge' });
        } else if (Math.abs(activeCenterX - oCenterX) <= snapThreshold) {
          snappedX = oCenterX - bounds.width / 2;
          didSnapX = true;
          lines.push({ orientation: 'vertical', position: oCenterX, start: Math.min(bounds.y, oy), end: Math.max(activeBottom, oBottom), type: 'node-center' });
        } else if (Math.abs(activeRight - oRight) <= snapThreshold) {
          snappedX = oRight - bounds.width;
          didSnapX = true;
          lines.push({ orientation: 'vertical', position: oRight, start: Math.min(bounds.y, oy), end: Math.max(activeBottom, oBottom), type: 'node-edge' });
        }
      }

      // Y-Axis Snapping (Top-to-Top, Center-to-Center, Bottom-to-Bottom)
      if (!didSnapY) {
        if (Math.abs(bounds.y - oy) <= snapThreshold) {
          snappedY = oy;
          didSnapY = true;
          lines.push({ orientation: 'horizontal', position: oy, start: Math.min(bounds.x, ox), end: Math.max(activeRight, oRight), type: 'node-edge' });
        } else if (Math.abs(activeCenterY - oCenterY) <= snapThreshold) {
          snappedY = oCenterY - bounds.height / 2;
          didSnapY = true;
          lines.push({ orientation: 'horizontal', position: oCenterY, start: Math.min(bounds.x, ox), end: Math.max(activeRight, oRight), type: 'node-center' });
        } else if (Math.abs(activeBottom - oBottom) <= snapThreshold) {
          snappedY = oBottom - bounds.height;
          didSnapY = true;
          lines.push({ orientation: 'horizontal', position: oBottom, start: Math.min(bounds.x, ox), end: Math.max(activeRight, oRight), type: 'node-edge' });
        }
      }
    }

    return {
      x: snappedX,
      y: snappedY,
      snappedX: didSnapX,
      snappedY: didSnapY,
      lines,
    };
  }

  // --- 60 FPS Render Scheduler ---

  public requestRender(): void {
    if (this.destroyed) return;
    if (this.rafTimer !== null) return;

    if (typeof window !== 'undefined' && typeof requestAnimationFrame !== 'undefined') {
      this.rafTimer = requestAnimationFrame(() => {
        this.rafTimer = null;
        if (!this.destroyed) {
          this.stage.batchDraw();
        }
      });
    } else {
      this.stage.draw();
    }
  }

  public onViewportChange(callback: ViewportChangeCallback): () => void {
    this.viewportChangeListeners.add(callback);
    return () => this.viewportChangeListeners.delete(callback);
  }

  // --- Export Capabilities ---

  public exportToDataURL(pixelRatio = 2): string {
    if (this.destroyed) return '';
    // Hide interaction and background helpers for clean export
    this.interactionTier.layer.visible(false);
    const dataUrl = this.stage.toDataURL({ pixelRatio });
    this.interactionTier.layer.visible(true);
    return dataUrl;
  }

  public destroy(): void {
    this.destroyed = true;
    if (this.rafTimer !== null) {
      if (typeof cancelAnimationFrame !== 'undefined') {
        cancelAnimationFrame(this.rafTimer);
      }
      this.rafTimer = null;
    }
    this.viewportChangeListeners.clear();
    this.stage.destroy();
  }

  // --- Private Helpers ---

  private clampZoom(zoom: number): number {
    return Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
  }

  private notifyViewportChange(viewport: ViewportState): void {
    for (const listener of this.viewportChangeListeners) {
      try {
        listener(viewport);
      } catch (err) {
        console.error('Error in viewport change listener:', err);
      }
    }
  }

  private setupEventListeners(): void {
    // Wheel Zoom & Pan handler
    this.stage.on('wheel', (e) => {
      e.evt.preventDefault();
      const pointer = this.stage.getPointerPosition() || {
        x: this.stage.width() / 2,
        y: this.stage.height() / 2,
      };

      if (e.evt.ctrlKey || e.evt.metaKey) {
        // Pinch / Ctrl+Wheel zoom
        const scaleBy = 1.05;
        const oldZoom = this.stage.scaleX() || 1;
        const newZoom = e.evt.deltaY > 0 ? oldZoom / scaleBy : oldZoom * scaleBy;
        this.zoomToPoint(newZoom, pointer);
      } else {
        // Trackpad / Wheel 2D Pan
        this.panBy(-e.evt.deltaX, -e.evt.deltaY);
      }
    });
  }
}

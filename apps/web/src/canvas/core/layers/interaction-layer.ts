/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/layers/interaction-layer.ts"
 * purpose: "Tier 3 Interaction Layer: handles selection bounding box, transformer, snap guidelines, and marquee selection."
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
import type { SnapLine, RectBounds, Point } from '../types';

function safeDraw(layer: Konva.Layer): void {
  if (typeof window === 'undefined') {
    layer.draw();
  } else {
    layer.batchDraw();
  }
}

export class InteractionLayer {
  public readonly layer: Konva.Layer;
  public readonly transformer: Konva.Transformer;
  private marqueeRect: Konva.Rect;
  private hoverOutline: Konva.Rect;
  private snapLinesGroup: Konva.Group;

  constructor() {
    this.layer = new Konva.Layer({ id: 'dnk-tier-3-interaction', listening: true });

    // Transformer for selection and resizing
    this.transformer = new Konva.Transformer({
      name: 'node-transformer',
      rotateEnabled: true,
      resizeEnabled: true,
      borderStroke: '#6366F1', // indigo-500
      borderStrokeWidth: 1.5,
      borderDash: [4, 4],
      anchorStroke: '#6366F1',
      anchorFill: '#FFFFFF',
      anchorSize: 8,
      anchorCornerRadius: 2,
      shouldOverdrawWholeArea: true,
      enabledAnchors: [
        'top-left',
        'top-center',
        'top-right',
        'middle-right',
        'bottom-right',
        'bottom-center',
        'bottom-left',
        'middle-left',
      ],
    });

    // Marquee selection box
    this.marqueeRect = new Konva.Rect({
      name: 'marquee-selection-box',
      visible: false,
      fill: 'rgba(99, 102, 241, 0.15)',
      stroke: '#6366F1',
      strokeWidth: 1,
      dash: [3, 3],
      listening: false,
    });

    // Hover outline
    this.hoverOutline = new Konva.Rect({
      name: 'hover-highlight-outline',
      visible: false,
      stroke: 'rgba(99, 102, 241, 0.7)',
      strokeWidth: 1,
      dash: [2, 2],
      listening: false,
    });

    // Snap lines container
    this.snapLinesGroup = new Konva.Group({
      name: 'snap-guidelines-group',
      listening: false,
    });

    this.layer.add(this.transformer);
    this.layer.add(this.marqueeRect);
    this.layer.add(this.hoverOutline);
    this.layer.add(this.snapLinesGroup);
  }

  public attachToNodes(nodes: Konva.Node[]): void {
    if (nodes.length === 0) {
      this.transformer.nodes([]);
    } else {
      this.transformer.nodes(nodes);
    }
    safeDraw(this.layer);
  }

  public getAttachedNodes(): Konva.Node[] {
    return this.transformer.nodes();
  }

  public clearSelection(): void {
    this.transformer.nodes([]);
    safeDraw(this.layer);
  }

  public updateHoverOutline(bounds: RectBounds | null): void {
    if (!bounds) {
      this.hoverOutline.visible(false);
    } else {
      this.hoverOutline.setAttrs({
        x: bounds.x,
        y: bounds.y,
        width: bounds.width,
        height: bounds.height,
        visible: true,
      });
    }
    safeDraw(this.layer);
  }

  public startMarquee(startPoint: Point): void {
    this.marqueeRect.setAttrs({
      x: startPoint.x,
      y: startPoint.y,
      width: 0,
      height: 0,
      visible: true,
    });
    safeDraw(this.layer);
  }

  public updateMarquee(currentPoint: Point): void {
    if (!this.marqueeRect.visible()) return;

    const startX = this.marqueeRect.x();
    const startY = this.marqueeRect.y();
    const width = currentPoint.x - startX;
    const height = currentPoint.y - startY;

    this.marqueeRect.width(width);
    this.marqueeRect.height(height);
    safeDraw(this.layer);
  }

  public getMarqueeBounds(): RectBounds | null {
    if (!this.marqueeRect.visible()) return null;

    const x = this.marqueeRect.x();
    const y = this.marqueeRect.y();
    const w = this.marqueeRect.width();
    const h = this.marqueeRect.height();

    return {
      x: w < 0 ? x + w : x,
      y: h < 0 ? y + h : y,
      width: Math.abs(w),
      height: Math.abs(h),
    };
  }

  public endMarquee(): RectBounds | null {
    const bounds = this.getMarqueeBounds();
    this.marqueeRect.visible(false);
    safeDraw(this.layer);
    return bounds;
  }

  public renderSnapLines(lines: SnapLine[]): void {
    this.snapLinesGroup.destroyChildren();

    if (lines.length === 0) {
      safeDraw(this.layer);
      return;
    }

    for (const line of lines) {
      const strokeColor = line.type === 'node-center' ? '#EC4899' : '#EF4444'; // pink-500 or red-500
      let points: number[];

      if (line.orientation === 'vertical') {
        points = [line.position, line.start, line.position, line.end];
      } else {
        points = [line.start, line.position, line.end, line.position];
      }

      const snapLine = new Konva.Line({
        points,
        stroke: strokeColor,
        strokeWidth: 1,
        dash: [4, 4],
        listening: false,
      });

      this.snapLinesGroup.add(snapLine);
    }

    safeDraw(this.layer);
  }

  public clearSnapLines(): void {
    this.snapLinesGroup.destroyChildren();
    safeDraw(this.layer);
  }
}

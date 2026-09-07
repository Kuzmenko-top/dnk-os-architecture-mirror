/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/core/stage.test.ts"
 * purpose: "Unit tests for Konva 3-Tier Stage architecture, viewport math, grid snapping, and node management."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * --- END DNK-MRH-HEADER ---
 */

import { test, describe, afterEach } from 'node:test';
import assert from 'node:assert';
import Konva from 'konva';
import { CanvasStageService } from './stage.service';
import { BackgroundLayer } from './layers/background-layer';
import { ContentLayer } from './layers/content-layer';
import { InteractionLayer } from './layers/interaction-layer';
import type { NodeProperties, LayerState } from '../storage/types/canvas';

// Prevent Konva background animation loop from accessing destroyed canvases in Node.js test environment
if (typeof window === 'undefined') {
  (Konva.Animation as any)._animationLoop = () => {};
  Konva.Layer.prototype.batchDraw = function (this: Konva.Layer) {
    if (this.getStage()) {
      try {
        this.draw();
      } catch {}
    }
    return this;
  };
  Konva.Stage.prototype.batchDraw = function (this: Konva.Stage) {
    try {
      this.draw();
    } catch {}
    return this;
  };
}

describe('Canvas Core Stage & 3-Tier Architecture', () => {
  describe('1. 3-Tier Layer Hierarchy & Initialization', () => {
    test('should initialize CanvasStageService with 3 distinct isolated layers in order', () => {
      const stageService = new CanvasStageService({
        width: 1200,
        height: 800,
        dimensions: { width: 1920, height: 1080 },
      });

      const layers = stageService.stage.getLayers();
      assert.strictEqual(layers.length, 3, 'Stage must contain exactly 3 layers');

      assert.strictEqual(layers[0].id(), 'dnk-tier-1-background', 'Tier 1 must be background');
      assert.strictEqual(layers[1].id(), 'dnk-tier-2-content', 'Tier 2 must be content');
      assert.strictEqual(layers[2].id(), 'dnk-tier-3-interaction', 'Tier 3 must be interaction');

      assert.strictEqual(stageService.backgroundTier.layer.listening(), false, 'Background tier should not listen to events');
      assert.strictEqual(stageService.contentTier.layer.listening(), true, 'Content tier must listen to events');
      assert.strictEqual(stageService.interactionTier.layer.listening(), true, 'Interaction tier must listen to events');

      stageService.destroy();
    });
  });

  describe('2. Viewport & Coordinate Transformations', () => {
    test('should transform coordinates accurately between screen and canvas space at 1x zoom', () => {
      const stageService = new CanvasStageService({
        width: 1000,
        height: 800,
        viewport: { x: 100, y: 50, zoom: 1.0 },
      });

      // Canvas -> Screen
      const screenPt = stageService.canvasToScreen({ x: 200, y: 300 });
      assert.strictEqual(screenPt.x, 300); // 200 * 1 + 100
      assert.strictEqual(screenPt.y, 350); // 300 * 1 + 50

      // Screen -> Canvas
      const canvasPt = stageService.screenToCanvas({ x: 300, y: 350 });
      assert.strictEqual(canvasPt.x, 200);
      assert.strictEqual(canvasPt.y, 300);

      stageService.destroy();
    });

    test('should transform coordinates accurately with non-unit zoom and pan', () => {
      const stageService = new CanvasStageService({
        width: 1000,
        height: 800,
        viewport: { x: 200, y: 100, zoom: 2.0 },
      });

      // Canvas (50, 50) at zoom 2 and pan (200, 100) -> Screen (50*2 + 200, 50*2 + 100) = (300, 200)
      const screenPt = stageService.canvasToScreen({ x: 50, y: 50 });
      assert.strictEqual(screenPt.x, 300);
      assert.strictEqual(screenPt.y, 200);

      const canvasPt = stageService.screenToCanvas({ x: 300, y: 200 });
      assert.strictEqual(canvasPt.x, 50);
      assert.strictEqual(canvasPt.y, 50);

      stageService.destroy();
    });

    test('should enforce min and max zoom limits', () => {
      const stageService = new CanvasStageService({
        width: 1000,
        height: 800,
        minZoom: 0.1,
        maxZoom: 5.0,
      });

      stageService.setViewport({ zoom: 0.01 });
      assert.strictEqual(stageService.getViewport().zoom, 0.1, 'Should clamp to minZoom');

      stageService.setViewport({ zoom: 20.0 });
      assert.strictEqual(stageService.getViewport().zoom, 5.0, 'Should clamp to maxZoom');

      stageService.destroy();
    });

    test('should zoom towards pointer location preserving focus', () => {
      const stageService = new CanvasStageService({
        width: 1000,
        height: 800,
        viewport: { x: 0, y: 0, zoom: 1.0 },
      });

      // Zoom from 1.0 to 2.0 focused on screen center (500, 400)
      stageService.zoomToPoint(2.0, { x: 500, y: 400 });

      const vp = stageService.getViewport();
      assert.strictEqual(vp.zoom, 2.0);
      // New pos = screenPoint - (canvasPoint * newZoom) = 500 - (500 * 2) = -500
      assert.strictEqual(vp.x, -500);
      assert.strictEqual(vp.y, -400);

      stageService.destroy();
    });
  });

  describe('3. Background Tier & Grid Snapping', () => {
    test('should snap points to nearest grid intersections', () => {
      const backgroundLayer = new BackgroundLayer(
        { width: 1920, height: 1080 },
        { x: 0, y: 0, zoom: 1 },
        { enabled: true, size: 20, snapThreshold: 6 }
      );

      // (22, 38) -> within threshold of (20, 40)
      const snapped1 = backgroundLayer.snapPoint({ x: 22, y: 38 });
      assert.strictEqual(snapped1.x, 20);
      assert.strictEqual(snapped1.y, 40);

      // (29, 31) -> delta 9 > threshold 6 -> should not snap
      const snapped2 = backgroundLayer.snapPoint({ x: 29, y: 31 });
      assert.strictEqual(snapped2.x, 29);
      assert.strictEqual(snapped2.y, 31);
    });
  });

  describe('4. Content Tier Node Operations', () => {
    test('should add, update, retrieve, and remove nodes correctly', () => {
      const contentTier = new ContentLayer();

      const nodeProps: NodeProperties = {
        id: 'node-btn-01',
        name: 'CTA Button',
        type: 'shape',
        x: 100,
        y: 150,
        width: 200,
        height: 50,
        rotation: 0,
        visible: true,
        locked: false,
        zIndex: 1,
        props: { fill: '#6366F1' },
      };

      const konvaNode = contentTier.addNode(nodeProps);
      assert.ok(konvaNode);
      assert.strictEqual(konvaNode.x(), 100);
      assert.strictEqual(konvaNode.y(), 150);
      assert.strictEqual(konvaNode.width(), 200);

      // Update node
      contentTier.updateNode({
        ...nodeProps,
        x: 180,
        width: 250,
      });

      const updated = contentTier.getNode('node-btn-01');
      assert.strictEqual(updated?.x(), 180);
      assert.strictEqual(updated?.width(), 250);

      // Remove node
      const removed = contentTier.removeNode('node-btn-01');
      assert.strictEqual(removed, true);
      assert.strictEqual(contentTier.getNode('node-btn-01'), undefined);
    });

    test('should sync node state cleanly from layer tree', () => {
      const contentTier = new ContentLayer();

      const mockLayers: LayerState[] = [
        {
          id: 'layer-1',
          name: 'Hero Section',
          visible: true,
          locked: false,
          zIndex: 0,
          opacity: 1,
          nodes: [
            {
              id: 'header-text',
              name: 'Heading',
              type: 'text',
              x: 50,
              y: 50,
              width: 300,
              height: 40,
              props: { text: 'Welcome to DNK' },
            },
            {
              id: 'hero-box',
              name: 'Background Box',
              type: 'shape',
              x: 0,
              y: 0,
              width: 800,
              height: 400,
            },
          ],
        },
      ];

      contentTier.syncFromState(mockLayers);
      assert.strictEqual(contentTier.getAllNodes().length, 2);

      // Deselect / Remove one node in next state sync
      const nextLayers: LayerState[] = [
        {
          id: 'layer-1',
          name: 'Hero Section',
          visible: true,
          locked: false,
          zIndex: 0,
          opacity: 1,
          nodes: [mockLayers[0].nodes[0]], // only header-text
        },
      ];

      contentTier.syncFromState(nextLayers);
      assert.strictEqual(contentTier.getAllNodes().length, 1);
      assert.strictEqual(contentTier.getNode('header-text')?.id(), 'header-text');
      assert.strictEqual(contentTier.getNode('hero-box'), undefined);
    });
  });

  describe('5. Interaction Tier & Marquee / Transformer Isolation', () => {
    test('should calculate marquee bounding boxes correctly across drag directions', () => {
      const interactionTier = new InteractionLayer();

      // Drag Top-Left to Bottom-Right
      interactionTier.startMarquee({ x: 100, y: 100 });
      interactionTier.updateMarquee({ x: 250, y: 300 });

      const bounds1 = interactionTier.endMarquee();
      assert.deepStrictEqual(bounds1, {
        x: 100,
        y: 100,
        width: 150,
        height: 200,
      });

      // Drag Bottom-Right to Top-Left (inverted)
      interactionTier.startMarquee({ x: 300, y: 400 });
      interactionTier.updateMarquee({ x: 100, y: 200 });

      const bounds2 = interactionTier.endMarquee();
      assert.deepStrictEqual(bounds2, {
        x: 100,
        y: 200,
        width: 200,
        height: 200,
      });
    });

    test('should calculate alignment guides against neighbouring nodes', () => {
      const stageService = new CanvasStageService({
        width: 1200,
        height: 800,
      });

      // Add stationary reference node at (100, 100, w: 100, h: 100)
      stageService.contentTier.addNode({
        id: 'ref-node',
        name: 'Reference',
        type: 'shape',
        x: 100,
        y: 100,
        width: 100,
        height: 100,
      });

      // Drag active node close to left alignment (at x: 103, snapThreshold: 6)
      const snapRes = stageService.calculateSnapping('active-node', {
        x: 103,
        y: 300,
        width: 80,
        height: 50,
      });

      assert.strictEqual(snapRes.snappedX, true, 'Should snap to left edge of reference node');
      assert.strictEqual(snapRes.x, 100, 'X should snap to 100');

      stageService.destroy();
    });
  });
});

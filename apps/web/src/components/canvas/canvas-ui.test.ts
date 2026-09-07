// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/canvas-ui.test.ts"
// purpose: "Unit tests for Zustand Reactive Store, UI actions, commands integration, AIPromptModal, and AI adapters."
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "3.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// license: "DNK-INTERNAL"
// --- END DNK-MRH-HEADER ---

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';
import { useCanvasStudioStore } from './store';
import { UndoRedoStack } from '../../canvas/history/undo-redo-stack';
import { STYLE_PRESETS, DIMENSION_OPTIONS } from './AIPromptModal';
import { CanvasAIClient } from '../../canvas/ai/ai-client';

// Mock IndexedDB
if (typeof globalThis.indexedDB === 'undefined') {
  (globalThis as any).indexedDB = {
    open: () => {
      const request: any = {
        result: {
          createObjectStore: () => ({
            createIndex: () => {},
          }),
          transaction: () => ({
            objectStore: () => ({
              get: () => ({ result: null, onsuccess: null }),
              put: () => ({ onsuccess: null }),
              delete: () => ({ onsuccess: null }),
              getAll: () => ({ result: [], onsuccess: null }),
            }),
          }),
        },
        onsuccess: null,
        onerror: null,
        onupgradeneeded: null,
      };
      setTimeout(() => {
        if (request.onupgradeneeded) request.onupgradeneeded({ target: request });
        if (request.onsuccess) request.onsuccess({ target: request });
      }, 0);
      return request;
    },
  };
}

describe('DNK OS Canvas Studio Zustand Store & UI Actions', () => {
  beforeEach(() => {
    useCanvasStudioStore.setState({
      canvasState: {
        id: 'canvas-test',
        name: 'Test Canvas',
        version: 1,
        viewport: { zoom: 1, x: 0, y: 0 },
        dimensions: { width: 1920, height: 1080 },
        layers: [
          {
            id: 'layer-1',
            name: 'Layer 1',
            visible: true,
            locked: false,
            opacity: 1,
            zIndex: 0,
            nodes: [],
          },
        ],
        activeLayerId: 'layer-1',
        selectedNodeIds: [],
        metadata: {},
        createdAt: Date.now(),
        updatedAt: Date.now(),
      },
      undoRedoStack: new UndoRedoStack({
        initialState: {
          id: 'canvas-test',
          name: 'Test Canvas',
          version: 1,
          viewport: { zoom: 1, x: 0, y: 0 },
          dimensions: { width: 1920, height: 1080 },
          layers: [
            {
              id: 'layer-1',
              name: 'Layer 1',
              visible: true,
              locked: false,
              opacity: 1,
              zIndex: 0,
              nodes: [],
            },
          ],
          activeLayerId: 'layer-1',
          selectedNodeIds: [],
          metadata: {},
          createdAt: Date.now(),
          updatedAt: Date.now(),
        },
      }),
      aiClient: new CanvasAIClient({ enableMockFallback: true }),
      currentTool: 'select',
      selectedNodeIds: [],
      zoom: 1.0,
      pan: { x: 0, y: 0 },
      isDirty: false,
      aiState: {
        isProcessing: false,
        actionType: null,
        progressMessage: null,
        progress: null,
        error: null,
      },
    });
  });

  it('Initial state correctness', () => {
    const state = useCanvasStudioStore.getState();
    assert.strictEqual(state.currentTool, 'select');
    assert.strictEqual(state.zoom, 1.0);
    assert.strictEqual(state.selectedNodeIds.length, 0);
    assert.strictEqual(state.canvasState.layers.length, 1);
  });

  it('Tool selection and navigation', () => {
    const store = useCanvasStudioStore.getState();
    store.setTool('rectangle');
    assert.strictEqual(useCanvasStudioStore.getState().currentTool, 'rectangle');

    store.setZoom(2.5);
    assert.strictEqual(useCanvasStudioStore.getState().zoom, 2.5);

    store.setPan({ x: 100, y: 200 });
    assert.deepStrictEqual(useCanvasStudioStore.getState().pan, { x: 100, y: 200 });
  });

  it('Add, update, and delete canvas layers/nodes via history', async () => {
    const store = useCanvasStudioStore.getState();

    await store.addNode({
      id: 'node-rect-1',
      type: 'rectangle',
      name: 'Blue Rectangle',
      x: 10,
      y: 20,
      width: 100,
      height: 100,
      rotation: 0,
      opacity: 1,
      visible: true,
      locked: false,
      zIndex: 0,
      fill: '#00f',
    });

    let state = useCanvasStudioStore.getState().canvasState;
    assert.strictEqual(state.layers[0].nodes.length, 1);
    assert.strictEqual(state.layers[0].nodes[0].name, 'Blue Rectangle');

    await store.updateNode('node-rect-1', { fill: '#ff0' });
    state = useCanvasStudioStore.getState().canvasState;
    assert.strictEqual(state.layers[0].nodes[0].fill, '#ff0');

    await store.deleteNode('node-rect-1');
    state = useCanvasStudioStore.getState().canvasState;
    assert.strictEqual(state.layers[0].nodes.length, 0);
  });

  it('AI Cutout Adapter triggers and records status in store', async () => {
    const store = useCanvasStudioStore.getState();

    await store.addNode({
      id: 'node-img-1',
      type: 'image',
      name: 'Product Sample',
      x: 50,
      y: 50,
      width: 200,
      height: 200,
      rotation: 0,
      opacity: 1,
      visible: true,
      locked: false,
      zIndex: 0,
      props: { src: 'data:image/png;base64,sample' },
    });

    const result = await store.runAICutout('node-img-1', { returnMask: false });
    assert.strictEqual(result.success, true);
    assert.strictEqual(result.nodeId, 'node-img-1');
    assert.strictEqual(useCanvasStudioStore.getState().aiState.isProcessing, false);
  });

  it('AI Generate and Relight state flow in store', async () => {
    const store = useCanvasStudioStore.getState();

    const genResult = await store.runAIGenerate('Futuristic sneaker showcase', {
      style: 'photorealistic',
      width: 1024,
      height: 1024,
    });

    assert.strictEqual(genResult.success, true);
    assert.ok(genResult.node && genResult.node.id);
    assert.strictEqual(genResult.node.props?.style, 'photorealistic');

    const relightResult = await store.runAIRelight(genResult.node.id, {
      foregroundNodeId: genResult.node.id,
      lightingPrompt: 'Golden hour sunlight',
      lightDirection: 'left',
    });

    assert.strictEqual(relightResult.success, true);
    assert.strictEqual(useCanvasStudioStore.getState().aiState.isProcessing, false);
  });

  it('AIPromptModal Style & Dimension Presets specifications', () => {
    assert.strictEqual(STYLE_PRESETS.length, 5);
    const photorealistic = STYLE_PRESETS.find((s) => s.id === 'photorealistic');
    assert.ok(photorealistic);
    assert.strictEqual(photorealistic.icon, '📷');

    const cyberpunk = STYLE_PRESETS.find((s) => s.id === 'cyberpunk');
    assert.ok(cyberpunk);
    assert.strictEqual(cyberpunk.icon, '🌆');

    assert.strictEqual(DIMENSION_OPTIONS.length, 5);
    const square = DIMENSION_OPTIONS.find((d) => d.label.includes('HD Square'));
    assert.ok(square);
    assert.strictEqual(square.width, 1024);
    assert.strictEqual(square.height, 1024);
  });
});

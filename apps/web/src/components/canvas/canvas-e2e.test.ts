// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/components/canvas/canvas-e2e.test.ts"
// purpose: "End-to-End Workflow Test for Canvas Studio: Upload ➡️ Cutout (BiRefNet) ➡️ Generate (FLUX.1) ➡️ Relight (IC-Light) ➡️ Undo/Redo."
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
import { CanvasAIClient } from '../../canvas/ai/ai-client';
import type { NodeProperties } from '../../canvas/storage/types/canvas';

// Mock IndexedDB for testing in Node environment
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

describe('Canvas Studio E2E Live AI Workflow', () => {
  beforeEach(() => {
    const aiClient = new CanvasAIClient({
      baseUrl: 'http://localhost:8000',
      workspaceId: 'ws-e2e-test',
      enableMockFallback: true,
    });
    useCanvasStudioStore.getState().setAIClient(aiClient);
    useCanvasStudioStore.getState().resetAIState();
  });

  it('executes full E2E workflow: Upload ➡️ Cutout ➡️ Generate ➡️ Relight ➡️ Undo/Redo', async () => {
    const initialStore = useCanvasStudioStore.getState();

    // =========================================================================
    // STEP 1: Upload Product Image Node
    // =========================================================================
    const productNodeId = 'product-sneaker-001';
    const productNode: NodeProperties = {
      id: productNodeId,
      type: 'image',
      name: 'Product Sneaker Studio Shot',
      x: 200,
      y: 150,
      width: 400,
      height: 400,
      rotation: 0,
      opacity: 1.0,
      visible: true,
      locked: false,
      zIndex: 1,
      props: {
        src: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkWPjfDwAEfQHzx5t0RAAAAABJRU5ErkJggg==',
        originalFileName: 'sneaker.png',
      },
    };

    await initialStore.addNode(productNode);
    initialStore.setSelectedNodeIds([productNodeId]);

    let state = useCanvasStudioStore.getState().canvasState;
    const uploadedNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === productNodeId);
    assert.ok(uploadedNode, 'Product node should be present in canvas layers');
    assert.strictEqual(uploadedNode.name, 'Product Sneaker Studio Shot');

    // =========================================================================
    // STEP 2: 1-Click Cutout (BiRefNet Background Removal)
    // =========================================================================
    const cutoutResult = await useCanvasStudioStore.getState().runAICutout(productNodeId, {
      returnMask: true,
      threshold: 0.5,
      replaceOriginal: true,
    });

    assert.strictEqual(cutoutResult.success, true, 'AI Cutout should succeed');
    assert.ok(cutoutResult.imageSrc, 'Cutout result should have transparent imageSrc');
    assert.strictEqual(cutoutResult.nodeId, productNodeId);

    state = useCanvasStudioStore.getState().canvasState;
    const cutoutNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === cutoutResult.nodeId);
    assert.ok(cutoutNode, 'Cutout node should exist in canvas');
    assert.ok(cutoutNode?.props?.aiCutout || cutoutNode?.props?.cutoutProcessed, 'Node properties should flag aiCutout');

    // =========================================================================
    // STEP 3: Generate Background Layer (FLUX.1 + LayerDiffuse)
    // =========================================================================
    const prompt = 'Cyberpunk neon rain street background with reflective puddles';
    const genResult = await useCanvasStudioStore.getState().runAIGenerate(prompt, {
      style: 'cyberpunk',
      width: 1024,
      height: 1024,
      transparentBackground: false,
      targetLayerId: 'layer-bg-root',
    });

    assert.strictEqual(genResult.success, true, 'AI Layer generation should succeed');
    assert.ok(genResult.node && genResult.node.id, 'Generated layer node should have a valid ID');

    state = useCanvasStudioStore.getState().canvasState;
    const generatedNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === genResult.node.id);
    assert.ok(generatedNode, 'Generated background node should exist in canvas state');
    assert.strictEqual(generatedNode.props?.style, 'cyberpunk');

    // =========================================================================
    // STEP 4: AI Relighting (IC-Light Illumination Harmonization)
    // =========================================================================
    useCanvasStudioStore.getState().setSelectedNodeIds([productNodeId]);

    const relightResult = await useCanvasStudioStore.getState().runAIRelight(genResult.node.id, {
      foregroundNodeId: productNodeId,
      lightingPrompt: 'Neon blue and purple rim light from background',
      lightDirection: 'right',
      intensity: 1.2,
      replaceOriginal: true,
    });

    assert.strictEqual(relightResult.success, true, 'AI Relighting should succeed');
    assert.strictEqual(relightResult.nodeId, productNodeId);

    state = useCanvasStudioStore.getState().canvasState;
    const relitNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === productNodeId);
    assert.ok(relitNode, 'Relit node should be present in canvas state');

    // =========================================================================
    // STEP 5: History Undo / Redo Workflow
    // =========================================================================
    assert.strictEqual(useCanvasStudioStore.getState().canUndo(), true, 'Store should allow undoing actions');

    // Undo Relight
    await useCanvasStudioStore.getState().undo();
    state = useCanvasStudioStore.getState().canvasState;
    const postUndoRelitNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === productNodeId);
    assert.ok(postUndoRelitNode, 'Product node should still exist after undo');

    // Undo Generate Layer
    await useCanvasStudioStore.getState().undo();
    state = useCanvasStudioStore.getState().canvasState;
    const postUndoGenNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === genResult.node.id);
    assert.strictEqual(postUndoGenNode, undefined, 'Generated node should be removed after undoing generation');

    // Redo Generate Layer
    assert.strictEqual(useCanvasStudioStore.getState().canRedo(), true, 'Store should allow redo');
    await useCanvasStudioStore.getState().redo();
    state = useCanvasStudioStore.getState().canvasState;
    const postRedoGenNode = state.layers.flatMap((l) => l.nodes).find((n) => n.id === genResult.node.id);
    assert.ok(postRedoGenNode, 'Generated node should be restored after redo');

    // =========================================================================
    // STEP 6: Draft Storage Persistence
    // =========================================================================
    await useCanvasStudioStore.getState().saveDraft();
    assert.strictEqual(useCanvasStudioStore.getState().isDirty, false, 'Canvas should be clean after saving');
  });

  it('gracefully handles and surfaces AI action failures through aiState', async () => {
    const brokenClient = new CanvasAIClient({
      baseUrl: 'http://invalid-nonexistent-ai-host:9999',
      timeoutMs: 50,
      enableMockFallback: false,
    });

    useCanvasStudioStore.getState().setAIClient(brokenClient);

    const store = useCanvasStudioStore.getState();
    await store.addNode({
      id: 'node-fail-test',
      type: 'image',
      name: 'Test Image',
      x: 0,
      y: 0,
      width: 100,
      height: 100,
      rotation: 0,
      opacity: 1.0,
      visible: true,
      locked: false,
      zIndex: 1,
      props: { src: 'data:image/png;base64,broken' },
    });

    const result = await useCanvasStudioStore.getState().runAICutout('node-fail-test');
    assert.strictEqual(result.success, false);

    const aiState = useCanvasStudioStore.getState().aiState;
    assert.strictEqual(aiState.isProcessing, false);
    assert.ok(aiState.error, 'aiState must record the error message');
  });
});

/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/ai/ai-actions.test.ts"
 * purpose: "Comprehensive unit tests for Canvas Engine AI Actions, AI Client, and Command Stack Undo/Redo integration."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym & Gerych"
 * license: "DNK-INTERNAL"
 * --- END DNK-MRH-HEADER ---
 */

import { test, describe, afterEach } from 'node:test';
import assert from 'node:assert';
import { UndoRedoStack } from '../history/undo-redo-stack';
import { AIClient } from './ai-client';
import { AIActions } from './ai-actions';
import type { AIActionContext } from './types';
import type { CanvasState, NodeProperties } from '../storage/types/canvas';

function createMockCanvasState(nodes: NodeProperties[] = []): CanvasState {
  return {
    id: 'canvas-test-100',
    name: 'AI Test Canvas',
    version: 1,
    viewport: { x: 0, y: 0, zoom: 1 },
    dimensions: { width: 1920, height: 1080 },
    layers: [
      {
        id: 'layer-default',
        name: 'Layer 1',
        visible: true,
        locked: false,
        opacity: 1,
        zIndex: 0,
        nodes: [...nodes],
      },
    ],
    activeLayerId: 'layer-default',
    selectedNodeIds: [],
    metadata: {},
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

describe('Canvas Engine AI Action Adapters & AIClient', () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  test('AIClient: sends correctly formatted request with auth headers for cutout', async () => {
    let capturedUrl = '';
    let capturedHeaders: Record<string, string> = {};
    let capturedBody: any = null;

    globalThis.fetch = (async (url: string, init?: RequestInit) => {
      capturedUrl = url;
      capturedHeaders = (init?.headers || {}) as Record<string, string>;
      capturedBody = JSON.parse((init?.body as string) || '{}');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          image_base64: 'data:image/png;base64,CUTOUT_MOCK_DATA',
          mask_base64: 'data:image/png;base64,MASK_MOCK_DATA',
          node_id: 'node-img-1',
          mime_type: 'image/png',
          execution_time_ms: 120.5,
          model: 'BiRefNet-v1',
          metadata: {},
        }),
      } as Response;
    }) as any;

    const client = new AIClient({
      baseUrl: 'http://127.0.0.1:8000',
      workspaceId: 'ws-alpha-001',
      authToken: 'jwt-token-12345',
    });

    const res = await client.cutout({
      imageBase64: 'data:image/png;base64,ORIGINAL_RAW_PNG',
      nodeId: 'node-img-1',
      canvasId: 'canvas-100',
      returnMask: true,
      threshold: 0.7,
    });

    assert.strictEqual(capturedUrl, 'http://127.0.0.1:8000/api/v1/canvas/ai/cutout');
    assert.strictEqual(capturedHeaders['X-Workspace-Id'], 'ws-alpha-001');
    assert.strictEqual(capturedHeaders['Authorization'], 'Bearer jwt-token-12345');
    assert.strictEqual(capturedBody.image_base64, 'data:image/png;base64,ORIGINAL_RAW_PNG');
    assert.strictEqual(capturedBody.return_mask, true);
    assert.strictEqual(capturedBody.threshold, 0.7);
    assert.strictEqual(res.success, true);
    assert.strictEqual(res.model, 'BiRefNet-v1');
  });

  test('AIClient: handles relight request correctly', async () => {
    let capturedBody: any = null;

    globalThis.fetch = (async (url: string, init?: RequestInit) => {
      capturedBody = JSON.parse((init?.body as string) || '{}');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          image_base64: 'RELIT_BASE64_RESULT',
          node_id: 'fg-node-1',
          mime_type: 'image/png',
          execution_time_ms: 350.0,
          model: 'IC-Light-v1',
          metadata: {},
        }),
      } as Response;
    }) as any;

    const client = new AIClient({ baseUrl: 'http://127.0.0.1:8000', enableMockFallback: false });
    const res = await client.relight({
      foregroundImageBase64: 'FG_DATA',
      backgroundImageBase64: 'BG_DATA',
      foregroundNodeId: 'fg-node-1',
      lightingPrompt: 'warm sunset glow from left',
      lightDirection: 'left',
      intensity: 1.5,
    });

    assert.strictEqual(capturedBody.foreground_image_base64, 'FG_DATA');
    assert.strictEqual(capturedBody.background_image_base64, 'BG_DATA');
    assert.strictEqual(capturedBody.light_direction, 'left');
    assert.strictEqual(capturedBody.intensity, 1.5);
    assert.strictEqual(res.success, true);
    assert.strictEqual(res.image_base64, 'RELIT_BASE64_RESULT');
  });

  test('AIClient: handles generateLayer request correctly', async () => {
    let capturedBody: any = null;

    globalThis.fetch = (async (url: string, init?: RequestInit) => {
      capturedBody = JSON.parse((init?.body as string) || '{}');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          image_base64: 'GENERATED_LAYER_BASE64',
          layer_data: { style: 'photorealistic' },
          mime_type: 'image/png',
          execution_time_ms: 800.0,
          model: 'FLUX.1-LayerDiffuse',
          metadata: {},
        }),
      } as Response;
    }) as any;

    const client = new AIClient({ baseUrl: 'http://127.0.0.1:8000', enableMockFallback: false });
    const res = await client.generateLayer({
      prompt: 'A transparent isolated glass bottle of perfume',
      style: 'cinematic',
      width: 512,
      height: 512,
      transparentBackground: true,
    });

    assert.strictEqual(capturedBody.prompt, 'A transparent isolated glass bottle of perfume');
    assert.strictEqual(capturedBody.style, 'cinematic');
    assert.strictEqual(capturedBody.width, 512);
    assert.strictEqual(capturedBody.transparent_background, true);
    assert.strictEqual(res.success, true);
    assert.strictEqual(res.model, 'FLUX.1-LayerDiffuse');
  });

  test('AIClient: throws structured error on HTTP failure status', async () => {
    globalThis.fetch = (async () => ({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      text: async () => JSON.stringify({ detail: 'Missing required image payload' }),
    })) as any;

    const client = new AIClient({ baseUrl: 'http://127.0.0.1:8000', enableMockFallback: false });
    await assert.rejects(
      async () => {
        await client.cutout({ nodeId: 'node-empty' });
      },
      (err: Error) => {
        assert.ok(err.message.includes('422'));
        assert.ok(err.message.includes('Unprocessable Entity'));
        return true;
      }
    );
  });

  test('AIActions.cutoutBackground: in-place replacement with Undo/Redo integration', async () => {
    const originalImageNode: NodeProperties = {
      id: 'node-img-1',
      type: 'image',
      name: 'Product Photo',
      x: 100,
      y: 100,
      width: 400,
      height: 400,
      fill: 'data:image/png;base64,RAW_IMG_DATA',
      props: {
        src: 'data:image/png;base64,RAW_IMG_DATA',
      },
    };

    const stack = new UndoRedoStack();
    const initialState = createMockCanvasState([originalImageNode]);
    stack.setState(initialState);

    globalThis.fetch = (async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        image_base64: 'data:image/png;base64,CUTOUT_PNG_PROCESSED',
        mask_base64: 'data:image/png;base64,CUTOUT_MASK',
        node_id: 'node-img-1',
        mime_type: 'image/png',
        execution_time_ms: 145.2,
      }),
    })) as any;

    const statusEvents: any[] = [];
    const context: AIActionContext = {
      state: stack.getState(),
      commandStack: stack,
      selectedNodeId: 'node-img-1',
      onStatusChange: (status) => statusEvents.push(status),
    };

    const result = await AIActions.cutoutBackground(context, {
      replaceOriginal: true,
      returnMask: true,
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.nodeId, 'node-img-1');
    assert.strictEqual(result.imageSrc, 'data:image/png;base64,CUTOUT_PNG_PROCESSED');
    assert.strictEqual(result.maskSrc, 'data:image/png;base64,CUTOUT_MASK');

    // Verify state was updated through command stack
    const updatedState = stack.getState();
    const updatedNode = updatedState.layers[0].nodes[0];
    assert.strictEqual((updatedNode.props as any)?.src, 'data:image/png;base64,CUTOUT_PNG_PROCESSED');
    assert.strictEqual((updatedNode.props as any)?.cutoutProcessed, true);

    // Verify undo restores original state
    assert.strictEqual(stack.canUndo(), true);
    await stack.undo();
    const revertedState = stack.getState();
    const revertedNode = revertedState.layers[0].nodes[0];
    assert.strictEqual((revertedNode.props as any)?.src, 'data:image/png;base64,RAW_IMG_DATA');
    assert.strictEqual((revertedNode.props as any)?.cutoutProcessed, undefined);

    // Verify status notifications
    assert.strictEqual(statusEvents[0].loading, true);
    assert.strictEqual(statusEvents[0].action, 'cutout');
    assert.strictEqual(statusEvents[1].loading, false);
  });

  test('AIActions.cutoutBackground: non-destructive copy mode', async () => {
    const originalImageNode: NodeProperties = {
      id: 'node-img-original',
      type: 'image',
      name: 'Original Image',
      x: 50,
      y: 50,
      width: 200,
      height: 200,
      props: {
        src: 'data:image/png;base64,ORIGINAL_PNG',
      },
    };

    const stack = new UndoRedoStack();
    stack.setState(createMockCanvasState([originalImageNode]));

    globalThis.fetch = (async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        image_base64: 'CUTOUT_COPY_BASE64',
        mime_type: 'image/png',
        execution_time_ms: 90.0,
      }),
    })) as any;

    const context: AIActionContext = {
      state: stack.getState(),
      commandStack: stack,
      selectedNodeId: 'node-img-original',
    };

    const result = await AIActions.cutoutBackground(context, {
      replaceOriginal: false,
    });

    assert.strictEqual(result.success, true);
    assert.notStrictEqual(result.nodeId, 'node-img-original');
    assert.strictEqual(result.originalNodeId, 'node-img-original');

    const state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 2);
    assert.strictEqual(state.layers[0].nodes[0].id, 'node-img-original');
    assert.strictEqual(state.layers[0].nodes[1].id, result.nodeId);
    assert.strictEqual((state.layers[0].nodes[1].props as any)?.cutoutProcessed, true);
  });

  test('AIActions.relight: environmental relighting of foreground node', async () => {
    const fgNode: NodeProperties = {
      id: 'fg-bottle',
      type: 'image',
      name: 'Bottle Cutout',
      x: 100,
      y: 100,
      width: 200,
      height: 400,
      props: {
        src: 'data:image/png;base64,FG_BOTTLE_DATA',
      },
    };

    const bgNode: NodeProperties = {
      id: 'bg-sunset',
      type: 'image',
      name: 'Sunset Background',
      x: 0,
      y: 0,
      width: 1920,
      height: 1080,
      props: {
        src: 'data:image/png;base64,BG_SUNSET_DATA',
      },
    };

    const stack = new UndoRedoStack();
    stack.setState(createMockCanvasState([bgNode, fgNode]));

    globalThis.fetch = (async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        image_base64: 'data:image/png;base64,RELIT_BOTTLE_SUNSET',
        node_id: 'fg-bottle',
        mime_type: 'image/png',
        execution_time_ms: 220.0,
      }),
    })) as any;

    const context: AIActionContext = {
      state: stack.getState(),
      commandStack: stack,
      selectedNodeId: 'fg-bottle',
    };

    const result = await AIActions.relight(context, 'bg-sunset', {
      lightDirection: 'right',
      intensity: 1.2,
      lightingPrompt: 'golden hour rim light',
      replaceOriginal: true,
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.nodeId, 'fg-bottle');
    assert.strictEqual(result.lightDirection, 'right');
    assert.strictEqual(result.intensity, 1.2);

    const state = stack.getState();
    const updatedFg = state.layers[0].nodes.find((n) => n.id === 'fg-bottle');
    assert.strictEqual((updatedFg?.props as any)?.src, 'data:image/png;base64,RELIT_BOTTLE_SUNSET');
    assert.strictEqual((updatedFg?.props as any)?.relighted, true);
  });

  test('AIActions.generateLayer: generates new layer node on canvas', async () => {
    const stack = new UndoRedoStack();
    stack.setState(createMockCanvasState([]));

    globalThis.fetch = (async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        image_base64: 'data:image/png;base64,GENERATED_NEON_SIGN',
        layer_data: { transparent: true, model: 'FLUX.1-LayerDiffuse' },
        mime_type: 'image/png',
        execution_time_ms: 540.0,
      }),
    })) as any;

    const context: AIActionContext = {
      state: stack.getState(),
      commandStack: stack,
    };

    const result = await AIActions.generateLayer(
      context,
      'Glowing neon cyan badge with 50% discount text',
      {
        style: 'neon-cyberpunk',
        width: 600,
        height: 600,
        transparentBackground: true,
      }
    );

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.node.width, 600);
    assert.strictEqual(result.node.height, 600);
    assert.strictEqual((result.node.props as any)?.aiGenerated, true);
    assert.strictEqual((result.node.props as any)?.style, 'neon-cyberpunk');

    const state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 1);
    assert.strictEqual(state.layers[0].nodes[0].id, result.node.id);

    // Verify undo removes generated layer
    await stack.undo();
    const stateAfterUndo = stack.getState();
    assert.strictEqual(stateAfterUndo.layers[0].nodes.length, 0);
  });

  test('AIActions: validation errors when node is missing or prompt is empty', async () => {
    const stack = new UndoRedoStack();
    stack.setState(createMockCanvasState([]));

    const context: AIActionContext = {
      state: stack.getState(),
      commandStack: stack,
    };

    // Missing node for cutout
    await assert.rejects(
      async () => {
        await AIActions.cutoutBackground(context, { nodeId: 'non-existent' });
      },
      (err: Error) => err.message.includes('not found')
    );

    // Empty prompt for generateLayer
    await assert.rejects(
      async () => {
        await AIActions.generateLayer(context, '   ');
      },
      (err: Error) => err.message.includes('Prompt cannot be empty')
    );
  });
});

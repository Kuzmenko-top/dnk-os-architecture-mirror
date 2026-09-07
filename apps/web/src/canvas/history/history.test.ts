/**
 * --- DNK-MRH-HEADER ---
 * mrh_id: "apps/web/src/canvas/history/history.test.ts"
 * purpose: "Unit tests for Command Pattern, Undo/Redo Engine, Ring Buffer invariant, and Storage Sync."
 * canonical_source: true
 * alters_files: []
 * triggers_tasks: []
 * status: "Active"
 * version: "1.0.0"
 * updated_at: "2026-09-02"
 * author: "DNK-e.com Maksym"
 * --- END DNK-MRH-HEADER ---
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { UndoRedoStack } from './undo-redo-stack';
import { AddNodeCommand } from './commands/add-node.command';
import { UpdateNodeCommand } from './commands/update-node.command';
import { DeleteNodeCommand } from './commands/delete-node.command';
import { MoveNodeCommand } from './commands/move-node.command';
import { BatchCommand } from './commands/batch.command';
import { ReorderLayerCommand } from './commands/reorder-layer.command';
import { CanvasStorageService } from '../storage/storage.service';
import type { NodeProperties } from '../storage/types/canvas';

describe('Canvas History & Command Pattern Engine', () => {
  const sampleNode: NodeProperties = {
    id: 'node-101',
    type: 'shape_rectangle',
    x: 100,
    y: 200,
    width: 300,
    height: 150,
    rotation: 0,
    scaleX: 1,
    scaleY: 1,
    fill: '#4F46E5',
    stroke: '#312E81',
    strokeWidth: 2,
    opacity: 1,
    visible: true,
    locked: false,
    zIndex: 0,
  };

  test('AddNodeCommand: execute, undo, and redo', async () => {
    const stack = new UndoRedoStack();
    const cmd = new AddNodeCommand(sampleNode);

    await stack.execute(cmd);
    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 1);
    assert.strictEqual(state.layers[0].nodes[0].id, 'node-101');
    assert.strictEqual(stack.canUndo(), true);
    assert.strictEqual(stack.canRedo(), false);

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 0);
    assert.strictEqual(stack.canUndo(), false);
    assert.strictEqual(stack.canRedo(), true);

    await stack.redo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 1);
    assert.strictEqual(state.layers[0].nodes[0].id, 'node-101');
  });

  test('UpdateNodeCommand: property updates and restoration', async () => {
    const stack = new UndoRedoStack();
    await stack.execute(new AddNodeCommand(sampleNode));

    const updateCmd = new UpdateNodeCommand('node-101', {
      fill: '#10B981',
      width: 500,
    });
    await stack.execute(updateCmd);

    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].fill, '#10B981');
    assert.strictEqual(state.layers[0].nodes[0].width, 500);

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].fill, '#4F46E5');
    assert.strictEqual(state.layers[0].nodes[0].width, 300);

    await stack.redo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].fill, '#10B981');
  });

  test('DeleteNodeCommand: node deletion and index restoration', async () => {
    const stack = new UndoRedoStack();
    await stack.execute(new AddNodeCommand(sampleNode));
    await stack.execute(new AddNodeCommand({ ...sampleNode, id: 'node-102', x: 200 }));

    const deleteCmd = new DeleteNodeCommand('node-101');
    await stack.execute(deleteCmd);

    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 1);
    assert.strictEqual(state.layers[0].nodes[0].id, 'node-102');

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 2);
    assert.strictEqual(state.layers[0].nodes[0].id, 'node-101');

    await stack.redo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 1);
  });

  test('MoveNodeCommand: coordinate transforms', async () => {
    const stack = new UndoRedoStack();
    await stack.execute(new AddNodeCommand(sampleNode));

    const moveCmd = new MoveNodeCommand('node-101', { x: 100, y: 200 }, { x: 450, y: 600 });
    await stack.execute(moveCmd);

    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].x, 450);
    assert.strictEqual(state.layers[0].nodes[0].y, 600);

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].x, 100);
    assert.strictEqual(state.layers[0].nodes[0].y, 200);
  });

  test('BatchCommand: macro execution and atomic reverse undo', async () => {
    const stack = new UndoRedoStack();
    const batch = new BatchCommand([
      new AddNodeCommand({ ...sampleNode, id: 'b1' }),
      new AddNodeCommand({ ...sampleNode, id: 'b2' }),
      new AddNodeCommand({ ...sampleNode, id: 'b3' }),
    ]);

    await stack.execute(batch);
    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 3);

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 0);

    await stack.redo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes.length, 3);
  });

  test('ReorderLayerCommand: node zIndex reordering', async () => {
    const stack = new UndoRedoStack();
    await stack.execute(new AddNodeCommand({ ...sampleNode, id: 'n1' }));
    await stack.execute(new AddNodeCommand({ ...sampleNode, id: 'n2' }));

    const reorderCmd = new ReorderLayerCommand('n1', 0, 1, false);
    await stack.execute(reorderCmd);

    let state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].id, 'n2');
    assert.strictEqual(state.layers[0].nodes[1].id, 'n1');

    await stack.undo();
    state = stack.getState();
    assert.strictEqual(state.layers[0].nodes[0].id, 'n1');
    assert.strictEqual(state.layers[0].nodes[1].id, 'n2');
  });

  test('UndoRedoStack: Ring Buffer invariant (max 100 commands)', async () => {
    const stack = new UndoRedoStack({ maxSize: 10 });

    for (let i = 0; i < 25; i++) {
      await stack.execute(new AddNodeCommand({ ...sampleNode, id: `node-${i}` }));
    }

    assert.strictEqual(stack.getUndoCount(), 10); // Ring buffer capped at 10

    // Executing new command clears redo stack
    await stack.undo();
    assert.strictEqual(stack.getRedoCount(), 1);
    await stack.execute(new AddNodeCommand({ ...sampleNode, id: 'fresh-node' }));
    assert.strictEqual(stack.getRedoCount(), 0);
  });

  test('UndoRedoStack: Storage Service integration and ring buffer transaction recording', async () => {
    const storageService = new CanvasStorageService({ useMemoryOnly: true });

    const stack = new UndoRedoStack({
      storageService,
      draftId: 'test-draft-1',
    });

    await stack.execute(new AddNodeCommand(sampleNode));
    await stack.execute(
      new UpdateNodeCommand('node-101', { fill: '#EC4899' })
    );

    const history = await storageService.getHistory('test-draft-1');
    assert.strictEqual(history.length, 2);
    assert.strictEqual(history[0].description.includes('Add node'), true);
    assert.strictEqual(history[1].description.includes('Update node'), true);

    const isDirty = await storageService.isDirty('test-draft-1');
    assert.strictEqual(isDirty, true);
  });
});

// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/store/canvasStore.test.ts"
// purpose: "Unit tests for useCanvasStore: mutations, Data-Flow propagation, history, and JSON Canvas import/export"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';
import { useCanvasStore } from './canvasStore';

describe('useCanvasStore', () => {
  beforeEach(() => {
    useCanvasStore.getState().resetToDefault();
  });

  it('adds and selects a new node', () => {
    const store = useCanvasStore.getState();
    const id = store.addNode('StrategyMarkdownNode', { x: 100, y: 200 }, { title: 'Strategy Card' });

    const state = useCanvasStore.getState();
    assert.strictEqual(state.nodes.length, 1);
    assert.strictEqual(state.nodes[0].id, id);
    assert.strictEqual(state.nodes[0].data.title, 'Strategy Card');
    assert.strictEqual(state.selectedNodeId, id);
  });

  it('updates node data correctly', () => {
    const store = useCanvasStore.getState();
    const id = store.addNode('DesignGalleryNode', { x: 50, y: 50 }, { primaryColor: '#ff0000' });
    
    store.updateNodeData(id, { primaryColor: '#00ff00', label: 'Brand Assets' });
    const updatedNode = useCanvasStore.getState().nodes.find((n) => n.id === id);

    assert.strictEqual(updatedNode?.data.primaryColor, '#00ff00');
    assert.strictEqual(updatedNode?.data.label, 'Brand Assets');
  });

  it('propagates Data-Flow from source to target connected nodes (Flowgram.ai pattern)', () => {
    const store = useCanvasStore.getState();
    const idSource = store.addNode('StrategyMarkdownNode', { x: 0, y: 0 }, { brandColor: '#10b981' });
    const idTarget = store.addNode('DesignGalleryNode', { x: 400, y: 0 });

    // Connect source -> target
    store.onConnect({
      source: idSource,
      target: idTarget,
      sourceHandle: 'right',
      targetHandle: 'left'
    });

    // Propagate output payload from source
    store.propagateDataFlow(idSource, { brandColor: '#10b981', brandVoice: 'Energetic' });

    const targetNode = useCanvasStore.getState().nodes.find((n) => n.id === idTarget);
    assert.ok(targetNode?.data.upstreamData);
    assert.deepStrictEqual((targetNode?.data.upstreamData as any)[idSource], {
      brandColor: '#10b981',
      brandVoice: 'Energetic'
    });
  });

  it('supports undo and redo', () => {
    const store = useCanvasStore.getState();
    store.addNode('StrategyMarkdownNode', { x: 0, y: 0 });
    assert.strictEqual(useCanvasStore.getState().nodes.length, 1);

    store.addNode('MarketResearchNode', { x: 200, y: 0 });
    assert.strictEqual(useCanvasStore.getState().nodes.length, 2);

    // Undo second add
    store.undo();
    assert.strictEqual(useCanvasStore.getState().nodes.length, 1);

    // Redo
    store.redo();
    assert.strictEqual(useCanvasStore.getState().nodes.length, 2);
  });

  it('exports and imports JSON Canvas documents', () => {
    const store = useCanvasStore.getState();
    const id1 = store.addNode('StrategyMarkdownNode', { x: 10, y: 20 }, { title: 'Strategy' });
    const id2 = store.addNode('SprintKanbanNode', { x: 300, y: 20 }, { title: 'Kanban' });

    store.onConnect({
      source: id1,
      target: id2,
      sourceHandle: 'right',
      targetHandle: 'left'
    });

    const doc = store.exportJSONCanvas();
    assert.strictEqual(doc.nodes.length, 2);
    assert.strictEqual(doc.edges.length, 1);

    // Reset and re-import
    store.resetToDefault();
    assert.strictEqual(useCanvasStore.getState().nodes.length, 0);

    store.importJSONCanvas(doc);
    assert.strictEqual(useCanvasStore.getState().nodes.length, 2);
    assert.strictEqual(useCanvasStore.getState().edges.length, 1);
  });
});

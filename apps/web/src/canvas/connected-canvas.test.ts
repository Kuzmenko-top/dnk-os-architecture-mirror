// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/connected-canvas.test.ts"
// purpose: "Integration test for Spatial Canvas Studio Phase 1: 6-Card lifecycle, Flowgram.ai Data-Flow, Undo/Redo and JSON Canvas roundtrip"
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
import { useCanvasStore } from '../../store/canvasStore';

describe('Spatial Canvas Studio Phase 1 Integration Gate', () => {
  beforeEach(() => {
    useCanvasStore.getState().resetToDefault();
  });

  it('verifies instantiation of all 6 CapCut/Linear core node types', () => {
    const store = useCanvasStore.getState();
    
    const types = [
      'StrategyMarkdownNode',
      'MarketResearchNode',
      'ConceptMindmapNode',
      'SprintKanbanNode',
      'DesignGalleryNode',
      'ApiDocsCodeNode',
    ];

    const ids = types.map((t, idx) => 
      store.addNode(t, { x: idx * 250, y: 100 }, { title: `Card ${idx + 1}` })
    );

    const currentNodes = useCanvasStore.getState().nodes;
    assert.strictEqual(currentNodes.length, 6);
    types.forEach((t) => {
      assert.ok(currentNodes.some((n) => n.type === t));
    });
  });

  it('executes Flowgram.ai multi-node reactive data pipeline', () => {
    const store = useCanvasStore.getState();

    // 1. Create Strategy node (Source)
    const strategyId = store.addNode('StrategyMarkdownNode', { x: 0, y: 0 }, { 
      brandName: 'ReBurn Energy',
      primaryHex: '#10b981'
    });

    // 2. Create Design node (Middle)
    const designId = store.addNode('DesignGalleryNode', { x: 350, y: 0 });

    // 3. Create Code node (Sink)
    const codeId = store.addNode('ApiDocsCodeNode', { x: 700, y: 0 });

    // Connect strategy -> design
    store.onConnect({
      source: strategyId,
      target: designId,
      sourceHandle: 'right',
      targetHandle: 'left'
    });

    // Connect design -> code
    store.onConnect({
      source: designId,
      target: codeId,
      sourceHandle: 'right',
      targetHandle: 'left'
    });

    // Propagate brand data from Strategy
    store.propagateDataFlow(strategyId, {
      brandName: 'ReBurn Energy',
      primaryHex: '#10b981'
    });

    let designNode = useCanvasStore.getState().nodes.find(n => n.id === designId);
    assert.deepStrictEqual((designNode?.data.upstreamData as any)[strategyId], {
      brandName: 'ReBurn Energy',
      primaryHex: '#10b981'
    });

    // Design generates assets and propagates to Code
    store.propagateDataFlow(designId, {
      cssVariables: '--brand-primary: #10b981;',
      themeTemplate: 'dawn-v15'
    });

    let codeNode = useCanvasStore.getState().nodes.find(n => n.id === codeId);
    assert.deepStrictEqual((codeNode?.data.upstreamData as any)[designId], {
      cssVariables: '--brand-primary: #10b981;',
      themeTemplate: 'dawn-v15'
    });
  });

  it('validates lossless roundtrip JSON Canvas (.canvas) export and import', () => {
    const store = useCanvasStore.getState();

    const n1 = store.addNode('StrategyMarkdownNode', { x: 50, y: 50 }, { title: 'Strategy Node' });
    const n2 = store.addNode('ApiDocsCodeNode', { x: 400, y: 50 }, { title: 'Code Node' });

    store.onConnect({
      source: n1,
      target: n2,
      sourceHandle: 'right',
      targetHandle: 'left'
    });

    // Export to JSON Canvas format
    const canvasDoc = store.exportJSONCanvas();

    // Verify JSON Canvas standard structure
    assert.ok(Array.isArray(canvasDoc.nodes));
    assert.ok(Array.isArray(canvasDoc.edges));
    assert.strictEqual(canvasDoc.nodes.length, 2);
    assert.strictEqual(canvasDoc.edges.length, 1);
    assert.strictEqual(canvasDoc.edges[0].fromNode, n1);
    assert.strictEqual(canvasDoc.edges[0].toNode, n2);

    // Reset workspace
    store.resetToDefault();
    assert.strictEqual(useCanvasStore.getState().nodes.length, 0);

    // Import from JSON Canvas document
    store.importJSONCanvas(canvasDoc);
    const restoredNodes = useCanvasStore.getState().nodes;
    const restoredEdges = useCanvasStore.getState().edges;

    assert.strictEqual(restoredNodes.length, 2);
    assert.strictEqual(restoredEdges.length, 1);
    assert.strictEqual(restoredNodes[0].id, n1);
    assert.strictEqual(restoredNodes[1].id, n2);
  });
});

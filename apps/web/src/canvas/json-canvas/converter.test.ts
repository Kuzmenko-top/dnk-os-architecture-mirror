// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/json-canvas/converter.test.ts"
// purpose: "Unit tests for bidirectional JSON Canvas v1.0 and @xyflow/react serialization"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { reactFlowToJSONCanvas, jsonCanvasToReactFlow } from './converter';
import type { Node, Edge } from '@xyflow/react';

describe('JSON Canvas v1.0 Converter', () => {
  it('converts React Flow nodes & edges to standard JSON Canvas', () => {
    const nodes: Node[] = [
      {
        id: 'node-strategy',
        type: 'StrategyMarkdownNode',
        position: { x: 100, y: 150 },
        width: 360,
        height: 240,
        data: {
          title: 'Brand Vision',
          content: '## Executive Summary\nLaunch coffee brand.'
        }
      },
      {
        id: 'node-shopify',
        type: 'ShopifyBuilderNode',
        position: { x: 500, y: 150 },
        width: 400,
        height: 300,
        data: {
          title: 'Shopify Store'
        }
      }
    ];

    const edges: Edge[] = [
      {
        id: 'edge-1',
        source: 'node-strategy',
        target: 'node-shopify',
        sourceHandle: 'right',
        targetHandle: 'left',
        data: {
          payloadType: 'brand.spec'
        }
      }
    ];

    const doc = reactFlowToJSONCanvas(nodes, edges);

    assert.strictEqual(doc.nodes.length, 2);
    assert.strictEqual(doc.edges.length, 1);
    assert.strictEqual(doc.nodes[0].id, 'node-strategy');
    assert.strictEqual(doc.nodes[0].x, 100);
    assert.strictEqual(doc.nodes[0].y, 150);
    assert.strictEqual(doc.edges[0].fromNode, 'node-strategy');
    assert.strictEqual(doc.edges[0].toNode, 'node-shopify');
    assert.strictEqual(doc.edges[0].fromSide, 'right');
    assert.strictEqual(doc.edges[0].toSide, 'left');
    assert.strictEqual(doc.edges[0].dataFlow?.payloadType, 'brand.spec');
  });

  it('restores React Flow nodes & edges from JSON Canvas document', () => {
    const jsonDoc = {
      nodes: [
        {
          id: 'card-1',
          type: 'text' as const,
          dnkType: 'MarketResearchNode',
          x: 200,
          y: 300,
          width: 380,
          height: 250,
          text: 'Market size $5B',
          data: { title: 'Market Trends' }
        }
      ],
      edges: [
        {
          id: 'e-1',
          fromNode: 'card-1',
          fromSide: 'bottom' as const,
          toNode: 'card-2',
          toSide: 'top' as const,
          dataFlow: { payloadType: 'market.insights' }
        }
      ]
    };

    const restored = jsonCanvasToReactFlow(jsonDoc);
    assert.strictEqual(restored.nodes.length, 1);
    assert.strictEqual(restored.nodes[0].id, 'card-1');
    assert.strictEqual(restored.nodes[0].type, 'MarketResearchNode');
    assert.strictEqual(restored.nodes[0].position.x, 200);
    assert.strictEqual(restored.nodes[0].position.y, 300);
    assert.strictEqual(restored.edges.length, 1);
    assert.strictEqual(restored.edges[0].source, 'card-1');
    assert.strictEqual(restored.edges[0].sourceHandle, 'bottom');
    assert.strictEqual(restored.edges[0].targetHandle, 'top');
  });
});

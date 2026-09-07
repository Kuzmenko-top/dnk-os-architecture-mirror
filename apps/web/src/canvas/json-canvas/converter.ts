// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/json-canvas/converter.ts"
// purpose: "Bidirectional serializer between @xyflow/react canvas state and standard JSON Canvas specification (.canvas)"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

import type { Node, Edge } from '@xyflow/react';
import type { 
  JSONCanvasDocument, 
  JSONCanvasNode, 
  JSONCanvasEdge, 
  CanvasSide, 
  DNKExtendedJSONCanvasNode 
} from './types';

function handleToSide(handle?: string | null): CanvasSide | undefined {
  if (!handle) return undefined;
  const lower = handle.toLowerCase();
  if (lower.includes('top') || lower === 't') return 'top';
  if (lower.includes('right') || lower === 'r') return 'right';
  if (lower.includes('bottom') || lower === 'b') return 'bottom';
  if (lower.includes('left') || lower === 'l') return 'left';
  return undefined;
}

function sideToHandle(side?: CanvasSide): string | undefined {
  return side;
}

/**
 * Converts @xyflow/react Nodes and Edges into a standard JSON Canvas v1.0 document.
 */
export function reactFlowToJSONCanvas(nodes: Node[], edges: Edge[]): JSONCanvasDocument {
  const jsonNodes: JSONCanvasNode[] = nodes.map((node) => {
    const width = Number(node.width) || Number(node.measured?.width) || 360;
    const height = Number(node.height) || Number(node.measured?.height) || 320;
    const dnkType = node.type || 'text';

    const base: DNKExtendedJSONCanvasNode = {
      id: node.id,
      x: Math.round(node.position.x),
      y: Math.round(node.position.y),
      width,
      height,
      type: 'text',
      dnkType,
      text: typeof node.data?.content === 'string' 
        ? node.data.content 
        : typeof node.data?.text === 'string'
          ? node.data.text
          : `# ${node.data?.title || node.id}\n${JSON.stringify(node.data || {}, null, 2)}`,
      data: node.data || {}
    };

    return base;
  });

  const jsonEdges: JSONCanvasEdge[] = edges.map((edge) => {
    return {
      id: edge.id,
      fromNode: edge.source,
      fromSide: handleToSide(edge.sourceHandle),
      fromEnd: 'none',
      toNode: edge.target,
      toSide: handleToSide(edge.targetHandle),
      toEnd: 'arrow',
      label: typeof edge.label === 'string' ? edge.label : undefined,
      color: edge.style?.stroke ? String(edge.style.stroke) : undefined,
      dataFlow: edge.data ? {
        payloadType: (edge.data as any)?.payloadType,
        variableMapping: (edge.data as any)?.variableMapping
      } : undefined
    };
  });

  return {
    nodes: jsonNodes,
    edges: jsonEdges
  };
}

/**
 * Parses a JSON Canvas v1.0 document back into @xyflow/react Nodes and Edges.
 */
export function jsonCanvasToReactFlow(doc: JSONCanvasDocument): { nodes: Node[]; edges: Edge[] } {
  if (!doc || !Array.isArray(doc.nodes)) {
    return { nodes: [], edges: [] };
  }

  const nodes: Node[] = doc.nodes.map((jNode) => {
    const extended = jNode as DNKExtendedJSONCanvasNode;
    const dnkType = extended.dnkType || (jNode.type === 'text' ? 'StrategyMarkdownNode' : 'StrategyMarkdownNode');

    return {
      id: jNode.id,
      type: dnkType,
      position: { x: jNode.x, y: jNode.y },
      width: jNode.width,
      height: jNode.height,
      data: {
        ...(extended.data || {}),
        title: extended.label || extended.data?.title || jNode.id,
        content: extended.text || extended.data?.content || '',
      }
    };
  });

  const edges: Edge[] = (doc.edges || []).map((jEdge) => {
    return {
      id: jEdge.id,
      source: jEdge.fromNode,
      target: jEdge.toNode,
      sourceHandle: sideToHandle(jEdge.fromSide),
      targetHandle: sideToHandle(jEdge.toSide),
      type: jEdge.dataFlow ? 'dataFlow' : 'default',
      animated: Boolean(jEdge.dataFlow),
      label: jEdge.label,
      style: jEdge.color ? { stroke: jEdge.color, strokeWidth: 2 } : undefined,
      data: jEdge.dataFlow
    };
  });

  return { nodes, edges };
}

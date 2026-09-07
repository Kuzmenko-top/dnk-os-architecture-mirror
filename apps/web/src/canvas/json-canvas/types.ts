// --- DNK-MRH-HEADER ---
// mrh_id: "apps/web/src/canvas/json-canvas/types.ts"
// purpose: "JSON Canvas v1.0 SSOT Specification Types and DNK OS Spatial Extensions"
// canonical_source: true
// alters_files: []
// triggers_tasks: []
// status: "Active"
// version: "1.0.0"
// updated_at: "2026-09-02"
// author: "DNK-e.com Maksym & Gerych"
// --- END DNK-MRH-HEADER ---

export type CanvasSide = 'top' | 'right' | 'bottom' | 'left';
export type CanvasEnd = 'none' | 'arrow';

/**
 * Standard JSON Canvas Node Types per jsoncanvas.org spec 1.0
 */
export type JSONCanvasGenericNodeType = 'text' | 'file' | 'link' | 'group';

export interface JSONCanvasBaseNode {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
}

export interface JSONCanvasTextNode extends JSONCanvasBaseNode {
  type: 'text';
  text: string;
}

export interface JSONCanvasFileNode extends JSONCanvasBaseNode {
  type: 'file';
  file: string;
  subpath?: string;
}

export interface JSONCanvasLinkNode extends JSONCanvasBaseNode {
  type: 'link';
  url: string;
}

export interface JSONCanvasGroupNode extends JSONCanvasBaseNode {
  type: 'group';
  label?: string;
  background?: string;
  backgroundStyle?: 'cover' | 'ratio' | 'repeat';
}

/**
 * Extended DNK Spatial Node (100% backward-compatible with JSON Canvas spec)
 */
export type DNKCardType = 
  | 'strategyMarkdown' 
  | 'marketResearch' 
  | 'conceptMindmap' 
  | 'designGallery' 
  | 'sprintKanban' 
  | 'apiDocsCode'
  | 'swarmAgent'
  | 'shopifyBuilder'
  | 'videoStoryboard';

export interface DNKExtendedJSONCanvasNode extends JSONCanvasBaseNode {
  type: JSONCanvasGenericNodeType;
  text?: string;
  file?: string;
  subpath?: string;
  url?: string;
  label?: string;
  // DNK OS Metadata
  dnkType?: DNKCardType | string;
  data?: Record<string, any>;
}

export type JSONCanvasNode = 
  | JSONCanvasTextNode 
  | JSONCanvasFileNode 
  | JSONCanvasLinkNode 
  | JSONCanvasGroupNode 
  | DNKExtendedJSONCanvasNode;

export interface JSONCanvasEdge {
  id: string;
  fromNode: string;
  fromSide?: CanvasSide;
  fromEnd?: CanvasEnd;
  toNode: string;
  toSide?: CanvasSide;
  toEnd?: CanvasEnd;
  color?: string;
  label?: string;
  // DNK Data-Flow metadata
  dataFlow?: {
    payloadType?: string;
    variableMapping?: Record<string, string>;
  };
}

export interface JSONCanvasDocument {
  nodes: JSONCanvasNode[];
  edges: JSONCanvasEdge[];
}

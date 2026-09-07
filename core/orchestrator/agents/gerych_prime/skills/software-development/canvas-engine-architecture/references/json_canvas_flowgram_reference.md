# JSON Canvas v1.0 & Flowgram.ai Data-Flow Reference

## 1. JSON Canvas v1.0 Standard Data Structures

Reference: [jsoncanvas.org/spec/1.0/](https://jsoncanvas.org/spec/1.0/)

### Root Schema
```json
{
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

### Generic Node Schema
```typescript
interface GenericNode {
  id: string;             // Unique identifier
  x: number;              // Horizontal coordinate in pixels
  y: number;              // Vertical coordinate in pixels
  width: number;          // Node width
  height: number;         // Node height
  color?: string;         // Preset color ("1"-"6") or hex ("#RRGGBB")
}
```

### Node Types
- **Text Node (`type: "text"`):**
  ```typescript
  interface TextNode extends GenericNode {
    type: 'text';
    text: string;         // Markdown content
  }
  ```
- **File Node (`type: "file"`):**
  ```typescript
  interface FileNode extends GenericNode {
    type: 'file';
    file: string;         // Relative path to file
    subpath?: string;     // Anchor or heading
  }
  ```
- **Link Node (`type: "link"`):**
  ```typescript
  interface LinkNode extends GenericNode {
    type: 'link';
    url: string;          // Target URL
  }
  ```
- **Group Node (`type: "group"`):**
  ```typescript
  interface GroupNode extends GenericNode {
    type: 'group';
    label?: string;
    background?: string;
    backgroundStyle?: 'cover' | 'ratio' | 'repeat';
  }
  ```

### Edge Schema
```typescript
interface CanvasEdge {
  id: string;
  fromNode: string;
  fromSide?: 'top' | 'right' | 'bottom' | 'left';
  fromEnd?: 'none' | 'arrow';
  toNode: string;
  toSide?: 'top' | 'right' | 'bottom' | 'left';
  toEnd?: 'none' | 'arrow';
  color?: string;
  label?: string;
}
```

---

## 2. Bidirectional Mapping with @xyflow/react

| React Flow Element | JSON Canvas Element | Notes |
|---|---|---|
| `Node.id` | `JSONCanvasNode.id` | Exact 1:1 match |
| `Node.position.x / y` | `JSONCanvasNode.x / y` | Direct integer coordinates |
| `Node.type` | `JSONCanvasNode.type` | Defaults to `"text"`; stored in `data.dnkType` |
| `Node.data` | `JSONCanvasNode.text` | Embedded as YAML frontmatter or extended attribute |
| `Edge.source / target` | `CanvasEdge.fromNode / toNode` | Source/target node IDs |
| `Edge.sourceHandle` | `CanvasEdge.fromSide` | Normalized to `'left'|'right'|'top'|'bottom'` |

---

## 3. Flowgram.ai Reactive Data-Flow Engine

When data changes in a node, propagate updates along directed edges:
```typescript
propagateDataFlow: (sourceId, payload) => {
  const { edges, nodes } = get();
  const outgoing = edges.filter((e) => e.source === sourceId);
  const targetIds = outgoing.map((e) => e.target);

  set({
    nodes: nodes.map((node) => {
      if (targetIds.includes(node.id)) {
        return {
          ...node,
          data: {
            ...node.data,
            upstreamData: {
              ...(node.data.upstreamData || {}),
              [sourceId]: payload,
            },
          },
        };
      }
      return node;
    }),
  });
}
```

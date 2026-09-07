# Custom React Flow Edges & Interaction Patterns (@xyflow/react v12)

## Key Implementation Patterns

### 1. BaseEdge markerEnd Typing Invariant
In `@xyflow/react` v12, `BaseEdge` expects `markerEnd?: string`.
- Valid: `markerEnd={markerEnd || MarkerType.ArrowClosed}` (MarkerType exports string identifiers like `'arrow'` or `'arrowclosed'`).
- Invalid: Passing `{ type: MarkerType.ArrowClosed, color: '...' }` directly to `BaseEdge.markerEnd` triggers TypeScript error TS2322. Custom marker styling should be configured in SVG `<defs>` or default marker attributes.

### 2. EdgeLabelRenderer Centering & Canvas Interaction
When rendering custom badges, pills, or interactive buttons along an edge:
- Wrap HTML elements inside `<EdgeLabelRenderer>`.
- Use transform positioning:
  ```tsx
  <div
    style={{
      position: 'absolute',
      transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
      pointerEvents: 'all',
    }}
    className="nodrag nopan"
  >
    {/* Badge Content */}
  </div>
  ```
- **Crucial**: Always add `className="nodrag nopan"` to prevent canvas drag/pan events from conflicting with edge labels.

### 3. Edge Type Registration Dual-Key Hygiene
When registering `edgeTypes` for `<ReactFlow edgeTypes={edgeTypes}>`, provide both lowercase and PascalCase keys:
```tsx
const edgeTypes = {
  dependency: DependencyEdge,
  DependencyEdge,
  relation: RelationEdge,
  RelationEdge,
  milestone: MilestoneEdge,
  MilestoneEdge,
};
```
This protects against schema drift between backend persistence (which may save raw PascalCase component names) and frontend graph builders.

### 4. Edge Taxonomy Matrix
- **DependencyEdge**: `getSmoothStepPath`, `#ef4444`, `markerEnd: MarkerType.ArrowClosed`, conditional `strokeDasharray: '5 5'` when blocked (`data.isBlocked || data.status === 'blocked'`).
- **RelationEdge**: `getBezierPath`, cyan `#06b6d4`, 2px solid stroke, semantic relationship badges.
- **MilestoneEdge**: `getBezierPath`, purple `#a855f7`, centered pulsating milestone pill via `EdgeLabelRenderer`.

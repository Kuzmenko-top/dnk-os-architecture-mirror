# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/canvas-engine-architecture/references/unified_workspace_ssot_integration.md"
# purpose: "Unified Workspace SSOT Integration Protocol: Zustand store, 13+ living node types, hotkeys, and JSON Canvas export/import."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# Unified Workspace SSOT Integration Guide (Canvas Engine)

## 1. Context & Problem Pattern
When migrating from multi-page or local state canvas components (`useState`, `useNodesState`) to an integrated Studio Workspace:
- Local state breaks cross-page workflows (Launchpad / Onboarding -> Studio Canvas).
- History (Undo/Redo) becomes fragmented and fails to sync with UI topbars.
- Missing node registrations in `nodeTypes` lead to silent fallback or React Flow crash when spawning domain-specific nodes.

## 2. SSOT Integration Pattern (`useCanvasStore.ts`)
Always bind the workspace container (`DNKStudioWorkspace.tsx`) directly to `useCanvasStore`:
```typescript
const {
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  setNodes,
  setEdges,
  addNode,
  removeNode,
  updateNodeData,
  selectedNodeId,
  selectNode,
  undo,
  redo,
  history,
  historyIndex,
  exportJSONCanvas,
  importJSONCanvas,
} = useCanvasStore();
```

### History State Invariant
Do NOT inspect a non-existent `canUndo` boolean directly on `CanvasState`. Calculate availability reactively from history indices:
```typescript
const canUndo = historyIndex > 0;
const canRedo = historyIndex < history.length - 1;
```

## 3. Hotkey Binding
Register global hotkeys cleanly inside a `useEffect` hook with key-code normalisation:
```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Ignore input/textarea typing
    const target = e.target as HTMLElement;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
      return;
    }

    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') {
      if (e.shiftKey) {
        e.preventDefault();
        if (canRedo) redo();
      } else {
        e.preventDefault();
        if (canUndo) undo();
      }
    } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'y') {
      e.preventDefault();
      if (canRedo) redo();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [canUndo, canRedo, undo, redo]);
```

## 4. Complete Node Registry Map (13+ Domain Node Types)
Register all node components inside `CanvasEngine.tsx` `nodeTypes` map:
1. **Living Notes**: `StrategyMarkdownNode`, `MarketResearchNode`, `ConceptMindmapNode`, `SprintKanbanNode`, `DesignGalleryNode`, `ApiDocsCodeNode`.
2. **Spec & Multimedia**: `ShopifyBuilderNode`, `ShopifySpecNoteNode`, `VideoCreatorNode`, `VideoStoryboardNoteNode`, `PhotoStudioNode`.
3. **Swarm & TaskDNA**: `TaskDNANoteNode`, `SwarmAgentNode`, `NoteDocumentNode`, `SmartNoteNode`, `GoalNode`, `TaskNode`, `AgentNode`, `ApprovalNode`, `ArtifactNode`.
4. **Live Preview & Slices**: `LiveWebPreviewNode`, `ComponentSliceNode`.

## 5. JSON Canvas Export / Import
Standard Obsidian JSON Canvas (v1.0) format compliance:
```typescript
const handleExportCanvas = () => {
  const jsonString = exportJSONCanvas();
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `dnk-canvas-${new Date().toISOString().slice(0, 10)}.canvas`;
  a.click();
  URL.revokeObjectURL(url);
};
```

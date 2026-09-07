# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-001_editors.md"
# purpose: "Component Inventory & Minimal Typed Interfaces for Artifact Editing"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🧬 COMPONENT SPEC: TYPED ARTIFACT EDITORS (DNK-COMP-001)

## 📌 Minimal TypeScript Interfaces

```typescript
export interface ArtifactRendererProps {
  artifactId: string;
  isEditing: boolean;
  onEditingChange: (editing: boolean) => void;
  chatCollapsed: boolean;
  onChatCollapseChange: (collapsed: boolean) => void;
}

export interface CodeRendererProps {
  content: string;
  language: string;
  isEditable: boolean;
  onContentChange: (newContent: string) => void;
  onSelectionChange?: (selectedText: string, start: number, end: number) => void;
}

export interface TextRendererProps {
  content: string;
  isEditable: boolean;
  onContentChange: (newContent: string) => void;
  onSelectionChange?: (selectedText: string, range: { start: number; end: number }) => void;
}
```

## 📡 Editor Interaction Protocol
The canvas editors communicate using a clean event-driven interface to prevent redundant component re-renders:

- `onContentChange`: Fired when text or code is edited in the Editor viewport.
- `onSelectionChange`: Fired during high-highlighting/context selection inside ProseMirror or CodeMirror.
- `onActionClick`: Fired on secondary action button clicks (e.g., "Run Code", "Rewrite Section").

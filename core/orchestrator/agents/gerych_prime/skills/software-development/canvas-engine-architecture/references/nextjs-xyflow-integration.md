# --- DNK-MRH-HEADER ---
# mrh_id: "references/nextjs-xyflow-integration.md"
# purpose: "Technical specification and pitfalls for Next.js and xyflow React Flow v12 integration."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🧬 Next.js & xyflow (React Flow v12) Integration Invariants

## 🚀 1. The Dynamic Loading Protocol (No SSR)
Due to browser-specific DOM usage inside `xyflow` and custom canvas components, Next.js page routers MUST dynamically import canvas and workspace components with SSR disabled:

```tsx
import dynamic from 'next/dynamic';

const DNKStudioWorkspace = dynamic(
  () => import('@/components/workspace/DNKStudioWorkspace'),
  { ssr: false, loading: () => <CanvasEngineSkeleton /> }
);
```

### ⚠️ CRITICAL INVARIANT: Double Export Pattern
When dynamically imported via `next/dynamic`, the imported file **MUST** provide both a default export and named exports to ensure seamless compatibility with both dynamic loaders and direct named imports:

```tsx
// 🟢 CORRECT
export default function DNKStudioWorkspace() { ... }
export { DNKStudioWorkspace };
```

Without the `default` export, Next.js runtime throws:
`Error: Element type is invalid. Received a promise that resolves to: [object Object]. Lazy element type must resolve to a class or function.`

---

## 📦 2. Package Import SSOT: `@xyflow/react` vs `reactflow`
React Flow v12 renamed its core package. NEVER mix import sources. All canvas components must exclusively import from the modern `@xyflow/react` scoped package.

### 🟢 Correct Imports
```typescript
import { Node, useReactFlow, ReactFlowProvider } from '@xyflow/react';
```

### 🔴 Incorrect Imports (Deprecated)
```typescript
import { Node, useReactFlow } from 'reactflow';
```

---

## 🛠️ 3. Troubleshooting Port Mismatches & Stale Servers on macOS
During rapid development cycles, background Node.js processes might hang on ports `3000`/`3001`.

### Verification & Cleanup Routine
1. **Identify the exact PID running on the port:**
   ```bash
   lsof -i :3000
   lsof -i :3001
   ```
2. **Gracefully terminate or force kill the stale processes:**
   ```bash
   kill -9 <PID>
   ```
3. **Restart the Next.js dev server to bind to the primary port 3000:**
   ```bash
   npm run dev
   ```

---

## 🌐 4. Docker Network Next.js Rewrites & Safe JSON Intake
When running Next.js alongside backend services in Docker Compose:

### ⚠️ The `localhost:8000` In-Container Trap
In `next.config.mjs`, setting `destination: 'http://localhost:8000/api/:path*'` fails inside containerized Next.js because `localhost` refers to the frontend container itself, throwing:
`connect ECONNREFUSED 127.0.0.1:8000 -> HTTP 500 Internal Server Error (HTML/text)`

### 🟢 SSOT Docker Proxy Rewrite Pattern
Dynamically bind `backendHost` based on container environment variables:
```javascript
// next.config.mjs
async rewrites() {
  const backendHost =
    process.env.BACKEND_INTERNAL_URL ||
    process.env.BACKEND_URL ||
    'http://127.0.0.1:8000';
  return [
    {
      source: '/api/:path*',
      destination: `${backendHost}/api/:path*`,
    },
  ];
}
```
In `Dockerfile.frontend` and `docker-compose.yml`, supply:
```yaml
# In Dockerfile.frontend (MUST BE SET IN BOTH builder AND runner STAGES!):
# Next.js compiles routes-manifest.json at build time; omitting it in builder stage bakes in localhost:8000!
ENV BACKEND_INTERNAL_URL="http://backend:8000"

# In docker-compose.yml:
environment:
  - BACKEND_INTERNAL_URL=http://backend:8000
```

### 🛡️ Safe JSON Intake Guard in Client Stores
Never call `await res.json()` directly on raw fetch responses without verifying `res.ok`. Non-JSON 500/502 gateway or rewrite errors cause `SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON`:
```typescript
if (!res.ok) {
  const errText = await res.text().catch(() => 'Network response failed');
  throw new Error(`API error (${res.status}): ${errText}`);
}
const data = await res.json();
```

---

## 🔍 5. Headless Browser CDP Error Capture Protocol for Next.js Client Exceptions
When Next.js encounters an unhandled runtime error in a client component, React Error Boundary catches it and renders a generic fallback:
`Application error: a client-side exception has occurred (see the browser console for more information)`

Because DOM inspection only sees this generic message, do not guess. Intercept the real exception stack trace headlessly using Chrome DevTools Protocol (`Page.addScriptToEvaluateOnNewDocument`):

```python
# Evaluate before navigating so early render errors are captured:
cdp('Page.addScriptToEvaluateOnNewDocument', source="""
  window.__capturedErrors = [];
  window.addEventListener('error', (e) => {
    // Note: Error objects serialize to {} under JSON.stringify, extract fields explicitly:
    window.__capturedErrors.push({
      message: e.message,
      filename: e.filename,
      lineno: e.lineno,
      colno: e.colno,
      stack: e.error ? e.error.stack : (e.message || String(e))
    });
  });
  window.addEventListener('unhandledrejection', (e) => {
    window.__capturedErrors.push({
      reason: String(e.reason),
      stack: e.reason && e.reason.stack ? e.reason.stack : null
    });
  });
""")

# Navigate to target page and check captured error stack:
goto_url('http://localhost:3000/tasks')
errors = js('window.__capturedErrors')
print(f"Captured errors: {errors}")
```

---

## 🛡️ 6. Defensive Data Contract & Normalization for Canvas/Graph Metrics
When React components read nested API models (such as `stats.by_type.idea`), backend updates or schema drift can return flat fields (`ideas_count`) or omit sub-objects (`by_type: undefined`). Direct property chaining throws:
`TypeError: Cannot read properties of undefined (reading 'idea')` which triggers the Next.js Error Boundary crash.

### Mandatory 3-Tier Defensive Invariants
1. **Component Safe Chaining & Dual Fallback**:
   Always use nullish coalescing against both flat and nested properties:
   ```tsx
   {stats?.ideas_count ?? stats?.by_type?.idea ?? 0}
   ```
2. **Store Layer Normalization (`zustandStore.ts`)**:
   Always normalize incoming responses in store fetchers with complete safe defaults:
   ```typescript
   const rawStats = data.stats || {};
   const normalizedStats: GraphStats = {
     total_nodes: rawStats.total_nodes ?? 0,
     ideas_count: rawStats.ideas_count ?? rawStats.by_type?.idea ?? 0,
     by_type: {
       idea: rawStats.by_type?.idea ?? rawStats.ideas_count ?? 0,
       epic: rawStats.by_type?.epic ?? rawStats.epics_count ?? 0,
       task: rawStats.by_type?.task ?? rawStats.tasks_count ?? 0,
       vertical_slice: rawStats.by_type?.vertical_slice ?? rawStats.slices_count ?? 0,
       gate: rawStats.by_type?.gate ?? rawStats.gates_count ?? 0,
       ...(rawStats.by_type || {}),
     },
     by_stage: {
       blocked: rawStats.by_stage?.blocked ?? rawStats.blocked_nodes_count ?? 0,
       ready: rawStats.by_stage?.ready ?? 0,
       in_progress: rawStats.by_stage?.in_progress ?? 0,
       done: rawStats.by_stage?.done ?? 0,
       ...(rawStats.by_stage || {}),
     },
   };
   ```
3. **Backend Pydantic Model Dual-Compatibility**:
   Backend models (e.g. `GraphStatistics`) should emit both flat counts and nested dictionaries (`by_type`, `by_stage`) to guarantee backwards compatibility across legacy and modern frontend clients.

---

## ⚡ 7. Next.js Hydration Mismatch & Client-Side Mount Guard
Components utilizing client-side Zustand stores, `localStorage`, or graph layout states render differently between the server pass and the client browser. This divergence triggers the fatal Next.js hydration error:
`Error: Hydration failed because the initial UI does not match what was rendered on the server.`

### 🟢 Canonical Mount Guard Pattern
Every client route/page hosting interactive Canvas or graph tables MUST implement the mounted guard:
```tsx
'use client';

import { useState, useEffect } from 'react';

export default function TasksPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null; // Or return a lightweight skeleton: <TaskBoardSkeleton />
  }

  return <TaskBoardContent />;
}
```

---

## 🎨 8. `@xyflow/react` v12 Custom Node Typing & CSS Bundle Invariants
Upgrading from `reactflow` to `@xyflow/react` (React Flow v12) introduces strict unknown typing in `NodeProps`:

### ⚠️ The `TS2571: Object is of type 'unknown'` Trap
In `@xyflow/react`, `NodeProps.data` defaults to `Record<string, unknown>`. Directly accessing `data.title` or `{data.label}` fails `tsc`:
`TS2571: Object is of type 'unknown'` and `TS2322: Type 'unknown' is not assignable to type 'ReactNode'`.

### 🟢 Type-Safe Node Data Handling Patterns
1. **Generic Node Specification (Recommended)**:
   ```tsx
   import { type Node, type NodeProps, Handle, Position } from '@xyflow/react';

   export interface CustomNodeData {
     title: string;
     status?: 'pending' | 'in_progress' | 'completed';
   }

   export type CustomNodeType = Node<CustomNodeData, 'custom'>;

   export function CustomNode({ data }: NodeProps<CustomNodeType>) {
     return (
       <div className="p-3 bg-zinc-900 border rounded">
         <Handle type="target" position={Position.Top} />
         <h4>{data.title}</h4>
         <Handle type="source" position={Position.Bottom} />
       </div>
     );
   }
   ```
2. **Defensive Record Casting**:
   ```tsx
   export function DynamicNode({ data }: NodeProps) {
     const nodeData = (data || {}) as Record<string, any>;
     return <span>{String(nodeData.title || nodeData.label || 'Node')}</span>;
   }
   ```

### 🟢 CSS Bundle SSOT
Never retain the legacy style import:
```typescript
// 🔴 FAILS AT RUNTIME / BUILD:
import 'reactflow/dist/style.css';

// 🟢 REQUIRED FOR @xyflow/react v12:
import '@xyflow/react/dist/style.css';
```

---

## 🛡️ 9. Next.js Monorepo `tsconfig.json` Exclusion Invariant
When Next.js runs alongside Storybook, Vitest, or experimental canvas suites, Next.js build-time typecheck (`tsc --noEmit`) will traverse non-production test files, throwing missing type definitions (`describe is not defined`, missing `@storybook/*`).

Always exclude non-production test and story paths in `apps/web/tsconfig.json`:
```json
{
  "exclude": [
    "node_modules",
    "stories",
    "**/*.stories.tsx",
    "vitest.config.ts",
    "src/canvas/test-setup.ts"
  ]
}
```



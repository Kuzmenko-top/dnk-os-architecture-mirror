---
name: generative-ui-pipeline
description: Synthesize full-stack Next.js UI from natural language.
version: 1.0.0
author: Maksym Kuzmenko, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [generative-ui, nextjs, react, tailwind, tanstack-query, shadcn]
    related_skills: [popular-web-designs, test-driven-development]
---

# Generative UI Pipeline

Autonomous synthesizer that translates natural language interface prompts into production-ready Next.js 15 App Router components, Tailwind v4 design tokens, shadcn/ui components, and TanStack React Query v5 data-binding hooks.

## When to Use

- Synthesizing web interfaces (dashboards, forms, metric cards, time-series charts, data tables) from natural language.
- Generating full-stack component bundles (`page.tsx`, client components, query hooks, TypeScript types).
- Binding design systems (`DNK-DS-001`, Tailwind v4, shadcn/ui) with strict Server/Client Component boundary enforcement.
- Automating frontend scaffolding with AST syntax verification.

## Core Architectural Layers

1. **`UISpecParser`**:
   - Parses intent and structured criteria (e.g., metric cards, chart configs, tables, forms).
   - Generates typed Pydantic models with title, description, layout, and component declarations.

2. **`ComponentGenerator` & Sub-Generators**:
   - **Server Components** (`page.tsx`): Default entry points with `Suspense` and Skeleton fallbacks.
   - **Client Components** (`*Cards.tsx`, `*Chart.tsx`, `*Table.tsx`, `*Form.tsx`): Explicit `"use client"` directives for interactive state and charts.
   - **`FormGenerator`**: Generates React Hook Form + dynamic Zod schemas (`zodResolver`) paired with TanStack Query mutation hooks (`useMutation` + `invalidateQueries`).
   - **`TableGenerator`**: Generates TanStack Table v8 data tables with sorting (`getSortedRowModel`), filtering (`getFilteredRowModel`), and pagination (`getPaginationRowModel`).
   - **`RegistryGenerator`**: Assembles Design System Component Registry (`apps/web/ui/`) with barrel exports and generates Storybook Next.js 15 stories.

3. **`DesignSystemBinder`**:
   - Integrates Tailwind v4 utility tokens and shadcn/ui primitives (`Card`, `Badge`, `Button`, `Table`, `Input`, `Skeleton`).

4. **`DataBindingLayer`**:
   - Synthesizes TanStack React Query v5 hooks (`use*.ts`) with typed fetchers, caching (`staleTime`), polling intervals (`refetchInterval`), mutation hooks, and retry resilience.

5. **`UIValidator`**:
   - AST validation for balanced braces/JSX tags.
   - Guard against missing `"use client"` directives in files using React hooks or browser APIs.
   - Path hygiene verification (relative imports only, no absolute host paths).

## Supporting Files

- `references/forms-and-tables-patterns.md`: Production-ready reference code snippets for React Hook Form + Zod and TanStack Table v8 components.
- `references/component-registry-and-storybook.md`: Reference architecture and snippets for Component Registry (`apps/web/ui/`) barrel exports and Storybook stories.
- `references/infinite-canvas-engine-patterns.md`: React Flow + Zustand Infinite Canvas architecture, viewport culling bounding box math, and FastAPI graph topology validation (Kahn's algorithm DAG & cycle detection).
- `references/generative-ui-sandbox-and-auto-layout.md`: Component sandbox iframe CSP envelopes, Shadow DOM encapsulation, lifecycle management, spatial auto-layout algorithms, and smart connector inference.

## Step-by-Step Generation Workflow

1. **Deconstruct Specification**:
   - Map user requirements to `UISpec` (determine component types, metrics, endpoints).
2. **Synthesize Type Definitions**:
   - Create `types.ts` reflecting backend DTOs and API payload contracts.
3. **Generate Query Hooks**:
   - Create typed React Query hooks (`use[Entity].ts`) with appropriate `staleTime` and error boundaries.
4. **Generate Client Presentation Components**:
   - Create modular UI cards/charts with `"use client"` directive at line 1.
5. **Generate Server Container / Page**:
   - Assemble components inside Next.js 15 App Router `page.tsx`.
6. **Validate Bundle**:
   - Run AST syntax checks, brace balancing, and path hygiene verification.

## Pitfalls & Invariants

- **Next.js 15 Boundary Invariant**: Any component using `useState`, `useEffect`, or `useQuery` MUST have `"use client"` at the very top. Server components (`page.tsx`) must NOT contain React hooks.
- **Missing Global Tailwind CSS Import & Unstyled Fallback**: When scaffolding or editing Next.js App Router projects, verify that `globals.css` with `@tailwind base; @tailwind components; @tailwind utilities;` exists and is explicitly imported in `app/layout.tsx` (`import './globals.css';`). If missing, all Tailwind classes are ignored at runtime, causing the browser to fall back to unstyled default HTML (raw white background, default serif fonts, unstyled elements).
- **Next.js Standalone Asset 404 / White Screen Pitfall**: `output: 'standalone'` in `next.config.mjs` causes `node .next/standalone/server.js` to return 404 for `/_next/static/chunks/...` because `.next/static` is not bundled into standalone by default. For local builds and standard node deployments, omit `output: 'standalone'` and use `next start -p 3000`, or explicitly copy `.next/static` to `.next/standalone/.next/static` and `public` to `.next/standalone/public`.
- **Visual Shell & Canvas SOTA UI Standard**: Interactive workflow designers must avoid raw stacked lists; render dark cyberpunk/glassmorphism surfaces (`bg-slate-950`, `border-slate-800`, `backdrop-blur-xl`), distinct node cards with semantic icons (⚡ Trigger, 🤖 Agent, 📦 Batch, 🛍️ Shopify), glowing status badges (Active, Queued, Executing, Done), directional connector arrows between pipeline stages, quick add-node toolbars, and a live terminal execution log console.
- **Cross-Port API Rewrites**: When frontend (e.g. port 3000) talks to backend FastAPI (port 8000), add `async rewrites() { return [{ source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }]; }` in `next.config.mjs` so client fetch calls work without CORS or port collisions.
- **Dynamic Parameter Route Fallback / Root Redirect**: When creating parameterized routes like `/canvas/[canvasId]/page.tsx`, always create a root `/canvas/page.tsx` that calls `redirect('/canvas/default-canvas-id')` to prevent 404 on base path navigation.
- **Unescaped Apostrophes in JSX Text**: Writing raw single quotes / apostrophes in JSX text or strings like `Рев'ю` or `z\'єднання` in `.tsx` files can trigger SWC compiler errors. Always wrap in curly string expressions `{"..."}` or use HTML entities `&apos;`.
- **Stale Container Port Binding**: If `localhost:3000` renders an unexpected or stale page despite running `npm run dev`, check for background Docker containers holding port 3000 (`docker ps --filter "publish=3000"`) and stop them before starting the dev server.
- **Local Next.js Production Build Stale Serving**: When running Next.js in production start mode (`next start`) instead of development mode (`next dev`), manual edits to styles, layouts, or component files will NOT show up in the browser because the node process serves pre-compiled bundles in `.next/`. Always trigger `npm run build` and restart the Next.js process/daemon to apply layout and Tailwind CSS styling updates.
- **FastAPI / Uvicorn Broken Pipe (Errno 32) Background Flow Handlers**: Background execution of agent flows invoking database/external network connectors (e.g. `asyncpg` timeline logging in `run_flow`) can raise `Broken Pipe (Errno 32)` or connection timeouts in the FastAPI response thread if the backend DB is unavailable. Always design routers and background flow coordinators to gracefully intercept connection failures within fail-safe blocks to avoid bubbling raw socket exceptions up as 500 API responses.
- **TypeScript Comment Syntax Invariant**: All comments and header banners in `.ts` / `.tsx` files MUST start with `//` (e.g. `// --- DNK-MRH-HEADER ---`), NEVER `#`. Using `#` in TypeScript files produces `Invalid character` compiler errors.
- **Import Hygiene**: Always use relative paths (`./types`, `../components`) rather than hardcoded absolute paths.
- **Data Resilience**: Always wrap API calls with loading states (Skeletons) and error alert fallbacks.
- **Cascading Graph Node Deletion**: Removing a node from canvas state store MUST clean up all connected edges (`source !== nodeId && target !== nodeId`) to prevent stale dangling edges.

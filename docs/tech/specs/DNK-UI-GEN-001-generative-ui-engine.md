# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-UI-GEN-001"
# purpose: "TaskDNA & Architectural Specification for Generative UI Engine (Next.js 15, Tailwind v4, shadcn/ui, React Query)"
# canonical_source: true
# alters_files: ["apps/api/services/generative_ui_engine.py", "tests/verification/test_generative_ui_engine.py"]
# triggers_tasks: ["DNK-UI-GEN-001-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

# 🎨 DNK-UI-GEN-001: Generative UI Engine Specification

## 1. Overview & Objective
The **Generative UI Engine** (`apps/api/services/generative_ui_engine.py`) provides an autonomous multi-layer pipeline for turning natural language prompts or structured AST schemas into production-ready Next.js 15 React components (Server & Client components), React Query / SWR data-binding hooks, and shadcn/ui + Tailwind v4 layouts.

## 2. Core Architecture & Pipeline
```
[Natural Language Prompt / Pydantic Schema]
                    │
                    ▼
          ┌───────────────────┐
          │   UISpecParser    │  (Extracts layout, components, data contracts, tokens)
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ ComponentGenerator│  (Synthesizes Next.js 15 Server/Client components)
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │DesignSystemBinder │  (Applies DNK-DS-001 tokens: Tailwind v4 + shadcn/ui)
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ DataBindingLayer  │  (Generates TanStack React Query v5 / SWR API hooks)
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │    UIValidator    │  (AST validation, TypeScript hygiene, prop integrity)
          └───────────────────┘
```

## 3. Data Contract Models (Pydantic v2)
- `UIComponentType`: `Dashboard` | `Form` | `Table` | `Chart` | `Card` | `Grid`
- `DesignSystemConfig`: Tailwind v4 theme, color palette, dark mode, typography scale.
- `DataBindingSpec`: Endpoint URL, query params, fetch interval, TanStack query key.
- `GeneratedUIArtifact`: File paths, TSX code, hook code, type definitions, exports.

## 4. Invariants & Guardrails
- **Next.js 15 App Router standard**: Default to React Server Components (`RSC`), explicitly declare `"use client"` where state/hooks are utilized.
- **Design System DNK-DS-001**: Strict utilization of `shadcn/ui` primitives (Card, Button, Table, Dialog, Badge) with Tailwind CSS v4 variables.
- **Relative Path Hygiene**: Generated code and imports strictly respect clean relative path standards (`@/components/...` or `./`).
- **Deterministic Quality Gate**: 100% Green test pass rate on every generation run.

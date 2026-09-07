# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-UI-GEN-003"
# purpose: "TaskDNA & Architecture Spec for Design System Component Registry (apps/web/ui/) & Storybook Integration"
# canonical_source: true
# alters_files: [
#   "apps/web/ui/index.ts",
#   "apps/web/ui/lib/utils.ts",
#   "apps/web/ui/lib/api.ts",
#   "apps/web/ui/components/ui/index.ts",
#   "apps/web/ui/components/forms/index.ts",
#   "apps/web/ui/components/tables/index.ts",
#   "apps/web/ui/components/charts/index.ts",
#   "apps/web/ui/hooks/index.ts",
#   "apps/web/.storybook/main.ts",
#   "apps/web/.storybook/preview.tsx",
#   "apps/web/stories/components/Button.stories.tsx",
#   "apps/web/stories/components/Card.stories.tsx",
#   "apps/web/stories/components/AgentForm.stories.tsx",
#   "apps/web/stories/components/AgentsTable.stories.tsx",
#   "apps/web/stories/components/ASRChart.stories.tsx",
#   "apps/api/services/generative_ui_engine.py",
#   "tests/verification/test_generative_ui_engine.py"
# ]
# triggers_tasks: ["DNK-UI-GEN-004"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

# 🧬 TaskDNA Specification: Design System Component Registry & Storybook (`DNK-UI-GEN-003`)

## 1. Executive Summary
`DNK-UI-GEN-003` establishes a centralized, tree-shakeable **Design System Component Registry** (`apps/web/ui/`) and **Storybook 8/Next.js 15 Integration** for interactive visual documentation and isolated component testing.

---

## 2. Architecture & Directory Hierarchy

```
apps/web/ui/
├── components/
│   ├── ui/          # Primitive shadcn/ui components (Button, Card, Input, Table, Skeleton)
│   ├── forms/       # RHF + Zod composite forms (AgentForm)
│   ├── tables/      # TanStack Table v8 composite tables (AgentsTable)
│   └── charts/      # Recharts visual components (ASRChart)
├── hooks/           # TanStack React Query v5 data-fetching & mutation hooks
├── lib/             # Utilities (cn, clsx, twMerge, api instance)
└── index.ts         # Main barrel export for `@/ui`
```

---

## 3. Storybook 8 Integration
- **Framework**: `@storybook/nextjs`
- **Addons**: `@storybook/addon-essentials`, `@storybook/addon-interactions`, `@storybook/addon-a11y`
- **Styling**: Tailwind v4 with CSS variables and dark mode support.
- **Stories**:
  - `Button.stories.tsx` (Variants: default, destructive, outline, secondary, ghost, link)
  - `Card.stories.tsx` (Default, Metric variant, interactive)
  - `AgentForm.stories.tsx` (Provisioning form with validation states)
  - `AgentsTable.stories.tsx` (Interactive data table with mock pagination)
  - `ASRChart.stories.tsx` (Real-time telemetry chart with gradient fill)

---

## 4. Master Quality Gate Invariants
- 100% Relative path hygiene (`./`, `../`, `@/ui`).
- MRH headers on all files (`DNK-STD-0075`).
- ASR < 5.0% on adversarial probe evaluation.

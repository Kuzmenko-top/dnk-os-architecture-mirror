# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-UI-GEN-002"
# purpose: "TaskDNA & Architecture Spec for Forms Generator (RHF + Zod) and Data Tables (TanStack Table v8)"
# canonical_source: true
# alters_files: ["apps/api/services/generative_ui_engine.py", "tests/verification/test_generative_ui_engine.py"]
# triggers_tasks: ["DNK-UI-GEN-002-FORMS-TABLES"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

# 📝 DNK-UI-GEN-002: Interactive Forms & Data Tables Generator

## 1. Scope & Objective
Expand the **Generative UI Engine** (`apps/api/services/generative_ui_engine.py`) to synthesize:
1. **Interactive Forms (`FormGenerator`)**:
   - React Hook Form + Zod validation schema generation.
   - Dynamic form controls: text input, select/enum dropdown, secure secret/API key inputs, switches/checkboxes.
   - TanStack React Query mutation hooks (`useCreateAgent.ts`).
2. **Data Tables (`TableGenerator`)**:
   - TanStack Table v8 generation with column sorting, fuzzy filtering, pagination controls, and badge cell formatters.
   - Server/Client data-fetching hooks with query param sync (`useAgents.ts`).
3. **Design System Integration (`apps/web/ui/`)**:
   - Reusable component exports, barrel file (`index.ts`), and Storybook-ready component definitions.

## 2. Invariants & Guardrails
- Strict Zod schema generation with runtime validation and friendly error messages.
- Clean component separation: Server Component wrapper (`page.tsx`) + Client form/table implementations.
- No hardcoded absolute paths; strict relative path hygiene (`@/components/...` or `./`).
- 100% Green Master Quality Gate.

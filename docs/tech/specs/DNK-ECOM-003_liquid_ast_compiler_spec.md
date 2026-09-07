# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ECOM-003_liquid_ast_compiler_spec.md"
# purpose: "Technical Specification & TaskDNA DAG for DNK-ECOM-003 Shopify Liquid Theme AST Compiler & Optimization Pipeline."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym / Gerych Prime"
# --- END DNK-MRH-HEADER ---

# DNK-ECOM-003 — Shopify Liquid Theme AST Compiler & Optimization Pipeline

## 🎯 Scope & Objectives
1. **Liquid AST Parser**: Custom AST parser in Python for Shopify Liquid grammar (TemplateNode, BlockNode, TagNode, VariableNode, FilterNode).
2. **Optimization Pipeline**: Tree-shaking of unused blocks, dead code elimination of unreachable Liquid branches, CSS/JS asset minification.
3. **App Block Schema Generator**: Automatic JSON Schema extraction conforming to Shopify Theme Store V2 / Theme Extension API.
4. **Performance Quality Gate**: Verification of bundle size (< 100KB), Core Web Vitals (LCP, FID, CLS), Lighthouse score (> 95).
5. **FastAPI & Real-Time Stream**: REST API endpoints and WebSocket live compilation progress.
6. **Frontend UI Components**: React / TypeScript AST tree visualizer, dashboard, and schema viewer.

## 🧬 TaskDNA Evolutionary DAG

```
[Phase 1: AST Parser & Tokenization] (gerych_builder)
       │
       ▼
[Phase 2: Optimization Engine (Tree-Shaking, DCE)] (gerych_builder)
       │
       ▼
[Phase 3: App Block Schema Generator] (dnk_shopify)
       │
       ▼
[Phase 4: Performance Quality Gate] (gerych_auditor)
       │
       ▼
[Phase 5: API Router & Live Stream] (dnk_dev_fullstack)
       │
       ▼
[Phase 6: Visual UI Cabinet Components] (gerych_builder)
       │
       ▼
[Phase 7: System Verification & Evidence] (antigravity_mentor / gerych_auditor)
```

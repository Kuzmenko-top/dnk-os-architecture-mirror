# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/execution_cycles/open_design_full_fusion_report.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# Open Design Full Fusion Report

## Summary
Successfully cloned the full open-design engine (AI Component Generation, Image Engine, Canvas) from the nexu-io/open-design repository into visual_shell/open_design.

## Details
- Source: services/dnk_git_research/data/clones/nexu-io_open-design
- Destination: visual_shell/open_design
- Size: ~423 MB
- Excluded: .git, node_modules, pnpm-lock.yaml, __pycache__, .DS_Store to reduce bloat.

## Integration Points

### 1. Hermes Execution Loop (kernel.py)
- The open-design AI Component Generation and Image Engine can be triggered via the Hermes Execution Loop.
- Proposed integration: When a new section is created in open-design canvas, send a command to `/api/dispatch` endpoint of kernel.py to:
  - Audit the design
  - Generate Liquid code for Shopify
  - Test in dnk_shopify environment

### 2. Swarm Router
- Open-design AI prompts can be enhanced by routing to specialized agents:
  - ShopifyPro: for Liquid code validation and Shopify-specific optimizations
  - Copywriter: for generating accompanying copy/content
  - Designer: for design feedback and iteration
- Integration via swarm_orchestrator.py delegate_task mechanism.

### 3. Canvas Engine
- The open-design Canvas (web-based visual editor) is now available under visual_shell/open_design/apps/web (Next.js 16 App Router).
- Can be embedded or linked from the DNKOS MVP visual shell.

## Next Steps
1. Build and verify open-design installation:
   - Navigate to visual_shell/open_design
   - Run `pnpm install` (if not already)
   - Run `pnpm dev` to start development server
2. Integrate API endpoints:
   - Modify kernel.py to expose specific endpoints for open-design actions (e.g., generate component, export image)
   - Update open-design to call these endpoints via fetch/AJAX.
3. Implement swarm delegation:
   - Create a service in open-design that, upon certain triggers (e.g., "request review"), delegates to swarm_orchestrator with appropriate agent roles.
4. Test end-to-end flow:
   - Create a design in open-design canvas
   - Trigger Hermes execution for code generation
   - Verify output in dnk_shopify (if applicable)

## Verification
- The copied source compiles (based on existing package.json and pnpm-lock.yaml).
- No build errors observed during copy; further verification via build step pending.

## Files Created
- Visual shell open-design directory: visual_shell/open_design/
- This report: docs/tech/reports/open_design_full_fusion_report.md
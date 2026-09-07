# Fast MCP License Audit and AST Dependency Call Graph

## 1. Zero-Clone License Audit via GitHub MCP
When auditing an external repository or package, do NOT immediately clone the entire repository. Use the GitHub MCP fast-path:
- Check for `LICENSE` or `LICENSE.md` via `mcp__github__get_file_contents(owner, repo, path='LICENSE')` or the fallback GitHub REST API `/repos/{owner}/{repo}/license`.
- Parse SPDX / header keywords:
  - **Track 1 (Permissive)**: `APACHE-2.0`, `MIT`, `BSD-2-CLAUSE`, `BSD-3-CLAUSE`, `ISC`.
  - **Track 2 (Copyleft / Clean-Room)**: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL-3.0`, `PROPRIETARY`.
- In code, invoke `DNAAssimilationEngine.audit_license(repo_info)` which automatically runs `audit_github_license_fast`.

## 2. Monorepo AST Dependency & Call Graph Resolution
Instead of executing sequential `search_files` / `grep` queries across dozens of files to locate where a class or function is used:
- Run `python3 scripts/system/repo_map.py --graph <Symbol>`:
  - Outputs definition locations (`file:line [kind]`).
  - Aggregates call sites and references grouped by file (`callers_by_file`).
  - Lists call sites with file, line number, and code snippet.
- Run `python3 scripts/system/repo_map.py --calls <Symbol>` for just reference call sites.
- Programmatically in Python:
  ```python
  from scripts.system.repo_map import resolve_symbol_graph, find_callers
  graph = resolve_symbol_graph("DNAAssimilationEngine")
  ```
- Or via tool: `dnk_resolve_symbol(symbol="...", include_calls=True)`.
Execution takes <50ms with ripgrep (`rg`) acceleration and pure-Python AST fallback, eliminating context bloat and multi-step turn exhaustion.

# 🧠 Gerych Core Fast Context (L1)
- **Owner & Workspace**: Maksym Kuzmenko (Maxim) | UA (🇺🇦) chat, EN (🇬🇧) code/docs | `ws-alpha-001` at `$HUB_ROOT`.
- **Invariants**: Relative paths only (`./`, `../`); mandatory MRH headers; SCONES retrieval first; 100% test pass before commit; strict branch isolation & explicit remote tracking (`git push dnk-mvp <branch>`).
- **Execution & Toolchain**: Always execute via `./.venv/bin/python3` with `PYTHONPATH=.`; run pytest via `./.venv/bin/pytest`.
- **Swarm Dispatch**: Triage step 0; parallel dispatch via `dnk_swarm_parallel` for multi-domain (C>3); atomic slices (<=25 tools/turn).
- **Self-Healing**: Query `dnk_query_error_solutions` on first failure; distill fix via `dnk_record_error_solution`.

## 💡 5. Active Dynamic Lessons (Distilled from Recent Sessions)
- **[ERROR_LOOP]**: Query dnk_query_error_solutions(error_text='IndentationError') immediately instead of repeated trial-and-error.
- **[ERROR_LOOP]**: Query dnk_query_error_solutions(error_text='nKeyError') immediately instead of repeated trial-and-error.
- **[ERROR_LOOP]**: Query dnk_query_error_solutions(error_text='KeyError') immediately instead of repeated trial-and-error.
- **[ZERO_WASTE_EFFICIENCY]**: Keep single-slice atomic focus: 1 turn = 1 focused slice.
- **[PATH_VIOLATION]**: Enforce relative path sanitization (./ or ../) before dispatching tool calls.

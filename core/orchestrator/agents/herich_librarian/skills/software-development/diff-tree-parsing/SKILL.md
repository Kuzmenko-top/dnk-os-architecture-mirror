---
name: diff-tree-parsing
description: "Parse unified diffs and extract AST symbol changes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Git, Diff, AST, Code-Analysis, Code-Review]
---

# Diff Tree Parsing & AST Symbol Extraction

Parsing unified git patches into structured file/directory trees and extracting high-level AST symbol changes (classes, functions, methods, headers) for fast code review, PR analysis, and UI visualization.

---

## When to Use

Use this skill when:
- Building or processing git diff parsing pipelines for code reviews, PR inspector UI components, or CLI tools.
- Extracting AST symbol-level diffs (classes, functions, methods) from Python or TypeScript/JavaScript source files.
- Implementing file-tree navigation and hunk-level diff visualization with lazy loading support.

---

## 1. Unified Patch Parsing to Tree Structure

Unified git diff patches (from `git diff` or API responses) can be parsed into a hierarchical file/directory tree with hunk-level detail.

### Data Structures
- **`FileDiff`**: Contains `filename`, `status` (`added`, `modified`, `deleted`, `renamed`), `is_binary`, `additions`, `deletions`, `hunks`.
- **`Hunk`**: Header (`old_start`, `old_lines`, `new_start`, `new_lines`), list of `lines` (`type: add/del/context`, `old_line`, `new_line`, `content`).
- **`DiffTree`**: Hierarchical directory nodes containing child folders and files with aggregated `additions`/`deletions`/`changes`.

### Implementation Pattern (Python)
1. Split patch text by `diff --git`.
2. Parse `--- a/` and `+++ b/` headers to derive filename and file status (`added`, `modified`, `deleted`, `renamed`).
3. Parse hunk headers (`@@ -old,len +new,len @@`) and categorize lines (`+`, `-`, or context).
4. Build nested directory tree by splitting file path components on `/`.

---

## 2. AST Symbol Diff Extraction

Extract high-level code structure changes to provide concise symbol-level summaries before inspecting line-level diffs.

### Supported Language Extractors

#### Python (`.py`)
- Use `ast.parse()` on source code before and after changes.
- Traverse AST to collect `FunctionDef`, `AsyncFunctionDef`, and `ClassDef` symbols.
- Track methods inside classes as `ClassName.method_name`.
- Compare old vs new symbol maps:
  - In new, not in old → **`added`**
  - In both → **`modified`**
  - In old, not in new → **`deleted`**

#### TypeScript / JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`)
- Use regex/AST scanning for `class`, `interface`, `type`, `function`, and class methods.
- Method notation: `ClassName.methodName`.
- Convert TypeScript interfaces and types into Python Pydantic `BaseModel` classes using explicit type mappings (`string -> str`, `number -> float | int`, `boolean -> bool`, `Array<T> | T[] -> list[T]`, `Record<K, V> -> dict[K, V]`, `optional ? -> Optional[...]`).

---

## 3. Pydantic Schema & Clean-Room Adapter Synthesis

When assimilating external donor repositories (e.g. TypeScript/Python SDKs or UI frameworks):
1. **Extract AST Signatures**: Extract all target classes, interfaces, and function signatures.
2. **Type Mapping**: Map primitive and container types to Python type hints and Pydantic fields.
3. **Pydantic Schema Generation**: Generate standalone, typed Pydantic models carrying `DNK-STD-0075` MRH headers.
4. **Clean-Room Specification**: For Track 2 (Copyleft/Restrictive) donors, emit Clean-Room specifications (`DNK-CLEANROOM-XXX.md`) separating public interface contracts from implementation details to prevent license contamination.

---

## 4. Best Practices & Performance Invariants

- **Lazy Loading**: For large PRs (>50 files or >2000 lines), load the file tree structure first and fetch file patch hunks lazily when a file is selected.
- **Fail-Closed Security**: Validate target repositories against `ALLOWED_REPOSITORIES` and redact sensitive credentials (`[REDACTED]`) before rendering or returning diff data.

---

## 4. Pitfalls & Implementation Notes

- **Tree Root Data Compatibility (`DiffTreeRoot`)**: When API contracts require both object metadata (e.g. `file_count`, `additions`) and list iteration over top-level tree nodes, inherit `DiffTreeRoot` from `dict` and implement list delegation (`__iter__`, `__getitem__`, `__len__`). Ensure all directory and file nodes include `file_count` (`1` for file nodes, sum of children for folder nodes).
- **Dual-Input AST Analyzers**: `analyze_file_ast_diff(filename, old_code="", new_code="", patch_text="")` should handle both direct source comparison (`old_code` vs `new_code`) and patch parsing from git diffs.
- **Line Field Standardisation**: Standardise AST symbol line fields to `line` (matching standard Python `ast.AST` attributes) rather than `line_start` to ensure seamless rendering across frontend AST badges.
- **GitHub Adapter Parameters**: Ensure router endpoints match exact parameter names expected by GitHub service adapters (e.g., passing `filename=target_path` for single file diff requests) and include `include_chunks: bool = True` in adapter signatures for optional chunk suppression.

# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_ast_diff"
# purpose: "AST-based diff analyzer extracting changes in classes, functions, methods, and MRH headers for Python and TypeScript/JavaScript."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import ast
import re
from typing import List, Dict, Any, Optional, Set, Literal
from pydantic import BaseModel, Field


class ASTSymbol(BaseModel):
    """Representing a code symbol (class, function, method, MRH header)."""
    file: str
    symbol_type: Literal["class", "function", "async_function", "method", "mrh_header", "interface", "type_alias"]
    name: str
    change_type: Literal["added", "modified", "deleted"]
    line: Optional[int] = None
    details: Optional[str] = None


class ASTDiffSummary(BaseModel):
    """Summary of AST changes."""
    classes_added: int = 0
    classes_modified: int = 0
    classes_deleted: int = 0
    functions_added: int = 0
    functions_modified: int = 0
    functions_deleted: int = 0
    mrh_header_updated: bool = False
    total_symbols_changed: int = 0


class ASTDiffResultData(BaseModel):
    """Overall container for AST diff response."""
    pr_number: Optional[int] = None
    summary: ASTDiffSummary
    symbols: List[ASTSymbol] = Field(default_factory=list)


# TypeScript / JavaScript symbol extraction regex patterns
TS_CLASS_REGEX = re.compile(r"^(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)", re.MULTILINE)
TS_INTERFACE_REGEX = re.compile(r"^(?:export\s+)?interface\s+([A-Za-z0-9_$]+)", re.MULTILINE)
TS_TYPE_REGEX = re.compile(r"^(?:export\s+)?type\s+([A-Za-z0-9_$]+)\s*=", re.MULTILINE)
TS_FN_REGEX = re.compile(r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)", re.MULTILINE)
TS_ARROW_FN_REGEX = re.compile(r"^(?:export\s+)?const\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?::\s*[^=]+)?=>", re.MULTILINE)
MRH_HEADER_REGEX = re.compile(r"# --- DNK-MRH-HEADER ---")


def extract_python_symbols(source_code: str, filename: str = "") -> List[Dict[str, Any]]:
    """Extract AST symbols from Python source code."""
    symbols: List[Dict[str, Any]] = []
    if not source_code:
        return symbols

    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError:
        # Fallback to regex-based extraction if syntax has partial errors
        return extract_regex_python_symbols(source_code, filename)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append({
                "file": filename,
                "symbol_type": "class",
                "name": node.name,
                "line": node.lineno,
                "details": f"class {node.name}"
            })
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    symbols.append({
                        "file": filename,
                        "symbol_type": "method",
                        "name": f"{node.name}.{sub.name}",
                        "line": sub.lineno,
                        "details": f"def {sub.name}()"
                    })
                elif isinstance(sub, ast.AsyncFunctionDef):
                    symbols.append({
                        "file": filename,
                        "symbol_type": "method",
                        "name": f"{node.name}.{sub.name}",
                        "line": sub.lineno,
                        "details": f"async def {sub.name}()"
                    })
        elif isinstance(node, ast.FunctionDef):
            symbols.append({
                "file": filename,
                "symbol_type": "function",
                "name": node.name,
                "line": node.lineno,
                "details": f"def {node.name}()"
            })
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append({
                "file": filename,
                "symbol_type": "async_function",
                "name": node.name,
                "line": node.lineno,
                "details": f"async def {node.name}()"
            })

    return symbols


def extract_regex_python_symbols(source_code: str, filename: str = "") -> List[Dict[str, Any]]:
    """Extract Python symbols via regex when AST fails."""
    symbols: List[Dict[str, Any]] = []
    lines = source_code.splitlines()
    for idx, line in enumerate(lines, 1):
        line_str = line.strip()
        if line_str.startswith("class "):
            match = re.match(r"^class\s+([A-Za-z0-9_]+)", line_str)
            if match:
                symbols.append({
                    "file": filename,
                    "symbol_type": "class",
                    "name": match.group(1),
                    "line": idx,
                    "details": line_str
                })
        elif line_str.startswith("def "):
            match = re.match(r"^def\s+([A-Za-z0-9_]+)", line_str)
            if match:
                symbols.append({
                    "file": filename,
                    "symbol_type": "function",
                    "name": match.group(1),
                    "line": idx,
                    "details": line_str
                })
        elif line_str.startswith("async def "):
            match = re.match(r"^async\s+def\s+([A-Za-z0-9_]+)", line_str)
            if match:
                symbols.append({
                    "file": filename,
                    "symbol_type": "async_function",
                    "name": match.group(1),
                    "line": idx,
                    "details": line_str
                })
    return symbols


def extract_ts_symbols(source_code: str, filename: str = "") -> List[Dict[str, Any]]:
    """Extract TypeScript / JavaScript symbols from source code."""
    symbols: List[Dict[str, Any]] = []
    lines = source_code.splitlines()
    current_class = None

    for idx, line in enumerate(lines, 1):
        line_str = line.strip()

        # Class
        match_cls = TS_CLASS_REGEX.match(line_str)
        if match_cls:
            current_class = match_cls.group(1)
            symbols.append({
                "file": filename,
                "symbol_type": "class",
                "name": current_class,
                "line": idx,
                "details": line_str
            })
            continue

        if line_str.startswith("}") and not line.startswith(" ") and not line.startswith("\t"):
            current_class = None

        # Interface
        match_iface = TS_INTERFACE_REGEX.match(line_str)
        if match_iface:
            symbols.append({
                "file": filename,
                "symbol_type": "interface",
                "name": match_iface.group(1),
                "line": idx,
                "details": line_str
            })
            continue

        # Type Alias
        match_type = TS_TYPE_REGEX.match(line_str)
        if match_type:
            symbols.append({
                "file": filename,
                "symbol_type": "type_alias",
                "name": match_type.group(1),
                "line": idx,
                "details": line_str
            })
            continue

        # Standard Function
        match_fn = TS_FN_REGEX.match(line_str)
        if match_fn:
            symbols.append({
                "file": filename,
                "symbol_type": "function",
                "name": match_fn.group(1),
                "line": idx,
                "details": line_str
            })
            continue

        # Arrow Function / React Component
        match_arrow = TS_ARROW_FN_REGEX.match(line_str)
        if match_arrow:
            symbols.append({
                "file": filename,
                "symbol_type": "function",
                "name": match_arrow.group(1),
                "line": idx,
                "details": line_str
            })
            continue

        # Class Method
        if current_class:
            match_method = re.match(r"^(?:async\s+)?([A-Za-z0-9_]+)\s*\([^)]*\)\s*(?::\s*[^{\n]+)?\s*\{", line_str)
            if match_method:
                method_name = match_method.group(1)
                if method_name not in ("constructor", "if", "for", "while", "switch", "catch"):
                    symbols.append({
                        "file": filename,
                        "symbol_type": "method",
                        "name": f"{current_class}.{method_name}",
                        "line": idx,
                        "details": line_str
                    })
                    continue

    return symbols


def extract_symbols_from_patch(patch_text: str, filename: str) -> List[ASTSymbol]:
    """Analyze a git diff patch to determine added/modified/deleted AST symbols and MRH headers."""
    symbols: List[ASTSymbol] = []
    if not patch_text:
        return symbols

    is_py = filename.endswith(".py")
    is_ts = filename.endswith((".ts", ".tsx", ".js", ".jsx"))

    lines = patch_text.splitlines()
    has_mrh_change = False

    added_code_lines = []
    deleted_code_lines = []

    for line in lines:
        if MRH_HEADER_REGEX.search(line):
            has_mrh_change = True

        if line.startswith("+") and not line.startswith("+++"):
            added_code_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deleted_code_lines.append(line[1:])

    if has_mrh_change:
        symbols.append(
            ASTSymbol(
                file=filename,
                symbol_type="mrh_header",
                name="DNK-MRH-HEADER",
                change_type="modified",
                line=1,
                details="MRH Header updated / verified"
            )
        )

    added_source = "\n".join(added_code_lines)
    deleted_source = "\n".join(deleted_code_lines)

    if is_py:
        added_syms = extract_python_symbols(added_source, filename)
        deleted_syms = extract_python_symbols(deleted_source, filename)
    elif is_ts:
        added_syms = extract_ts_symbols(added_source, filename)
        deleted_syms = extract_ts_symbols(deleted_source, filename)
    else:
        return symbols

    added_names = {s["name"]: s for s in added_syms}
    deleted_names = {s["name"]: s for s in deleted_syms}

    # Intersect for modified vs added vs deleted
    common_names = set(added_names.keys()) & set(deleted_names.keys())
    only_added = set(added_names.keys()) - common_names
    only_deleted = set(deleted_names.keys()) - common_names

    for name in common_names:
        item = added_names[name]
        symbols.append(
            ASTSymbol(
                file=filename,
                symbol_type=item["symbol_type"],
                name=name,
                change_type="modified",
                line=item.get("line"),
                details=item.get("details")
            )
        )

    for name in only_added:
        item = added_names[name]
        symbols.append(
            ASTSymbol(
                file=filename,
                symbol_type=item["symbol_type"],
                name=name,
                change_type="added",
                line=item.get("line"),
                details=item.get("details")
            )
        )

    for name in only_deleted:
        item = deleted_names[name]
        symbols.append(
            ASTSymbol(
                file=filename,
                symbol_type=item["symbol_type"],
                name=name,
                change_type="deleted",
                line=item.get("line"),
                details=item.get("details")
            )
        )

    return symbols


def extract_ast_diff(
    files: List[Dict[str, Any]],
    pr_number: Optional[int] = None
) -> ASTDiffResultData:
    """Extract full AST diff across all changed files in a PR."""
    all_symbols: List[ASTSymbol] = []
    classes_added = 0
    classes_mod = 0
    classes_del = 0
    fns_added = 0
    fns_mod = 0
    fns_del = 0
    mrh_updated = False

    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if not patch:
            continue

        file_symbols = extract_symbols_from_patch(patch, filename)
        for sym in file_symbols:
            all_symbols.append(sym)
            if sym.symbol_type == "class":
                if sym.change_type == "added":
                    classes_added += 1
                elif sym.change_type == "modified":
                    classes_mod += 1
                elif sym.change_type == "deleted":
                    classes_del += 1
            elif sym.symbol_type in ("function", "async_function", "method"):
                if sym.change_type == "added":
                    fns_added += 1
                elif sym.change_type == "modified":
                    fns_mod += 1
                elif sym.change_type == "deleted":
                    fns_del += 1
            elif sym.symbol_type == "mrh_header":
                mrh_updated = True

    summary = ASTDiffSummary(
        classes_added=classes_added,
        classes_modified=classes_mod,
        classes_deleted=classes_del,
        functions_added=fns_added,
        functions_modified=fns_mod,
        functions_deleted=fns_del,
        mrh_header_updated=mrh_updated,
        total_symbols_changed=len(all_symbols)
    )

    return ASTDiffResultData(
        pr_number=pr_number,
        summary=summary,
        symbols=all_symbols
    )


def analyze_file_ast_diff(
    filename: str,
    old_code: str = "",
    new_code: str = "",
    patch_text: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze single file AST symbol diffs from source or patch."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    language = "python" if ext in ("py", "pyw") else ("typescript" if ext in ("ts", "tsx", "js", "jsx") else "unsupported")

    symbols = []

    if old_code or new_code:
        old_syms = extract_python_symbols(old_code, filename) if language == "python" else extract_ts_symbols(old_code, filename)
        new_syms = extract_python_symbols(new_code, filename) if language == "python" else extract_ts_symbols(new_code, filename)

        old_map = {s["name"]: s for s in old_syms}
        new_map = {s["name"]: s for s in new_syms}

        for name, sym in new_map.items():
            if name not in old_map:
                symbols.append({
                    "name": name,
                    "kind": sym.get("symbol_type", "function"),
                    "change_type": "added",
                    "line_start": sym.get("line"),
                    "details": sym.get("details", "")
                })
            else:
                symbols.append({
                    "name": name,
                    "kind": sym.get("symbol_type", "function"),
                    "change_type": "modified",
                    "line_start": sym.get("line"),
                    "details": sym.get("details", "")
                })

        for name, sym in old_map.items():
            if name not in new_map:
                symbols.append({
                    "name": name,
                    "kind": sym.get("symbol_type", "function"),
                    "change_type": "deleted",
                    "line_start": sym.get("line"),
                    "details": sym.get("details", "")
                })
    elif patch_text:
        ast_syms = extract_symbols_from_patch(patch_text, filename)
        for s in ast_syms:
            symbols.append({
                "name": s.name,
                "kind": s.symbol_type,
                "change_type": s.change_type,
                "line_start": s.line,
                "details": f"{s.symbol_type} {s.name}"
            })

    added_count = sum(1 for s in symbols if s.get("change_type") == "added")
    modified_count = sum(1 for s in symbols if s.get("change_type") == "modified")
    deleted_count = sum(1 for s in symbols if s.get("change_type") == "deleted")

    return {
        "filename": filename,
        "language": language,
        "symbols": symbols,
        "symbols_count": len(symbols),
        "added_count": added_count,
        "modified_count": modified_count,
        "deleted_count": deleted_count
    }


# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_diff_parser"
# purpose: "Unified git diff parser producing structured JSON tree, hunks, and line-level diff models for Cabinet UX."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
from typing import List, Dict, Any, Optional, Tuple, Literal
from pydantic import BaseModel, Field


class DiffLine(BaseModel):
    """Line-level diff model."""
    type: Literal["context", "add", "delete", "header", "binary"]
    old_num: Optional[int] = None
    new_num: Optional[int] = None
    content: str


class DiffHunk(BaseModel):
    """Diff Hunk model representing a continuous chunk of changes."""
    header: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[DiffLine] = Field(default_factory=list)


class DiffFileEntry(BaseModel):
    """File entry in a diff tree."""
    path: str
    name: str = ""
    directory: str = ""
    status: str = "modified"  # added, modified, removed, renamed, copied, changed, unchanged
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    is_binary: bool = False
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    hunks: List[DiffHunk] = Field(default_factory=list)
    hunks_count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.name and self.path:
            self.name = self.path.split("/")[-1]
        if not self.directory and self.path:
            parts = self.path.split("/")
            self.directory = "/".join(parts[:-1]) if len(parts) > 1 else ""


class DiffTreeNode(BaseModel):
    """Hierarchical directory/file tree node for Cabinet UX FileTree."""
    name: str
    path: str
    type: Literal["file", "directory"]
    status: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    file_count: Optional[int] = None
    file_entry: Optional[DiffFileEntry] = None
    children: List["DiffTreeNode"] = Field(default_factory=list)


class DiffSummary(BaseModel):
    """Overall summary of a PR diff."""
    pr_number: Optional[int] = None
    total_files: int = 0
    additions: int = 0
    deletions: int = 0
    files: List[DiffFileEntry] = Field(default_factory=list)
    tree: Any = Field(default_factory=list)


HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def parse_patch_hunks(patch_text: str) -> List[DiffHunk]:
    """Parse unified diff patch text into structured hunks and lines."""
    if not patch_text:
        return []

    lines = patch_text.splitlines()
    hunks: List[DiffHunk] = []
    current_hunk: Optional[DiffHunk] = None
    old_line_counter = 0
    new_line_counter = 0

    for line in lines:
        if line.startswith("@@"):
            match = HUNK_HEADER_REGEX.match(line)
            if match:
                old_start = int(match.group(1))
                old_lines = int(match.group(2)) if match.group(2) is not None else 1
                new_start = int(match.group(3))
                new_lines = int(match.group(4)) if match.group(4) is not None else 1

                current_hunk = DiffHunk(
                    header=line,
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                    lines=[]
                )
                hunks.append(current_hunk)
                old_line_counter = old_start
                new_line_counter = new_start
                continue

        if current_hunk is None:
            continue

        if line.startswith("+"):
            current_hunk.lines.append(
                DiffLine(
                    type="add",
                    old_num=None,
                    new_num=new_line_counter,
                    content=line[1:]
                )
            )
            new_line_counter += 1
        elif line.startswith("-"):
            current_hunk.lines.append(
                DiffLine(
                    type="delete",
                    old_num=old_line_counter,
                    new_num=None,
                    content=line[1:]
                )
            )
            old_line_counter += 1
        elif line.startswith(" "):
            current_hunk.lines.append(
                DiffLine(
                    type="context",
                    old_num=old_line_counter,
                    new_num=new_line_counter,
                    content=line[1:]
                )
            )
            old_line_counter += 1
            new_line_counter += 1
        elif line.startswith("\\ No newline at end of file"):
            pass
        else:
            # Fallback treat as context or header
            current_hunk.lines.append(
                DiffLine(
                    type="context",
                    old_num=old_line_counter,
                    new_num=new_line_counter,
                    content=line
                )
            )
            old_line_counter += 1
            new_line_counter += 1

    return hunks


class DiffTreeRoot(dict):
    """Container that behaves both as a root dict and as a list of top-level children."""
    def __init__(self, children: List[Any], total_files: int = 0, additions: int = 0, deletions: int = 0):
        node_children = [c.model_dump() if hasattr(c, "model_dump") else c for c in children]
        super().__init__({
            "name": "root",
            "path": "",
            "type": "directory",
            "file_count": total_files,
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
            "children": node_children
        })
        self._children = children

    def __iter__(self):
        return iter(self._children)

    def __len__(self):
        return len(self._children)

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return self._children[item]
        return super().__getitem__(item)


def build_diff_tree(file_entries: List[Any]) -> DiffTreeRoot:
    """Build nested directory/file hierarchy for tree navigation."""
    root_nodes: Dict[str, Any] = {}
    total_files = 0
    total_adds = 0
    total_dels = 0

    for raw_entry in file_entries:
        if isinstance(raw_entry, dict):
            entry_path = raw_entry.get("path") or raw_entry.get("filename") or ""
            entry_status = raw_entry.get("status", "modified")
            entry_additions = raw_entry.get("additions", 0)
            entry_deletions = raw_entry.get("deletions", 0)
        else:
            entry_path = getattr(raw_entry, "path", getattr(raw_entry, "filename", ""))
            entry_status = getattr(raw_entry, "status", "modified")
            entry_additions = getattr(raw_entry, "additions", 0)
            entry_deletions = getattr(raw_entry, "deletions", 0)

        total_files += 1
        total_adds += entry_additions
        total_dels += entry_deletions

        parts = entry_path.split("/")
        current_level = root_nodes

        for i, part in enumerate(parts):
            is_file = (i == len(parts) - 1)
            partial_path = "/".join(parts[:i + 1])

            if part not in current_level:
                if is_file:
                    file_entry_obj = raw_entry if isinstance(raw_entry, DiffFileEntry) else DiffFileEntry(
                        path=entry_path,
                        filename=entry_path,
                        status=entry_status,
                        additions=entry_additions,
                        deletions=entry_deletions,
                        changes=entry_additions + entry_deletions,
                        hunks=[]
                    )
                    current_level[part] = {
                        "_type": "file",
                        "_node": DiffTreeNode(
                            name=part,
                            path=entry_path,
                            type="file",
                            status=entry_status,
                            additions=entry_additions,
                            deletions=entry_deletions,
                            file_entry=file_entry_obj,
                            children=[]
                        )
                    }
                else:
                    current_level[part] = {
                        "_type": "directory",
                        "_path": partial_path,
                        "_children": {},
                        "_additions": 0,
                        "_deletions": 0
                    }

            if not is_file:
                current_level[part]["_additions"] += entry_additions
                current_level[part]["_deletions"] += entry_deletions
                current_level = current_level[part]["_children"]

    def _convert_to_nodes(level_dict: Dict[str, Any]) -> List[DiffTreeNode]:
        result: List[DiffTreeNode] = []
        for name, data in sorted(level_dict.items(), key=lambda x: (0 if x[1]["_type"] == "directory" else 1, x[0])):
            if data["_type"] == "file":
                node = data["_node"]
                node.file_count = 1
                result.append(node)
            else:
                children_nodes = _convert_to_nodes(data["_children"])
                dir_file_count = sum(c.file_count or 1 for c in children_nodes)
                dir_node = DiffTreeNode(
                    name=name,
                    path=data["_path"],
                    type="directory",
                    status=None,
                    additions=data["_additions"],
                    deletions=data["_deletions"],
                    file_count=dir_file_count,
                    file_entry=None,
                    children=children_nodes
                )
                result.append(dir_node)
        return result

    children = _convert_to_nodes(root_nodes)
    return DiffTreeRoot(children=children, total_files=total_files, additions=total_adds, deletions=total_dels)


def parse_git_diff(
    raw_diff: str,
    pr_number: Optional[int] = None,
    include_hunks: bool = True
) -> DiffSummary:
    """Parse a full raw unified git diff into DiffSummary with files and tree."""
    if not raw_diff or not raw_diff.strip():
        return DiffSummary(pr_number=pr_number, total_files=0, additions=0, deletions=0, files=[], tree=[])

    # Split into file diff blocks
    # Unified diff starts file blocks with 'diff --git'
    file_chunks = re.split(r"(?=^diff --git )", raw_diff, flags=re.MULTILINE)
    file_entries: List[DiffFileEntry] = []
    total_adds = 0
    total_dels = 0

    for chunk in file_chunks:
        chunk = chunk.strip()
        if not chunk or not chunk.startswith("diff --git"):
            continue

        lines = chunk.splitlines()
        first_line = lines[0]  # diff --git a/path b/path
        match = re.match(r"^diff --git a/(.*) b/(.*)$", first_line)
        if not match:
            continue

        old_path = match.group(1)
        new_path = match.group(2)
        final_path = new_path if new_path != "/dev/null" else old_path

        status: Literal["added", "modified", "removed", "renamed", "copied", "changed", "unchanged"] = "modified"
        is_binary = False

        for l in lines[1:10]:
            if l.startswith("new file mode"):
                status = "added"
            elif l.startswith("deleted file mode"):
                status = "removed"
            elif l.startswith("similarity index") or l.startswith("rename from"):
                status = "renamed"
            elif "Binary files" in l or "GIT binary patch" in l:
                is_binary = True

        hunks = []
        additions = 0
        deletions = 0

        if not is_binary:
            hunk_lines = []
            hunk_started = False
            for l in lines:
                if l.startswith("@@"):
                    hunk_started = True
                if hunk_started:
                    hunk_lines.append(l)
                    if l.startswith("+") and not l.startswith("+++"):
                        additions += 1
                    elif l.startswith("-") and not l.startswith("---"):
                        deletions += 1

            if include_hunks and hunk_lines:
                hunks = parse_patch_hunks("\n".join(hunk_lines))

        dir_name = "/".join(final_path.split("/")[:-1])
        base_name = final_path.split("/")[-1]

        entry = DiffFileEntry(
            path=final_path,
            name=base_name,
            directory=dir_name,
            status=status,
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            is_binary=is_binary,
            old_path=old_path,
            new_path=new_path,
            hunks=hunks if include_hunks else [],
            hunks_count=len(hunks) if include_hunks else (1 if additions + deletions > 0 else 0)
        )
        file_entries.append(entry)
        total_adds += additions
        total_dels += deletions

    tree = build_diff_tree(file_entries)

    return DiffSummary(
        pr_number=pr_number,
        total_files=len(file_entries),
        additions=total_adds,
        deletions=total_dels,
        files=file_entries,
        tree=tree
    )


def parse_normalized_files_to_summary(
    raw_files: List[Dict[str, Any]],
    pr_number: Optional[int] = None,
    include_hunks: bool = True
) -> DiffSummary:
    """Parse list of normalized GitHub changed files into DiffSummary."""
    file_entries: List[DiffFileEntry] = []
    total_adds = 0
    total_dels = 0

    for f in raw_files:
        filename = f.get("filename", "")
        status = f.get("status", "modified")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        changes = f.get("changes", additions + deletions)
        patch = f.get("patch", "")

        dir_name = "/".join(filename.split("/")[:-1])
        base_name = filename.split("/")[-1]

        hunks = parse_patch_hunks(patch) if (include_hunks and patch) else []

        entry = DiffFileEntry(
            path=filename,
            name=base_name,
            directory=dir_name,
            status=status,
            additions=additions,
            deletions=deletions,
            changes=changes,
            is_binary=False,
            old_path=filename,
            new_path=filename,
            hunks=hunks,
            hunks_count=len(hunks)
        )
        file_entries.append(entry)
        total_adds += additions
        total_dels += deletions

    tree = build_diff_tree(file_entries)

    return DiffSummary(
        pr_number=pr_number,
        total_files=len(file_entries),
        additions=total_adds,
        deletions=total_dels,
        files=file_entries,
        tree=tree
    )


def parse_file_patch(filename: str, patch_text: Optional[str], status: str = "modified") -> Dict[str, Any]:
    """Parse single file patch into dictionary with hunks and stats (backward compatibility)."""
    hunks = parse_patch_hunks(patch_text) if patch_text else []
    additions = sum(sum(1 for l in h.lines if l.type == "add") for h in hunks)
    deletions = sum(sum(1 for l in h.lines if l.type == "delete") for h in hunks)
    return {
        "filename": filename,
        "status": status,
        "additions": additions,
        "deletions": deletions,
        "changes": additions + deletions,
        "hunks": [h.model_dump() for h in hunks],
        "hunks_count": len(hunks),
        "patch": patch_text
    }


# Aliases for convenience and backward-compatibility
parse_unified_diff = parse_git_diff
build_diff_tree_from_files = build_diff_tree

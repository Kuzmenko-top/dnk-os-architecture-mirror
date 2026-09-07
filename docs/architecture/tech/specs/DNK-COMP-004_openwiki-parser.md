# 🧬 Component Interfaces & Contracts: OpenWiki Parser (DNK-COMP-004)
## Title: OpenWiki Frontmatter & Indexing Ports
## Status: Active | Version: 1.0.0 | Author: Yuriy Slicer

This specification defines the logical ports and Python-based implementations for parsing YAML frontmatter blocks and recursively synchronizing directory indexes in the DNK OS Markdown wiki.

### 1. Frontmatter Parser Port

The frontmatter parser is a finite state machine that processes a YAML block in a Markdown file:

```python
import yaml

class FrontmatterParser:
    def __init__(self, content: str):
        self.content = content
        self.frontmatter_block = None
        self.fields = None

    def parse(self) -> dict:
        lines = self.content.splitlines()
        if not lines or lines[0] != "---":
            return {"valid": False, "issues": ["missing_opening_delimiter"]}

        try:
            closing_line = lines.index("---", 1)
        except ValueError:
            return {"valid": False, "issues": ["missing_closing_delimiter"]}

        self.frontmatter_block = "\n".join(lines[1:closing_line])
        try:
            self.fields = yaml.safe_load(self.frontmatter_block)
        except yaml.YAMLError:
            return {"valid": False, "issues": ["invalid_yaml"]}

        if not isinstance(self.fields, dict):
            return {"valid": False, "issues": ["invalid_yaml_root"]}

        issues = []
        if "type" not in self.fields:
            issues.append({"code": "missing_type", "message": "Required field `type` is missing."})

        for field in ["title", "description", "resource", "timestamp"]:
            if field in self.fields and (not isinstance(self.fields[field], str) or not self.fields[field].strip()):
                issues.append({"code": f"invalid_{field}", "message": f"Field `{field}` must be a non-empty string."})

        return {"valid": len(issues) == 0, "issues": issues}
```

### 2. Index Synchronization Port

The index synchronization algorithm recursively traverses the directory tree of a wiki and synchronizes the index for each directory:

```python
import os

class IndexSynchronizer:
    def __init__(self, backend, output_mode, labels, concept_type):
        self.backend = backend
        self.output_mode = output_mode
        self.labels = labels
        self.concept_type = concept_type

    def synchronize_directory(self, directory, root):
        files = []
        directories = []

        for entry in directory.entries:
            name = os.path.basename(entry.name)
            if not name or name.startswith(".") or not name.endswith(".md"):
                continue

            if entry.is_dir:
                directories.append({"href": f"{os.path.basename(entry.name)}/", "label": name})
                continue

            files.append({"description": "", "href": entry.name, "label": name})

        index = self._build_index(files, directories)
        self._write_index(directory.path, index)

    def _build_index(self, files, directories):
        return {"files": files, "directories": directories}

    def _write_index(self, path, index):
        # Write index JSON or YAML file to storage
        pass
```

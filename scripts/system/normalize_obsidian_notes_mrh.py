#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/normalize_obsidian_notes_mrh.py"
# purpose: "Normalize all Obsidian notes to canonical Dual-Reader standard: Frontmatter at line 1, MRH header in HTML comment (gray/compact)."
# canonical_source: true
# alters_files: ["docs/notes/**/*.md"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "Antigravity (Mentor & Chief Architect) & DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
import sys
from pathlib import Path

def normalize_note(file_path: Path, dry_run: bool = False) -> bool:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    
    # 1. Match MRH header block (either <!-- ... --> or # ... or // ...)
    mrh_pattern = re.compile(
        r'(?:<!--\s*)?(?:#\s*|//\s*)?---\s*DNK-MRH-HEADER\s*---.*?(?:#\s*|//\s*)?---\s*END DNK-MRH-HEADER\s*(?:---|-->|---\s*-->)?',
        re.DOTALL
    )
    
    mrh_match = mrh_pattern.search(content)
    if not mrh_match:
        return False

    raw_mrh = mrh_match.group(0)
    
    # Extract clean lines of MRH (strip <!--, -->, #, //, and header delimiters)
    mrh_lines = []
    for line in raw_mrh.splitlines():
        l = line.strip()
        if "DNK-MRH-HEADER" in l:
            continue
        l = re.sub(r"^<!--\s*", "", l)
        l = re.sub(r"\s*-->$", "", l)
        l = re.sub(r"^(#|//)\s*", "", l)
        if l:
            mrh_lines.append(l)

    clean_mrh = "<!-- --- DNK-MRH-HEADER ---\n" + "\n".join(mrh_lines) + "\n--- END DNK-MRH-HEADER -->"
    
    # Remove raw MRH from content to parse frontmatter and body cleanly
    content_without_mrh = content[:mrh_match.start()] + content[mrh_match.end():]
    
    # Check if there is YAML frontmatter in content_without_mrh
    # It might be at the start, or preceded by blank lines
    fm_pattern = re.compile(r'^\s*---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    fm_match = fm_pattern.search(content_without_mrh)
    
    if fm_match:
        frontmatter = fm_match.group(1).strip()
        body = content_without_mrh[fm_match.end():].lstrip()
        new_content = f"---\n{frontmatter}\n---\n\n{clean_mrh}\n\n{body}"
    else:
        # Check if there is any --- block anywhere
        any_fm_pattern = re.compile(r'\n---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        any_fm_match = any_fm_pattern.search(content_without_mrh)
        if any_fm_match:
            frontmatter = any_fm_match.group(1).strip()
            rest = content_without_mrh[:any_fm_match.start()] + content_without_mrh[any_fm_match.end():]
            body = rest.lstrip()
            new_content = f"---\n{frontmatter}\n---\n\n{clean_mrh}\n\n{body}"
        else:
            # Note without frontmatter
            body = content_without_mrh.lstrip()
            new_content = f"{clean_mrh}\n\n{body}"

    # Normalize trailing newline
    if not new_content.endswith("\n"):
        new_content += "\n"

    if new_content == content:
        return False
        
    if not dry_run:
        file_path.write_text(new_content, encoding="utf-8")
        
    return True

def main():
    dry_run = "--dry-run" in sys.argv
    repo_root = Path(__file__).resolve().parent.parent.parent
    notes_dir = repo_root / "docs" / "notes"
    
    if not notes_dir.exists():
        print(f"❌ Notes directory not found at {notes_dir}")
        sys.exit(1)
        
    modified = 0
    total = 0
    
    for note_path in sorted(notes_dir.glob("**/*.md")):
        if ".obsidian" in str(note_path):
            continue
        total += 1
        changed = normalize_note(note_path, dry_run=dry_run)
        if changed:
            modified += 1
            rel_path = note_path.relative_to(repo_root)
            print(f"✨ {'[DRY-RUN] Would normalize' if dry_run else 'Normalized'}: {rel_path}")

    print(f"\n📊 Summary: {modified}/{total} notes normalized (dry_run={dry_run}).")

if __name__ == "__main__":
    main()

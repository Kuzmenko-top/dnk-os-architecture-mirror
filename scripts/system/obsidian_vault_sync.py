#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/obsidian_vault_sync.py"
# purpose: "Bidirectional sync between in-repo docs/notes SSOT and external Obsidian Vault (~/Documents/DNK_HUB My Notes)."
# canonical_source: true
# alters_files: ["docs/notes/**"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class ObsidianVaultSync:
    """
    Synchronizes architectural notes (ADRs, tasks, ideas) between the in-repo
    SSOT (docs/notes/) and the external Obsidian Vault (~/Documents/DNK_HUB My Notes).
    """

    IGNORED_DIRS = {".obsidian", ".git", ".trash", "__pycache__"}
    IGNORED_FILES = {".DS_Store"}

    def __init__(
        self,
        repo_notes_dir: Optional[Path] = None,
        vault_dir: Optional[Path] = None,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.repo_notes_dir = repo_notes_dir or (self.repo_root / "docs" / "notes")
        self.dry_run = dry_run
        self.verbose = verbose

        # Determine vault directory
        self.vault_dir = self._resolve_vault_dir(vault_dir)

    def _resolve_vault_dir(self, override_dir: Optional[Path]) -> Optional[Path]:
        if override_dir:
            return Path(override_dir).expanduser().resolve()

        env_dir = os.environ.get("OBSIDIAN_VAULT_DIR")
        if env_dir:
            return Path(env_dir).expanduser().resolve()

        # Check Obsidian desktop app configuration for registered vaults
        obsidian_app_json = Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
        if obsidian_app_json.exists():
            try:
                import json
                app_config = json.loads(obsidian_app_json.read_text(encoding="utf-8"))
                vaults = app_config.get("vaults", {})
                for v in vaults.values():
                    v_path = Path(v.get("path", "")).resolve()
                    if v_path == self.repo_notes_dir.resolve():
                        return v_path
                    if v_path.exists() and "DNK_HUB" in v_path.name:
                        return v_path
            except Exception:
                pass

        home = Path.home()
        candidates = [
            home / "Documents" / "DNK_HUB My Notes" / "DNK_HUB My Notes",
            home / "Documents" / "DNK_HUB My Notes",
        ]

        for cand in candidates:
            if cand.exists() and cand.is_dir():
                return cand.resolve()

        return None

    @staticmethod
    def _file_hash(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _collect_markdown_files(self, base_dir: Path) -> Dict[str, Path]:
        files_map: Dict[str, Path] = {}
        if not base_dir.exists():
            return files_map

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            for file in files:
                if file in self.IGNORED_FILES:
                    continue
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(base_dir).as_posix()
                    files_map[rel_path] = full_path
        return files_map

    def sync(self, direction: str = "bidirectional") -> Dict[str, int]:
        stats = {
            "copied_to_vault": 0,
            "copied_to_repo": 0,
            "unchanged": 0,
            "conflicts": 0,
        }

        if not self.vault_dir or not self.vault_dir.exists():
            print("ℹ️ External Obsidian Vault directory not found. In-repo docs/notes/ remains SSOT.")
            return stats

        if self.vault_dir == self.repo_notes_dir.resolve():
            repo_files = self._collect_markdown_files(self.repo_notes_dir)
            stats["unchanged"] = len(repo_files)
            print(f"✨ Native SSOT Vault Active: Obsidian desktop app is directly opened on {self.repo_notes_dir}.")
            print(f"   -> Zero-copy sync: {len(repo_files)} notes live and instantly accessible in Obsidian.")
            return stats

        if not self.repo_notes_dir.exists():
            if not self.dry_run:
                self.repo_notes_dir.mkdir(parents=True, exist_ok=True)

        repo_files = self._collect_markdown_files(self.repo_notes_dir)
        vault_files = self._collect_markdown_files(self.vault_dir)

        all_keys: Set[str] = set(repo_files.keys()) | set(vault_files.keys())

        for rel_key in sorted(all_keys):
            repo_path = repo_files.get(rel_key)
            vault_path = vault_files.get(rel_key)

            dest_repo = self.repo_notes_dir / rel_key
            dest_vault = self.vault_dir / rel_key

            if repo_path and not vault_path:
                # Exists only in repo
                if direction in ("bidirectional", "to-vault"):
                    if self.verbose:
                        print(f"  [Repo -> Vault] + {rel_key}")
                    if not self.dry_run:
                        dest_vault.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(repo_path, dest_vault)
                    stats["copied_to_vault"] += 1

            elif vault_path and not repo_path:
                # Exists only in vault
                if direction in ("bidirectional", "to-repo"):
                    if self.verbose:
                        print(f"  [Vault -> Repo] + {rel_key}")
                    if not self.dry_run:
                        dest_repo.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(vault_path, dest_repo)
                    stats["copied_to_repo"] += 1

            elif repo_path and vault_path:
                # Exists in both: compare hash
                repo_hash = self._file_hash(repo_path)
                vault_hash = self._file_hash(vault_path)

                if repo_hash == vault_hash:
                    stats["unchanged"] += 1
                    continue

                # Files differ: compare modification time
                repo_mtime = repo_path.stat().st_mtime
                vault_mtime = vault_path.stat().st_mtime

                if direction == "to-vault":
                    if self.verbose:
                        print(f"  [Repo -> Vault] ~ {rel_key} (forced to-vault)")
                    if not self.dry_run:
                        shutil.copy2(repo_path, dest_vault)
                    stats["copied_to_vault"] += 1
                elif direction == "to-repo":
                    if self.verbose:
                        print(f"  [Vault -> Repo] ~ {rel_key} (forced to-repo)")
                    if not self.dry_run:
                        shutil.copy2(vault_path, dest_repo)
                    stats["copied_to_repo"] += 1
                else:  # bidirectional: newer wins
                    if repo_mtime > vault_mtime:
                        if self.verbose:
                            print(f"  [Repo -> Vault] ~ {rel_key} (repo is newer)")
                        if not self.dry_run:
                            shutil.copy2(repo_path, dest_vault)
                        stats["copied_to_vault"] += 1
                    else:
                        if self.verbose:
                            print(f"  [Vault -> Repo] ~ {rel_key} (vault is newer)")
                        if not self.dry_run:
                            shutil.copy2(vault_path, dest_repo)
                        stats["copied_to_repo"] += 1

        return stats


def main():
    parser = argparse.ArgumentParser(description="Synchronize Obsidian ADRs and notes with in-repo SSOT.")
    parser.add_argument(
        "--direction",
        choices=["bidirectional", "to-vault", "to-repo"],
        default="bidirectional",
        help="Sync direction (default: bidirectional)",
    )
    parser.add_argument("--vault-dir", type=Path, default=None, help="Path to external Obsidian Vault")
    parser.add_argument("--repo-notes-dir", type=Path, default=None, help="Path to in-repo notes directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    syncer = ObsidianVaultSync(
        repo_notes_dir=args.repo_notes_dir,
        vault_dir=args.vault_dir,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    print("==================================================")
    print("📓 DNK OS Obsidian Vault Sync Engine")
    print("==================================================")
    print(f"📁 In-repo Notes (SSOT): {syncer.repo_notes_dir}")
    print(f"📁 External Vault:      {syncer.vault_dir or 'Not found'}")
    print(f"🔄 Direction:           {args.direction}")
    if args.dry_run:
        print("⚠️ DRY RUN MODE: No files will be modified.")
    print("--------------------------------------------------")

    stats = syncer.sync(direction=args.direction)

    print(f"✅ Sync complete:")
    print(f"   -> Copied to Vault: {stats['copied_to_vault']}")
    print(f"   -> Copied to Repo:  {stats['copied_to_repo']}")
    print(f"   == Unchanged:       {stats['unchanged']}")
    print("==================================================")


if __name__ == "__main__":
    main()

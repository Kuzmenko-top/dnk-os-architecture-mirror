# --- DNK-MRH-HEADER ---
# mrh_id: "test_path_hygiene"
# purpose: "Automated test to verify absolute path hygiene and prevent hardcoded absolute host paths"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.1"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]  # корінь репо

# Шаблон для заборонених абсолютних шляхів користувача
USER_PATH_PATTERN = re.compile(r"/Users/[A-Za-z0-9._-]+/")

# Файли/директорії, які варто сканувати
SCAN_DIRS = [
    ROOT / "docs",
    ROOT / "services",
    ROOT / "core",
    ROOT / "scripts",
]

ALLOWED_PLACEHOLDER = "/Users/<username>/"


def iter_text_files():
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            # Skip virtual environments, node_modules, upstream vendor tests, runtime caches/sessions, checkpoints, audit logs, and external skills
            if any(part.startswith(".") or "venv" in part or "node_modules" in part or "hermes_agent" in part or "cache" in part or "sessions" in part or "checkpoints" in part or "skills" in part or "audit" in part for part in path.parts) or path.name in ["processes.json", "hermes.json"]:
                continue
            # Скануємо тільки текстові файли
            if path.suffix in [".md", ".py", ".yaml", ".yml", ".toml", ".json", ".sh"]:
                yield path


def test_no_raw_user_absolute_paths():
    """
    Перевіряє, що в коді та документації немає жорстко захардкожених /Users/<name>/ шляхів.
    Допускається тільки універсальний плейсхолдер /Users/<username>/.
    """
    bad_hits = []

    for path in iter_text_files():
        # Skip checking the test file itself or any external virtual env files (already skipped by SCAN_DIRS)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in USER_PATH_PATTERN.finditer(text):
                snippet = match.group(0)
                bad_hits.append((path.relative_to(ROOT), snippet))
        except Exception:
            pass

    assert not bad_hits, (
        "Found forbidden absolute user paths.\n" +
        "\n".join(f"{p}: {s}" for p, s in bad_hits)
    )

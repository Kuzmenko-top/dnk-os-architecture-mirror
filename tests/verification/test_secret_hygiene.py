# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_secret_hygiene"
# purpose: "Regression suite ensuring strict zero-secret leakage across frontend code, public bundles, and env vars"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import re
from pathlib import Path

def test_no_hardcoded_secrets_in_web():
    """Verify that no frontend source files contain hardcoded API keys, JWT secrets, or leaked tokens."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    web_dir = repo_root / "apps" / "web"
    
    forbidden_patterns = [
        re.compile(r"dnk_secret_prod_key_2026", re.IGNORECASE),
        re.compile(r"X-API-Key['\"]\s*:\s*['\"][a-zA-Z0-9_\-]+['\"]", re.IGNORECASE),
        re.compile(r"NEXT_PUBLIC_.*(?:SECRET|KEY|PASSWORD|TOKEN)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
        re.compile(r"postgresql://\w+:\w+@", re.IGNORECASE),
    ]

    extensions = {".ts", ".tsx", ".js", ".jsx", ".json", ".mjs", ".env", ".env.local", ".env.production"}

    leaks = []
    for root, dirs, files in os.walk(web_dir):
        # Skip build artifacts and node_modules
        if "node_modules" in root or ".next" in root:
            continue
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in extensions or file.startswith(".env"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    for pattern in forbidden_patterns:
                        matches = pattern.findall(content)
                        if matches:
                            leaks.append(f"{file_path.relative_to(repo_root)}: matched {pattern.pattern}")
                except Exception:
                    pass

    assert not leaks, f"Hardcoded secrets detected in frontend source:\n" + "\n".join(leaks)

def test_next_public_env_hygiene():
    """Verify that NEXT_PUBLIC_ variables do not leak backend secrets."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    env_files = list(repo_root.glob("**/.env*"))

    suspicious_public_keys = []
    for env_file in env_files:
        if "node_modules" in str(env_file) or ".next" in str(env_file):
            continue
        try:
            lines = env_file.read_text(encoding="utf-8").splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("NEXT_PUBLIC_") and any(secret_term in line.upper() for secret_term in ["SECRET", "PRIVATE", "KEY", "TOKEN", "PASSWORD", "DATABASE_URL", "DSN"]):
                    # If it's a real value assignment (not just empty template or public harmless config)
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if v.strip() and v.strip() != '""' and v.strip() != "''":
                            suspicious_public_keys.append(f"{env_file}: {line}")
        except Exception:
            pass

    assert not suspicious_public_keys, f"Insecure NEXT_PUBLIC secrets detected:\n" + "\n".join(suspicious_public_keys)

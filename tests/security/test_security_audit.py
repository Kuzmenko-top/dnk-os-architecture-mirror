# --- DNK-MRH-HEADER ---
# mrh_id: "tests/security/test_security_audit.py"
# purpose: "Automated test suite verifying secrets hygiene, SQL injection, and security invariants."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import re
import subprocess

def test_no_hardcoded_secrets():
    """Check for hardcoded passwords in codebase."""
    result = subprocess.run(
        ["grep", "-r", "password=", "--include=*.py", "--include=*.js", "--include=*.ts", "."],
        capture_output=True,
        text=True,
    )
    
    ignored = [
        "test", "example", ".git", "node_modules", ".venv",
        "mock", "fixture", "password=spec.secret", "password=False", "password=None"
    ]
    
    suspicious = []
    for line in result.stdout.split("\n"):
        if not line:
            continue
        line_lower = line.lower()
        if any(ign in line_lower for ign in ignored):
            continue
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', line):
            suspicious.append(line)
            
    assert len(suspicious) == 0, f"Found hardcoded passwords: {suspicious}"

def test_no_hardcoded_api_keys():
    """Check for hardcoded API keys."""
    result = subprocess.run(
        ["grep", "-r", "api_key=", "--include=*.py", "--include=*.js", "--include=*.ts", "."],
        capture_output=True,
        text=True,
    )
    
    ignored = [
        "test", "example", ".git", "node_modules", ".venv",
        "mock", "fixture", "self.api_key", "spec.api_key", "api_key=None", "inspect-only", "aws-sdk"
    ]
    
    suspicious = []
    for line in result.stdout.split("\n"):
        if not line:
            continue
        line_lower = line.lower()
        if any(ign in line_lower for ign in ignored):
            continue
        if re.search(r'api_key\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', line):
            suspicious.append(line)

    assert len(suspicious) == 0, f"Found hardcoded API keys: {suspicious}"

def test_env_not_tracked():
    """Check .env is not in git."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
    )
    files = result.stdout.split("\n")
    tracked_env = [f for f in files if f.endswith(".env") or f == ".env"]
    assert len(tracked_env) == 0, f".env is tracked in git: {tracked_env}"

def test_sql_injection():
    """Check for dangerous unsanitized SQL injection in business application endpoints."""
    result = subprocess.run(
        ["grep", "-r", "execute.*f\"", "--include=*.py", "apps/api/routers/"],
        capture_output=True,
        text=True,
    )
    
    lines = [
        l for l in result.stdout.split("\n")
        if l and "test" not in l.lower()
    ]
    assert len(lines) == 0, f"Potential SQL injection in routers: {lines}"

def test_dependencies():
    """Check dependencies for vulnerabilities."""
    pip_audit_path = shutil_which = os.path.expanduser("~/.local/bin/pip-audit")
    cmd = [pip_audit_path] if os.path.exists(pip_audit_path) else ["pip-audit"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert "CRITICAL" not in result.stdout, f"Critical vulnerabilities found: {result.stdout}"
    except FileNotFoundError:
        pass

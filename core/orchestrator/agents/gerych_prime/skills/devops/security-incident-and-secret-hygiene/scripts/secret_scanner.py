#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "skills/devops/security-incident-and-secret-hygiene/scripts/secret_scanner.py"
# purpose: "Fail-closed centralized secret scanning SSOT for local, pre-commit, and CI gates."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
import sys
from typing import Dict, List, Tuple

# SSOT Secret Pattern Registry with word boundaries
SECRET_PATTERNS: Dict[str, str] = {
    "github_classic_pat": r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    "github_fine_grained_pat": r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
    "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
    "google_api_key": r"\bAIza[0-9A-Za-z_-]{20,}\b",
    "openai_or_compatible_key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "shopify_admin_token": r"\bshpat_[A-Za-z0-9]+\b",
    "shopify_secret": r"\bshpss_[A-Za-z0-9]+\b",
}

SAFE_TEST_PLACEHOLDERS = [
    "ghp_example_",
    "gho_example_",
    "AKIAEXAMPLE",
    "AIzaSyExample",
    "sk-example-test-key",
    "shpat_example_",
    "shpss_example_",
    "[REDACTED",
]

def redact_secret(token: str) -> str:
    """Mask secret value preserving only prefix and short suffix."""
    if len(token) <= 8:
        return "[REDACTED]"
    prefix = token[:4]
    suffix = token[-4:]
    return f"{prefix}...[REDACTED]...{suffix}"

def is_safe_placeholder(match: str) -> bool:
    """Check if matched string is an explicitly safe test placeholder."""
    return any(p in match for p in SAFE_TEST_PLACEHOLDERS)

def scan_text(text: str, filename: str = "<stdin>") -> List[Tuple[str, int, str, str]]:
    """
    Scan text content against SECRET_PATTERNS.
    Returns list of tuples: (pattern_name, line_number, redacted_fingerprint, filename)
    """
    findings = []
    lines = text.splitlines()
    for line_idx, line in enumerate(lines, start=1):
        for pat_name, pat_regex in SECRET_PATTERNS.items():
            matches = re.finditer(pat_regex, line)
            for m in matches:
                secret_str = m.group(0)
                if not is_safe_placeholder(secret_str):
                    findings.append((pat_name, line_idx, redact_secret(secret_str), filename))
    return findings

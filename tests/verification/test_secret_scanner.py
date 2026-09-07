# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_secret_scanner.py"
# purpose: "Comprehensive unit tests for Secret Scanner SSOT v1.2.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.1"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from pathlib import Path
import subprocess
import sys
import pytest

# Import scanner functions from scripts
scripts_dir = Path(__file__).resolve().parents[2] / "scripts" / "system"
sys.path.insert(0, str(scripts_dir))

from secret_scanner import (
    Finding,
    SECRET_PATTERNS,
    is_safe_placeholder,
    redact_secret,
    scan_content,
    scan_text,
)


def test_github_classic_pat_pattern_contract() -> None:
    assert SECRET_PATTERNS["github_classic_pat"] == (
        r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"
    )


def test_github_classic_pat_requires_literal_underscore() -> None:
    valid = ("ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890")
    invalid = "ghpabcdefghijklmnopqrstuvwxyz1234567890"

    valid_findings = scan_text(valid, source="valid.txt")
    invalid_findings = scan_text(invalid, source="invalid.txt")

    assert any(item.kind == "github_classic_pat" for item in valid_findings)
    assert not any(item.kind == "github_classic_pat" for item in invalid_findings)



@pytest.mark.parametrize(
    "label,candidate",
    [
        ("ghp", ("ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890")),
        ("gho", "gho_abcdefghijklmnopqrstuvwxyz1234567890"),
        ("ghs", "ghs_abcdefghijklmnopqrstuvwxyz1234567890"),
        ("ghu", "ghu_abcdefghijklmnopqrstuvwxyz1234567890"),
        ("ghr", "ghr_abcdefghijklmnopqrstuvwxyz1234567890"),
    ],
)
def test_detects_github_classic_tokens(label: str, candidate: str) -> None:
    findings = scan_text(candidate, source=f"{label}.txt")
    assert any(item.kind == "github_classic_pat" for item in findings)


@pytest.mark.parametrize(
    "malformed_candidate",
    [
        "ghpABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
        "ghp-example-placeholder",
        "ghp_",
        ("xghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"),
    ],
)
def test_malformed_strings_not_detected_as_github_classic_pat(malformed_candidate: str) -> None:
    findings = scan_text(malformed_candidate, source="malformed.txt")
    assert not any(item.kind == "github_classic_pat" for item in findings)


def test_redaction_never_returns_full_secret() -> None:
    candidate = ("ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890")
    findings = scan_text(candidate, source="fixture.txt")

    assert findings
    rendered = findings[0].redacted_value

    assert candidate not in rendered
    assert "[REDACTED]" in rendered


def test_placeholder_is_explicitly_ignored() -> None:
    text = "GH_TOKEN=ghp_example_placeholder_not_a_real_token"
    findings = scan_text(text, source="example.env")

    assert findings == []


def test_github_fine_grained_pat_detection() -> None:
    candidate = "github_pat_11AAAAAA00000000000000_1234567890abcdefghijklmnopqrstuvwxyz"
    findings = scan_text(f"export PAT={candidate}", source="test_pat.sh")
    assert len(findings) == 1
    assert findings[0].kind == "github_fine_grained_pat"
    assert "[REDACTED]" in findings[0].redacted_value


def test_aws_google_openai_shopify_detection() -> None:
    samples = [
        ("AKIA" + "1234567890ABCDEF", "aws_access_key"),
        ("AIza1234567890abcdef1234567890abcdef", "google_api_key"),
        ("sk-1234567890abcdef1234567890abcdef", "openai_or_compatible_key"),
        ("shpat_" + "1234567890abcdef1234567890abcdef", "shopify_admin_token"),
        ("shpss_" + "1234567890abcdef1234567890abcdef", "shopify_secret"),
    ]
    for token, expected_kind in samples:
        findings = scan_text(f"KEY = '{token}'", source="test_keys.env")
        assert len(findings) == 1, f"Failed for {expected_kind}: {token}"
        assert findings[0].kind == expected_kind


def test_finding_dataclass_interface() -> None:
    candidate = "gho_abcdefghijklmnopqrstuvwxyz1234567890"
    findings = scan_text(candidate, source="test.txt")
    assert findings
    f = findings[0]
    assert f.kind == "github_classic_pat"
    assert f.type == "github_classic_pat"
    assert f["kind"] == "github_classic_pat"
    assert f["type"] == "github_classic_pat"
    assert f["source"] == "test.txt"
    assert f.redacted_value == f.fingerprint


def test_cli_fail_closed_exit_code(tmp_path: Path) -> None:
    scanner_path = scripts_dir / "secret_scanner.py"
    # Run with text containing synthetic token
    cmd = [
        sys.executable,
        str(scanner_path),
        "--mode",
        "text",
        "--target",
        ("export GH=" + "ghp_" + "abcdefghijklmnopqrstuvwxyz1234567890"),
        "--fail-on-finding",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "[FAIL-CLOSED]" in res.stdout or "[FAIL-CLOSED]" in res.stderr

# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/check_license_policy.py"
# purpose: "Two-Track License Firewall Policy Checker and Clean-Room Architecture Spec Generator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Track 1: Permissive licenses (Auto-Approved for Direct Assimilation)
PERMISSIVE_LICENSES = {
    "mit", "apache-2.0", "apache 2.0", "bsd-2-clause", "bsd-3-clause", 
    "bsd", "isc", "cc0-1.0", "unlicense", "psf", "mit-0", "0bsd", "zlib"
}

# Track 2: Restrictive / Copyleft licenses (Require Clean-Room Spec & Synthetic Architecture)
RESTRICTIVE_LICENSES = {
    "gpl-2.0", "gpl-3.0", "gpl", "agpl-3.0", "agpl", "lgpl-2.1", "lgpl-3.0",
    "lgpl", "mpl-2.0", "sspl", "eupl-1.2", "cc-by-sa-4.0", "gpl-2.0-only", "gpl-3.0-only"
}


def normalize_license_key(license_str: str) -> str:
    """Normalize license identifier string."""
    if not license_str:
        return "unknown"
    return license_str.strip().lower().replace("_", "-")


def classify_license(license_str: str) -> Tuple[str, str]:
    """
    Classify license into Track 1 (Permissive), Track 2 (Restrictive/Copyleft), or Unknown.
    Returns: (track_name, rationale)
    """
    norm = normalize_license_key(license_str)
    
    for perm in PERMISSIVE_LICENSES:
        if perm in norm or norm in perm:
            return ("Track 1 (Permissive)", f"Permissive license '{license_str}' allows direct template/component assimilation.")
            
    for rest in RESTRICTIVE_LICENSES:
        if rest in norm or norm in rest:
            return ("Track 2 (Copyleft/Clean-Room)", f"Restrictive license '{license_str}' requires Clean-Room reverse engineering and synthetic architecture.")
            
    return ("Unknown/Review", f"License '{license_str}' requires manual compliance triage.")


def generate_clean_room_spec(package_name: str, license_name: str, version: str = "latest", output_dir: str = "docs/tech/clean_room") -> str:
    """Generate DNK-CLEANROOM specification document for copyleft dependencies."""
    os.makedirs(output_dir, exist_ok=True)
    spec_id = f"DNK-CLEANROOM-{package_name.upper().replace('-', '_').replace('.', '_')}"
    file_path = os.path.join(output_dir, f"{spec_id}.md")
    
    content = f"""# --- DNK-MRH-HEADER ---
# mrh_id: "{output_dir}/{spec_id}.md"
# purpose: "Clean-Room Reverse Engineering & Architecture Synthesis Specification for {package_name} ({license_name})."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Clean-Room Specification: {spec_id}

## 1. Compliance Audit & Isolation Rationale
- **Target Component / Library:** `{package_name}` (Version: `{version}`)
- **Detected License:** `{license_name}` (Track 2: Copyleft / Restrictive)
- **Isolation Policy:** Direct source inclusion is strictly forbidden to preserve permissive MIT/Apache-2.0 IP boundary of DNK OS.
- **Assigned Swarm Builder:** `gerych_builder` (Clean-Room Synthesizer)
- **Assigned Swarm Auditor:** `gerych_auditor` (AST Isolation & License Guard)

## 2. Functional Abstract & AST Signatures Required
1. **Interface Contract:**
   - Define abstract Pydantic / TypeScript domain models representing core input/output boundaries.
2. **Behavioral Protocol:**
   - Re-implement core algorithmic primitives using pure standard libraries and permissive dependencies.
3. **Zero-Derivative Invariant:**
   - No direct copy-pasting of original code or comments.

## 3. Verification & Acceptance Criteria
- [ ] 100% test coverage with clean-room test fixtures.
- [ ] AST similarity scan confirms zero verbatim code reuse.
- [ ] Registered in `docs/tech/sota_assimilation/` registry.
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return file_path


def parse_scancode_or_custom_report(report_path: str) -> List[Dict[str, Any]]:
    """Parse Scancode JSON, pip-licenses JSON, or custom license manifest."""
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report file not found: {report_path}")
        
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    
    # Handle Scancode format
    if "files" in data and isinstance(data["files"], list):
        for f in data["files"]:
            path = f.get("path", "unknown")
            licenses = f.get("licenses", [])
            for lic in licenses:
                lic_key = lic.get("key") or lic.get("spdx_license_key") or "unknown"
                results.append({
                    "package": path,
                    "license": lic_key,
                    "version": "scancode"
                })
                
    # Handle array of dependencies (pip-licenses or custom format)
    elif isinstance(data, list):
        for item in data:
            name = item.get("Name") or item.get("name") or item.get("package") or "unknown"
            lic = item.get("License") or item.get("license") or "unknown"
            ver = item.get("Version") or item.get("version") or "unknown"
            results.append({
                "package": name,
                "license": lic,
                "version": ver
            })
            
    # Handle simple dict format {pkg: license}
    elif isinstance(data, dict):
        for pkg, lic in data.items():
            results.append({
                "package": pkg,
                "license": lic if isinstance(lic, str) else lic.get("license", "unknown"),
                "version": lic.get("version", "unknown") if isinstance(lic, dict) else "unknown"
            })
            
    return results


def run_license_firewall(
    report_path: str,
    strict: bool = False,
    cleanroom_dir: str = "docs/tech/clean_room"
) -> Dict[str, Any]:
    """Execute Two-Track License Policy Audit."""
    entries = parse_scancode_or_custom_report(report_path)
    
    track1_approved = []
    track2_copyleft = []
    unknown_review = []
    
    for entry in entries:
        pkg = entry["package"]
        lic = entry["license"]
        ver = entry.get("version", "unknown")
        
        track, rationale = classify_license(lic)
        record = {
            "package": pkg,
            "license": lic,
            "version": ver,
            "track": track,
            "rationale": rationale
        }
        
        if "Track 1" in track:
            track1_approved.append(record)
        elif "Track 2" in track:
            spec_file = generate_clean_room_spec(pkg, lic, ver, cleanroom_dir)
            record["clean_room_spec"] = spec_file
            track2_copyleft.append(record)
        else:
            unknown_review.append(record)
            
    is_blocked = strict and (len(track2_copyleft) > 0 or len(unknown_review) > 0)
    
    summary = {
        "status": "BLOCKED" if is_blocked else "PASSED",
        "total_scanned": len(entries),
        "track1_approved_count": len(track1_approved),
        "track2_copyleft_count": len(track2_copyleft),
        "unknown_review_count": len(unknown_review),
        "track1_approved": track1_approved,
        "track2_copyleft": track2_copyleft,
        "unknown_review": unknown_review
    }
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="DNK OS Two-Track License Firewall Checker")
    parser.add_argument("report", help="Path to scancode or license JSON report")
    parser.add_argument("--strict", action="store_true", help="Fail with exit code 1 if Track 2 or Unknown licenses are detected")
    parser.add_argument("--cleanroom-dir", default="docs/tech/clean_room", help="Directory for Clean-Room spec output")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    
    args = parser.parse_args()
    
    try:
        result = run_license_firewall(args.report, strict=args.strict, cleanroom_dir=args.cleanroom_dir)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 60)
            print("🛡️  DNK OS Two-Track License Firewall Report")
            print("=" * 60)
            print(f"Status: {result['status']}")
            print(f"Total Components Scanned: {result['total_scanned']}")
            print(f"✅ Track 1 (Permissive - Approved): {result['track1_approved_count']}")
            print(f"⚠️ Track 2 (Copyleft - Clean-Room Required): {result['track2_copyleft_count']}")
            print(f"❓ Unknown / Needs Review: {result['unknown_review_count']}")
            print("=" * 60)
            
            if result['track2_copyleft_count'] > 0:
                print("\n[Track 2 Clean-Room Specs Generated]:")
                for item in result['track2_copyleft']:
                    print(f" - {item['package']} ({item['license']}) -> {item.get('clean_room_spec')}")
                    
            if result['status'] == "BLOCKED":
                sys.exit(1)
                
    except Exception as e:
        print(f"Error executing license firewall: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

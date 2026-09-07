# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/scripts/pattern_auditor.py"
# purpose: "Audit the local agentic patterns registry and compile audit reports (Object-Oriented Suite)."
# canonical_source: true
# alters_files: ["docs/reports/PATTERN_AUDIT_REPORT.md"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import sys
import time
from pathlib import Path

# Setup python path to find core/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from core.pattern_synthesizer import PatternSynthesizer

REPORT_PATH = "docs/reports/PATTERN_AUDIT_REPORT.md"

class PatternAuditor:
    def __init__(self, registry_path: str = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md", schema_path: str = "docs/schemas/agentic_pattern_schema.json"):
        self.registry_path = registry_path
        self.schema_path = schema_path
        self.synthesizer = PatternSynthesizer(registry_path=registry_path, schema_path=schema_path)

    def run_audit(self) -> dict:
        start_time = time.perf_counter()
        errors = []
        
        # 1. Schema validity check
        schema_validity = "PASSED"
        for p in self.synthesizer.patterns:
            try:
                self.synthesizer.validate_pattern(p)
            except Exception as e:
                schema_validity = "FAILED"
                errors.append(f"Pattern {p.get('id', 'Unknown')} failed schema validation: {e}")

        # 2. Deduplication check
        deduplication = "PASSED"
        ids = [p.get("id") for p in self.synthesizer.patterns if p.get("id")]
        if len(ids) != len(set(ids)):
            deduplication = "FAILED"
            errors.append("Duplicate Pattern IDs found in registry.")

        # 3. MRH Compliance
        mrh_compliance = "PASSED"
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r", encoding="utf-8") as f:
                header_text = f.read(500)
            if "DNK-MRH-HEADER" not in header_text:
                mrh_compliance = "FAILED"
                errors.append("Registry file lacks the mandatory DNK-MRH-HEADER.")
        else:
            mrh_compliance = "FAILED"
            errors.append("Registry file not found.")

        # 4. Performance Check (<0.05s lookup budget)
        duration = time.perf_counter() - start_time
        performance_check = "PASSED" if duration < 0.05 else "FAILED"
        if duration >= 0.05:
            errors.append(f"Audit lookup took {duration:.4f}s, exceeding 0.05s budget.")

        return {
            "schema_validity": schema_validity,
            "deduplication": deduplication,
            "mrh_compliance": mrh_compliance,
            "performance_check": performance_check,
            "errors": errors,
            "total_checked": len(self.synthesizer.patterns)
        }

    def generate_report(self, results: dict, output_path: str = REPORT_PATH) -> None:
        status = "PASSED" if len(results["errors"]) == 0 else "WARNINGS/ERRORS"
        
        report_lines = [
            "# Звіт автоматичного аудиту реєстру патернів",
            f"**Дата:** 2026-08-08  ",
            f"**Status:** {status}  ",
            "",
            "## Summary",
            f"- **Schema Validity:** {results['schema_validity']}",
            f"- **Deduplication Check:** {results['deduplication']}",
            f"- **MRH Compliance:** {results['mrh_compliance']}",
            f"- **Performance Check:** {results['performance_check']}",
            f"- **Total Patterns Scanned:** {results['total_checked']}",
            "",
            "## Validated Patterns List",
        ]

        for p in self.synthesizer.patterns:
            p_id = p.get("id") or p.get("pattern_id", "Unknown")
            p_name = p.get("name", "Unknown Name")
            p_type = p.get("type", "Unknown Type")
            report_lines.append(f"- **[{p_id}]** {p_name} (Type: {p_type})")

        if results["errors"]:
            report_lines.extend([
                "",
                "## Validation Errors",
            ])
            for err in results["errors"]:
                report_lines.append(f"- ❌ {err}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(chr(10).join(report_lines))

def run_audit(registry_path: str = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md", report_path: str = REPORT_PATH):
    auditor = PatternAuditor(registry_path=registry_path)
    results = auditor.run_audit()
    auditor.generate_report(results, output_path=report_path)
    print(f"Legacy wrapper: Audit completed. Report saved to {report_path}")

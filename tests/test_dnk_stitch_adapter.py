# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_dnk_stitch_adapter.py"
# purpose: "Unit tests for DNKStitchAdapter, DESIGN.md parser, WCAG AA linter, and Open Canvas DTOs."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-ENGINE-002"]
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import unittest
import asyncio
from core.adapters.dnk_stitch_adapter import (
    DNKStitchAdapter,
    DesignSystemTokenSpec,
    ColorTokens,
    ScreenNode,
    ScreenEdge,
    CanvasProjectGraph,
    parse_design_md,
    validate_wcag_contrast,
    calculate_contrast_ratio,
    export_to_tailwind_v4,
    export_to_dtcg_json
)

SAMPLE_DESIGN_MD = """---
version: 1.0.0
name: Heritage Test System
description: Test design system for DNK OS Open Canvas
colors:
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"
  background: "#FFFFFF"
components:
  card-dark:
    backgroundColor: "#1A1C1E"
    textColor: "#000000"
---

## Overview
Heritage design system test spec.
"""

class TestDNKStitchAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = DNKStitchAdapter(api_key="[REDACTED]")

    def test_stitch_adapter_initialization_and_list_projects(self):
        projects = asyncio.run(self.adapter.list_projects())
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["project_id"], "proj-main-001")

    def test_generate_screen_and_edge_linking(self):
        screen1 = asyncio.run(
            self.adapter.generate_screen("proj-main-001", "Home Screen", device_type="mobile")
        )
        self.assertIsNotNone(screen1.id)
        self.assertIn("Home Screen", screen1.title)

        screen2 = asyncio.run(
            self.adapter.generate_screen(
                "proj-main-001", "Details Screen", device_type="mobile", parent_screen_id=screen1.id
            )
        )
        self.assertIsNotNone(screen2.id)

        proj = asyncio.run(self.adapter.get_project("proj-main-001"))
        self.assertIsNotNone(proj)
        assert proj is not None
        self.assertEqual(len(proj.screens), 2)
        self.assertEqual(len(proj.edges), 1)
        self.assertEqual(proj.edges[0].source_screen_id, screen1.id)
        self.assertEqual(proj.edges[0].target_screen_id, screen2.id)

    def test_extract_design_system_from_url(self):
        ds = asyncio.run(self.adapter.extract_design_system_from_url("https://stitch.withgoogle.com"))
        self.assertIsInstance(ds, DesignSystemTokenSpec)
        self.assertEqual(ds.colors.primary, "#0F172A")

    def test_design_md_parser_and_exports(self):
        parsed = parse_design_md(SAMPLE_DESIGN_MD)
        self.assertEqual(parsed["frontmatter"]["name"], "Heritage Test System")
        self.assertIn("Heritage design system test spec.", parsed["markdown"])

        tw = export_to_tailwind_v4(parsed["frontmatter"])
        self.assertIn("@theme {", tw)
        self.assertIn("--color-primary: #1A1C1E;", tw)

        dtcg = export_to_dtcg_json(parsed["frontmatter"])
        self.assertIn("colors", dtcg)
        self.assertEqual(dtcg["colors"]["primary"]["$value"], "#1A1C1E")

    def test_wcag_contrast_linter(self):
        # #1A1C1E vs #FFFFFF is high contrast (>4.5)
        cr_high = calculate_contrast_ratio("#1A1C1E", "#FFFFFF")
        self.assertGreater(cr_high, 4.5)

        # #1A1C1E vs #000000 is low contrast (<4.5)
        cr_low = calculate_contrast_ratio("#1A1C1E", "#000000")
        self.assertLess(cr_low, 4.5)

        parsed = parse_design_md(SAMPLE_DESIGN_MD)
        findings = validate_wcag_contrast(parsed["frontmatter"])

        # card-dark has #1A1C1E bg and #000000 text -> should fail WCAG AA
        low_contrast_components = [f.get("component") for f in findings if f.get("component")]
        self.assertIn("card-dark", low_contrast_components)


if __name__ == "__main__":
    unittest.main()

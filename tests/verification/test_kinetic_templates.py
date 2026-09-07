# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_kinetic_templates.py"
# purpose: "Unit tests verifying Remotion kinetic video template generation and spec formatting."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from core.video.kinetic_templates import (
    kinetic_templates,
    KineticTemplateSpec,
    TemplateStyle,
)


def test_kinetic_template_generation():
    spec = KineticTemplateSpec(
        template_name="test_viral_reel",
        style=TemplateStyle.VIRAL_TIKTOK,
        title="DNK Ergo Chair X1",
        hook="Why 90% of Desk Workers Have Back Pain",
        price=299.0,
        original_price=450.0,
        cta_text="Claim 35% Discount Today",
        captions=["Ergonomic lumbar support", "Breathable matrix mesh", "Next-gen posture alignment"],
    )

    tsx_code = kinetic_templates.generate_viral_reel_tsx(spec)
    assert "ViralReelComposition" in tsx_code
    assert 'title = "DNK Ergo Chair X1"' in tsx_code
    assert "price = 299.0" in tsx_code
    assert "Why 90% of Desk Workers Have Back Pain" in tsx_code
    assert "Ergonomic lumbar support" in tsx_code
    assert "useVideoConfig" in tsx_code

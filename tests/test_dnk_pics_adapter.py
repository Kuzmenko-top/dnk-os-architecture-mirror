# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_dnk_pics_adapter.py"
# purpose: "Unit tests for DNKPicsAdapter (Google Pics / Nano Banana integration in DNK OS)."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-GOOGLE-PICS-ASSIMILATION"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import unittest
import asyncio
from core.adapters.dnk_pics_adapter import (
    DNKPicsAdapter,
    PicsGenerationRequest,
    PicsEditRequest,
    PicsTypographyEditRequest
)


class TestDNKPicsAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = DNKPicsAdapter(api_key="[REDACTED]", use_mock=True)

    def test_generate_image_mock(self):
        req = PicsGenerationRequest(prompt="E-commerce summer hero banner", aspect_ratio="16:9")
        res = asyncio.run(self.adapter.generate_image(req))
        self.assertIsNotNone(res.image_b64)
        self.assertEqual(res.mime_type, "image/png")
        self.assertTrue(res.metadata.get("mock"))

    def test_edit_image_mock(self):
        req = PicsEditRequest(base_image_b64="dGVzdA==", prompt="Remove background object")
        res = asyncio.run(self.adapter.edit_image(req))
        self.assertIsNotNone(res.image_b64)
        self.assertTrue(res.metadata.get("mock"))

    def test_edit_typography_mock(self):
        req = PicsTypographyEditRequest(
            base_image_b64="dGVzdA==",
            target_text="OLD SALE",
            replacement_text="NEW SALE"
        )
        res = asyncio.run(self.adapter.edit_typography(req))
        self.assertIsNotNone(res.image_b64)
        self.assertEqual(res.metadata.get("replacement_text"), "NEW SALE")

    def test_composite_images_mock(self):
        images = ["dGVzdDE=", "dGVzdDI="]
        res = asyncio.run(self.adapter.composite_images(images, "Blend product onto studio background"))
        self.assertIsNotNone(res.image_b64)
        self.assertEqual(res.metadata.get("reference_count"), 2)

    def test_upscale_image_mock(self):
        res = asyncio.run(self.adapter.upscale_image("dGVzdA==", factor=4))
        self.assertIsNotNone(res.image_b64)
        self.assertEqual(res.metadata.get("upscale_factor"), 4)


if __name__ == "__main__":
    unittest.main()

"""Release guard: the declared workbook layout must match the actual renderer."""
import json
import unittest
from pathlib import Path
from export_xlsx import HEADERS, SHOT_HEADERS

ROOT = Path(__file__).resolve().parents[1]

class LayoutContractTests(unittest.TestCase):
    def test_layout_matches_renderer_and_current_source_scope(self):
        layout = json.loads((ROOT / "assets" / "spoken-batch-layout.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "assets" / "kb-snapshot" / "release-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(layout["platform_columns"], len(HEADERS))
        self.assertEqual(layout["shooting_columns"], len(SHOT_HEADERS))
        self.assertEqual(layout["engine_contract_version"], "3.0.0")
        self.assertEqual(layout["knowledge_release"], policy["active_source_release"])
        self.assertEqual(layout["sample_scope"], "illustration_only")
        self.assertIs(layout["legacy_fallback"], False)
        self.assertEqual(layout["renderer"], "scripts/export_xlsx.py")

    def test_stale_16_column_contract_is_not_the_current_contract(self):
        layout = json.loads((ROOT / "assets" / "spoken-batch-layout.json").read_text(encoding="utf-8"))
        self.assertNotEqual(layout["platform_columns"], 16)
        self.assertEqual(layout["platform_columns"], 17)

if __name__ == "__main__":
    unittest.main()

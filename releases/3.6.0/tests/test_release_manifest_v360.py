import json
import unittest
from pathlib import Path

RELEASE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

class PublicReleaseManifestV360Tests(unittest.TestCase):
    def test_registry_targets_v360_overlay(self):
        registry = json.loads((REPO_ROOT / "REPO-REGISTRY.json").read_text(encoding="utf-8"))
        # This is a historical 3.6.0 regression suite. The root registry may advance,
        # but the 3.6.0 overlay must remain in the ordered compatibility chain.
        version = tuple(int(x) for x in registry["version"].split("."))
        self.assertGreaterEqual(version, (3, 6, 0))
        self.assertIn("releases/3.6.0/", registry["overlay_paths"])
        self.assertEqual(registry["asset_ref"], registry["active_overlay_ref"])
        self.assertNotEqual(registry["asset_ref"], "PENDING_V360_OVERLAY_COMMIT")
        self.assertIn(registry["active_overlay_path"], registry["overlay_paths"])
        if registry["version"] == "3.6.0":
            self.assertEqual(registry["active_overlay_path"], "releases/3.6.0/")

    def test_required_release_files_exist(self):
        for path in [
            "SKILL.md", "UPGRADE-3.6.0.md", "references/benchmark-governance-v360.json",
            "references/v3.6.0-runtime-quality-overlay.md", "scripts/marketing_quality_gate_v360.py",
            "scripts/run_pipeline_v3_6.py", "tests/test_marketing_quality_gate_v360.py",
            "schemas/marketing-review-v360.schema.json", "schemas/source-inventory-v360.schema.json"
        ]:
            with self.subTest(path=path):
                self.assertTrue((RELEASE_ROOT / path).is_file())

    def test_public_benchmark_catalog_is_redacted(self):
        catalog = json.loads((RELEASE_ROOT / "references/benchmark-governance-v360.json").read_text(encoding="utf-8"))
        blob = json.dumps(catalog, ensure_ascii=False)
        self.assertNotIn("300USD", blob)
        self.assertNotIn("300 美元", blob)
        self.assertNotIn("北美客户", blob)
        self.assertEqual(len(catalog["benchmarks"]), 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)

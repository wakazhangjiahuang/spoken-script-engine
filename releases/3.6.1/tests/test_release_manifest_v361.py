import json
import unittest
from pathlib import Path

RELEASE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

class PublicReleaseManifestV360Tests(unittest.TestCase):
    def test_registry_targets_v360_overlay(self):
        registry = json.loads((REPO_ROOT / "REPO-REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["version"], "3.6.1")
        self.assertEqual(registry["active_overlay_path"], "releases/3.6.1/")
        self.assertIn("releases/3.6.1/", registry["overlay_paths"])
        self.assertEqual(registry["asset_ref"], registry["active_overlay_ref"])
        self.assertNotEqual(registry["asset_ref"], "PENDING_V360_OVERLAY_COMMIT")

    def test_required_release_files_exist(self):
        for path in [
            "SKILL.md", "UPGRADE-3.6.1.md", "references/benchmark-governance-v360.json",
            "references/v3.6.1-runtime-quality-overlay.md", "scripts/marketing_quality_gate_v361.py",
            "scripts/run_pipeline_v3_6_1.py", "tests/test_marketing_quality_gate_v361.py",
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

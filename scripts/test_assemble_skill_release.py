import json, tempfile, unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assemble_skill_release", ROOT / "scripts" / "assemble_skill_release.py")
assembler = importlib.util.module_from_spec(spec); spec.loader.exec_module(assembler)

class SkillAssemblerTests(unittest.TestCase):
    def test_missing_342_overlay_is_only_skipped_after_343_retention_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp); base=repo/"base"; base.mkdir()
            (base/"SKILL.md").write_text("skill",encoding="utf-8")
            (base/"PACKAGE-METADATA.json").write_text(json.dumps({"skill_package_version":"3.6.1","skill_core_version":"3.6.1","skill_runtime_overlay_version":"3.6.1"}),encoding="utf-8")
            for name in assembler.SUPERSEDED_OVERLAYS["releases/3.4.2/"]["required_retained_files"]:
                p=repo/"releases/3.4.3"/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("retained",encoding="utf-8")
            v=repo/"releases/3.6.1"; (v/"scripts").mkdir(parents=True)
            (v/"SKILL.md").write_text("v361",encoding="utf-8"); (v/"UPGRADE-3.6.1.md").write_text("upgrade",encoding="utf-8")
            (v/"PACKAGE-METADATA.json").write_text(json.dumps({"skill_package_version":"3.6.1","skill_core_version":"3.6.1","skill_runtime_overlay_version":"3.6.1"}),encoding="utf-8")
            (v/"scripts/run_pipeline_v3_6_1.py").write_text("entry",encoding="utf-8"); (v/"scripts/acceptance_contract_v361.py").write_text("contract",encoding="utf-8")
            (v/"tests").mkdir(); (v/"tests/test_acceptance_contract_v361.py").write_text("tests",encoding="utf-8")
            (v/"references").mkdir(); (v/"references/acceptance-15-v361.md").write_text("15",encoding="utf-8")
            (v/"schemas").mkdir(); (v/"schemas/acceptance-15-v361.schema.json").write_text("{}",encoding="utf-8")
            (repo/"REPO-REGISTRY.json").write_text(json.dumps({"version":"3.6.1","base_path":"base/","overlay_paths":["releases/3.4.2/","releases/3.4.3/","releases/3.6.1/"],"asset_ref":"a","manifest_ref":"b"}),encoding="utf-8")
            result=assembler.assemble(repo,repo/"out",repo/"dist/skill.zip")
            manifest=json.loads((repo/"out/BUILD-MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(result["version"],"3.6.1")
            self.assertEqual(manifest["superseded_overlay_paths"][0]["path"],"releases/3.4.2/")
            self.assertTrue((repo/"out/scripts/content_decision_gate_v342.py").is_file())

    def test_unknown_missing_overlay_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp); (repo/"base").mkdir(); (repo/"base/SKILL.md").write_text("skill",encoding="utf-8")
            (repo/"REPO-REGISTRY.json").write_text(json.dumps({"version":"3.6.1","base_path":"base/","overlay_paths":["releases/9.9.9/"]}),encoding="utf-8")
            with self.assertRaises(FileNotFoundError): assembler.assemble(repo,repo/"out",repo/"dist/skill.zip")

if __name__=="__main__": unittest.main(verbosity=2)

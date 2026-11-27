from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from openpyxl import load_workbook

from delivery_v3 import export_with_readback
from execution_contract import fresh, read
from export_xlsx import build
from outcome_v3 import validate_outcome
from production_v3 import STAGES, validate_production
from retrieve_assets import ROOT
from test_pipeline import fixture


class DeliveryV3Tests(unittest.TestCase):
    def setUp(self):
        self.batch, self.review = fixture()
        script = self.batch["scripts"][0]
        self.shots = []
        for seg in script["segments"]:
            self.shots.append({"id": "H3-" + seg["id"], "segment_id": seg["id"], "text": seg["text"],
                               "duration_seconds": seg["duration_seconds"], "subject": "讲解人",
                               "shot_size": "中景", "camera": "正面", "action": "平稳讲解",
                               "cut_point": "段尾", "subtitle": seg["text"], "sound": "人声",
                               "acceptance": "对照台词", "prompt": "正面固定镜头，结束保持", "motion": "固定",
                               "negative_constraints": "不覆盖真实截屏", "lighting": "窗边自然光",
                               "expression": "平静", "background": "纯色", "selection": "用已授权身份参考",
                               "asset_ids": ["REAL"], "post_insert_asset_ids": ["REAL"]})
        self.production = {"plan_id": "fixture-synthetic",
                           "assets": [{"id": "REAL", "role": "R", "source_id": "PHONE",
                                       "locator": "测试素材路径", "rights": "authorized"}],
                           "gates": [{"id": stage, "status": "NOT_RUN" if stage in {"h3", "final"} else "PASS",
                                      "reason": "测试夹具", "evidence_refs": ["T"]} for stage in STAGES],
                           "cards": [{"script_id": script["id"], "05": self.shots}]}

    def test_h3_and_workbook_readback_against_canonical_script(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "script.xlsx"
            fresh(base / "v3.6.1-validation-status.json", {"status": "VALIDATION_PENDING"})

            def render(argv):
                build(self.batch, self.review, argv[2], ROOT / "assets/kb-snapshot",
                      {"publication_status": "VALIDATION_PENDING", "editorial_status": "REVIEWED"})

            validate_production(self.production, "05", self.batch)
            export_with_readback(render, ["export", "--output", str(target)],
                                 target, base, self.batch, self.production, "05")
            report = read(target.with_suffix(".delivery.json"))
            self.assertEqual(report["acceptance_status"], "VALIDATION_PENDING")
            self.assertEqual(report["readback_status"], "PASS")
            workbook = load_workbook(target)
            self.assertEqual(workbook["05 H3逐镜指令"]["D2"].value, self.shots[0]["text"])
            workbook.close()

    def test_real_material_cannot_be_generated_as_h3(self):
        self.shots[0].update(generation_asset_ids=["REAL"], post_insert_asset_ids=[])
        with self.assertRaisesRegex(ValueError, "H3_REAL_EVIDENCE_POST_ONLY"):
            validate_production(self.production, "05", self.batch)

    def test_after_publication_not_run_cannot_invent_zero(self):
        with self.assertRaisesRegex(ValueError, "OUTCOME_NOT_OBSERVED"):
            validate_outcome({"script_id": "S1", "status": "NOT_RUN", "metrics": [0]}, Path("."))

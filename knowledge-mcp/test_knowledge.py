from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from knowledge import Snapshot


class KnowledgeTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Knowledge test")
        self.git("config", "user.email", "test@example.invalid")
        self.path = self.root / "assets.jsonl"
        rows = [
            ("CURRENT", "家纺采购与样卡", "illustration", "xiaohongshu", "editorial_reference", "样卡" * 2600),
            ("HIST", "历史家纺样卡", "illustration", "xiaohongshu", "historical_only", "老样例"),
            ("VIDEO", "AI 视频证据", "ai_video", "douyin", "current_guidance", "屏录"),
        ]
        self.path.write_text("".join(
            json.dumps({"id": ident, "title": title, "domain": domain, "platform": platform,
                        "kind": "sample", "status": status, "source": {"locator": "ROW:1"}, "text": body},
                       ensure_ascii=False) + "\n"
            for ident, title, domain, platform, status, body in rows
        ), encoding="utf-8")
        manifest = {
            "schema_version": 1, "version": "test", "archives": [],
            "assets": [{"path": self.path.name, "records": len(rows),
                        "sha256": sha256(self.path.read_bytes()).hexdigest()}],
        }
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        self.asset_ref = self.commit("assets")
        self.registry = {
            "schema_version": 1, "visibility_required": "private", "repository": "example/knowledge",
            "asset_ref": self.asset_ref, "version": "test", "manifest_path": self.manifest.name,
            "manifest_sha256": sha256(self.manifest.read_bytes()).hexdigest(),
        }
        self.registry_path = self.root / "KNOWLEDGE-REGISTRY.json"
        self.registry_path.write_text(json.dumps(self.registry), encoding="utf-8")
        self.registry_ref = self.commit("registry")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def test_search_filters_and_history(self):
        db = Snapshot(self.root)
        self.assertEqual(["CURRENT"], [r["id"] for r in db.search("家纺样卡", domain="illustration")["results"]])
        self.assertEqual(["HIST"], [r["id"] for r in db.search("家纺样卡", status="historical_only")["results"]])
        self.assertFalse(db.search("家纺样卡", platform="douyin")["results"])
        self.assertFalse(db.search("zebra")["results"])

    def test_pinned_read_pagination_and_worktree_isolation(self):
        self.path.write_text("dirty working file", encoding="utf-8")
        db = Snapshot(self.root, self.registry_ref)
        first = db.read("CURRENT")
        end = db.read("CURRENT", first["next_offset"])
        self.assertEqual("样卡" * 2600, first["text"] + end["text"])
        self.assertIsNone(end["next_offset"])
        self.assertEqual(self.asset_ref, first["asset_ref"])
        self.assertEqual("ROW:1", first["source"]["locator"])

    def test_tampered_shard_fails(self):
        self.path.write_text("corrupted file", encoding="utf-8")
        self.registry["asset_ref"] = self.commit("change assets")
        self.registry_path.write_text(json.dumps(self.registry), encoding="utf-8")
        self.commit("point to inconsistent assets")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch: assets.jsonl"):
            Snapshot(self.root)


if __name__ == "__main__":
    unittest.main()

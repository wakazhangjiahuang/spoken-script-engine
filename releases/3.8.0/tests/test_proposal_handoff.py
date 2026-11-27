"""Exercise A/B routing with fresh processes and synthetic project material."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts/run_pipeline_v3_6_1.py"
sys.path.insert(0, str(ROOT / "scripts"))
from proposal_handoff import check_b_batch, check_b_plan
from run_pipeline_v3 import uses_historical_illustration_workbook
from v3_fixtures import context, populate, script_for


class ProposalHandoffTests(unittest.TestCase):
    def setUp(self):
        location = tempfile.TemporaryDirectory()
        self.addCleanup(location.cleanup)
        self.root = Path(location.name)
        self.a, self.b = self.root / "a", self.root / "b"
        self.request = self.root / "request.txt"
        quote = "Synthetic request for three demonstrations of different development decisions."
        self.request.write_text(quote, encoding="utf-8")
        self.brief = {
            "task_id": "synthetic-ab", "topic": "Product selection",
            "audience": "Product teams", "goal": "Explain development decisions",
            "domain": "general", "platforms": ["xiaohongshu"], "facts": [],
            "content_context": {"scene": "Planning", "problem": "Selection",
                                "memory_point": "Decision criteria", "content_type": "diagnosis"},
            "voice_profile": "Plain language", "objective": "education", "content_task": "diagnosis",
            "input_resolution": ["Synthetic request"], "case_policy": "prefer_real",
            "production_resources": [{"id": "PHONE", "description": "Fixed camera", "status": "available"}],
            "source_inventory": {"status": "complete", "selection_reason": quote,
                "checked_assets": [{"asset_id": "REQ", "source_file": "sources/01.txt",
                 "source_sha256": hashlib.sha256(self.request.read_bytes()).hexdigest(),
                 "source_quote": quote, "locator": "line 1", "read": True}],
                "fact_evidence": [], "relevant_real_case_ids": [], "selected_real_case_ids": [],
                "excluded_relevant_source_ids": []},
        }
        self.topics = []
        for i, decision in enumerate(("Choose a first concept", "Choose the next SKU", "Choose the approved brief"), 1):
            self.topics.append({
                "id": f"0{i}", "platform": "xiaohongshu", "audience": "Product teams",
                "buyer_decision": decision, "payoff": "A check to use before " + decision.lower(),
                "next_step": "Bring a development brief", "evidence_refs": ["REQ"],
                "copy": {"cover_main": "Collection | " + decision, "cover_sub": "Concept demonstration",
                         "hook": "Here is a concept.", "suspense": decision + " with one check.",
                         "body": "Compare two product treatments before selection.",
                         "calling": "Bring a development brief", "comment": "Which product is next?"},
                "locks": {"cover_main": {"scope": "prefix", "text": "Collection |"},
                          "hook": {"scope": "exact", "text": "Here is a concept."}},
            })

        for topic in self.topics:
            populate(topic, self.brief["source_inventory"]["checked_assets"][0])

    def data(self, name, content):
        path = self.root / name
        path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, *args, error=None):
        result = subprocess.run([sys.executable, str(ENGINE), *map(str, args)],
                                capture_output=True, text=True, timeout=90)
        if error:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(error, result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def intake(self, run, brief, *extra):
        if run == self.a:
            extra += ("--run-context", self.data("context.json", context()))
        self.cli("intake", "--run", run, "--input", self.data(f"{run.name}.json", brief),
                 "--request", self.request, *extra)

    def test_a_only_then_select_a_subset_into_fresh_b(self):
        locks = self.data("locks.json", {row["id"]: row["locks"] for row in self.topics})
        self.intake(self.a, self.brief, "--mode", "A", "--locks", locks)
        proposal = self.data("proposal.json", {"topics": self.topics})
        self.cli("plan", "--run", self.a, "--input", proposal, error="finish A")
        result = self.cli("proposal", "--run", self.a, "--input", proposal)
        self.assertEqual(result.stdout.count("Here is a concept."), 3)
        self.assertFalse((self.a / "decision.json").exists())
        self.assertFalse(list(self.a.glob("*.xlsx")))

        handoff_path = self.root / "handoff.json"
        self.cli("select", "--run", self.a, "--topic", "02", "--authorization",
                 "Synthetic confirmation of 02", "--output", handoff_path)
        brief_b = {**self.brief, "count_per_platform": {"xiaohongshu": 1}}
        changed = self.data("b-changed.json", {**brief_b, "goal": "Change A's accepted objective"})
        self.cli("intake", "--run", self.b, "--input", changed, "--request", self.request,
                 "--mode", "B", "--handoff", handoff_path, error="changed the approved A task context")
        self.intake(self.b, brief_b, "--mode", "B", "--handoff", handoff_path)
        approval = json.loads((self.b / "a-handoff.json").read_text())
        self.assertEqual(approval["topic_ids"], ["02"])
        self.assertFalse(uses_historical_illustration_workbook(self.b))
        self.assertTrue(uses_historical_illustration_workbook(self.root / "legacy"))
        self.cli("plan", "--run", self.b, "--input", self.data("unselected-plan.json",
                 {"selected": self.topics}), error="only the selected topic IDs")

        row = self.topics[1]
        from execution_contract import canonical
        row["v3_handoff_sha256"] = canonical(row["decision_v3"])
        row["selected_entry_candidate_id"] = row["decision_v3"]["value_map"]["entry_id"]
        row["content_mode"] = row["decision_v3"]["narrative_mode"]
        check_b_plan(approval, {"selected": [row]})
        script = script_for(row)
        script["cover_main"] = "Collection | A revised suffix"
        check_b_batch(approval, {"scripts": [script]})
        script["segments"][0]["text"] += " "
        with self.assertRaisesRegex(ValueError, "exact lock"):
            check_b_batch(approval, {"scripts": [script]})
        with self.assertRaisesRegex(ValueError, "changed payoff"):
            check_b_plan(approval, {"selected": [{**row, "payoff": "A different promise"}]})
        (self.b / "a-handoff.json").unlink()
        self.cli("plan", "--run", self.b, "--input", proposal, error="handoff is missing or changed")

    def test_a_rejects_changed_prefix_and_repeated_customer_decision(self):
        locks = self.data("locks.json", {row["id"]: row["locks"] for row in self.topics})
        self.intake(self.a, self.brief, "--mode", "A", "--locks", locks)
        row = self.topics[1]
        approved_title = row["copy"]["cover_main"]
        row["copy"]["cover_main"] = "Wrong prefix"
        cmd = ("proposal", "--run", self.a, "--input")
        self.cli(*cmd, self.data("prefix.json", {"topics": self.topics}), error="prefix lock")
        row["copy"]["cover_main"] = approved_title
        lock = row["locks"].pop("cover_main")
        self.cli(*cmd, self.data("removed-lock.json", {"topics": self.topics}), error="omitted the declared")
        row["locks"]["cover_main"] = lock
        row["buyer_decision"] = self.topics[0]["buyer_decision"]
        self.cli(*cmd, self.data("repeat.json", {"topics": self.topics}), error="repeated customer decision")
        self.assertFalse((self.a / "a-proposal.json").exists())


if __name__ == "__main__":
    unittest.main()

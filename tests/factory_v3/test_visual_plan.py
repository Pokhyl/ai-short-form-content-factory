import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("visual_plan", ROOT / "factory_v3/visual_plan.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PlanTests(unittest.TestCase):
    def test_real_failed_execution_blocks_before_voice(self):
        source = json.loads((ROOT / "acceptance/release-coverage/12126-assignment-deficits.json").read_text())
        report = m.plan_visuals(source["approved_choices"])
        self.assertEqual((report["required"], report["matched"]), (9, 7))
        self.assertEqual(report["status"], "blocked")
        self.assertIn({"shots": ["S6-A", "S8-A"], "assets": ["wikimedia:12612756"], "deficit": 1}, report["deficits"])
        self.assertIn({"shots": ["S9-A"], "assets": [], "deficit": 1}, report["deficits"])
        with self.assertRaisesRegex(ValueError, "TTS must not start"):
            m.require_complete_plan(report, source["approved_choices"])

    def test_reassigns_earlier_choices_instead_of_greedy_failure(self):
        graph = {"a": ["x", "y"], "b": ["x", "z"], "c": ["x", "z"]}
        report = m.plan_visuals(graph)
        self.assertEqual(report["matched"], 3)
        self.assertEqual(len(set(m.require_complete_plan(report, graph).values())), 3)

    def test_changed_asset_receipt_cannot_unlock_voice(self):
        graph = {"a": ["x"]}
        report = m.plan_visuals(graph)
        with self.assertRaisesRegex(ValueError, "changed"):
            m.require_complete_plan(report, {"a": ["y"]})

    def test_forged_feasible_flag_does_not_unlock_voice(self):
        graph = {"a": ["x"], "b": ["x"]}
        report = m.plan_visuals(graph)
        report["status"] = "feasible"
        with self.assertRaises(ValueError):
            m.require_complete_plan(report, graph)

    def test_invalid_or_empty_plan_rejected(self):
        for graph in ({}, {"a": [None]}, {"a": "x"}):
            with self.assertRaises(ValueError):
                m.plan_visuals(graph)


if __name__ == "__main__":
    unittest.main()

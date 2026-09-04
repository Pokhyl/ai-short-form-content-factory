from __future__ import annotations

import unittest

from prototype.v4.selftest_director_contract import (
    normalize_director_visual_contract,
    validate_director_shot_contract,
)


def shot(sid: str, narration: str, mode: str = "exact_media", query: str = "GPS satellite", must_show=None):
    return {
        "shot_id": sid,
        "narration": narration,
        "visual_mode": mode,
        "visual_query": query,
        "must_show": must_show or ["GPS satellite"],
        "must_not_show": ["misleading substitute"],
    }


def scene(scene_id: str, narration: str, shots, purpose: str = "explain"):
    return {
        "scene_id": scene_id,
        "narration": narration,
        "purpose": purpose,
        "visual_mode": shots[0]["visual_mode"],
        "visual_query": shots[0]["visual_query"],
        "must_show": shots[0]["must_show"],
        "shots": shots,
    }


class SelfTestDirectorContractTests(unittest.TestCase):
    def test_rejects_underpopulated_15_second_storyboard(self):
        raw = {"scenes": [
            scene("S1", "a b", [shot("S1A", "a"), shot("S1B", "b")]),
            scene("S2", "c", [shot("S2A", "c")]),
            scene("S3", "d", [shot("S3A", "d")]),
        ]}
        with self.assertRaisesRegex(ValueError, "below duration minimum 5"):
            validate_director_shot_contract(raw, 15)

    def test_rejects_semantic_scene_equals_shot_collapse(self):
        raw = {"scenes": [scene(f"S{i}", str(i), [shot(f"S{i}A", str(i))]) for i in range(1, 7)]}
        with self.assertRaisesRegex(ValueError, "semantic scenes collapsed"):
            validate_director_shot_contract(raw, 15)

    def test_allows_more_than_normal_target_when_semantics_require_it(self):
        shots = [shot(f"S1{chr(65+i)}", str(i)) for i in range(11)]
        raw = {"scenes": [scene("S1", " ".join(str(i) for i in range(11)), shots)]}
        self.assertEqual(validate_director_shot_contract(raw, 30), 11)

    def test_normalizer_removes_factual_stock(self):
        raw = {"scenes": [scene("S1", "a", [shot("S1A", "a", mode="stock")], purpose="explain")]}
        fixed = normalize_director_visual_contract(raw)
        self.assertEqual(fixed["scenes"][0]["shots"][0]["visual_mode"], "exact_media")

    def test_normalizer_replaces_placeholder_must_show_with_query(self):
        raw = {"scenes": [scene("S1", "a b c d e", [
            shot("S1A", "a", query="Volodymyr Zelenskyy", must_show=["subject"]),
            shot("S1B", "b"), shot("S1C", "c"), shot("S1D", "d"), shot("S1E", "e"),
        ], purpose="hook")]}
        fixed = normalize_director_visual_contract(raw)
        self.assertEqual(fixed["scenes"][0]["shots"][0]["must_show"], ["Volodymyr Zelenskyy"])

    def test_valid_multishot_15_second_plan_passes(self):
        raw = {"scenes": [
            scene("S1", "a b", [shot("S1A", "a", mode="stock"), shot("S1B", "b", mode="stock")], purpose="hook"),
            scene("S2", "c d", [shot("S2A", "c"), shot("S2B", "d")]),
            scene("S3", "e f", [shot("S3A", "e"), shot("S3B", "f")]),
        ]}
        self.assertEqual(validate_director_shot_contract(raw, 15), 6)


if __name__ == "__main__":
    unittest.main()

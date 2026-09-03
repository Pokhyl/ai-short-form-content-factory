from __future__ import annotations

import unittest

from prototype.v4.schema import parse_director_payload
from prototype.v4.speech import ensure_speech_ready, speech_issues
from prototype.v4.upstream_mpt import PINNED_MPT_COMMIT
from prototype.v4.visual_router import build_visual_manifest


def payload():
    return {
        "topic": "Як працює індукційна плита",
        "language": "uk",
        "target_seconds": 30,
        "hook": "Плита може нагрівати каструлю майже без нагрівання самої поверхні.",
        "spoken_script": "Плита може нагрівати каструлю майже без нагрівання самої поверхні. Під склом котушка створює змінне магнітне поле, а воно породжує струми прямо в металевому дні посуду.",
        "facts": [{"fact_id":"F1","claim":"Induction heats cookware through induced currents.","source_urls":["https://example.test/fact"]}],
        "scenes": [
            {"scene_id":"S1","narration":"Плита може нагрівати каструлю майже без нагрівання самої поверхні.","purpose":"hook","visual_mode":"exact_media","visual_query":"induction cooktop pot heating","must_show":["induction cooktop", "metal pot"],"must_not_show":["gas flame"],"source_refs":["F1"],"on_screen_text":"Індукція"},
            {"scene_id":"S2","narration":"Під склом котушка створює змінне магнітне поле, а воно породжує струми прямо в металевому дні посуду.","purpose":"explain","visual_mode":"diagram","visual_query":"","must_show":["coil", "magnetic field", "metal cookware"],"must_not_show":["open flame"],"source_refs":["F1"],"on_screen_text":None},
        ],
    }


class V4ContractTest(unittest.TestCase):
    def test_valid_plan(self):
        plan=parse_director_payload(payload())
        self.assertEqual(len(plan.scenes),2)
        self.assertEqual(build_visual_manifest(plan)[1]["production_adapter"],"remotion-diagram")

    def test_raw_written_units_fail_speech_guard(self):
        issues=speech_issues("Поле працює на частоті 20 кГц.")
        self.assertTrue(any("digits" in issue for issue in issues))
        self.assertTrue(any("abbreviations" in issue for issue in issues))

    def test_spoken_units_pass(self):
        self.assertEqual(ensure_speech_ready("Поле працює на частоті двадцять кілогерців."), "Поле працює на частоті двадцять кілогерців.")

    def test_scene_text_must_reconstruct_script(self):
        p=payload(); p["spoken_script"] += " зайве"
        with self.assertRaisesRegex(ValueError,"reconstruct"):
            parse_director_payload(p)

    def test_stock_requires_query(self):
        p=payload(); p["scenes"][1]["visual_mode"]="stock"; p["scenes"][1]["visual_query"]=""
        with self.assertRaisesRegex(ValueError,"requires visual_query"):
            parse_director_payload(p)

    def test_upstream_pin_is_exact_commit(self):
        self.assertEqual(PINNED_MPT_COMMIT,"cbbb366393105d5cefc254dc9ed492d43da0711b")


if __name__ == "__main__":
    unittest.main()

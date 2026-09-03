from __future__ import annotations

import json
import unittest
from pathlib import Path

from prototype.v4.graphic_spec import FORBIDDEN_GEOMETRY_FIELDS, validate_graphic_spec_map
from prototype.v4.graphic_compiler import compile_graphic_spec

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'cross_topic_graphic_specs_20260903.json'


class CrossTopicGraphicFixtureTest(unittest.TestCase):
    def test_all_three_non_induction_cases_validate_and_compile(self):
        payload=json.loads(FIXTURE.read_text(encoding='utf-8'))
        expected_counts={'eiffel-pl':3,'zipper-ru':7,'oled-en':6}
        for case,expected in expected_counts.items():
            with self.subTest(case=case):
                specs=payload[case]
                valid=validate_graphic_spec_map(specs,list(specs))
                self.assertEqual(len(valid),expected)
                for spec in valid.values():
                    compiled=compile_graphic_spec(spec,4.0)
                    self.assertGreater(len(compiled['elements']),0)

    def test_fixture_contains_no_raw_geometry_fields(self):
        payload=json.loads(FIXTURE.read_text(encoding='utf-8'))
        def walk(value):
            if isinstance(value,dict):
                for key,child in value.items():
                    self.assertNotIn(key,FORBIDDEN_GEOMETRY_FIELDS)
                    walk(child)
            elif isinstance(value,list):
                for child in value: walk(child)
        walk(payload)


if __name__ == '__main__':
    unittest.main()

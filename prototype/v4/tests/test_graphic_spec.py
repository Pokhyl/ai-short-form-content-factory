from __future__ import annotations

import unittest

from prototype.v4.graphic_spec import validate_graphic_spec, validate_graphic_spec_map
from prototype.v4.graphic_compiler import compile_graphic_spec, compile_timeline_graphics


def entity(i, label, role, **extra):
    return {"id": i, "label": label, "role": role, **extra}


def eiffel():
    return {"beat_id":"E2","archetype":"assembly","title":"prefabrication",
            "entities":[entity("foundation","foundation","subject",phase=0),entity("parts","prefabricated parts","input",phase=0),entity("assembly","on-site assembly","result",phase=2)],
            "relations":[{"from":"foundation","to":"assembly","kind":"joins","phase":1},{"from":"parts","to":"assembly","kind":"joins","phase":1}]}


def zipper_merge():
    return {"beat_id":"Z3","archetype":"merge",
            "entities":[entity("left","left row","input",phase=0),entity("right","right row","input",phase=0),entity("slider","slider channels","process",phase=1),entity("joined","joined rows","output",phase=3)],
            "relations":[{"from":"left","to":"slider","phase":1},{"from":"right","to":"slider","phase":1},{"from":"slider","to":"joined","kind":"joins","phase":2}]}


def oled():
    return {"beat_id":"O1","archetype":"comparison","title":"light origin",
            "entities":[entity("lcd-backlight","backlight","layer",lane="left",order=0,phase=0),entity("lcd-pixel","LCD pixel","layer",lane="left",order=1,phase=1),entity("oled-pixel","OLED pixel","layer",lane="right",order=0,phase=0),entity("oled-light","self-emitted light","output",lane="right",order=1,phase=1)],
            "relations":[{"from":"lcd-backlight","to":"lcd-pixel","kind":"flow","phase":1},{"from":"oled-pixel","to":"oled-light","kind":"emits","phase":1}]}


class GraphicSpecTest(unittest.TestCase):
    def test_cross_topic_specs_share_same_validator_and_compiler(self):
        for value in (eiffel(), zipper_merge(), oled()):
            with self.subTest(beat=value["beat_id"]):
                valid=validate_graphic_spec(value)
                compiled=compile_graphic_spec(valid, 4.0)
                self.assertGreater(len(compiled["elements"]), 0)
                self.assertEqual(compiled["source"]["beat_id"], value["beat_id"])

    def test_raw_geometry_is_rejected(self):
        value=zipper_merge(); value["entities"][0]["x"]=123
        with self.assertRaisesRegex(ValueError,"raw geometry"):
            validate_graphic_spec(value)

    def test_missing_constructed_spec_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"missing graphic specs"):
            validate_graphic_spec_map({"A": eiffel()}, ["A","B"])

    def test_nonconstructed_extra_spec_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"non-constructed"):
            validate_graphic_spec_map({"E2": eiffel(), "X": zipper_merge()}, ["E2"])

    def test_compile_timeline_replaces_construction_requirement(self):
        timeline={"beats":[
            {"beat_id":"Z3","start_seconds":0,"end_seconds":4,"primary_visual":{"source_class":"constructed"},"construction_required":True},
            {"beat_id":"PHOTO","start_seconds":4,"end_seconds":6,"primary_visual":{"source_class":"exact"},"resolved_asset":{"sha256":"abc"}},
        ]}
        out=compile_timeline_graphics(timeline,{"Z3":zipper_merge()})
        self.assertTrue(out["graphic_compilation"]["all_constructed_beats_compiled"])
        self.assertFalse(out["beats"][0]["construction_required"])
        self.assertNotIn("compiled_graphic",out["beats"][1])

    def test_merge_requires_two_inputs(self):
        value=zipper_merge(); value["entities"]=[e for e in value["entities"] if e["id"]!="right"]
        value["relations"]=[r for r in value["relations"] if r["from"]!="right"]
        with self.assertRaisesRegex(ValueError,"two inputs"):
            validate_graphic_spec(value)

    def test_two_merge_inputs_are_laid_out_symmetrically(self):
        compiled=compile_graphic_spec(validate_graphic_spec(zipper_merge()),4.0)
        shapes={e["id"]:e for e in compiled["elements"] if e["id"] in {"left-shape","right-shape"}}
        left_center=shapes["left-shape"]["x"] + shapes["left-shape"]["width"]/2
        right_center=shapes["right-shape"]["x"] + shapes["right-shape"]["width"]/2
        self.assertEqual((left_center,right_center),(180,540))

    def test_long_labels_are_wrapped_by_compiler_not_director_geometry(self):
        value=zipper_merge(); value["entities"][0]["label"]="very long semantic mechanism label"
        compiled=compile_graphic_spec(validate_graphic_spec(value),4.0)
        labels=[e for e in compiled["elements"] if e["id"].startswith("left-label-")]
        self.assertGreaterEqual(len(labels),2)
        self.assertTrue(all(len(e["text"]) <= 24 for e in labels[:-1]))


if __name__ == "__main__":
    unittest.main()

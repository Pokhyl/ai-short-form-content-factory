from __future__ import annotations

import unittest

from prototype.v4.timeline_contract import validate_timeline_payload


def beat(beat_id, start, end, *, mode, kind, source_class, visible_subject, layout, orientation, context_justification=None):
    primary = {
        "mode": mode,
        "kind": kind,
        "source_class": source_class,
        "visible_subject": visible_subject,
        "layout": layout,
        "source_orientation": orientation,
    }
    if context_justification is not None:
        primary["context_justification"] = context_justification
    return {
        "beat_id": beat_id,
        "start_seconds": start,
        "end_seconds": end,
        "primary_visual": primary,
        "overlays": [{"type": "caption"}],
    }


def induction_fixture():
    return {
        "duration_seconds": 6,
        "beats": [
            beat("I1", 0, 2, mode="exact_media", kind="video", source_class="exact", visible_subject="induction cooktop heating compatible pan", layout="fullscreen", orientation="portrait"),
            beat("I2", 2, 4, mode="motion_graphic", kind="motion_graphic", source_class="constructed", visible_subject="coil creating alternating magnetic field", layout="fullscreen", orientation="not_applicable"),
            beat("I3", 4, 6, mode="diagram", kind="diagram", source_class="constructed", visible_subject="induced current and heat in cookware base", layout="contain", orientation="landscape"),
        ],
    }


def eiffel_fixture():
    return {
        "duration_seconds": 6,
        "beats": [
            beat("E1", 0, 3, mode="exact_media", kind="photo", source_class="exact", visible_subject="Eiffel Tower under construction in 1888", layout="contain", orientation="landscape"),
            beat("E2", 3, 6, mode="exact_media", kind="video", source_class="exact", visible_subject="finished Eiffel Tower", layout="fullscreen", orientation="portrait"),
        ],
    }


def zipper_fixture():
    return {
        "duration_seconds": 6,
        "beats": [
            beat("Z1", 0, 3, mode="exact_media", kind="video", source_class="exact", visible_subject="macro zipper slider and teeth engaging", layout="fullscreen", orientation="portrait"),
            beat("Z2", 3, 6, mode="motion_graphic", kind="motion_graphic", source_class="constructed", visible_subject="slider channels bending two element rows into engagement", layout="fullscreen", orientation="not_applicable"),
        ],
    }


def oled_fixture():
    return {
        "duration_seconds": 6,
        "beats": [
            beat("O1", 0, 3, mode="motion_graphic", kind="motion_graphic", source_class="constructed", visible_subject="LCD backlight passing through liquid crystal and color layers", layout="fullscreen", orientation="not_applicable"),
            beat("O2", 3, 6, mode="motion_graphic", kind="motion_graphic", source_class="constructed", visible_subject="OLED pixels emitting their own light without backlight", layout="fullscreen", orientation="not_applicable"),
        ],
    }


class TimelineContractMatrixTest(unittest.TestCase):
    def test_all_matrix_classes_pass_same_contract(self):
        for fixture in (induction_fixture(), eiffel_fixture(), zipper_fixture(), oled_fixture()):
            with self.subTest(fixture=fixture["beats"][0]["beat_id"]):
                result = validate_timeline_payload(fixture)
                self.assertGreater(result["beat_count"], 0)

    def test_text_only_primary_visual_is_rejected(self):
        value = induction_fixture()
        value["beats"][0]["primary_visual"]["mode"] = "text"
        value["beats"][0]["primary_visual"]["kind"] = "photo"
        with self.assertRaisesRegex(ValueError, "replace the primary visual with text"):
            validate_timeline_payload(value)

    def test_generic_stock_fallback_is_rejected(self):
        value = zipper_fixture()
        value["beats"][0]["primary_visual"]["source_class"] = "generic_stock"
        with self.assertRaisesRegex(ValueError, "generic_stock"):
            validate_timeline_payload(value)

    def test_landscape_photo_cannot_be_fullscreen(self):
        value = eiffel_fixture()
        value["beats"][0]["primary_visual"]["layout"] = "fullscreen"
        with self.assertRaisesRegex(ValueError, "cannot fullscreen landscape photo"):
            validate_timeline_payload(value)

    def test_contextual_media_requires_explicit_justification(self):
        value = induction_fixture()
        visual = value["beats"][0]["primary_visual"]
        visual["mode"] = "justified_context"
        visual["source_class"] = "contextual"
        with self.assertRaisesRegex(ValueError, "context_justification"):
            validate_timeline_payload(value)

    def test_timeline_gap_is_rejected(self):
        value = oled_fixture()
        value["beats"][1]["start_seconds"] = 3.5
        with self.assertRaisesRegex(ValueError, "gap/overlap"):
            validate_timeline_payload(value)


if __name__ == "__main__":
    unittest.main()

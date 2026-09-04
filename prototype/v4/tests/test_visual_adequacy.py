from __future__ import annotations

import unittest

from prototype.v4.visual_adequacy import validate_primary_motion_graphic


class VisualAdequacyTest(unittest.TestCase):
    def test_box_label_diagram_cannot_be_primary_visual(self):
        graphic = {
            "elements": [
                {"id":"a","type":"rect"},
                {"id":"b","type":"text","text":"backlight"},
                {"id":"c","type":"line","arrow":True},
            ],
            "source":{"beat_id":"O2","compiler":"graphic_compiler_v1"},
        }
        with self.assertRaisesRegex(ValueError, "not a valid primary visual"):
            validate_primary_motion_graphic(graphic, beat_id="O2")

    def test_pictorial_primitive_can_be_primary_visual(self):
        graphic = {
            "elements":[{"id":"pixel-grid","type":"rect"}],
            "source":{"beat_id":"O4","visual_basis":"pictorial_primitive"},
        }
        validate_primary_motion_graphic(graphic, beat_id="O4")

    def test_exact_media_annotation_basis_is_accepted(self):
        graphic = {
            "elements":[{"id":"arrow","type":"line","arrow":True}],
            "source":{"beat_id":"Z3","visual_basis":"exact_media_annotation"},
        }
        validate_primary_motion_graphic(graphic, beat_id="Z3")


if __name__ == "__main__":
    unittest.main()

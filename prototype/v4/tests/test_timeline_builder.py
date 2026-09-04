from __future__ import annotations

import unittest

from prototype.v4.timeline_builder import compile_segment_timeline, sha256_text


def visual(beat_id: str, narration: str):
    return {
        'beat_id': beat_id,
        'narration': narration,
        'primary_visual': {
            'mode': 'motion_graphic',
            'kind': 'motion_graphic',
            'source_class': 'constructed',
            'visible_subject': f'mechanism step {beat_id}',
            'layout': 'fullscreen',
            'source_orientation': 'not_applicable',
        },
        'overlays': [{'type': 'caption'}],
    }


def word(start: float, end: float, text: str):
    return {'start': start, 'end': end, 'word': text}


class TimelineBuilderTest(unittest.TestCase):
    def test_semantic_scene_boundaries_ignore_whisper_segment_boundaries(self):
        whisper = {
            'duration': 4.0,
            # Deliberately different boundaries from the two semantic scenes.
            'segments': [
                {'start': 0.0, 'end': 1.1, 'text': 'alpha beta'},
                {'start': 1.2, 'end': 2.4, 'text': 'gamma delta'},
                {'start': 2.5, 'end': 4.0, 'text': 'epsilon zeta'},
            ],
            'words': [
                word(0.0, 0.4, 'alpha'),
                word(0.5, 0.9, 'beta'),
                word(1.2, 1.6, 'gamma'),
                word(2.0, 2.3, 'delta'),
                word(2.5, 2.9, 'epsilon'),
                word(3.1, 3.5, 'zeta'),
            ],
        }
        result = compile_segment_timeline(
            whisper_payload=whisper,
            visual_obligations=[
                visual('A', 'alpha beta gamma'),
                visual('B', 'delta epsilon zeta'),
            ],
            script_text='alpha beta gamma delta epsilon zeta',
            audio_sha256='a' * 64,
        )
        self.assertEqual(
            [(b['start_seconds'], b['end_seconds']) for b in result['beats']],
            [(0.0, 2.0), (2.0, 4.0)],
        )
        self.assertEqual(result['provenance']['timing_source'], 'actual_audio_whisper_word_alignment')
        self.assertEqual([b['source_scene_index'] for b in result['beats']], [0, 1])

    def test_scene_alignment_tolerates_recognition_error_inside_scene(self):
        whisper = {
            'duration': 4.0,
            'segments': [{'start': 0.0, 'end': 4.0, 'text': 'one two tree four'}],
            'words': [
                word(0.0, 0.4, 'one'),
                word(0.5, 0.9, 'two'),
                word(2.0, 2.4, 'tree'),
                word(2.5, 3.0, 'four'),
            ],
        }
        result = compile_segment_timeline(
            whisper_payload=whisper,
            visual_obligations=[visual('A', 'one two'), visual('B', 'three four')],
            script_text='one two three four',
            audio_sha256='a' * 64,
        )
        # "three" is misrecognized, but "four" still anchors semantic scene B.
        self.assertEqual(result['beats'][1]['start_seconds'], 2.5)

    def test_narration_must_reconstruct_script(self):
        whisper = {
            'duration': 2.0,
            'segments': [{'start': 0.0, 'end': 2.0, 'text': 'one two'}],
            'words': [word(0.0, 0.5, 'one'), word(1.0, 1.5, 'two')],
        }
        with self.assertRaisesRegex(ValueError, 'reconstruct script_text'):
            compile_segment_timeline(
                whisper_payload=whisper,
                visual_obligations=[visual('A', 'one')],
                script_text='one two',
                audio_sha256='a' * 64,
            )

    def test_low_alignment_coverage_is_rejected(self):
        whisper = {
            'duration': 2.0,
            'segments': [{'start': 0.0, 'end': 2.0, 'text': 'unrelated tokens'}],
            'words': [word(0.0, 0.5, 'unrelated'), word(1.0, 1.5, 'tokens')],
        }
        with self.assertRaisesRegex(ValueError, 'coverage too low'):
            compile_segment_timeline(
                whisper_payload=whisper,
                visual_obligations=[visual('A', 'alpha beta gamma')],
                script_text='alpha beta gamma',
                audio_sha256='a' * 64,
            )

    def test_script_provenance_changes_when_script_changes(self):
        self.assertNotEqual(sha256_text('old script'), sha256_text('new script'))


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import unittest

from prototype.v4.timeline_builder import compile_segment_timeline, sha256_text


def visual(beat_id: str):
    return {
        'beat_id': beat_id,
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


class TimelineBuilderTest(unittest.TestCase):
    def test_timing_comes_from_whisper_segment_starts_and_covers_silence(self):
        whisper = {
            'duration': 8.0,
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': 'one'},
                {'start': 3.0, 'end': 5.0, 'text': 'two'},
                {'start': 6.5, 'end': 8.0, 'text': 'three'},
            ],
        }
        result = compile_segment_timeline(
            whisper_payload=whisper,
            visual_obligations=[visual('A'), visual('B'), visual('C')],
            script_text='one two three',
            audio_sha256='a' * 64,
        )
        self.assertEqual([(b['start_seconds'], b['end_seconds']) for b in result['beats']], [(0.0, 3.0), (3.0, 6.5), (6.5, 8.0)])
        self.assertEqual(result['provenance']['timing_source'], 'actual_audio_whisper_segments')

    def test_obligation_count_must_match_actual_segments(self):
        whisper = {'duration': 2.0, 'segments': [{'start': 0.0, 'end': 2.0, 'text': 'one'}]}
        with self.assertRaisesRegex(ValueError, 'must match Whisper segment count'):
            compile_segment_timeline(
                whisper_payload=whisper,
                visual_obligations=[visual('A'), visual('B')],
                script_text='one',
                audio_sha256='a' * 64,
            )

    def test_script_provenance_changes_when_script_changes(self):
        self.assertNotEqual(sha256_text('old script'), sha256_text('new script'))


if __name__ == '__main__':
    unittest.main()

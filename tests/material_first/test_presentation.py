import unittest
from material_first.presentation import visual_timeline,preferred_shots,tempo_factor

class PresentationTests(unittest.TestCase):
    def test_visual_cuts_cover_exact_requested_frames_without_long_holds(self):
        for seconds,count in [(15,8),(30,15),(45,23),(60,30)]:
            cuts=visual_timeline(seconds,count)
            self.assertEqual(cuts[0]['start_frame'],0)
            self.assertEqual(cuts[-1]['end_frame'],seconds*30)
            self.assertEqual(sum(c['end_frame']-c['start_frame'] for c in cuts),seconds*30)
            self.assertLessEqual(max(c['end_frame']-c['start_frame'] for c in cuts),60)
            self.assertEqual(preferred_shots(seconds),count)
    def test_previous_six_or_eight_photos_cannot_cover_long_video(self):
        for seconds,count in [(30,6),(45,8),(60,8)]:
            with self.assertRaises(ValueError):visual_timeline(seconds,count)
    def test_saved_three_voices_fit_requested_duration_with_bounded_tempo(self):
        for original,seconds in [(22.248,30),(57.552,45),(73.416,60)]:
            rate=tempo_factor(original,seconds)
            self.assertAlmostEqual(original/rate,seconds)
        for original in [5,100]:
            with self.assertRaises(ValueError):tempo_factor(original,30)
    def test_nonfinite_audio_and_unsupported_target_are_rejected(self):
        for duration in [float('nan'),float('inf'),0,-1]:
            with self.assertRaises(ValueError):tempo_factor(duration,30)
        for target in [0,17,30.0,True]:
            with self.assertRaises(ValueError):tempo_factor(30,target)
    def test_twenty_nine_distinct_water_photos_cover_sixty_seconds(self):
        cuts=visual_timeline(60,29)
        self.assertEqual(cuts[-1]['end_frame'],1800)
        self.assertTrue(all(62<=c['end_frame']-c['start_frame']<=63 for c in cuts))

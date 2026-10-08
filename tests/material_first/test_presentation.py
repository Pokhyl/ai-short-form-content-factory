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
    def test_duration_mismatch_cannot_be_hidden_by_slowing_or_accelerating_voice(self):
        for original, seconds in [(50.928,60),(22.248,30),(57.552,45),(73.416,60)]:
            with self.assertRaisesRegex(ValueError, 'changing speech speed is forbidden'):
                tempo_factor(original,seconds)
        for original, seconds in [(59,60),(59.9,60),(60,60),(14,15)]:
            self.assertEqual(tempo_factor(original,seconds),1.0)
        for original in [58.999,60.001]:
            with self.assertRaises(ValueError):tempo_factor(original,60)
    def test_nonfinite_audio_and_unsupported_target_are_rejected(self):
        for duration in [float('nan'),float('inf'),0,-1]:
            with self.assertRaises(ValueError):tempo_factor(duration,30)
        for target in [0,17,30.0,True]:
            with self.assertRaises(ValueError):tempo_factor(30,target)
    def test_twenty_nine_distinct_water_photos_cover_sixty_seconds(self):
        cuts=visual_timeline(60,29)
        self.assertEqual(cuts[-1]['end_frame'],1800)
        self.assertTrue(all(62<=c['end_frame']-c['start_frame']<=63 for c in cuts))

    def test_calm_cadence_uses_moderate_counts_and_prefers_phrase_boundaries(self):
        from material_first.presentation import CALM_POLICY, phrase_frames
        for seconds,count in [(15,5),(30,9),(45,13),(60,18)]:
            self.assertEqual(preferred_shots(seconds,CALM_POLICY),count)
            cuts=visual_timeline(seconds,count,CALM_POLICY)
            self.assertEqual(cuts[-1]['end_frame'],seconds*30)
            self.assertTrue(all(75<=c['end_frame']-c['start_frame']<=150 for c in cuts))
        boundaries=phrase_frames([{'start_ms':0,'end_ms':6100},{'start_ms':6100,'end_ms':60000}],60000,60)
        cuts=visual_timeline(60,18,CALM_POLICY,boundaries)
        self.assertIn(183,[c['end_frame'] for c in cuts])
        self.assertTrue(all(75<=c['end_frame']-c['start_frame']<=150 for c in cuts))
        with self.assertRaises(ValueError):visual_timeline(60,30,CALM_POLICY)
        # Existing immutable v1 output retains its original exact 2s timeline.
        self.assertEqual(visual_timeline(60,30)[0],{'start_frame':0,'end_frame':60})

    def test_calm_schedule_keeps_every_frame_with_dense_adversarial_phrase_edges(self):
        from material_first.presentation import CALM_POLICY, validate_timeline
        for seconds,count in [(15,5),(30,9),(45,13),(60,18)]:
            cuts=visual_timeline(seconds,count,CALM_POLICY,range(1,seconds*30,13))
            validate_timeline(seconds,count,cuts,CALM_POLICY)
            self.assertEqual(sum(c['end_frame']-c['start_frame'] for c in cuts),seconds*30)
            altered=[dict(c) for c in cuts];altered[1]['start_frame']+=1
            with self.assertRaises(ValueError):validate_timeline(seconds,count,altered,CALM_POLICY)

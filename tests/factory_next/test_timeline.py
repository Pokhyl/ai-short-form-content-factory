import copy
import unittest
from factory_next.timeline import compile_edit, EditUnavailable


class MeasuredEditTests(unittest.TestCase):
    def inputs(self, seconds):
        photos=[{'id':f'{f}-{i}','sha256':f'hash-{f}-{i}','media_type':'photo',
                 'supported_fact_ids':[f'f{f}']} for f in range(3) for i in range(10)]
        scenes=[{'id':f's{f}','material_id':f'{f}-0','narration':'Source grounded paragraph.',
                 'evidence_ids':[f'f{f}']} for f in range(3)]
        duration=seconds*1000-500
        timings=[{'start_ms':duration*i/3,'end_ms':duration*(i+1)/3} for i in range(3)]
        return scenes,photos,timings,duration

    def test_all_durations_and_languages_preserve_real_voice_and_cover_frames(self):
        for seconds in (15,30,45,60):
            for phrase in ('Natural speech.', 'Naturalna mowa.', 'Естественная речь.', 'Природне мовлення.'):
                scenes,photos,timings,duration=self.inputs(seconds)
                for scene in scenes:scene['narration']=phrase
                plan=compile_edit(scenes,photos,timings,duration,seconds)
                self.assertEqual(plan['audio_tempo_factor'],1)
                self.assertEqual(plan['shots'][0]['start_frame'],0)
                self.assertEqual(plan['shots'][-1]['end_frame'],seconds*30)
                self.assertEqual(plan['tail_silence_ms'],500)
                self.assertEqual(len({s['material_id'] for s in plan['shots']}),len(plan['shots']))
                for left,right in zip(plan['shots'],plan['shots'][1:]):
                    self.assertEqual(left['end_frame'],right['start_frame'])

    def test_real_dna_second_recording_compiles_without_speed_change(self):
        scenes,photos,_,_=self.inputs(45)
        audio_ms=43656  # measured TTS #2 from the live DNA 45-second run
        timings=[{'start_ms':audio_ms*i/3,'end_ms':audio_ms*(i+1)/3}
                 for i in range(3)]
        plan=compile_edit(scenes,photos,timings,audio_ms,45)
        self.assertEqual(plan['tail_silence_ms'],1344)
        self.assertEqual(plan['audio_tempo_factor'],1.0)
        self.assertEqual(plan['shots'][-1]['end_frame'],45*30)

    def test_actual_audio_not_text_length_controls_photo_assignment(self):
        scenes,photos,timings,duration=self.inputs(15)
        first=compile_edit(scenes,photos,timings,duration,15)
        scenes[0]['narration']='Very long words ' * 50
        self.assertEqual(first,compile_edit(scenes,photos,timings,duration,15))

    def test_reviewed_scene_anchor_covers_fact_id_mismatch(self):
        scenes,photos,timings,duration=self.inputs(15)
        for i,scene in enumerate(scenes):
            photos[i*10]['supported_fact_ids']=['different-fact']
        plan=compile_edit(scenes,photos,timings,duration,15)
        self.assertTrue({'0-0','1-0','2-0'} <= {s['material_id'] for s in plan['shots']})

    def test_bad_audio_alignment_and_duplicate_assets_are_rejected(self):
        scenes,photos,timings,duration=self.inputs(15)
        for invalid in (10000,15001,float('nan')):
            with self.assertRaises(EditUnavailable):compile_edit(scenes,photos,timings,invalid,15)
        bad=copy.deepcopy(timings);bad[1]['start_ms']=0
        with self.assertRaises(EditUnavailable):compile_edit(scenes,photos,bad,duration,15)
        with self.assertRaises(EditUnavailable):compile_edit(scenes,photos+[photos[0]],timings,duration,15)

"""Controlled connected contracts; actual ffmpeg evidence is recorded separately."""
import copy
import hashlib
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from factory_v3.preflight import digest
from material_first.engine import Producer, verify, MaterialUnavailable
from material_first.portrait import PortraitDownload
from material_first.operations import Operations
from material_first.visuals import POLICY, ordered_visuals, candidate_limit
from material_first.worker import PhotoWorker
from factory_v3.server import Application
from test_engine import Operations as Fixtures


class ModernFixtures(Fixtures):
    presentation_policy = POLICY

    def __init__(self, root, count):
        super().__init__(root, ['photo'] * count)
        for a in self.assets:
            self.support[a['id']] = ['f0', 'f1', 'f2']

    def discover(self, request, queries):
        return super().discover(request, queries)[:candidate_limit(request['seconds'])]

    def inspect_many(self, assets, evidence):
        self.events.append('batch:' + str(len(assets)))
        return [self.inspect(a, evidence) for a in assets]

    def compose(self, context):
        self.events.append('compose')
        return {'beats': [{'material_id': m['id'], 'narration': 'Source fact ' + str(i),
                           'fact_ids': ['f0', 'f1', 'f2']}
                          for i, m in enumerate(context['materials'][:5])]}


class ConnectedPresentationTests(unittest.TestCase):
    def test_all_durations_freeze_many_visuals_independent_of_five_paragraphs(self):
        for seconds, count in [(15, 8), (30, 15), (45, 23), (60, 30)]:
            with self.subTest(seconds=seconds), tempfile.TemporaryDirectory() as tmp:
                ops = ModernFixtures(Path(tmp), 32)
                frozen = Producer(tmp, ops, probe=ops.probe).prepare('topic', 'ru', seconds)
                p = verify(tmp, frozen, ops.probe)
                self.assertEqual(len(p['scenes']), 5)
                self.assertEqual(len(p['visuals']), count)
                self.assertEqual(len(p['assets']), count)
                self.assertEqual(len({a['sha256'] for a in p['assets']}), count)
                self.assertLessEqual(sum(e.startswith('batch:') for e in ops.events), 8)
                self.assertNotIn('inspect:a' + str(((count + 3)//4)*4), ops.events)

    def test_wrong_photo_count_stops_before_composition(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = ModernFixtures(Path(tmp), 8)
            with self.assertRaisesRegex(MaterialUnavailable, 'cadence'):
                Producer(tmp, ops, probe=ops.probe).prepare('topic', 'en', 30)
            self.assertNotIn('compose', ops.events)

    def test_source_grounding_does_not_require_photographs_to_prove_every_fact(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = ModernFixtures(Path(tmp), 8)
            for a in ops.assets:
                ops.support[a['id']] = ['f0']
            p = Producer(tmp, ops, probe=ops.probe).prepare('topic', 'ru', 15)['payload']
            self.assertEqual(set(p['scenes'][0]['evidence_ids']), {'f0', 'f1', 'f2'})
            self.assertTrue(p['script_review']['no_unsupported_claims'])

    def test_recomputed_hash_cannot_hide_sparse_repeated_or_cropped_visual_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = ModernFixtures(Path(tmp), 16)
            frozen = Producer(tmp, ops, probe=ops.probe).prepare('topic', 'en', 30)
            mutations = [
                lambda p: p['visuals'].__setitem__(1, {**p['visuals'][1], 'material_id': p['visuals'][0]['material_id']}),
                lambda p: p.__setitem__('visuals', p['visuals'][:6]),
                lambda p: p['assets'][0].__setitem__('framing', 'center-crop-9x16'),
            ]
            for mutate in mutations:
                altered = copy.deepcopy(frozen)
                mutate(altered['payload']); altered['sha256'] = digest(altered['payload'])
                with self.assertRaises(ValueError): verify(tmp, altered, ops.probe)

    def test_staging_and_owner_photo_route_use_entire_pool_not_only_paragraphs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); ops = ModernFixtures(root, 16)
            frozen = Producer(root, ops, probe=ops.probe).prepare('topic', 'en', 30)
            p = frozen['payload']; job = str(uuid.uuid4())
            worker = PhotoWorker(root, None, 'http://localhost:3001', None, probe=ops.probe)
            staged = worker._stage_photos(job, p)
            self.assertEqual(len(staged), 15)
            self.assertEqual(len(worker._scene_inputs(job, p)), 5)
            last = p['visuals'][-1]
            a = next(a for a in p['assets'] if a['id'] == last['material_id'])
            self.assertEqual(Path(staged[last['id']]['path']).read_bytes(), (root/a['path']).read_bytes())
            runtime = Mock(root=root, settings={'owner_token': 'x'*40})
            runtime.status.return_value = {'status': 'prepared'}
            runtime.ledger.snapshot.return_value = {'status': 'prepared', 'frozen': frozen}
            app = Application(runtime, 'https://example.invalid');app.review = Mock(return_value=None)
            try:
                self.assertEqual(len(app.detail(job)['scenes']), 15)
                self.assertEqual(app.photo(job, last['id'])[0], (root/a['path']).resolve())
            finally: app.pool.shutdown()

    def test_scheduled_cut_cadence_is_unaffected_by_a_long_narration_paragraph(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = ModernFixtures(Path(tmp), 32)
            p = Producer(tmp, ops, probe=ops.probe).prepare('topic', 'uk', 60)['payload']
            timings = [{'start_ms': 0, 'end_ms': 50000}] + [{'start_ms': 50000+(i-1)*5000, 'end_ms': 50000+i*5000} for i in range(1,5)]
            ordered = ordered_visuals(p, timings, 70000)
            self.assertEqual(len({v['material_id'] for v in ordered}), 30)
            self.assertTrue(all(v['end_frame']-v['start_frame'] == 60 for v in ordered))
            self.assertEqual(ordered[-1]['end_frame'], 1800)

    def test_whole_download_preserves_bytes_dimensions_and_provider_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops = ModernFixtures(Path(tmp), 1)
            before = copy.deepcopy(ops.assets[0]);ops.calls = None
            after = PortraitDownload(tmp, ops).download(before)
            self.assertEqual(after['path'], before['path'])
            self.assertEqual(after['sha256'], before['sha256'])
            self.assertEqual(after['source_url'], before['source_url'])
            self.assertEqual(after['framing'], 'original-whole')
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_fitted_voice_window_accepts_saved_samples_without_resynthesis(self):
        worker = PhotoWorker('.', None, 'http://localhost:3001', None)
        for seconds, duration in [(30,22248),(45,57552),(60,73416)]:
            low, high = worker._duration_window({'seconds':seconds,'presentation_policy':POLICY})
            self.assertLessEqual(low, duration);self.assertGreaterEqual(high, duration)
            self.assertLessEqual(candidate_limit(seconds), 42)

    def test_completed_bad_inspection_row_rejects_only_that_photo_without_retry(self):
        from factory_v3.gemini import ModelSchemaError
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);fixtures = ModernFixtures(root, 2)
            for i,a in enumerate(fixtures.assets):
                (root/a['path']).write_bytes(b'\xff\xd8\xffphoto'+bytes([i]))
                a['sha256'] = hashlib.sha256((root/a['path']).read_bytes()).hexdigest()
            valid = {'asset_id':'a0','accepted':True,'is_real_material':True,
                     'subject_fully_visible':True,'visible_description':'Source-related object',
                     'visible_fact_details':[{'fact_id':'f0','detail':'Visible source-related subject'}]}
            completed = ModelSchemaError({'photos':[valid, {'asset_id':'a1','accepted':'wrong-type'}]}, 'bad row')
            completed.provenance = {'receipt_id':'actual-completed-receipt'}
            model = SimpleNamespace(model='controlled-model', generate=Mock(side_effect=completed))
            result = Operations(root,None,model,None,None).inspect_many(fixtures.assets,fixtures.evidence)
            self.assertTrue(result[0]['accepted']);self.assertFalse(result[1]['accepted'])
            self.assertEqual(result[0]['asset_sha256'],fixtures.assets[0]['sha256'])
            self.assertEqual(result[0]['receipt_id'],'actual-completed-receipt')
            self.assertEqual(model.generate.call_count, 1)
            images = model.generate.call_args.kwargs['photos']
            self.assertEqual(images[0]['bytes'],(root/fixtures.assets[0]['path']).read_bytes())

    def test_batch_unknown_asset_identity_is_terminal(self):
        from factory_v3.gemini import ModelSchemaError
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixtures=ModernFixtures(root,1)
            a=fixtures.assets[0];(root/a['path']).write_bytes(b'\xff\xd8\xffphoto')
            a['sha256']=hashlib.sha256((root/a['path']).read_bytes()).hexdigest()
            error=ModelSchemaError({'photos':[{'asset_id':'invented'}]},'bad identity')
            error.provenance={'receipt_id':'completed'}
            model=SimpleNamespace(model='controlled',generate=Mock(side_effect=error))
            with self.assertRaisesRegex(ValueError,'identity'):
                Operations(root,None,model,None,None).inspect_many(fixtures.assets,fixtures.evidence)
            self.assertEqual(model.generate.call_count,1)

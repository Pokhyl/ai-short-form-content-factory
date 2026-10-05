import tempfile
import unittest
import uuid
from pathlib import Path
from factory_v3.worker_adapters import WorkerAdapters
from material_first.worker import PhotoWorker
from test_engine import Operations
from material_first.engine import Producer


class PhotoWorkerTests(unittest.TestCase):
    def test_material_plan_stages_exact_photo_without_legacy_density(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ops = Operations(root, ['photo'])
            ops.support['a0'] = ['f0', 'f1', 'f2']
            payload = Producer(root, ops, probe=ops.probe).prepare('topic', 'pl', 60)['payload']
            worker = PhotoWorker(root, None, 'http://localhost:3001', None, probe=ops.probe)
            worker._validate_scene_count(payload)
            staged = worker._stage_photos(str(uuid.uuid4()), payload)
            self.assertEqual(Path(staged['beat-1']['path']).read_bytes(), (root / '0.jpg').read_bytes())
            with self.assertRaises(ValueError):
                WorkerAdapters._validate_scene_count(worker, payload)

    def test_video_is_not_silently_sent_to_legacy_loop_renderer(self):
        worker = PhotoWorker('.', None, 'http://localhost:3001', None)
        with self.assertRaises(ValueError):
            worker._validate_scene_count({'schema': 'material-first', 'scenes': [{}],
                                         'assets': [{'media_type': 'video'}]})

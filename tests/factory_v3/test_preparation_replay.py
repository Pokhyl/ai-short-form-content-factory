"""Exercise the replay entrypoint against requests built by DurableProducer."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from factory_v3.preflight import digest
from material_first.engine import MaterialUnavailable
from material_first.producer import DurableProducer
from material_first.visuals import TOPIC_POLICY


class ReplayEntrypointTests(unittest.TestCase):
    def test_saved_request_matches_normal_producer_for_each_visual_mode(self):
        for mode, state in itertools.product((None, 'gemini', 'metadata'), ('succeeded', 'failed', 'unknown')):
            with self.subTest(mode=mode, state=state):
                request = {'topic': 'Neutron star', 'language': 'uk', 'seconds': 60}
                if mode is not None:
                    request['visual_validation_mode'] = mode
                captured = []

                def operations(research):
                    return SimpleNamespace(
                        source=SimpleNamespace(calls=None),
                        gemini=SimpleNamespace(calls=None),
                        search=SimpleNamespace(calls=None),
                        downloader=SimpleNamespace(calls=None, downloader=SimpleNamespace()),
                        presentation_policy=TOPIC_POLICY, voice_correction_enabled=True,
                        research=research, review_script=lambda value: value,
                        inspect_many=lambda *args: [])

                def capture(value):
                    captured.append(value)
                    raise MaterialUnavailable('boundary reached')

                ledger = Mock()
                ledger.claim_run.return_value = {'cached': False, 'request': request}
                with self.assertRaises(MaterialUnavailable):
                    DurableProducer('/data', ledger, operations(capture)).prepare('test-id')
                saved = {'key': 'brief', 'state': state, 'response': {},
                         'request_hash': digest(captured[0])}

                def replay_research(value):
                    ops.gemini.calls.run('brief', 'gemini', value,
                                         lambda: self.fail('replay invoked provider'))
                    raise MaterialUnavailable('boundary reached')

                ops = operations(replay_research)
                runtime = Mock(revision='a' * 40)
                runtime.preparations.snapshot.return_value = {
                    'status': 'unknown', 'request': request}
                runtime.ledger._call.return_value = [saved]
                runtime.producer.return_value = SimpleNamespace(operations=ops)
                output = io.StringIO()
                script = Path(__file__).resolve().parents[2] / 'scripts/replay_material_preparation.py'
                with patch('factory_v3.runtime.Runtime', return_value=runtime), \
                     patch('factory_v3.runtime.load_settings', return_value={}), \
                     patch.dict('os.environ', FACTORY_V3_REVISION='a' * 40), \
                     patch('sys.argv', [str(script), '--id', 'test-id']), \
                     contextlib.redirect_stdout(output):
                    runpy.run_path(str(script), run_name='__main__')
                result = json.loads(output.getvalue())
                self.assertEqual(result['state'], 'material_unavailable' if state == 'succeeded'
                                 else 'saved_call_unavailable:brief:' + state)
                self.assertEqual(result['used_saved_calls'], ['brief'] if state == 'succeeded' else [])
                self.assertEqual(result['new_provider_calls'], 0)
                runtime.preparations.claim_run.assert_not_called()
                runtime.preparations.reject.assert_not_called()

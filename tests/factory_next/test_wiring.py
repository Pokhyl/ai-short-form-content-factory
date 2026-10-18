"""Construct production-compatible provider adapters with zero external sends."""
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_next.wiring import connected_adapters
from factory_next.budget import PROFILE
from factory_next.preparation import PreparationStages
from factory_next.voice import VoiceStages
from factory_next.media import MediaStages


class FakeProducer:
    def __init__(self, sink):
        self.operations=object()
        self.authorize=lambda:sink.append('billing_gate_invoked')


class StubPreparations:
    def snapshot(self, job_id):
        return {'status':'preparing','source_revision':'a'*40,
                'request':{'factory_next_budget_profile':PROFILE}}


class TrustedRuntime:
    def __init__(self,root,*,authorized=True):
        self.root=Path(root)
        self.gateway=object()
        self.direct=object()
        self.ledger=object()
        self.preparations=StubPreparations()
        self.revision='a'*40
        self.settings={}
        self.authorized=authorized
        self.producer_calls=[]
        self.external_calls=[]
    def producer(self,job_id):
        self.producer_calls.append(job_id)
        if not self.authorized:
            raise ValueError('verified free-only Gemini configuration required')
        return FakeProducer(self.external_calls)


class ConnectedWiringTests(unittest.TestCase):
    def test_all_real_components_are_bound_without_external_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=TrustedRuntime(directory)
            job=str(uuid4())
            adapters=connected_adapters(runtime,job)
            self.assertEqual(runtime.producer_calls,[job])
            self.assertIsInstance(adapters.preparation,PreparationStages)
            self.assertIsInstance(adapters.voice_stages,VoiceStages)
            self.assertIsInstance(adapters.media,MediaStages)
            self.assertIs(adapters.voice_stages.quota,runtime.ledger)
            self.assertIs(adapters.voice_stages.http,runtime.direct)
            self.assertIs(adapters.voice_stages.provider.http,runtime.gateway)
            self.assertFalse(adapters.voice_stages.tts_billing_verified)
            self.assertEqual(runtime.external_calls,[])

    def test_only_explicit_billing_verification_enables_tts(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=TrustedRuntime(directory)
            runtime.settings['google_tts_external_usage_verified']='true'
            adapter=connected_adapters(runtime,str(uuid4()))
            self.assertFalse(adapter.voice_stages.tts_billing_verified)
            runtime.settings['google_tts_external_usage_verified']=True
            adapter=connected_adapters(runtime,str(uuid4()))
            self.assertTrue(adapter.voice_stages.tts_billing_verified)

    def test_unverified_project_blocks_assembly_before_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=TrustedRuntime(directory,authorized=False)
            with self.assertRaisesRegex(ValueError,'free-only'):
                connected_adapters(runtime,str(uuid4()))
            self.assertEqual(runtime.external_calls,[])

    def test_invalid_identity_is_rejected_without_runtime_activity(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=TrustedRuntime(directory)
            with self.assertRaises(ValueError):
                connected_adapters(runtime,'reused-or-malformed-identity')
            self.assertEqual(runtime.producer_calls,[])

    def test_preflight_hook_is_optional_and_construction_only(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime=TrustedRuntime(directory)
            marker=[]
            adapters=connected_adapters(runtime,str(uuid4()),
                                        preflight_gate=lambda s,c:marker.append(s))
            self.assertEqual(marker,[])
            adapters.preflight('research',{'id':str(uuid4()),'request':{},'outputs':{}})
            self.assertEqual(marker,['research'])


if __name__=='__main__': unittest.main()

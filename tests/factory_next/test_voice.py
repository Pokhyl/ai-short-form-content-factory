from uuid import uuid4
import tempfile
import unittest
from factory_next.voice import VoiceStages


class BudgetTests(unittest.TestCase):
    def test_quota_rejection_prevents_synthesis(self):
        calls=[]
        class Quota:
            def _call(self,sql,args):calls.append('quota');raise ValueError('budget exhausted')
        class Provider:
            def synthesize(self,*args):calls.append('synthesis');raise AssertionError('must not send')
        with tempfile.TemporaryDirectory() as root:
            stage=VoiceStages(root,Provider(),object(),Quota(),tts_billing_verified=True)
            with self.assertRaisesRegex(ValueError,'budget exhausted'):
                stage.voice({'id':str(uuid4()),'request':{'language':'pl'},'outputs':{'story':{'script':'Test'}}})
        self.assertEqual(calls,['quota'])

    def test_unverified_google_tts_account_blocks_before_database_and_provider(self):
        events=[]
        class Quota:
            def _call(self,*args): events.append('database');raise AssertionError('no reservation allowed')
        class Provider:
            def synthesize(self,*args): events.append('google_tts');raise AssertionError('no Google request allowed')
        with tempfile.TemporaryDirectory() as root:
            stage=VoiceStages(root,Provider(),object(),Quota())
            with self.assertRaisesRegex(ValueError,'TTS_BILLING_NOT_VERIFIED'):
                stage._synthesize_once(str(uuid4()),'pl','Grounded narration.',1)
        self.assertEqual(events,[])

    def test_tts_billing_authorization_must_be_actual_boolean(self):
        class Provider: pass
        class Quota: pass
        with tempfile.TemporaryDirectory() as root:
            for unsafe_value in ('true',1,None,{'verified':True}):
                with self.subTest(value=unsafe_value):
                    with self.assertRaisesRegex(ValueError,'trusted TTS billing'):
                        VoiceStages(root,Provider(),object(),Quota(),
                                    tts_billing_verified=unsafe_value)

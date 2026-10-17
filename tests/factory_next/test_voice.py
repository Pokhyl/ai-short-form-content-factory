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
            stage=VoiceStages(root,Provider(),object(),Quota())
            with self.assertRaisesRegex(ValueError,'budget exhausted'):
                stage.voice({'id':'test','request':{'language':'pl'},'outputs':{'story':{'script':'Test'}}})
        self.assertEqual(calls,['quota'])

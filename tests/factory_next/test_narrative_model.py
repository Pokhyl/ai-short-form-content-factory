import unittest
from types import SimpleNamespace
from copy import deepcopy
from factory_next.wiring import narrative_model_for

class NarrativeModelProofTests(unittest.TestCase):
    def setUp(self):
        self.proof={'model':'gemini-3.8-flash','billing_enabled':False,
            'standard_free_tier':True,'verification_id':'actual-evaluation',
            'project_id':'project-one','credential_sha256':'digest-one'}
        self.runtime=SimpleNamespace(settings={'free_tier_proof':{
            'project_id':'project-one','credential_sha256':'digest-one'},
            'factory_next_narrative_proof':self.proof})
        self.calls=object()
        self.original=SimpleNamespace(model='gemini-3.1-flash-lite',calls=self.calls)
        self.producer=SimpleNamespace(operations=SimpleNamespace(gemini=self.original))
    def test_verified_fixed_model_keeps_durable_meter_and_original_model(self):
        selected=narrative_model_for(self.runtime,self.producer)
        self.assertEqual(selected.model,'gemini-3.8-flash')
        self.assertIs(selected.calls,self.calls)
        self.assertEqual(self.original.model,'gemini-3.1-flash-lite')
    def test_missing_opt_in_preserves_existing_behavior(self):
        del self.runtime.settings['factory_next_narrative_proof']
        self.assertIsNone(narrative_model_for(self.runtime,self.producer))
    def test_paid_unknown_model_and_wrong_credentials_are_rejected(self):
        for key,value in [('model','gemini-paid'),('billing_enabled',True),
                ('standard_free_tier',False),('project_id','other-project'),
                ('credential_sha256','other-key'),('verification_id','')]:
            with self.subTest(key=key):
                runtime=deepcopy(self.runtime)
                runtime.settings['factory_next_narrative_proof'][key]=value
                with self.assertRaisesRegex(ValueError,'free-tier'):
                    narrative_model_for(runtime,self.producer)
    def test_partial_proof_cannot_enable_model(self):
        self.runtime.settings['factory_next_narrative_proof']={}
        with self.assertRaises(ValueError):narrative_model_for(self.runtime,self.producer)

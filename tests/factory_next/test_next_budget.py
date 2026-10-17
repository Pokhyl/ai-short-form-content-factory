"""Next-only provider-call budget, immutable profile, and TTS send guard."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from material_first.operations import preparation_budgets
from factory_v3.runtime import Runtime
from factory_next.budget import (PROFILE,EXTRA_GEMINI_CALLS,
                                 MIN_VOICE_CORRECTION_HEADROOM,next_preparation_budgets)
from factory_next.wiring import register_next,NextBudgetGate


class SavedPreparations:
    def __init__(self,rev):
        self.rows={};self.rev=rev
    def snapshot(self,job):
        if job not in self.rows:raise KeyError(job)
        row=self.rows[job]
        return {'request':row['request'],'source_revision':self.rev,'status':'preparing'}
    def create(self,job,request,budgets):
        if job in self.rows:raise AssertionError('duplicate preparation registration')
        self.rows[job]={'request':request,'budgets':budgets}


def unconnected_runtime(root):
    runtime=Runtime.__new__(Runtime)
    runtime.root=Path(root)
    runtime.revision='b'*40
    runtime.preparations=SavedPreparations(runtime.revision)
    runtime.direct=object()
    return runtime


class BudgetRegistrationTests(unittest.TestCase):
    def test_next_only_adds_three_to_base_without_changing_other_limits(self):
        for seconds in (15,30,45,60):
            with self.subTest(seconds=seconds):
                original=preparation_budgets(seconds)
                expanded=next_preparation_budgets(seconds)
                self.assertEqual(expanded['gemini'],original['gemini']+EXTRA_GEMINI_CALLS)
                for kind,amount in original.items():
                    if kind!='gemini':self.assertEqual(expanded[kind],amount)
                self.assertEqual(preparation_budgets(seconds),original)

    def test_trusted_next_registration_is_immutable_and_does_not_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=unconnected_runtime(folder)
            job=str(uuid4())
            with patch('factory_v3.runtime.ensure_visible'),                 patch('factory_v3.runtime.check_gateway') as gateway:
                result=register_next(runtime,job,'Pollinating bees','pl',15)
                self.assertTrue(result['created'])
                gateway.assert_called_once()
                saved=runtime.preparations.rows[job]
                self.assertEqual(saved['request']['factory_next_budget_profile'],PROFILE)
                self.assertEqual(saved['request']['visual_validation_mode'],'gemini')
                self.assertEqual(saved['budgets'],next_preparation_budgets(15))
                self.assertFalse(register_next(runtime,job,'Pollinating bees','pl',15)['created'])
                with self.assertRaisesRegex(ValueError,'identity changed'):
                    runtime.create(job,'Pollinating bees','pl',15,
                                   visual_validation_mode='gemini')

    def test_legacy_registration_keeps_exact_prior_budget_and_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=unconnected_runtime(folder)
            job=str(uuid4())
            with patch('factory_v3.runtime.ensure_visible'),                 patch('factory_v3.runtime.check_gateway'):
                runtime.create(job,'Flower pollination','en',30,visual_validation_mode='gemini')
                saved=runtime.preparations.rows[job]
                self.assertEqual(saved['budgets'],preparation_budgets(30))
                self.assertNotIn('factory_next_budget_profile',saved['request'])
                with self.assertRaisesRegex(ValueError,'identity changed'):
                    register_next(runtime,job,'Flower pollination','en',30)


class FakeLedger:
    def __init__(self,limit,used,unknown=0):
        self.result={'limit':limit,'used':used,'unknown':unknown}
        self.calls=[]
    def _call(self,sql,args):
        self.calls.append((sql,args))
        return self.result


class FakeRuntime:
    def __init__(self,limit=19,used=17,unknown=0,profile=PROFILE):
        self.revision='b'*40
        self.ledger=FakeLedger(limit,used,unknown)
        self.profile=profile
        self.preparations=self
    def snapshot(self,job):
        return {'source_revision':self.revision,
                'request':{'factory_next_budget_profile':self.profile}}


class HeadroomGateTests(unittest.TestCase):
    def test_at_least_two_real_ledger_calls_remain_before_voice(self):
        runtime=FakeRuntime(limit=19,used=17)
        gate=NextBudgetGate(runtime)
        job=str(uuid4())
        gate('voice',{'id':job,'request':{},'outputs':{}})
        self.assertEqual(len(runtime.ledger.calls),1)
        self.assertEqual(runtime.ledger.calls[0][1],(job,job,job))
        self.assertEqual(MIN_VOICE_CORRECTION_HEADROOM,2)

    def test_insufficient_quota_or_ambiguous_call_blocks_before_tts(self):
        for used,unknown in ((18,0),(19,0),(17,1)):
            with self.subTest(used=used,unknown=unknown):
                runtime=FakeRuntime(limit=19,used=used,unknown=unknown)
                with self.assertRaisesRegex(ValueError,'insufficient reviewed'):
                    NextBudgetGate(runtime)('voice',{'id':str(uuid4())})
                self.assertEqual(len(runtime.ledger.calls),1)

    def test_all_stages_require_matching_immutable_profile_and_revision(self):
        runtime=FakeRuntime(profile='legacy')
        with self.assertRaisesRegex(ValueError,'profile mismatch'):
            NextBudgetGate(runtime)('research',{'id':str(uuid4())})
        self.assertEqual(len(runtime.ledger.calls),0)
        runtime=FakeRuntime()
        runtime.preparations=type('WrongRev',(),{'snapshot':lambda self,job:{
            'source_revision':'a'*40,'request':{'factory_next_budget_profile':PROFILE}}})()
        with self.assertRaisesRegex(ValueError,'profile mismatch'):
            NextBudgetGate(runtime)('research',{'id':str(uuid4())})


if __name__=='__main__':unittest.main()

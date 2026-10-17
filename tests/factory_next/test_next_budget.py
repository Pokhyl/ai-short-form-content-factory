"""Next-only provider-call budget, immutable profile, and TTS send guard."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from material_first.operations import preparation_budgets
from factory_v3.runtime import Runtime
from factory_next.budget import (PROFILE,EXTRA_GEMINI_CALLS,
                                 MIN_VOICE_CORRECTION_HEADROOM,
                                 MIN_STORY_AND_VOICE_HEADROOM,
                                 next_preparation_budgets)
from factory_next.wiring import register_next,NextBudgetGate
from factory_next.pipeline import Pipeline, fingerprint, ReconciliationRequired


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
    def test_next_only_adds_seven_to_base_without_changing_other_limits(self):
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
    def __init__(self,limit=23,used=17,unknown=0,profile=PROFILE):
        self.revision='b'*40
        self.ledger=FakeLedger(limit,used,unknown)
        self.profile=profile
        self.preparations=self
    def snapshot(self,job):
        return {'source_revision':self.revision,
                'request':{'factory_next_budget_profile':self.profile}}


class HeadroomGateTests(unittest.TestCase):
    def test_at_least_six_real_ledger_calls_remain_before_voice(self):
        runtime=FakeRuntime(limit=23,used=17)
        gate=NextBudgetGate(runtime)
        job=str(uuid4())
        gate('voice',{'id':job,'request':{},'outputs':{}})
        self.assertEqual(len(runtime.ledger.calls),1)
        self.assertEqual(runtime.ledger.calls[0][1],(job,job,job))
        self.assertEqual(MIN_VOICE_CORRECTION_HEADROOM,6)

    def test_insufficient_quota_or_ambiguous_call_blocks_before_tts(self):
        for used,unknown in ((18,0),(19,0),(17,1)):
            with self.subTest(used=used,unknown=unknown):
                runtime=FakeRuntime(limit=23,used=used,unknown=unknown)
                with self.assertRaisesRegex(ValueError,'insufficient reserved'):
                    NextBudgetGate(runtime)('voice',{'id':str(uuid4())})
                self.assertEqual(len(runtime.ledger.calls),1)

    def test_story_requires_draft_review_one_repair_and_voice_review_headroom(self):
        self.assertEqual(MIN_STORY_AND_VOICE_HEADROOM,9)
        # Exactly 9 is permitted; 8 is not. This check runs before any
        # draft/model call and does not consume a Gemini quota claim.
        runtime=FakeRuntime(limit=23,used=14)
        job=str(uuid4())
        gate=NextBudgetGate(runtime)
        gate('story',{'id':job,'request':{},'outputs':{}})
        self.assertEqual(runtime.ledger.calls[0][1],(job,job,job))
        self.assertEqual(len(runtime.ledger.calls),1)
        runtime=FakeRuntime(limit=23,used=15)
        with self.assertRaisesRegex(ValueError,'before story'):
            NextBudgetGate(runtime)('story',{'id':job,'request':{},'outputs':{}})
        self.assertEqual(len(runtime.ledger.calls),1)

    def test_in_progress_call_blocks_story_as_well_as_voice(self):
        runtime=FakeRuntime(limit=19,used=0,unknown=1)
        with self.assertRaisesRegex(ValueError,'before story'):
            NextBudgetGate(runtime)('story',{'id':str(uuid4())})
        self.assertEqual(len(runtime.ledger.calls),1)

    def test_preflight_never_queries_budget_during_photo_research(self):
        runtime=FakeRuntime(limit=19,used=19)
        gate=NextBudgetGate(runtime)
        job=str(uuid4())
        for stage in ('research','materials','alignment','render','audit'):
            gate(stage,{'id':job})
        self.assertEqual(runtime.ledger.calls,[])

    def test_regression_last_real_pl15_story_guard_prevents_wasted_draft(self):
        # The saved 2026-10-17 PL15 job consumed 16 of 16 by voice.
        # Simulate the penultimate stage: with only four remaining calls,
        # beginning the story would permit a script but not protect the
        # measured voice correction. The guard blocks *before* first send.
        runtime=FakeRuntime(limit=16,used=12)
        with self.assertRaisesRegex(ValueError,'before story'):
            NextBudgetGate(runtime)('story',{'id':str(uuid4())})
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



class CheckpointedBudgetAdmission(unittest.TestCase):
    def test_pipeline_story_never_sends_with_only_four_remaining_calls(self):
        with tempfile.TemporaryDirectory() as root:
            job=str(uuid4())
            runtime=FakeRuntime(limit=23,used=15)
            class Adapter:
                sent=0
                def preflight(self,stage,context):
                    return NextBudgetGate(runtime)(stage,context)
                def story(self,context):
                    self.sent+=1
                    raise AssertionError('Gemini story must not be sent')
            adapter=Adapter()
            pipeline=Pipeline(Path(root),adapter,'b'*40)
            pipeline.create(job,'Checked source topic','pl',15)
            state=pipeline.snapshot(job)
            for stage in ('research','materials'):
                output={'saved_stage':stage}
                state['outputs'][stage]=output
                state['receipts'][stage]=fingerprint(output)
            state['next_stage']='story'
            pipeline.save(pipeline.directory(job),state)
            with self.assertRaisesRegex(ValueError,'before story'):
                pipeline.step(job)
            final=pipeline.snapshot(job)
            self.assertEqual(final['status'],'needs_attention')
            self.assertEqual(final['next_stage'],'story')
            self.assertNotIn('story',final['outputs'])
            self.assertEqual(adapter.sent,0)
            self.assertEqual(len(runtime.ledger.calls),1)
            with self.assertRaises(ReconciliationRequired):
                pipeline.step(job)


if __name__=='__main__':unittest.main()

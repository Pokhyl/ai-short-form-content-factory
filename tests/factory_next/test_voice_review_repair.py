"""A negative review can trigger one new rewrite, never unreviewed TTS or a loop."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import test_measured_voice_length as measured
from factory_next.preparation import PreparationStages
from factory_next.duration import revision_length_window
from factory_v3.gemini import ScriptReviewRejected


class ReviewRepairTests(TestCase):
    def run_case(self,reviews):
        context=measured.LengthProtectionTests().context()
        context['outputs']['research']['request']['voice_review_repair_policy']='one-reviewed-repair-v1'
        window=revision_length_window(context['outputs']['story']['script'],40824,45)
        draft=measured.sentence_draft(window,context['outputs']['story']['scenes'])
        class Model(measured.FakeGemini):
            def review_script(self,request,**kwargs):
                self.reviews.append(kwargs.get('review_key','script-review'))
                result=reviews.pop(0)
                if isinstance(result,Exception):raise result
                return result
        model=Model([draft,deepcopy(draft)])
        stage=PreparationStages('/empty',SimpleNamespace(gemini=model),lambda:None)
        def bind(_request,_evidence,_photos,draft):
            return [{'id':f'b{i}','material_id':beat['material_id'],
                     'evidence_ids':beat['fact_ids'],'narration':beat['narration']}
                    for i,beat in enumerate(draft['beats'])]
        with patch('factory_next.preparation.validate_story',side_effect=bind), \
             patch('factory_next.preparation.validate_native_surface'), \
             patch('factory_next.preparation.validate_script_review'), \
             patch('factory_next.preparation.compact_materials',return_value=[]):
            try:result=stage.revise_story(context,40824)
            except Exception as error:result=error
        return model,result

    def test_feedback_is_used_once_and_new_text_independently_reviewed(self):
        negative={'coverage_checks':{'f1':{'covered':False,'missing_details':['required cause']}}}
        model,result=self.run_case([ScriptReviewRejected('missing cause',negative),{'native_language_quality':True}])
        self.assertIsInstance(result,dict)
        self.assertEqual(model.keys,['next-measured-duration-revision','next-measured-duration-review-repair'])
        self.assertEqual(model.reviews,['script-review','script-review-repaired'])
        self.assertEqual(model.requests[-1][1]['negative_review'],negative)

    def test_second_negative_review_is_terminal(self):
        model,result=self.run_case([ScriptReviewRejected('missing cause',{}),ScriptReviewRejected('still missing',{})])
        self.assertIsInstance(result,ScriptReviewRejected)
        self.assertEqual(len(model.keys),2)
        self.assertEqual(len(model.reviews),2)

    def test_transport_error_does_not_trigger_semantic_rewrite(self):
        model,result=self.run_case([TimeoutError('unknown send')])
        self.assertIsInstance(result,TimeoutError)
        self.assertEqual(model.keys,['next-measured-duration-revision'])

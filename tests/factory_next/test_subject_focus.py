"""Generic visual-focus contract; controlled decisions, not live semantic acceptance."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import Mock
from factory_v3.grounding import validate_evidence
from factory_v3.gemini import validate_json, ModelSchemaError
from material_first.operations import Operations
from material_first.engine import inspected_material
from material_first.subject_focus import POLICY
from tests.factory_next.test_scientific_illustrations import evidence,diagram_asset,response

class SubjectFocusTests(TestCase):
    def setUp(self):
        self.ops=Operations('/unused',None,Mock(model='controlled'),None,None)
        self.ops.allow_source_illustrations=True
        self.ops.require_subject_focus=True
        self.asset=diagram_asset();self.asset['subject_focus_policy']=POLICY
        self.evidence=evidence()

    def receipt(self,primary=True,unrelated=False,subject='DNA structure',connection='Depicts the topic'):
        result=response()
        for detail in result['visible_fact_details']:detail['relationship']='direct_observation'
        result['subject_focus']={'dominant_subject':subject,'topic_connection':connection,
             'relevant_content_is_primary':primary,'unrelated_subject_dominates':unrelated}
        return self.ops._inspection_receipt(self.asset,self.evidence,result,{'receipt_id':'controlled'})

    def test_unrelated_foreground_rejects_even_if_other_checks_approve(self):
        for subject,detail in [('Festival dancers','Incidental rain'),
                               ('Advertised car','Trees in background'),
                               ('Fashion model','Ocean behind model')]:
            with self.subTest(subject=subject):
                receipt=self.receipt(False,True,subject,detail)
                self.assertFalse(receipt['accepted'])
                receipt['accepted']=True # downstream cannot trust this field alone
                self.assertIsNone(inspected_material(self.asset,receipt,self.evidence,
                    validate_evidence(self.evidence),'gemini_scientific'))

    def test_relevant_people_and_diagrams_are_not_categorically_banned(self):
        for subject in ('DNA structure','People demonstrating the requested dance'):
            receipt=self.receipt(subject=subject)
            self.assertTrue(receipt['accepted'])
            self.assertIsNotNone(inspected_material(self.asset,receipt,self.evidence,
                validate_evidence(self.evidence),'gemini_scientific'))

    def test_missing_and_contradictory_focus_fail_closed(self):
        for primary,unrelated in [(False,False),(True,True),(False,True)]:
            self.assertFalse(self.receipt(primary,unrelated)['accepted'])
        for key in ('subject_focus','subject_focus_policy'):
            receipt=self.receipt();del receipt[key]
            self.assertIsNone(inspected_material(self.asset,receipt,self.evidence,
                validate_evidence(self.evidence),'gemini_scientific'))
        self.assertFalse(self.receipt(subject=' ')['accepted'])

    def test_schema_requires_focus_only_for_new_policy(self):
        schema=self.ops._inspection_schema(self.evidence,None)
        self.assertIn('subject_focus',schema['required'])
        with self.assertRaises(ValueError):validate_json(response(),schema)
        self.ops.require_subject_focus=False
        schema=self.ops._inspection_schema(self.evidence,None)
        validate_json(response(),schema)

    def test_policy_is_server_owned_for_all_languages_and_durations(self):
        from factory_next.preparation import PreparationStages
        from types import SimpleNamespace
        facts=evidence()
        brief={'evidence':facts,'required_fact_ids':['f1'],'queries':[]}
        for language in ('pl','en','ru','uk'):
            for seconds in (15,30,45,60):
                ops=SimpleNamespace(research=lambda request: deepcopy(brief))
                stage=PreparationStages('/unused',ops,lambda:None)
                result=stage.research({'request':{'topic':'DNA','language':language,
                    'seconds':seconds,'subject_focus_policy':'untrusted-override'}})
                self.assertEqual(result['request']['subject_focus_policy'],POLICY)

    def test_context_does_not_become_observed_physical_process(self):
        from material_first.engine import validate_story
        from material_first.presentation import TOPIC_POLICY
        result=response();result['subject_focus']=self.receipt()['subject_focus']
        for detail in result['visible_fact_details']:detail['relationship']='topic_context'
        receipt=self.ops._inspection_receipt(self.asset,self.evidence,result,{'receipt_id':'controlled'})
        photo=inspected_material(self.asset,receipt,self.evidence,validate_evidence(self.evidence),'gemini_scientific')
        self.assertEqual(photo['direct_fact_ids'],[])
        draft={'beats':[{'material_id':photo['id'],'narration':'DNA has paired strands.', 'fact_ids':['f1']}]}
        scenes=validate_story({'presentation_policy':TOPIC_POLICY,'required_fact_ids':['f1'],'seconds':15,'language':'en'},
            self.evidence,[photo],draft,allow_topic_context=True)
        self.assertEqual(scenes[0]['visual_relation'],'topic_context')

    def test_only_parts_cannot_replace_main_topic(self):
        from material_first.subject_focus import shows_main_topic
        parts=[{'inspection':{'topic_relation':{'kind':'direct_part_or_stage'}}}]*3
        self.assertFalse(shows_main_topic(parts))
        self.assertTrue(shows_main_topic(parts+[{'inspection':{'topic_relation':{'kind':'direct_subject'}}}]))

    def test_component_context_is_explicit_and_cannot_claim_observation(self):
        from material_first.subject_focus import COMPONENT_CONTEXT,shows_main_topic
        result=response();result['medium']='photograph';result['illustration_type']='not_applicable'
        result['topic_relation']['kind']=COMPONENT_CONTEXT
        result['subject_focus']=self.receipt()['subject_focus']
        for d in result['visible_fact_details']:d['relationship']='topic_context'
        validate_json(result,self.ops._inspection_schema(self.evidence,None))
        receipt=self.ops._inspection_receipt(self.asset,self.evidence,result,{'receipt_id':'controlled'})
        photo=inspected_material(self.asset,receipt,self.evidence,validate_evidence(self.evidence),'gemini_scientific')
        self.assertIsNotNone(photo)
        self.assertEqual(photo['direct_fact_ids'],[])
        self.assertFalse(shows_main_topic([photo]))
        result['visible_fact_details'][0]['relationship']='direct_observation'
        receipt=self.ops._inspection_receipt(self.asset,self.evidence,result,{'receipt_id':'controlled'})
        self.assertFalse(receipt['accepted'])
        receipt['accepted']=True
        self.assertIsNone(inspected_material(self.asset,receipt,self.evidence,validate_evidence(self.evidence),'gemini_scientific'))
        self.ops.require_subject_focus=False
        with self.assertRaises(ValueError):validate_json(result,self.ops._inspection_schema(self.evidence,None))

    def test_actual_failed_probe_is_not_semantic_acceptance(self):
        import json
        from pathlib import Path
        from material_first.targets import matched_targets
        from factory_v3.preflight import digest
        saved=json.loads((Path(__file__).parent/'fixtures/actual-focus-e079.json').read_text())
        self.assertEqual(saved['result']['status'],'failed')
        rows={r['asset_id']:r for r in saved['receipts']}
        self.assertFalse(rows['wikimedia:116034921']['accepted'])
        self.assertTrue(rows['pixabay:7381976']['accepted'])
        # A component's broad match cannot bypass its failed qualification.
        receipt=deepcopy(rows['pexels:9850703'])
        targets=[{'id':f'v{i}','fact_ids':[f'f{i+1}'],'must_show':f'Role {i}',
                  'must_not_show':'Unrelated objects','query':f'Role {i}'} for i in range(3)]
        receipt['visual_targets_sha256']=digest(targets)
        asset={'visual_targets':targets,'visual_qualification_protocol':'qualified-target-v1'}
        self.assertEqual(matched_targets(asset,receipt),{})

    def test_actual_empty_nonmatches_preserve_valid_target_without_inventing_matches(self):
        import json
        from pathlib import Path
        from material_first.targets import matched_targets
        saved=json.loads((Path(__file__).parent/'fixtures/actual-focus-db268.json').read_text())
        targets=[{'id':f'v{i}','fact_ids':[f'f{i+1}'],'must_show':f'Role {i}',
                  'must_not_show':'Unrelated objects','query':f'Role {i}'} for i in range(3)]
        evidence={'facts':[{'id':f'f{i}'} for i in (1,2,3)]}
        schema=self.ops._inspection_schema(evidence,targets,True)
        receipts={}
        for original in saved['result']['photos']:
            row=deepcopy(original);identity=row.pop('asset_id')
            validate_json(row,schema)
            asset={**self.asset,'id':identity,'visual_targets':targets,
                   'visual_qualification_protocol':'qualified-target-v1'}
            receipt=self.ops._inspection_receipt(asset,evidence,row,{'receipt_id':'saved'})
            receipts[identity]=(asset,receipt)
        asset,receipt=receipts['pixabay:7381976']
        self.assertEqual(set(matched_targets(asset,receipt)),{'v2'})
        receipt['target_matches'][2]['visible_detail']=''
        self.assertEqual(matched_targets(asset,receipt),{})
        for identity in ('wikimedia:116034921','pexels:9850703','wikimedia:32200400'):
            asset,receipt=receipts[identity]
            self.assertFalse(receipt['accepted'])
            self.assertEqual(matched_targets(asset,receipt),{})

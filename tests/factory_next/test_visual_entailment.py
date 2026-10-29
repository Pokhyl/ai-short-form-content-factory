"""Saved failure replay with controlled verdicts; not live semantic acceptance."""
import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock
from material_first.visual_entailment import apply_review, verified, review_batch, POLICY
from material_first.targets import matched_targets
from factory_v3.preflight import digest


class VisualEntailmentTests(TestCase):
    def setUp(self):
        saved=json.loads((Path(__file__).parents[2]/'acceptance/factory-next/component-contract-result-20261029.json').read_text())
        self.receipts=saved['receipts']
        self.evidence={'facts':[{'id':f'f{i}','text':f'Controlled full claim {i}'} for i in (1,2,3)]}
        targets=[{'id':f'v{i}','fact_ids':[f'f{i+1}'],'must_show':f'Role {i}',
                  'must_not_show':'Unrelated subjects','query':f'Role {i}'} for i in range(3)]
        self.assets=[{'id':r['asset_id'],'sha256':r['asset_sha256'],
                     'visual_targets':targets,'visual_qualification_protocol':'qualified-target-v1',
                     'visual_entailment_policy':POLICY} for r in self.receipts]
        for r in self.receipts:r['visual_targets_sha256']=digest(targets)
        self.verdict={'facts':{f'f{i}':{'verdict':'not_visible','reason':'Mechanism not visible'} for i in (1,2,3)},
                      'targets':{f'v{i}':{'verdict':'exact_match' if i==1 else 'component_only',
                                         'reason':'Controlled independent comparison'} for i in range(3)}}
        self.provenance={'receipt_id':'independent-review','model':'controlled'}

    def test_saved_false_causal_observation_is_downgraded(self):
        a,r=self.assets[2],self.receipts[2]
        self.assertEqual(r['direct_fact_ids'],['f3'])
        result=apply_review(a,self.evidence,r,self.verdict,self.provenance)
        self.assertEqual(result['direct_fact_ids'],[])
        self.assertEqual(result['visible_fact_details'][0]['relationship'],'topic_context')
        self.assertTrue(verified(a,self.evidence,result))
        result['direct_fact_ids']=['f3']
        self.assertFalse(verified(a,self.evidence,result))

    def test_saved_false_qualified_target_is_removed_but_component_role_remains(self):
        a,r=self.assets[1],self.receipts[1]
        self.assertEqual(set(matched_targets(a,r)),{'v0','v1'})
        result=apply_review(a,self.evidence,r,self.verdict,self.provenance)
        self.assertEqual(set(matched_targets(a,result)),{'v1'})
        result['target_matches'][0]['matches']=True
        self.assertFalse(verified(a,self.evidence,result))

    def test_review_cannot_upgrade_prior_rejections_or_context(self):
        verdict=deepcopy(self.verdict)
        for d in verdict['facts'].values():d['verdict']='entire_claim_visible'
        for d in verdict['targets'].values():d['verdict']='exact_match'
        for a,r in zip(self.assets,self.receipts):
            reviewed=apply_review(a,self.evidence,r,verdict,self.provenance)
            self.assertEqual(reviewed['accepted'],r['accepted'])
            self.assertEqual(reviewed['direct_fact_ids'],r['direct_fact_ids'])
            self.assertEqual(reviewed['target_matches'],r['target_matches'])

    def test_review_is_bound_to_exact_assets_sources_targets_and_separate_receipt(self):
        a,r=self.assets[1],self.receipts[1]
        result=apply_review(a,self.evidence,r,self.verdict,self.provenance)
        for key in ('asset_sha256','evidence_sha256','targets_sha256','inspection_receipt_id'):
            altered=deepcopy(result);altered['visual_entailment'][key]='wrong'
            self.assertFalse(verified(a,self.evidence,altered))
        result['visual_entailment']['provenance']['receipt_id']=r['receipt_id']
        self.assertFalse(verified(a,self.evidence,result))

    def test_one_independent_call_only_for_accepted_rows_and_no_retry(self):
        ops=Mock();ops._photo=lambda a:{'bytes':b'controlled','mime_type':'image/jpeg'}
        ops._image_metadata=lambda a:{}
        ops.gemini.generate.return_value=({a['id']:self.verdict for a,r in zip(self.assets,self.receipts) if r['accepted']},self.provenance)
        results=review_batch(ops,self.assets,self.evidence,self.receipts)
        self.assertEqual(results[0],self.receipts[0])
        ops.gemini.generate.assert_called_once()
        self.assertNotIn('accepted',str(ops.gemini.generate.call_args.args[2]))
        ops.gemini.generate.reset_mock();ops.gemini.generate.side_effect=TimeoutError()
        with self.assertRaises(TimeoutError):review_batch(ops,self.assets,self.evidence,self.receipts)
        ops.gemini.generate.assert_called_once()

    def test_actual_independent_response_removed_both_false_claims(self):
        saved=json.loads((Path(__file__).parents[2]/'acceptance/factory-next/independent-visibility-result-20261029.json').read_text())
        self.assertEqual(saved['result']['status'],'passed')
        rows={r['asset_id']:r for r in saved['receipts']}
        self.assertFalse(rows['wikimedia:116034921']['accepted'])
        for identity in ('pexels:9850703','wikimedia:32200400','pixabay:7381976'):
            row=rows[identity]
            self.assertTrue(row['accepted'])
            self.assertEqual(row['direct_fact_ids'],[])
            matches={m['target_id'] for m in row['target_matches'] if m['matches']}
            self.assertEqual(matches,{'v2'} if identity=='pixabay:7381976' else {'v1'})
            self.assertTrue(all(v['verdict']=='not_visible' for v in row['visual_entailment']['verdict']['facts'].values()))

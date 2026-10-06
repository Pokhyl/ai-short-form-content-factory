import copy,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from material_first.operations import Operations
from material_first.metadata import receipt
from material_first.engine import Producer,verify,inspected_material
from material_first.visuals import POLICY
from factory_v3.preflight import digest
from test_engine import Operations as Fixtures

class MetadataFixtures(Fixtures):
    presentation_policy=POLICY
    visual_validation_mode='metadata'
    def __init__(self, root):
        super().__init__(root,['photo']*16)
        self.targets=[{'id':'v'+str(i),'fact_ids':['f'+str(i)],'must_show':'Setting '+str(i),
                       'must_not_show':'Unrelated subject','query':q}
                      for i,q in enumerate(['bread flour','bread dough','bread loaf'])]
        self.gemini=Mock()
        self.gemini.generate.side_effect=AssertionError('Vision must not be called')
        self.real=Operations(root,None,self.gemini,None,None)
        self.real.visual_validation_mode='metadata'
        for i,a in enumerate(self.assets):
            f=root/a['path'];f.write_bytes(b'\xff\xd8\xffcontrolled '+str(i).encode())
            a.update(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),description=self.targets[i%3]['query'],
                     discovery_query=self.targets[i%3]['query'],discovery_target_id=self.targets[i%3]['id'],
                     visual_targets=copy.deepcopy(self.targets))
    def research(self, request):
        return {**super().research(request),'queries':copy.deepcopy(self.targets),'visual_targets':copy.deepcopy(self.targets)}
    def inspect_many(self, assets, evidence):return self.real.inspect_many(assets,evidence)
    def compose(self, context):
        return {'beats':[{'material_id':m['id'],'fact_ids':m['supported_fact_ids'],
                         'visual_target_id':next(iter(m['matched_visual_targets'])), 'narration':'Source fact '+str(i)}
                        for i,m in enumerate(context['materials'][:5])]}

class MetadataModeTests(unittest.TestCase):
    def test_metadata_freezes_distinct_originals_without_any_vision_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops=MetadataFixtures(Path(tmp))
            frozen=Producer(tmp,ops,probe=ops.probe).prepare('Bread','ru',30)
            payload=verify(tmp,frozen,ops.probe)
            self.assertEqual(payload['visual_validation_mode'],'metadata')
            self.assertEqual(len(payload['visuals']),15)
            self.assertEqual(len({a['sha256'] for a in payload['assets']}),15)
            ops.gemini.generate.assert_not_called()
            for observed in payload['observations']:
                self.assertEqual(observed['inspection']['validation_method'],'metadata')
                self.assertNotIn('model',observed['inspection'])
            altered=copy.deepcopy(frozen);altered['payload']['visual_validation_mode']='gemini';altered['sha256']=digest(altered['payload'])
            with self.assertRaisesRegex(ValueError,'mode changed'):verify(tmp,altered,ops.probe)
    def test_metadata_receipt_rejects_irrelevant_synthetic_and_changed_descriptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops=MetadataFixtures(Path(tmp));a=copy.deepcopy(ops.assets[0])
            valid=receipt(a,ops.evidence)
            a['description']='Bread diagram'
            self.assertFalse(receipt(a,ops.evidence)['accepted'])
            a['description']='Office desk'
            self.assertFalse(receipt(a,ops.evidence)['accepted'])
            with self.assertRaisesRegex(ValueError,'receipt changed'):
                inspected_material(a,valid,ops.evidence,{f['id']:f for f in ops.evidence['facts']},'metadata')
    def test_mode_checks_actual_original_bytes_before_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            ops=MetadataFixtures(Path(tmp));a=ops.assets[0]
            (Path(tmp)/a['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError):ops.inspect_many([a],ops.evidence)
            ops.gemini.generate.assert_not_called()

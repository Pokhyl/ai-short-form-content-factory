import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from factory_v3.gemini import array, obj, string
from material_first.retrieved_contexts import _repair_duplicate_context_labels
from material_first.targets import validate_targets


class RetrievedContextRepairTests(unittest.TestCase):
    def test_live_duplicate_neutron_star_labels_get_one_bounded_repair(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/duplicate-neutron-context-plan.json').read_text())
        metadata=fixture['metadata']
        known={row['id']:{'id':row['id'],'description':row['title'],
                         'source_metadata':{'title':row['title']}} for row in metadata}
        anchors=[{'id':row['id']} for row in metadata]
        selected=fixture['duplicate_plan']
        fact_ids=['fact-1','fact-2','fact-3']
        schema=obj({key:obj({'anchor_id':string(known),
            'english_photo_object':{**string(),'maxLength':100},
            'source_mention':{**string(),'maxLength':160},
            'support_span_ids':array(string(['s1-0-1094','s1-1094-2113','s1-2113-3302']),1,3),
            'fact_ids':array(string(fact_ids),1,8)}) for key in ('v0','v1','v2')})
        repaired={key:dict(row) for key,row in selected.items()}
        repaired['v0'].update(anchor_id='wikimedia:155249958',english_photo_object='pulsar')
        repaired['v2'].update(anchor_id='wikimedia:125053149',english_photo_object='Vela supernova remnant')
        gemini=Mock();gemini.generate.return_value=(repaired,{})
        spans=[{'id':'s1-0-1094','source_id':'source','text':'Нейтронная звезда формируется.'},
               {'id':'s1-1094-2113','source_id':'source','text':'Нейтронную зорю наблюдают как пульсар.'},
               {'id':'s1-2113-3302','source_id':'source','text':'После коллапса возникает сверхновую.'}]
        result=_repair_duplicate_context_labels(gemini,{'topic':'Нейтронная звезда'},
            [{'id':identity} for identity in fact_ids],spans,schema,selected,anchors,known)
        self.assertEqual(gemini.generate.call_count,1)
        self.assertEqual(gemini.generate.call_args.args[0],'material-photo-plan-structural-repair')
        self.assertEqual([result[key]['english_photo_object'] for key in ('v0','v1','v2')],
                         ['pulsar','supernova remnant','Vela supernova remnant'])
        self.assertEqual(result['v1'],selected['v1'])
        targets=[{'id':key,'fact_ids':row['fact_ids'],'must_show':row['english_photo_object'],
                  'query':row['english_photo_object'],'must_not_show':'unrelated imagery'}
                 for key,row in result.items()]
        validate_targets(targets,set(fact_ids))

    def test_distinct_contexts_do_not_make_a_repair_call(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/duplicate-neutron-context-plan.json').read_text())
        selected={key:dict(row) for key,row in fixture['duplicate_plan'].items()}
        selected['v2']['english_photo_object']='pulsar'
        known={row['id']:{'id':row['id'],'description':row['title'],
                         'source_metadata':{'title':row['title']}} for row in fixture['metadata']}
        gemini=Mock()
        spans=[{'id':span,'source_id':'source','text':'Нейтронная звезда нейтронную зорю сверхновую'}
               for span in ('s1-0-1094','s1-1094-2113','s1-2113-3302')]
        result=_repair_duplicate_context_labels(gemini,{'topic':'Нейтронная звезда'},[],spans,{},
            selected,[{'id':identity} for identity in known],known)
        self.assertEqual(result,selected)
        gemini.generate.assert_not_called()


if __name__=='__main__':
    unittest.main()

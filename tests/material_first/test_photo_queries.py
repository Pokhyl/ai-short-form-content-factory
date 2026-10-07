import unittest
from types import SimpleNamespace
from material_first.photo_queries import photograph_query, described_as_synthetic
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY, LEGACY_POLICY


class PhotographSearchTests(unittest.TestCase):
    def test_unobservable_modifiers_removed_without_replacing_actual_entity(self):
        for query, expected in [('neutron star artist concept','neutron star'),
                                ('pulsar magnetic field beam','pulsar'),
                                ('neutron star magnetosphere','neutron star'),
                                ('diagram of office stapler mechanism','office stapler mechanism'),
                                ('Crab Nebula supernova remnant','Crab Nebula supernova remnant'),
                                ("artist’s impression of a steam engine",'a steam engine')]:
            self.assertEqual(photograph_query(query),expected)
        with self.assertRaises(ValueError):photograph_query('artist concept')

    def test_known_art_excluded_but_companion_illustrator_credit_not_a_photo_rejection(self):
        self.assertTrue(described_as_synthetic({'description':'A pulsar', 'source_metadata':{'title':"File:Artist's concept of PSR B1257.jpg"}}))
        self.assertFalse(described_as_synthetic({'description':'X-ray observation of a pulsar', 'source_metadata':{'imageinfo':[{'extmetadata':{'Artist':{'value':'Illustrations: Controlled'}}}]}}))

    def test_whole_photo_search_keeps_all_aspects_and_prioritizes_caption_match_without_excluding_sparse_photos(self):
        calls=[]
        pool=[{'id':'a','description':'A hermit crab'}, {'id':'b','description':'Crab Nebula observation'},
              {'id':'c','description':'', 'source_metadata':{'title':'File:Observation.jpg'}},
              {'id':'d','description':'Artist concept of Crab Nebula'}]
        def search(provider,query,orientation):
            calls.append((provider,query,orientation));return {'candidates':pool}
        ops=Operations('.',None,None,SimpleNamespace(search=search),None)
        found=ops.discover({'seconds':15,'presentation_policy':TOPIC_POLICY},['Crab Nebula'])
        self.assertEqual([a['id'] for a in found],['b','a','c'])
        self.assertEqual(len(calls),3);self.assertEqual({x[2] for x in calls},{'all'})
        calls.clear()
        legacy=ops.discover({'seconds':15,'presentation_policy':LEGACY_POLICY},['Crab Nebula'])
        self.assertEqual([a['id'] for a in legacy],['a','b','c','d'])
        self.assertEqual({x[2] for x in calls},{'all'})

    def test_deeper_relevant_results_are_not_buried_by_equal_provider_quotas(self):
        calls=[]
        queries=['Crab Nebula','Cassiopeia remnant','Westerlund cluster']
        def search(provider,query,orientation):
            calls.append((provider,query,orientation))
            rows=[{'id':provider+query+str(i), 'description':query if provider=='wikimedia' else 'Generic wallpaper'} for i in range(12)]
            if provider=='pexels':rows[0]['description']=''
            return {'candidates':rows}
        found=Operations('.',None,None,SimpleNamespace(search=search),None).discover(
            {'seconds':60,'presentation_policy':TOPIC_POLICY},queries)
        self.assertEqual(len(found),30)
        self.assertEqual(len(calls),9)
        self.assertEqual(len({c['id'] for c in found}),30)
        for query in queries:
            self.assertIn('wikimedia'+query+'7',{c['id'] for c in found})
            for provider in ('wikimedia','pexels','pixabay'):
                self.assertIn(provider+query+'0',{c['id'] for c in found})
        self.assertTrue(all(c['visual_qualification_protocol']=='qualified-target-v1' for c in found))

    def test_file_title_can_rank_sparse_caption_without_admitting_it_as_visible_proof(self):
        from material_first.photo_queries import relevance
        self.assertEqual(relevance({'description':'','source_metadata':{'title':'File:Crab Nebula.jpg'}},'Crab Nebula'),2)

    def test_explicit_computer_simulation_is_not_a_photograph_caption(self):
        self.assertTrue(described_as_synthetic({'description':'This simulation shows orbiting objects'}))
        self.assertTrue(described_as_synthetic({'description':'New supercomputer simulations explore plasma'}))
        self.assertFalse(described_as_synthetic({'description':'A photograph of a physical supercomputer'}))
        self.assertFalse(described_as_synthetic({'description':'A Hubble observation compared with a simulation'}))

    def test_actual_saved_pools_keep_budget_and_initial_provider_exposure(self):
        import json
        from pathlib import Path
        saved=json.loads((Path(__file__).parent/'fixtures/saved-neutron-query-pools.json').read_text())
        def search(provider,query,orientation):
            return {'candidates':next(p['candidates'] for p in saved['pools'] if p['provider']==provider and p['query']==query)}
        found=Operations('.',None,None,SimpleNamespace(search=search),None).discover(
            {'seconds':60,'presentation_policy':TOPIC_POLICY},saved['targets'])
        self.assertEqual(len(found),30)
        self.assertEqual(len({c['id'] for c in found}),30)
        self.assertGreater(sum(c['provider']=='wikimedia' for c in found),11)
        for provider in ('wikimedia','pexels','pixabay'):
            self.assertTrue(any(c['provider']==provider for c in found))
        self.assertFalse(any(described_as_synthetic(c) for c in found))

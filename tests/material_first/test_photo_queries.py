import unittest
from types import SimpleNamespace
from material_first.photo_queries import photograph_query, described_as_synthetic
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY, LEGACY_POLICY


class PhotographSearchTests(unittest.TestCase):
    def test_unobservable_modifiers_removed_without_replacing_actual_entity(self):
        for query, expected in [('neutron star artist concept','neutron star'),
                                ('pulsar magnetic field beam','pulsar'),
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

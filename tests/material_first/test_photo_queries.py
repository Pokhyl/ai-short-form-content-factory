import unittest
from types import SimpleNamespace
from material_first.photo_queries import photograph_query, described_as_synthetic, observational_archive_topic
from material_first.operations import Operations
from material_first.presentation import TOPIC_POLICY, LEGACY_POLICY


class PhotographSearchTests(unittest.TestCase):
    def test_actual_caption_approved_poster_is_excluded_before_any_model_call(self):
        import json, copy
        from pathlib import Path
        saved = json.loads((Path(__file__).parent/'fixtures/actual-caption-review-false-positive-27fb.json').read_text())
        poster = next(c for c in saved['candidates'] if c['id'] == 'wikimedia:83600934')
        observation = next(c for c in saved['candidates'] if c['id'] == 'wikimedia:35293317')
        self.assertTrue(saved['model_results']['material-photo-plan-review']['contexts']['v2']['metadata_compatible'])
        self.assertTrue(described_as_synthetic(poster))
        self.assertFalse(described_as_synthetic(observation))
        original = {'evidence': {'facts': []}, 'required_fact_ids': ['f1'], 'queries': ['pulsar']}
        brief = copy.deepcopy(original)
        def search(*args): return {'candidates': [poster, observation]}
        def generate(*args, **kwargs): self.fail('caption model must not run before pixels')
        ops = Operations('.', None, SimpleNamespace(generate=generate), SimpleNamespace(search=search), None)
        ops.availability_first_contexts = True
        resolved, candidates = ops.resolve_photos({'topic': 'Neutron star', 'seconds': 60,
            'presentation_policy': TOPIC_POLICY, 'visual_validation_mode': 'gemini'}, brief)
        self.assertEqual([c['id'] for c in candidates], [observation['id']])
        self.assertTrue(resolved.pop('_pixel_review_fallback'))
        self.assertEqual(resolved, original)
        self.assertEqual(brief, original)
        self.assertNotIn('visual_targets', candidates[0])
        self.assertEqual(candidates[0]['visual_qualification_protocol'], 'qualified-target-v1')

    def test_actual_celestia_category_rejects_render_but_keeps_observations(self):
        import json
        from pathlib import Path
        saved = json.loads((Path(__file__).parent/'fixtures/actual-photo-plan-53a0.json').read_text())
        decisions = {c['id']: described_as_synthetic(c) for c in saved['candidates']}
        self.assertEqual(decisions, {'wikimedia:129539683': False,
                                    'wikimedia:177378121': False, 'wikimedia:1758217': True})
        calls = []
        def search(provider, query, orientation):
            calls.append(provider)
            return {'candidates': saved['candidates']}
        ops = Operations('.', None, None, SimpleNamespace(search=search), None)
        candidates = ops.discover({'topic': 'Neutron star', 'seconds': 60,
                                  'presentation_policy': TOPIC_POLICY}, ['neutron star'])
        self.assertEqual({c['id'] for c in candidates},
                         {'wikimedia:129539683', 'wikimedia:177378121'})
        self.assertEqual(calls, ['wikimedia'])

    def test_provenance_categories_do_not_reject_photographed_equipment_or_processed_data(self):
        for categories in ('Computer simulation laboratories', 'False-color astronomical images',
                           'Photographs of artists', 'Hubble images of individual stars'):
            candidate = {'description': 'Actual observation', 'source_metadata': {
                'imageinfo': [{'extmetadata': {'Categories': {'value': categories}}}]}}
            self.assertFalse(described_as_synthetic(candidate), categories)

    def test_remote_astronomical_objects_use_observational_archive_search(self):
        for topic in ('Neutron star', 'Pulsar PSR J0437', 'Нейтронная звезда', 'Нейтронна зоря'):
            self.assertTrue(observational_archive_topic(topic))
        for topic in ('How coffee is roasted', 'How a factory makes steel'):
            self.assertFalse(observational_archive_topic(topic))

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
        self.assertTrue(described_as_synthetic({'description':"Computer artist's rendering of a compact neutron star with accretion disk."}))
        self.assertTrue(described_as_synthetic({'source_metadata':{'title':"File:Artist's rendering of neutron star.png"}}))
        self.assertTrue(described_as_synthetic({'description':"Artist's rendition of a distant galaxy."}))
        for title, description in [
            ('File:Image 13382-4U-1820-30.jpg', 'Size comparison of a neutron star and white dwarf'),
            ('File:Neutron Star characteristics.png', 'Neutron Star characteristics'),
            ('File:Neutron star over Munich.jpg', 'Displayed at the ESO Supernova Planetarium and Visitor Centre'),
            ('File:Neutron star infographic.jpg', 'An infographic about neutron stars'),
        ]:
            self.assertTrue(described_as_synthetic({'description':description,'source_metadata':{'title':title}}))
        self.assertFalse(described_as_synthetic({'description':'Direct Hubble observation of a lone neutron star',
            'source_metadata':{'title':'File:Hubble Sees a Neutron Star Alone in Space.jpg'}}))
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

    def test_astronomy_search_uses_wikimedia_instead_of_generic_stock_results(self):
        calls=[]
        def search(provider,query,orientation):
            calls.append((provider,query,orientation))
            return {'candidates':[{'id':provider+str(len(calls)),'description':'Direct observatory image'}]}
        ops=Operations('.',None,None,SimpleNamespace(search=search),None)
        rows=ops.discover({'topic':'Нейтронная звезда','seconds':60,'presentation_policy':TOPIC_POLICY},
                          ['neutron star','pulsar','supernova remnant'])
        self.assertEqual([row[0] for row in calls],['wikimedia']*3)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(row['topic_protocol']=='topic-specific-v1' for row in rows))

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
        self.assertEqual(len(found),45)
        self.assertEqual(len(calls),9)
        self.assertEqual(len({c['id'] for c in found}),45)
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
        self.assertEqual(len(found),45)
        self.assertEqual(len({c['id'] for c in found}),45)
        self.assertGreater(sum(c['provider']=='wikimedia' for c in found),11)
        for provider in ('wikimedia','pexels','pixabay'):
            self.assertTrue(any(c['provider']==provider for c in found))
        self.assertFalse(any(described_as_synthetic(c) for c in found))

    def test_actual_art_query_becomes_an_observable_entity_requirement(self):
        import json
        from pathlib import Path
        saved=json.loads((Path(__file__).parent/'fixtures/observable-candidate-failure.json').read_text())
        contexts=saved['model_brief']['photo_contexts']
        self.assertEqual(photograph_query(contexts['subject']['query']),'neutron star space')
        self.assertEqual(photograph_query(contexts['detail']['query']),'pulsar')
        self.assertIn('Художня',contexts['subject']['subject'])
        self.assertIn('Стилізоване',contexts['detail']['subject'])

    def test_actual_tiny_candidate_is_excluded_before_download_and_other_pools_survive(self):
        import json
        from pathlib import Path
        small=json.loads((Path(__file__).parent/'fixtures/observable-candidate-failure.json').read_text())['small_asset']
        good=dict(small,id='adequate-observation',width=1920,height=1920)
        search=SimpleNamespace(search=lambda *args:{'candidates':[small,good]})
        found=Operations('.',None,None,search,None).discover({'seconds':60,'presentation_policy':TOPIC_POLICY},['pulsar'])
        self.assertEqual([c['id'] for c in found],['adequate-observation'])
        self.assertEqual(small['width'],300);self.assertEqual(small['height'],200)

    def test_provider_source_slug_declaring_visualization_rejects_even_with_sparse_caption(self):
        self.assertTrue(described_as_synthetic({'description':'A star in space',
            'source_url':'https://www.pexels.com/photo/dramatic-visualization-of-magnetic-neutron-star-38039464/'}))
        self.assertTrue(described_as_synthetic({'description':'A subject',
            'source_url':'https://www.pexels.com/photo/artist-s-concept-of-a-star-1/'}))
        self.assertFalse(described_as_synthetic({'description':'A photograph of an artist',
            'source_url':'https://www.pexels.com/photo/an-artist-at-work-1/'}))

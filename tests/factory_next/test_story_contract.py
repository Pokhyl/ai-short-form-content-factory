import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from factory_next.story_contract import story_contract,assemble_story,sufficient_fact_anchors


class StoryContractTests(TestCase):
    def setUp(self):
        saved=json.loads((Path(__file__).parent/'fixtures/actual-story-4369.json').read_text())
        self.source=saved['context']['outputs']['research']
        self.photos=saved['context']['outputs']['materials']['photos']

    def test_actual_four_photos_need_another_distinct_observed_anchor(self):
        required=self.source['request']['required_fact_ids']
        self.assertFalse(sufficient_fact_anchors(required,self.photos))
        with self.assertRaisesRegex(ValueError,'insufficient distinct anchors'):
            story_contract(self.source['request'],self.source['evidence'],self.photos)

    def test_augmenting_assignment_keeps_source_ids_and_distinct_photos(self):
        # Explicit synthetic eligibility control, not accepted additional media.
        photos=deepcopy(self.photos)
        photos.append({**photos[-1],'id':'controlled-second-autumn','sha256':'a'*64})
        beats,schema=story_contract(self.source['request'],self.source['evidence'],photos)
        self.assertEqual(len({v['material_id'] for v in beats.values()}),3)
        for beat in beats.values():
            photo=next(p for p in photos if p['id']==beat['material_id'])
            self.assertIn(beat['fact_ids'][0],photo['supported_fact_ids'])
        reply={key:{'narration':'Controlled structural prose, not factual acceptance.'} for key in beats}
        result=assemble_story(reply,beats,schema)
        self.assertEqual([b['fact_ids'] for b in result['beats']],[['f1'],['f2'],['f3']])
        reply['beat_3']['fact_ids']=['f1']
        with self.assertRaises(ValueError):assemble_story(reply,beats,schema)

    def test_unobserved_mechanism_uses_existing_topic_policy_without_inventing_pixels(self):
        photos=deepcopy(self.photos)
        for p in photos:p['supported_fact_ids']=[f for f in p['supported_fact_ids'] if f!='f3']
        beats,_=story_contract(self.source['request'],self.source['evidence'],photos)
        self.assertEqual(beats['beat_3']['visual_relation'],'topic_context')
        self.assertEqual(len({b['material_id'] for b in beats.values()}),3)

    def test_repeated_pixels_cannot_supply_missing_anchor(self):
        photos=deepcopy(self.photos)
        photos.append({**photos[-1],'id':'different-url-same-image'})
        with self.assertRaisesRegex(ValueError,'photo identities'):
            story_contract(self.source['request'],self.source['evidence'],photos)

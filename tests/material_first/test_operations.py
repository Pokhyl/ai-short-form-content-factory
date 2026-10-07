import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from factory_v3.gemini import validate_json, provider_schema
from material_first.operations import Operations, preparation_budgets
from material_first.engine import Producer
from test_engine import Operations as Fixtures


class Model:
    model = 'controlled-model'
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []
        for i, asset in enumerate(fixtures.assets):
            asset.setdefault('description', 'Controlled physical detail ' + str(i % 3))
    def generate(self, key, instruction, context, schema, **kwargs):
        self.calls.append(key)
        provider_schema(schema)
        if key == 'material-brief':
            facts = copy.deepcopy(self.fixtures.evidence['facts'])
            for fact in facts:
                fact['support'] = [{'span_id': next(s['id'] for s in context['source_spans']
                    if support['source_id'] == s['source_id'] and support['quote'] in s['text'])}
                    for support in fact['support']]
            result = {'facts': facts,
                      'required_fact_ids': ['f0', 'f1', 'f2'], 'photo_contexts': {
                          role: {'subject': 'Prominent explanatory detail '+str(i), 'query': 'detail '+str(i), 'fact_ids':['f'+str(i)]}
                          for i, role in enumerate(('setting', 'subject', 'detail'))}}
        elif key == 'material-photo-plan':
            result = {'contexts': [{'anchor_id': context['candidates'][i]['id'],
                                    'object_label': 'detail ' + str(i), 'fact_ids': ['f' + str(i)]}
                                   for i in range(3)]}
        elif key.startswith('material-inspect-batch:'):
            saved_calls = self.calls[:]
            row_schema = copy.deepcopy(schema['properties']['photos']['items'])
            del row_schema['properties']['asset_id']; row_schema['required'].remove('asset_id')
            rows = []
            for asset in context['assets']:
                row, _ = self.generate('material-inspect:' + asset['id'], instruction, context, row_schema)
                rows.append({**row, 'asset_id': asset['id']})
            self.calls = saved_calls
            result = {'photos': rows}
        elif key.startswith('material-inspect:'):
            result = {'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                      'medium':'photograph','topic_relation':{'kind':'direct_subject','visible_subject':'Fixture subject','connection':'Depicts the supplied actual subject'},
                      'visible_description': 'Real subject visible',
                      'visible_fact_details': [{'fact_id': f, 'detail': 'Concrete visible structure '+f}
                                               for f in ['f0', 'f1', 'f2']]}
            if context.get('visual_targets') is not None:
                role = int(key.rsplit('a', 1)[1]) % 3
                result['target_matches'] = [{'target_id': t['id'], 'matches': t['id'] == 'v'+str(role),
                    'detail_prominent': t['id'] == 'v'+str(role), 'visible_detail': 'Observed concrete detail '+str(role)}
                    for t in context['visual_targets']]
                if 'subject_qualifications_match' in schema['properties']['target_matches']['items']['properties']:
                    for match in result['target_matches']:
                        match['subject_qualifications_match'] = True
        elif key == 'material-language-edit':
            assert set(context) == {'language', 'narration'}
            result = {'narration':context['narration'][:]}
        elif key == 'material-compose':
            words = ['Source-supported'] + ['narration'] * (schema['properties']['words']['minItems'] - 1 if 'words' in schema['properties'] else 23)
            count = schema['properties']['beats']['minItems']
            result = {'words': words, 'beats': [
                {'material_id': context['materials'][i]['id'],
                 'word_start': len(words)*i//count, 'word_end': len(words)*(i+1)//count,
                 'fact_ids': ['f'+str(i%3)], 'visual_target_id': 'v'+str(i%3)} for i in range(count)]}
            if 'words' not in schema['properties']:
                for beat in result['beats']:
                    beat['narration']=' '.join(words[beat.pop('word_start'):beat.pop('word_end')])
                del result['words']
        else:
            raise AssertionError(key)
        validate_json(result, schema)
        return copy.deepcopy(result), {'receipt_id': key}
    def review_script(self, context):
        result = self.fixtures.review_script(context)
        from material_first.presentation import TOPIC_POLICY
        if context.get('presentation_policy') == TOPIC_POLICY: result['native_language_quality'] = True
        return result


class OperationTests(unittest.TestCase):
    def test_observed_source_copy_russianisms_cannot_pass_ukrainian_surface_gate(self):
        from material_first.paragraphs import validate_native_surface
        for text in ['спалаху сверхнової', 'радіус остатка зорі', 'оболонка відброшується', 'ы']:
            with self.subTest(text=text), self.assertRaises(ValueError): validate_native_surface('uk', text)
        validate_native_surface('uk', 'Залишок зорі: оболонка відкидається під час спалаху наднової.')
        validate_native_surface('ru', 'Вспышка сверхновой')

    def test_large_original_photos_split_before_model_claim_without_reencoding(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fixtures = Fixtures(root, ['photo'] * 4)
            originals = {}
            for i, asset in enumerate(fixtures.assets):
                data = b'\xff\xd8\xff' + bytes([i]) * (3 * 1024 * 1024)
                (root / asset['path']).write_bytes(data)
                asset['sha256'] = hashlib.sha256(data).hexdigest()
                originals[asset['id']] = data
            model = Model(fixtures); generate = model.generate; batches = []
            def checked(key, instruction, context, schema, **kwargs):
                if 'photos' in kwargs:
                    photos = kwargs['photos']; batches.append([p['asset_id'] for p in photos])
                    self.assertLessEqual(sum(len(p['bytes']) for p in photos), 8 * 1024 * 1024)
                    for photo in photos: self.assertEqual(photo['bytes'], originals[photo['asset_id']])
                return generate(key, instruction, context, schema, **kwargs)
            model.generate = checked
            operations = Operations(root, None, model, None, fixtures)
            receipts = operations.inspect_many(fixtures.assets, fixtures.evidence)
            self.assertEqual([r['asset_id'] for r in receipts], [a['id'] for a in fixtures.assets])
            self.assertEqual([len(b) for b in batches], [2, 2])
            self.assertEqual(sum(k.startswith('material-inspect-batch:') for k in model.calls), 2)

    def test_saved_uk60_95_words_preserved_without_rewrite_or_trailing_clause_loss(self):
        import json
        from material_first.visuals import POLICY
        saved = json.loads((Path(__file__).parent / 'fixtures/neutron-uk60-word-count-failure.json').read_text())
        response = saved['responses']['material-compose']
        self.assertEqual(len(response['words']), 95)
        self.assertEqual(response['beats'][-1]['word_end'], 91)
        contexts = saved['responses']['material-brief']['photo_contexts']
        targets = [{'id': 'v'+str(i), 'must_show': contexts[role]['subject'], 'must_not_show': 'Diagrams',
                    'fact_ids': ['fact-'+str(i) for i in range(1,9)], 'query': contexts[role]['query']}
                   for i, role in enumerate(('setting','subject','detail'))]
        materials = [{'id': b['material_id']} for b in response['beats']]
        calls = []
        def generate(key, instruction, context, schema):
            calls.append(key); validate_json(response, schema)
            return copy.deepcopy(response), {'receipt_id': 'saved-real-draft'}
        context = {'request': {'seconds': 60, 'presentation_policy': POLICY, 'visual_targets': targets},
                   'materials': materials, 'evidence': {'sources': [],
                     'facts': saved['responses']['material-brief']['facts']}}
        draft = Operations('.', None, SimpleNamespace(generate=generate), None, None).compose(context)
        self.assertEqual(calls, ['material-compose'])
        self.assertEqual(' '.join(b['narration'] for b in draft['beats']), ' '.join(response['words']))
        self.assertEqual(draft['beats'][-1]['fact_ids'], response['beats'][-1]['fact_ids'])

    def test_topic_related_photo_without_visible_fact_detail_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'])
            asset = fixtures.assets[0]
            import hashlib
            file = root / asset['path']
            file.write_bytes(b'\xff\xd8\xffcontrolled-photo')
            asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = SimpleNamespace(model='controlled-model', generate=lambda *args, **kwargs:
                ({'accepted': True, 'is_real_material': True, 'subject_fully_visible': True,
                  'visible_description': 'Bee sitting on a flower', 'visible_fact_details': [],
                  'medium':'photograph','topic_relation':{'kind':'direct_subject','visible_subject':'Bee','connection':'Actual subject'}},
                 {'receipt_id': 'inspection'}))
            result = Operations(root, None, model, None, None).inspect(asset, fixtures.evidence)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['supported_fact_ids'], [])

    def test_real_adapter_contracts_connect_research_search_inspection_and_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            import hashlib
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffcontrolled-photo' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = Model(fixtures)
            searches = []
            def search(provider, query, orientation):
                searches.append((provider, query, orientation))
                return {'candidates': fixtures.assets}
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=search), fixtures)
            frozen = Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertEqual(len(frozen['payload']['scenes']), 3)
            self.assertEqual({s['visual_target_id'] for s in frozen['payload']['scenes']}, {'v0', 'v1', 'v2'})
            self.assertEqual(len(searches), 9)
            self.assertEqual(model.calls[0], 'material-brief')
            self.assertEqual(model.calls[-1], 'material-language-edit')
            self.assertEqual(sum(k.startswith('material-inspect-batch:') for k in model.calls), 2)
            self.assertEqual(len(frozen['payload']['visuals']), 5)
            self.assertEqual(preparation_budgets(60)['gemini'], 16)
            from material_first.engine import verify
            from factory_v3.preflight import digest
            altered = copy.deepcopy(frozen)
            altered['payload']['visual_targets'][0]['must_show'] = 'Different explanatory detail'
            altered['sha256'] = digest(altered['payload'])
            with self.assertRaisesRegex(ValueError, 'asset targets differ'):
                verify(root, altered, fixtures.probe)

    def test_six_topic_related_photos_with_one_visual_role_stop_before_composition(self):
        from material_first.engine import MaterialUnavailable
        class SameRoleModel(Model):
            def generate(self, key, *args, **kwargs):
                result, provenance = super().generate(key, *args, **kwargs)
                if key.startswith('material-inspect:'):
                    for match in result['target_matches']:
                        match['matches'] = match['target_id'] == 'v0'
                        match['detail_prominent'] = match['target_id'] == 'v0'
                return result, provenance
        with tempfile.TemporaryDirectory() as directory:
            import hashlib
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffphoto' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = SameRoleModel(fixtures)
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=lambda *args: {'candidates': fixtures.assets}), fixtures)
            with self.assertRaisesRegex(MaterialUnavailable, 'different explanatory visuals unavailable'):
                Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertNotIn('material-compose', model.calls)

    def test_missing_exact_third_role_does_not_block_a_varied_contextual_short(self):
        class TwoRoleModel(Model):
            def generate(self, key, *args, **kwargs):
                result, provenance = super().generate(key, *args, **kwargs)
                if key.startswith('material-inspect:'):
                    role = int(key.rsplit('a', 1)[1]) % 2
                    for match in result['target_matches']:
                        match['matches'] = match['target_id'] == 'v'+str(role)
                        match['detail_prominent'] = match['matches']
                elif key == 'material-compose':
                    for i, beat in enumerate(result['beats']):
                        beat['visual_target_id'] = 'v'+str(i%2)
                return result, provenance
        with tempfile.TemporaryDirectory() as directory:
            import hashlib
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffphoto' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            model = TwoRoleModel(fixtures)
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=lambda *args: {'candidates': fixtures.assets}), fixtures)
            frozen = Producer(root, operations, probe=fixtures.probe).prepare('topic', 'pl', 15)
            self.assertEqual({s['visual_target_id'] for s in frozen['payload']['scenes']}, {'v0', 'v1'})
            self.assertEqual(len(frozen['payload']['scenes']), 3)

    def test_total_narration_budget_blocks_before_voice(self):
        from material_first.operations import NarrationBudgetExceeded
        model = SimpleNamespace(generate=lambda *args, **kwargs:
            ({"words": ["word"] * 50, "beats": []}, {}))
        operations = Operations('.', None, model, None, None)
        context = {"request": {"seconds": 15}, "materials": [{"id": "a"+str(i)} for i in range(5)],
                   "evidence": {"facts": [{"id": "f"}]}}
        with self.assertRaises(NarrationBudgetExceeded):
            operations.compose(context)

    def test_exact_source_span_preserves_intervening_heading(self):
        import hashlib
        from material_first.operations import contiguous_support
        from factory_v3.grounding import validate_evidence
        text = 'First statement. Section heading Second statement.'
        evidence = {'sources': [{'id': 's', 'url': 'https://example.invalid/source',
            'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}],
            'facts': [{'id': 'f', 'text': 'Source-backed claim', 'support': [
                {'source_id': 's', 'quote': 'First statement. Second statement.'}]}]}
        resolved = contiguous_support(evidence)
        validate_evidence(resolved)
        self.assertEqual(resolved['facts'][0]['support'][0]['quote'], text)
        evidence['facts'][0]['support'][0]['quote'] = 'First statement. Invented statement.'
        with self.assertRaises(ValueError):
            validate_evidence(contiguous_support(evidence))

    def test_two_photos_cannot_become_an_entire_short(self):
        from material_first.engine import MaterialUnavailable
        model = SimpleNamespace(generate=lambda *args, **kwargs: self.fail("model called with insufficient photos"))
        operations = Operations('.', None, model, None, None)
        with self.assertRaises(MaterialUnavailable):
            operations.compose({"request": {"seconds": 15}, "materials": [{"id": "a"}, {"id": "b"}]})

    def test_saved_english_case_uses_eight_accepted_photos_instead_of_demanding_ten(self):
        import json
        saved = json.loads((Path(__file__).parent / 'fixtures/coffee-en30-cadence-failure.json').read_text())
        self.assertEqual(len(saved['materials']), 8)
        class Composer:
            def generate(self, key, instruction, context, schema):
                count = len(context['materials'])
                assert schema['properties']['beats']['minItems'] <= count == 8
                words = ['word'] * schema['properties']['words']['minItems']
                return {'words': words, 'beats': [
                    {'material_id': m['id'], 'word_start': len(words)*i//count,
                     'word_end': len(words)*(i+1)//count,
                     'fact_ids': m['supported_fact_ids'],
                     'visual_target_id': next(iter(m['matched_visual_targets']))}
                    for i,m in enumerate(context['materials'])]}, {}
        context = {'request': {'seconds': 30, 'visual_targets': saved['visual_targets']},
                   'materials': saved['materials'], 'evidence': {'facts': saved['facts']}}
        draft = Operations('.', None, Composer(), None, None).compose(context)
        self.assertEqual(len(draft['beats']), 8)

    def test_longer_duration_keeps_variety_without_requiring_twelve_perfect_candidates(self):
        class Composer:
            def generate(self, key, instruction, context, schema):
                count = len(context['materials'])
                words = ['word'] * schema['properties']['words']['minItems']
                return {'words': words, 'beats': [
                    {'material_id': m['id'], 'word_start': len(words)*i//count,
                     'word_end': len(words)*(i+1)//count, 'fact_ids': ['f']}
                    for i,m in enumerate(context['materials'])]}, {}
        for seconds,count in [(45, 6), (60, 6), (45, 9), (60, 10)]:
            context = {'request': {'seconds': seconds},
                       'materials': [{'id': 'a'+str(i)} for i in range(count)],
                       'evidence': {'facts': [{'id': 'f'}]}}
            self.assertEqual(len(Operations('.', None, Composer(), None, None).compose(context)['beats']), count)

    def test_independent_photos_allow_three_or_four_narration_paragraphs(self):
        from material_first.visuals import POLICY
        for count in (3, 4):
            with self.subTest(count=count):
                class Composer:
                    def generate(self, key, instruction, context, schema):
                        words = ['source'] * 60
                        draft = {'words': words, 'beats': [
                            {'material_id': 'a'+str(i), 'word_start': 60*i//count,
                             'word_end': 60*(i+1)//count, 'fact_ids': ['f']}
                            for i in range(count)]}
                        validate_json(draft, schema)
                        return draft, {}
                context = {'request': {'seconds':30, 'presentation_policy':POLICY},
                           'materials': [{'id':'a'+str(i)} for i in range(15)],
                           'evidence': {'facts':[{'id':'f'}]}}
                draft = Operations('.', None, Composer(), None, None).compose(context)
                self.assertEqual(len(draft['beats']), count)
                self.assertEqual(' '.join(b['narration'] for b in draft['beats']), ' '.join(['source']*60))
                context['request'].pop('presentation_policy')
                with self.assertRaises(ValueError):
                    Operations('.', None, Composer(), None, None).compose(context)

    def test_saved_ukrainian_source_ellipsis_restores_only_actual_original_text(self):
        import json
        from material_first.operations import contiguous_support
        from factory_v3.grounding import validate_evidence
        saved = json.loads((Path(__file__).parent / 'fixtures/uk60-ellipsis-source-failure.json').read_text())
        with self.assertRaises(ValueError):
            validate_evidence(saved)
        restored = contiguous_support(saved)
        validate_evidence(restored)
        self.assertEqual(restored['facts'][0]['support'][0]['quote'], saved['sources'][0]['text'])
        saved['facts'][0]['support'][0]['quote'] += ' Invented words.'
        with self.assertRaises(ValueError):
            validate_evidence(contiguous_support(saved))

    def test_saved_russian_eighty_word_script_is_not_rejected_for_missing_one_estimated_word(self):
        import json
        saved = json.loads((Path(__file__).parent / 'fixtures/bread-ru45-pacing-failure.json').read_text())
        self.assertEqual(len(saved['draft']['words']), 80)
        class Composer:
            def generate(self, key, instruction, context, schema):
                validate_json(saved['draft'], schema)
                return saved['draft'], {}
        context = {'request': {'seconds':45,'visual_targets':saved['brief']['visual_targets']},
                   'materials':saved['materials'],'evidence':{'facts':saved['brief']['facts']}}
        result = Operations('.',None,Composer(),None,None).compose(context)
        self.assertEqual(' '.join(b['narration'] for b in result['beats']), ' '.join(saved['draft']['words']))

    def test_saved_short_draft_gets_one_length_repair_without_redoing_research_or_images(self):
        import json
        from factory_v3.gemini import ModelSchemaError
        saved = json.loads((Path(__file__).parent / 'fixtures/bread-ru45-short-draft.json').read_text())
        calls = []
        class Composer:
            def generate(self, key, instruction, context, schema):
                calls.append(key)
                if key == 'material-compose':
                    raise ModelSchemaError(copy.deepcopy(saved['draft']), 'array exceeds bounds')
                self_expected = 'material-compose-length-repair'
                assert key == self_expected
                assert context['completed_draft'] == saved['draft']
                words = ['controlled'] * 95
                beats = copy.deepcopy(saved['draft']['beats'])
                for i, beat in enumerate(beats):
                    beat['word_start'] = len(words)*i//len(beats)
                    beat['word_end'] = len(words)*(i+1)//len(beats)
                result = {'words': words, 'beats': beats}
                validate_json(result, schema)
                return result, {}
        context = {'request': {'seconds': 45, 'visual_targets': saved['brief']['visual_targets']},
                   'materials': saved['materials'], 'evidence': {'facts': saved['brief']['facts']}}
        draft = Operations('.', None, Composer(), None, None).compose(context)
        self.assertEqual(len(' '.join(b['narration'] for b in draft['beats']).split()), 95)
        self.assertEqual(calls, ['material-compose', 'material-compose-length-repair'])

    def test_length_repair_never_retries_provider_errors_or_invalid_identities(self):
        from factory_v3.gemini import ModelSchemaError
        from factory_v3.http import HTTPFailure
        context = {'request': {'seconds': 45}, 'materials': [{'id': 'a'+str(i)} for i in range(5)],
                   'evidence': {'facts': [{'id': 'f'}]}}
        errors = [HTTPFailure(429, {}), RuntimeError('ambiguous transport'),
                  ModelSchemaError({'words': ['short'], 'beats': [{'material_id': 'invented'}]}, 'invalid')]
        for error in errors:
            calls = []
            def generate(key, *args, **kwargs):
                calls.append(key)
                raise error
            with self.assertRaises((ValueError, RuntimeError)):
                Operations('.', None, SimpleNamespace(generate=generate), None, None).compose(context)
            self.assertEqual(calls, ['material-compose'])

    def test_invalid_length_repair_is_terminal_after_two_completed_drafts(self):
        from factory_v3.gemini import ModelSchemaError
        import json
        saved = json.loads((Path(__file__).parent / 'fixtures/bread-ru45-short-draft.json').read_text())
        calls = []
        def generate(key, *args, **kwargs):
            calls.append(key)
            raise ModelSchemaError(copy.deepcopy(saved['draft']), 'array exceeds bounds')
        context = {'request': {'seconds': 45, 'visual_targets': saved['brief']['visual_targets']},
                   'materials': saved['materials'], 'evidence': {'facts': saved['brief']['facts']}}
        with self.assertRaises(ModelSchemaError):
            Operations('.', None, SimpleNamespace(generate=generate), None, None).compose(context)
        self.assertEqual(calls, ['material-compose', 'material-compose-length-repair'])

    def test_calm_short_composition_cannot_create_more_anchors_than_the_hold_budget(self):
        from material_first.visuals import CALM_POLICY
        captured=[]
        class Composer:
            def generate(self,key,instruction,context,schema):
                captured.append(schema)
                raise RuntimeError('schema captured before any model call')
        ops=Operations.__new__(Operations);ops.gemini=Composer()
        materials=[{'id':str(i)} for i in range(8)]
        # Only schema construction matters; source evidence stays compactable.
        context={'request':{'seconds':15,'presentation_policy':CALM_POLICY},'materials':materials,'evidence':Fixtures(Path('.'),[]).evidence}
        with self.assertRaisesRegex(RuntimeError,'schema captured'):
            ops.compose(context)
        self.assertEqual(captured[0]['properties']['beats']['maxItems'],6)

    def test_reencoded_duplicate_pool_stops_before_image_calls_and_composition(self):
        import hashlib, base64
        from material_first.engine import MaterialUnavailable
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = Fixtures(root, ['photo'] * 6)
            for i, asset in enumerate(fixtures.assets):
                file = root / asset['path']
                file.write_bytes(b'\xff\xd8\xffcontrolled-photo' + str(i).encode())
                asset['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
                asset['visual_fingerprint'] = {'algorithm':'rgb32-v1', 'source_sha256':asset['sha256'],
                    'width':1080,'height':1920, 'rgb':base64.b64encode(bytes(range(256))*12).decode()}
            model = Model(fixtures)
            operations = Operations(root,
                SimpleNamespace(fetch=lambda *args: fixtures.evidence['sources']), model,
                SimpleNamespace(search=lambda *args: {'candidates':fixtures.assets}), fixtures)
            with self.assertRaisesRegex(MaterialUnavailable,'distinct photographs'):
                Producer(root,operations,probe=fixtures.probe).prepare('topic','pl',15)
            self.assertEqual(sum(k.startswith('material-inspect-batch:') for k in model.calls),1)
            self.assertNotIn('material-compose',model.calls)

    def test_one_stale_dimension_small_file_does_not_abort_other_topic_photos(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);fixtures=Fixtures(root,['photo']*7)
            for i,asset in enumerate(fixtures.assets):
                file=root/asset['path'];file.write_bytes(b'\xff\xd8\xffphoto'+str(i).encode())
                asset['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
                asset.update(width=1920,height=1920)  # Provider may overstate actual selected file.
            model=Model(fixtures)
            operations=Operations(root,SimpleNamespace(fetch=lambda *args:fixtures.evidence['sources']),model,
                SimpleNamespace(search=lambda *args:{'candidates':fixtures.assets}),fixtures)
            probe=lambda path:({'width':300,'height':200,'duration_ms':None} if path.name=='0.jpg' else fixtures.probe(path))
            frozen=Producer(root,operations,probe=probe).prepare('topic','pl',15)
            self.assertNotIn('a0',{a['id'] for a in frozen['payload']['assets']})
            self.assertEqual(len(frozen['payload']['visuals']),5)
            self.assertIn('material-compose',model.calls)

    def test_inspector_receives_bounded_object_identifying_caption(self):
        asset={'source_url':'https://example.invalid/source','author':'Author','license':'CC0',
               'description':'Actual named observational object '+('x'*5000),
               'source_metadata':{'title':'File:Observed object.jpg'}}
        metadata=Operations._image_metadata(asset)
        self.assertEqual(len(metadata['description']),4000)
        self.assertEqual(metadata['file_title'],'File:Observed object.jpg')
        self.assertEqual(metadata['source_url'],asset['source_url'])

    def test_current_physical_target_contract_cannot_retain_a_native_language_art_requirement(self):
        import json
        from material_first.presentation import TOPIC_POLICY
        saved=json.loads((Path(__file__).parent/'fixtures/observable-candidate-failure.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            fixtures=Fixtures(Path(directory),['photo']*3)
            class ArtContextModel(Model):
                def generate(self,key,*args,**kwargs):
                    result,provenance=super().generate(key,*args,**kwargs)
                    if key=='material-brief':
                        for i,role in enumerate(('setting','subject','detail')):
                            result['photo_contexts'][role]={**saved['model_brief']['photo_contexts'][role], 'fact_ids':['f'+str(i)]}
                    return result,provenance
            ops=Operations(directory,SimpleNamespace(fetch=lambda *args:fixtures.evidence['sources']),ArtContextModel(fixtures),None,None)
            brief=ops.research({'topic':'test','language':'uk','seconds':60,'presentation_policy':TOPIC_POLICY})
            for target in brief['visual_targets']:
                self.assertEqual(target['must_show'],target['query'])
                self.assertNotIn('Художня',target['must_show'])
                self.assertNotIn('Стилізоване',target['must_show'])
            self.assertEqual(brief['visual_targets'][1]['must_show'],'neutron star space')
            self.assertEqual(brief['visual_targets'][2]['must_show'],'pulsar')

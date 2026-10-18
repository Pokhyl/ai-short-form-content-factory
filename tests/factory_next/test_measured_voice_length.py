"""Metered measured-voice rewrites and bounded completed-schema repair."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

from factory_next.duration import revision_length_window, revision_length_fits, NaturalDurationRejected
from factory_v3.gemini import ModelSchemaError
from factory_next.preparation import PreparationStages
from factory_next.voice_length_repair import sentence_contract, assemble_sentence_repair


def beats(words):
    text=' '.join(['galaxy']*words)
    lines=[' '.join(text.split()[i::3]) for i in range(3)]
    return {'beats':[{'material_id':f'p{i}',
                      'fact_ids':[f'f{i}'],'narration':line}
                     for i,line in enumerate(lines)]}


class FakeGemini:
    def __init__(self,drafts):
        self.drafts=list(drafts);self.calls=object();self.keys=[];self.reviews=[]
        self.requests=[]
    def generate(self,key,*args):
        self.keys.append(key);self.requests.append(args)
        draft=self.drafts.pop(0)
        if isinstance(draft,Exception):
            raise draft
        return deepcopy(draft),{'cached':True}
    def review_script(self,*args):
        self.reviews.append(1)
        return {'native_language_quality':True}


def sentence_draft(window,scenes,words_per_sentence=None):
    schema,counts=sentence_contract(scenes,window)
    if words_per_sentence is None:
        words_per_sentence=max(5,round(window['target_words']/sum(counts)))
    keys={}
    for i,count in enumerate(counts,1):
        keys['beat_'+str(i)]={ 'sentence_'+str(j+1):
            ' '.join(['galaxy']*(words_per_sentence-1)+[f'galaxy{i}{j}.'])
            for j in range(count)}
    return keys


class LengthProtectionTests(TestCase):
    def context(self):
        old=beats(83)['beats']
        scenes=[{'id':f'b{i}','material_id':f'p{i}','evidence_ids':[f'f{i}'],
                 'narration':x['narration']} for i,x in enumerate(old)]
        return {'id':'11111111-1111-4111-8111-111111111111',
                'request':{'language':'uk','seconds':45},
                'outputs':{
                 'story':{'scenes':scenes,'script':' '.join(['galaxy']*83),
                          'review':{'native_language_quality':True}},
                 'research':{'request':{'language':'uk','seconds':45,'topic':'Andromeda'},
                             'evidence':{'facts':[{'id':f'f{i}'} for i in range(3)]}},
                 'materials':{'photos':[{'id':f'p{i}'} for i in range(3)]}}}

    def run_revision(self,drafts):
        context=self.context()
        gemini=FakeGemini(drafts)
        stage=PreparationStages('/empty',SimpleNamespace(gemini=gemini),lambda:None)
        def bind(_request,_evidence,_photos,draft):
            return [{'id':f'b{i}','material_id':beat['material_id'],
                     'evidence_ids':beat['fact_ids'],'narration':beat['narration']}
                    for i,beat in enumerate(draft['beats'])]
        with patch('factory_next.preparation.validate_story',side_effect=bind),\
             patch('factory_next.preparation.validate_native_surface'),\
             patch('factory_next.preparation.validate_script_review'),\
             patch('factory_next.preparation.compact_materials',return_value=[]):
            result=stage.revise_story({**context,'_voice_correction_round':3},40824)
        return result,gemini

    def test_actual_83_word_audio_40_seconds_rejects_161_word_draft(self):
        base=self.context()['outputs']['story']['script']
        window=revision_length_window(base,40824,45)
        self.assertTrue(86<=window['target_words']<=95)
        self.assertFalse(revision_length_fits(' '.join(['galaxy']*161),window))
        self.assertTrue(revision_length_fits(' '.join(['galaxy']*91),window))

    def test_single_structured_revision_then_independent_review(self):
        old=self.context()['outputs']['story']
        window=revision_length_window(old['script'],40824,45)
        repaired=sentence_draft(window,old['scenes'])
        result,gemini=self.run_revision([repaired])
        self.assertEqual(gemini.keys,['next-measured-duration-revision'])
        self.assertEqual(len(gemini.reviews),1)
        self.assertIn('sentence_limits',gemini.requests[0][1])
        self.assertEqual(len(gemini.requests[0][1]['sentence_limits']['beat_1']),3)
        self.assertTrue(revision_length_fits(result['script'],window))
        self.assertEqual(len(result['scenes']),3)

    def test_live_dna_calibration_bounded_natural_sentences(self):
        original=' '.join(['ДНК']*66)
        # The production script had 512 Ukrainian characters and 66 words;
        # preserve both real measurements without storing an account-dependent
        # provider response in this fixture.
        original='ДНК ' * 66
        original=original.rstrip().ljust(512,'.')
        window=revision_length_window(original,33576,45)
        self.assertEqual(window['target_words'],88)
        self.assertEqual(window['min_words'],83)
        self.assertEqual(window['max_words'],93)
        self.assertEqual(window['min_characters'],625)
        self.assertEqual(window['max_characters'],733)
        scenes=self.context()['outputs']['story']['scenes']
        schema,counts=sentence_contract(scenes,window)
        self.assertEqual(counts,[3,3,2])
        # Eight fluent 11-word fields fit the same calibrated window.
        # No scene, fact identity or independent reviewer is removed.
        rows=sentence_draft(window,scenes,words_per_sentence=11)
        result=assemble_sentence_repair(rows,schema,scenes,window)
        self.assertEqual(len(result['beats']),3)
        self.assertEqual(len(' '.join(b['narration'] for b in result['beats']).split()),88)
        self.assertEqual([b['material_id'] for b in result['beats']],['p0','p1','p2'])

    def test_sentence_contract_across_every_supported_duration(self):
        scenes=self.context()['outputs']['story']['scenes']
        for seconds,measured in ((15,10000),(30,21000),(45,33576),(60,42000)):
            with self.subTest(seconds=seconds):
                script=' '.join(['galaxy']*round(seconds*1.5))
                window=revision_length_window(script,measured,seconds)
                schema,counts=sentence_contract(scenes,window)
                self.assertEqual(len(schema['required']),3)
                self.assertEqual(len(counts),3)
                self.assertTrue(all(1<=count<=5 for count in counts))

    def test_durable_schema_error_repairs_in_one_new_claim_then_reviews(self):
        context=self.context()
        original=context['outputs']['story']
        window=revision_length_window(original['script'],40824,45)
        valid=sentence_draft(window,original['scenes'])
        first=deepcopy(valid)
        first['beat_2']['sentence_2']='Short.'
        received=ModelSchemaError(first,'model response contains empty text')
        result,gemini=self.run_revision([received,valid])
        self.assertEqual(gemini.keys,[
            'next-measured-duration-revision',
            'next-measured-duration-structured-repair'])
        self.assertEqual(len(gemini.reviews),1)
        self.assertEqual(len(gemini.requests),2)
        self.assertIn('rejected_completed_draft',gemini.requests[1][1])
        self.assertEqual(
            gemini.requests[1][1]['rejected_completed_draft'],first)
        self.assertTrue(revision_length_fits(result['script'],window))
        self.assertEqual([x['material_id'] for x in result['scenes']],
                         [x['material_id'] for x in original['scenes']])

    def test_local_length_rejection_repairs_once_without_resynthesizing(self):
        context=self.context()
        original=context['outputs']['story']
        window=revision_length_window(original['script'],40824,45)
        short=sentence_draft(window,original['scenes'],words_per_sentence=2)
        repaired=sentence_draft(window,original['scenes'])
        result,gemini=self.run_revision([short,repaired])
        self.assertEqual(len(gemini.keys),2)
        self.assertEqual(len(gemini.reviews),1)
        self.assertEqual(gemini.keys[1],
                         'next-measured-duration-structured-repair')
        self.assertTrue(revision_length_fits(result['script'],window))

    def test_real_measured_overlong_45s_revision_uses_seven_not_nine_sentences(self):
        # Archived job 30cab913: TTS #1 = 54.504s, 96 words, 789 chars.
        # Gemini wrote 96 then 98 words in nine sentences. The corrected
        # schema must avoid forcing that number of naturally lengthy fields.
        source=('молекула ДНК довга закручена подвійна спіраль ')*16
        source=source.strip().ljust(789,'.')
        window=revision_length_window(source,54504,45)
        self.assertEqual(window['target_characters'],644)
        self.assertEqual(window['min_words'],74)
        self.assertEqual(window['max_words'],84)
        _,counts=sentence_contract(self.context()['outputs']['story']['scenes'],window)
        self.assertEqual(counts,[3,2,2])
        self.assertEqual(sum(counts),7)
        self.assertTrue(all(n>=2 for n in counts))

    def test_schema_sentence_count_tracks_actual_duration_for_all_video_lengths(self):
        scenes=self.context()['outputs']['story']['scenes']
        for seconds in (15,30,45,60):
            # Calibrated words from the actual measured MP3 determine number
            # of natural sentences, never a fixed per-topic 9-field schema.
            window={'target_words':round(seconds*1.8),
                    'target_characters':round(seconds*14)}
            schema,counts=sentence_contract(scenes,window)
            self.assertEqual(sum(counts),max(3,round(window['target_words']/10.6)))
            self.assertEqual(len(counts),3)
            self.assertTrue(all(n>=1 for n in counts))
            self.assertEqual(len(schema['properties']),3)

    def test_saved_ukrainian_45s_response_is_rejected_without_loose_validation(self):
        # Recorded 2026-10-18 real completed model output, no secret fields.
        # TTS #1 = 47.424s, original script 88 words; this reply was
        # 72 words and had a sentence with only 37 (<52) characters.
        scenes=self.context()['outputs']['story']['scenes']
        window={'target_words':83,'min_words':78,'max_words':88,
                'target_characters':673,'min_characters':619,'max_characters':727}
        reply={
            'beat_1':{'sentence_1':'Дезоксирибонуклеїнова кислота або ДНК є важливою макромолекулою живих організмів.',
                      'sentence_2':'Вона складається з двох антипаралельних ланцюгів нуклеотидів.',
                      'sentence_3':'Ці ланцюги закручені у формі складної подвійної спіралі.'},
            'beat_2':{'sentence_1':"Нуклеотиди з'єднуються всередині структури за принципом комплементарності.",
                      'sentence_2':'Аденін завжди утворює пару з тиміном.',
                      'sentence_3':"Гуанін при цьому незмінно поєднується з цитозином, гарантуючи міцність зв'язків."},
            'beat_3':{'sentence_1':'ДНК відповідає за довготривале зберігання нашої біологічної інформації.',
                      'sentence_2':'Вона передає генетичну програму наступним поколінням організмів.',
                      'sentence_3':'Молекула також забезпечує реалізацію життєвих інструкцій клітини через біосинтез білків.'}}
        schema,_=sentence_contract(scenes,window)
        # A previously recorded nine-field response is not valid under a
        # newly calibrated eight-field schema. It remains strictly rejected.
        with self.assertRaises(ValueError):
            assemble_sentence_repair(reply,schema,scenes,window)
        text=' '.join(v for row in reply.values() for v in row.values())
        self.assertEqual(len(text.split()),72)
        self.assertEqual(len(reply['beat_2']['sentence_2']),37)
        self.assertFalse(revision_length_fits(text,window))

    def test_duplicate_sentence_is_not_sent_for_tts(self):
        context=self.context()
        window=revision_length_window(context['outputs']['story']['script'],40824,45)
        schema,_=sentence_contract(context['outputs']['story']['scenes'],window)
        draft=sentence_draft(window,context['outputs']['story']['scenes'])
        sentence=draft['beat_1']['sentence_1']
        draft['beat_1']['sentence_2']=sentence
        with self.assertRaisesRegex(NaturalDurationRejected,'repeats a sentence'):
            assemble_sentence_repair(draft,schema,context['outputs']['story']['scenes'],window)

    def test_invalid_structured_revision_stops_before_review_or_tts(self):
        context=self.context()
        old=self.context()['outputs']['story']
        window=revision_length_window(old['script'],40824,45)
        # Complete sentence fields with only one word each are invalid;
        # do not try a second unreviewed TTS.
        broken=sentence_draft(window,old['scenes'],words_per_sentence=1)
        gemini=FakeGemini([broken,broken])
        stage=PreparationStages('/empty',SimpleNamespace(gemini=gemini),lambda:None)
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaises((NaturalDurationRejected,ValueError)):
                stage.revise_story({**context,'_voice_correction_round':3},40824)
        self.assertEqual(len(gemini.reviews),0)
        self.assertEqual(gemini.keys,[
            'next-measured-duration-revision',
            'next-measured-duration-structured-repair'])


if __name__=="__main__":
    main()

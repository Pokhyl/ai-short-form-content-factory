"""One metered structured Gemini rewrite protects measured voice retries."""
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

from factory_next.duration import revision_length_window, revision_length_fits, NaturalDurationRejected
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
        return deepcopy(self.drafts.pop(0)),{'cached':True}
    def review_script(self,*args):
        self.reviews.append(1)
        return {'native_language_quality':True}


def sentence_draft(window,scenes,words_per_sentence=10):
    schema,counts=sentence_contract(scenes,window)
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

    def test_live_dna_calibration_bounded_nine_natural_sentences(self):
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
        self.assertEqual(counts,[3,3,3])
        # Ten synthetic complete utterances per scene would overshoot;
        # nine complete, 10-word sentences can pass the calibrated contract.
        rows=sentence_draft(window,scenes,words_per_sentence=10)
        result=assemble_sentence_repair(rows,schema,scenes,window)
        self.assertEqual(len(result['beats']),3)
        self.assertEqual(len(' '.join(b['narration'] for b in result['beats']).split()),90)
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
        # Complete sentence fields whose 9 sentences total only 9 words are
        # invalid; do not try a second unreviewed TTS.
        broken=sentence_draft(window,old['scenes'],words_per_sentence=1)
        gemini=FakeGemini([broken])
        stage=PreparationStages('/empty',SimpleNamespace(gemini=gemini),lambda:None)
        with patch('factory_next.preparation.compact_materials',return_value=[]):
            with self.assertRaises((NaturalDurationRejected,ValueError)):
                stage.revise_story({**context,'_voice_correction_round':3},40824)
        self.assertEqual(len(gemini.reviews),0)
        self.assertEqual(len(gemini.keys),1)


if __name__=="__main__":
    main()

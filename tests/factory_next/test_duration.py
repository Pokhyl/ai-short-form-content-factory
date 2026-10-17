import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_next.duration import (duration_fits, revision_word_target,
                                   NaturalDurationRejected)
from factory_next.voice import VoiceStages


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class Provider:
    def __init__(self, sounds):
        self.sounds=list(sounds)
        self.calls=[]
    def synthesize(self, language, text):
        self.calls.append((language,text))
        raw=self.sounds.pop(0)
        return base64.b64encode(raw).decode(), digest(raw)


class Ledger:
    def __init__(self,fail_at=None):
        self.calls=[]
        self.fail_at=fail_at
    def _call(self,sql,args):
        self.calls.append((sql,args))
        if self.fail_at==len(self.calls):
            raise ValueError('quota exhausted')


class Worker:
    def __init__(self,root,durations,fail_on=None):
        self.root=Path(root)
        self.durations=durations
        self.calls=[]
        self.fail_on=fail_on
        self.selected=None
    def request(self,method,url,payload,timeout=None):
        self.calls.append(url)
        if self.fail_on and self.fail_on in url:
            raise TimeoutError('ambiguous worker response')
        raw=base64.b64decode(payload['audio_base64']) if 'audio_base64' in payload else None
        if url.endswith('/voiceover-probe'):
            return {'status':'ready','sha256':digest(raw),
                    'duration_ms':self.durations[raw]}
        if url.endswith('/promote'):
            assert self.selected is not None
            raw=self.selected[1]
            assert payload['expected_sha256']==digest(raw)
            assert payload['expected_duration_ms']==self.durations[raw]
            output=self.root/'voiceovers'/self.selected[0]/'final.mp3'
            output.parent.mkdir(parents=True,exist_ok=False)
            output.write_bytes(raw)
            return {'status':'ready','sha256':digest(raw),
                    'duration_ms':self.durations[raw]}
        if '/voiceover-candidates/' in url:
            job=url.rsplit('/',1)[-1]
            self.selected=(job,raw)
            return {'status':'ready','sha256':digest(raw),
                    'duration_ms':self.durations[raw]}
        raise AssertionError(url)


class NaturalDurationTests(unittest.TestCase):
    def context(self):
        return {'id':str(uuid4()),'request':{'language':'pl','seconds':15},
                'outputs':{'story':{'script':'Original reviewed narration.',
                                     'scenes':[{'id':'beat-1','material_id':'p0',
                                                'narration':'Original reviewed narration.',
                                                'evidence_ids':['f1']}],
                                     'review':{'native_language_quality':True}}}}
    def revision(self):
        return {'script':'Longer revised source-grounded narration.',
                'scenes':[{'id':'beat-1','material_id':'p0',
                           'narration':'Longer revised source-grounded narration.',
                           'evidence_ids':['f1']}],
                'review':{'native_language_quality':True}}

    def create(self,root,durations,fail_at=None,fail_on=None):
        values=list(durations)
        sounds=[('test-audio-%d' % (i+1)).encode() for i in range(len(values))]
        provider=Provider(sounds)
        worker=Worker(root,dict(zip(sounds,values)),fail_on=fail_on)
        quota=Ledger(fail_at)
        stage=VoiceStages(root,provider,worker,quota)
        return stage,provider,worker,quota

    def test_first_actual_measurement_passes_without_correction(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[14500])
            ctx=self.context()
            result=stage.voice(ctx)
            self.assertEqual(result['attempt_count'],1)
            self.assertEqual(len(provider.calls),1)
            self.assertEqual(len(quota.calls),2)
            self.assertEqual(len(worker.calls),3)
            self.assertEqual(result['reviewed_story'],ctx['outputs']['story'])
            self.assertEqual(result['audio_tempo_factor'],1)
            self.assertEqual((Path(root)/'voiceover-attempts'/ctx['id']/'attempt-1.mp3').read_bytes(),b'test-audio-1')

    def test_second_reviewed_attempt_is_measured_and_selected(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[9000,14900])
            ctx=self.context()
            revisions=[]
            def rewrite(context,measured):
                revisions.append(measured)
                return self.revision()
            result=stage.voice(ctx,revision_builder=rewrite)
            self.assertEqual(revisions,[9000])
            self.assertEqual(result['attempt_count'],2)
            self.assertEqual(result['reviewed_story']['script'],self.revision()['script'])
            self.assertEqual(result['duration_ms'],14900)
            self.assertEqual(len(provider.calls),2)
            self.assertEqual(len(quota.calls),4)
            self.assertIn(':voice:1',quota.calls[0][1][0])
            self.assertIn(':voice:2',quota.calls[2][1][0])
            self.assertEqual(sum('/voiceover-candidates/' in u and not u.endswith('/promote')
                                 for u in worker.calls),1)
            self.assertEqual((Path(root)/'voiceovers'/ctx['id']/'final.mp3').read_bytes(),b'test-audio-2')
            self.assertEqual((Path(root)/'voiceover-attempts'/ctx['id']/'attempt-1.mp3').read_bytes(),b'test-audio-1')

    def test_second_attempt_miss_stops_without_promotion_or_third_send(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[9000,11000])
            ctx=self.context()
            with self.assertRaisesRegex(NaturalDurationRejected,'exhausted'):
                stage.voice(ctx,revision_builder=lambda *_:self.revision())
            self.assertEqual(len(provider.calls),2)
            self.assertEqual(len(quota.calls),4)
            self.assertFalse(any('/voiceover-candidates/' in u for u in worker.calls))
            self.assertFalse((Path(root)/'voiceovers'/ctx['id']/'final.mp3').exists())

    def test_missing_independent_revision_review_stops_before_tts_two(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[8000])
            ctx=self.context()
            replacement=self.revision();replacement['review']={}
            with self.assertRaises(NaturalDurationRejected):
                stage.voice(ctx,revision_builder=lambda *_:replacement)
            self.assertEqual(len(provider.calls),1)
            self.assertEqual(len(quota.calls),2)

    def test_quota_failure_for_second_attempt_blocks_synthesis(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[9000],fail_at=3)
            ctx=self.context()
            with self.assertRaisesRegex(ValueError,'quota exhausted'):
                stage.voice(ctx,revision_builder=lambda *_:self.revision())
            self.assertEqual(len(provider.calls),1)
            self.assertEqual(len(quota.calls),3)

    def test_uncertain_worker_send_does_not_fall_back_or_promote(self):
        with tempfile.TemporaryDirectory() as root:
            stage,provider,worker,quota=self.create(root,[14500],fail_on='/voiceover-probe')
            ctx=self.context()
            with self.assertRaises(TimeoutError):
                stage.voice(ctx)
            self.assertEqual(len(provider.calls),1)
            self.assertEqual(len(quota.calls),2)
            self.assertFalse(any('/voiceover-candidates/' in u for u in worker.calls))

    def test_strict_measured_bounds_and_nonbinding_word_hint(self):
        self.assertTrue(duration_fits(14000,15))
        self.assertTrue(duration_fits(15000,15))
        self.assertFalse(duration_fits(13999,15))
        self.assertFalse(duration_fits(15001,15))
        self.assertGreater(revision_word_target('one two three four',9000,15),4)
        for value in (float('nan'),float('inf'),0,-1):
            with self.assertRaises(ValueError):duration_fits(value,15)


if __name__=='__main__': unittest.main()

"""Real MP3 measurements across bounded correction; no provider or production calls."""
import base64
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from factory_next.voice import VoiceStages
from material_first.rendering import probe, sha


def digest(raw):return hashlib.sha256(raw).hexdigest()


class RecordedProvider:
    def __init__(self, originals):
        self.files=iter(originals);self.calls=0
    def synthesize(self,language,script):
        self.calls+=1
        raw=next(self.files).read_bytes()
        return base64.b64encode(raw).decode(),digest(raw)


class MeasuredWorker:
    def __init__(self,root):
        self.root=Path(root)
        self.candidate=None
        self.posts=[]
    def request(self,method,url,payload,timeout=None):
        self.posts.append(url)
        if url.endswith('/voiceover-probe') or '/voiceover-candidates/' in url:
            if 'audio_base64' in payload:
                raw=base64.b64decode(payload['audio_base64'])
                tmp=self.root/('candidate-' + digest(raw)[:12]+'.mp3')
                tmp.write_bytes(raw)
                ms=round(float(probe(tmp)['format']['duration'])*1000)
                tmp.unlink()
                answer={'status':'ready','sha256':digest(raw),'duration_ms':ms}
                if '/voiceover-candidates/' in url:
                    self.candidate=(url.rsplit('/',1)[-1],raw,ms)
                return answer
        if url.endswith('/promote'):
            job,raw,ms=self.candidate
            assert job in url
            assert payload['expected_sha256']==digest(raw)
            assert payload['expected_duration_ms']==ms
            final=self.root/'voiceovers'/job/'final.mp3'
            final.parent.mkdir(parents=True,exist_ok=False)
            final.write_bytes(raw)
            return {'status':'ready','sha256':sha(final),'duration_ms':ms}
        raise AssertionError(url)


class Meter:
    def __init__(self):self.calls=[]
    def _call(self,sql,args):self.calls.append((sql,args))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'requires real FFmpeg')
class RealMeasuredMP3(unittest.TestCase):
    def test_actual_audio_correction_preserves_first_and_promotes_second(self):
        with tempfile.TemporaryDirectory(prefix='factory-next-two-mp3-') as folder:
            root=Path(folder)
            sounds=[]
            for index,duration in enumerate((9.0,14.6),1):
                path=root/f'tts-{index}.mp3'
                subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','lavfi',
                                '-i',f'sine=frequency={400+index*60}:duration={duration}',
                                '-ar','48000','-ac','1','-c:a','libmp3lame','-q:a','4',
                                str(path)],check=True,timeout=20)
                sounds.append(path)
            first=round(float(probe(sounds[0])['format']['duration'])*1000)
            second=round(float(probe(sounds[1])['format']['duration'])*1000)
            self.assertLess(first,14000)
            self.assertGreaterEqual(second,14000)
            self.assertLessEqual(second,15000)
            provider=RecordedProvider(sounds);http=MeasuredWorker(root);quota=Meter()
            stage=VoiceStages(root,provider,http,quota)
            job=str(uuid4())
            original={'script':'Original reviewed text',
                      'scenes':[{'id':'beat-1','material_id':'photo-1',
                                 'narration':'Original reviewed text','evidence_ids':['fact-1']}],
                      'review':{'native_language_quality':True}}
            revised={'script':'More natural sourced words with measured length',
                     'scenes':[{'id':'beat-1','material_id':'photo-1',
                                'narration':'More natural sourced words with measured length',
                                'evidence_ids':['fact-1']}],
                     'review':{'native_language_quality':True}}
            context={'id':job,'request':{'language':'pl','seconds':15},
                     'outputs':{'story':original}}
            result=stage.voice(context,revision_builder=lambda *_:revised)
            self.assertEqual(result['duration_ms'],second)
            self.assertEqual(result['attempt_count'],2)
            self.assertEqual(provider.calls,2)
            self.assertEqual(len(quota.calls),4)
            self.assertEqual(sha(root/'voiceovers'/job/'final.mp3'),sha(sounds[1]))
            self.assertEqual(sha(root/'voiceover-attempts'/job/'attempt-1.mp3'),sha(sounds[0]))
            self.assertEqual(sha(root/'voiceover-attempts'/job/'attempt-2.mp3'),sha(sounds[1]))
            self.assertEqual(result['audio_tempo_factor'],1.0)


if __name__=='__main__':unittest.main()

"""Real localhost media-worker HTTP contract, no external API or live volume."""
import base64
import hashlib
import importlib.util
from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
import unittest
from uuid import uuid4

from factory_next.voice import VoiceStages
from factory_next.pipeline import Pipeline
from factory_next.adapters import FactoryNextAdapters
from factory_next.media import MediaStages
from factory_v3.http import HTTPFailure, JSONHTTP
from factory_v3.worker_adapters import WorkerAdapters
from material_first.rendering import sha


def audio_hash(raw):
    return hashlib.sha256(raw).hexdigest()


def audio_file(directory, name, seconds, frequency):
    path=directory/name
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y',
                    '-f','lavfi','-i',f'sine=frequency={frequency}:duration={seconds}',
                    '-ar','48000','-ac','1','-c:a','libmp3lame','-q:a','4',str(path)],
                   check=True,timeout=25)
    return path


class FixedVoiceProvider:
    def __init__(self,files):
        self.files=iter(files)
        self.calls=0
    def synthesize(self,language,text):
        self.calls+=1
        raw=next(self.files).read_bytes()
        return base64.b64encode(raw).decode(),audio_hash(raw)


class Quota:
    def __init__(self):self.operations=[]
    def _call(self,sql,args):self.operations.append((sql,args))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),
                     'requires actual FFmpeg')
class WorkerHTTPBoundary(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='factory-next-worker-http-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        source=Path(__file__).resolve().parents[2]/'services'/'media-worker'/'server.py'
        spec=importlib.util.spec_from_file_location('factory_next_isolated_media_worker',source)
        self.module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        # Point ALL file-backed voice routes at the isolated directory.
        self.module.DATA_ROOT=self.root
        self.module.VOICEOVER_ROOT=self.root/'voiceovers'
        self.module.VOICEOVER_CANDIDATE_ROOT=self.root/'voiceover-candidates'
        self.module.ALIGNMENT_ROOT=self.root/'alignments'
        self.module.VISUAL_ROOT=self.root/'visuals'
        self.module.RENDER_ROOT=self.root/'renders'
        self.server=ThreadingHTTPServer(('127.0.0.1',0),self.module.Handler)
        self.thread=Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'
        self.http=JSONHTTP()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def create_stage(self,files):
        provider=FixedVoiceProvider(files)
        quota=Quota()
        voice=VoiceStages(self.root,provider,self.http,quota)
        # Production uses the fixed internal worker address; this test alone
        # substitutes the explicitly allowlisted localhost HTTP endpoint.
        voice.worker=WorkerAdapters(self.root,provider,self.url,None,http=self.http)
        return voice,provider,quota

    def context(self,job):
        story={'script':'Grounded first version.',
               'scenes':[{'id':'beat-1','material_id':'photo-a',
                          'narration':'Grounded first version.','evidence_ids':['fact-a']}],
               'review':{'native_language_quality':True}}
        return {'id':job,'request':{'language':'pl','seconds':15},
                'outputs':{'story':story}}

    def test_first_measured_mp3_is_exclusively_promoted_and_rejects_duplicate(self):
        source=audio_file(self.root,'source.mp3',14.6,480)
        voice,provider,quota=self.create_stage([source])
        job=str(uuid4());ctx=self.context(job)
        result=voice.voice(ctx)
        self.assertEqual(result['attempt_count'],1)
        self.assertEqual(sha(self.root/'voiceovers'/job/'final.mp3'),sha(source))
        self.assertEqual(sha(self.root/'voiceover-candidates'/job/'accepted.mp3'),sha(source))
        self.assertEqual(result['duration_ms'],round(float(self.module.ffprobe_audio(source)['duration_ms'])))
        self.assertEqual(len(quota.operations),2)
        self.assertEqual(provider.calls,1)
        # A duplicate job is a conflict, never a silent overwrite.
        raw=source.read_bytes()
        with self.assertRaises(HTTPFailure) as error:
            self.http.request('POST',self.url+'/voiceover-candidates/'+job,
                              {'audio_base64':base64.b64encode(raw).decode()})
        self.assertEqual(error.exception.receipt['status'],409)
        self.assertEqual(sha(self.root/'voiceovers'/job/'final.mp3'),sha(source))

    def test_measured_second_attempt_only_promotes_reviewed_fitting_audio(self):
        first=audio_file(self.root,'too-short.mp3',8.5,420)
        second=audio_file(self.root,'corrected.mp3',14.7,490)
        voice,provider,quota=self.create_stage([first,second])
        job=str(uuid4());context=self.context(job)
        corrected={'script':'Re-reviewed, source grounded longer narration.',
                   'scenes':[{'id':'beat-1','material_id':'photo-a',
                              'narration':'Re-reviewed, source grounded longer narration.',
                              'evidence_ids':['fact-a']}],
                   'review':{'native_language_quality':True}}
        passed=[]
        def revision(ctx,duration):
            passed.append(duration)
            return corrected
        result=voice.voice(context,revision_builder=revision)
        self.assertEqual(result['attempt_count'],2)
        self.assertEqual(result['reviewed_story'],corrected)
        self.assertEqual(provider.calls,2)
        self.assertEqual(len(quota.operations),4)
        self.assertEqual(len(passed),1)
        self.assertLess(passed[0],14000)
        self.assertEqual(sha(self.root/'voiceovers'/job/'final.mp3'),sha(second))
        self.assertEqual(sha(self.root/'voiceover-attempts'/job/'attempt-1.mp3'),sha(first))
        self.assertEqual(sha(self.root/'voiceover-attempts'/job/'attempt-2.mp3'),sha(second))
        self.assertEqual(result['audio_tempo_factor'],1.0)


    def test_full_checkpointed_pipeline_writes_real_mp4_and_passes_audit(self):
        """Real HTTP candidate + real render/audit, controlled non-provider sources/ASR."""
        audio=audio_file(self.root,'narration.mp3',14.6,430)
        voice,provider,quota=self.create_stage([audio])
        self.assertEqual(provider.calls,0)
        photo_dir=self.root/'photos'
        photo_dir.mkdir()
        assets=[];photos=[]
        for index,color in enumerate(('red','green','blue','yellow','magenta','cyan')):
            path=photo_dir/f'frame-{index}.png'
            subprocess.run(['ffmpeg','-nostdin','-v','error','-y',
                            '-f','lavfi','-i',f'color=c={color}:s=144x256:d=0.1',
                            '-frames:v','1',str(path)],check=True,timeout=15)
            signature=sha(path)
            assets.append({'id':f'photo-{index}','path':str(path.relative_to(self.root)),
                           'sha256':signature,'media_type':'photo',
                           'source_url':f'https://example.invalid/fixture/{index}',
                           'author':'local isolated test',
                           'license':'CC0',
                           'license_url':'https://creativecommons.org/publicdomain/zero/1.0/'})
            photos.append({'id':f'photo-{index}','sha256':signature,
                           'media_type':'photo','supported_fact_ids':[f'fact-{index//2}']})
        scenes=[{'id':f'beat-{index+1}','material_id':f'photo-{2*index}',
                 'narration':f'Reviewed source-bound paragraph {index+1}.',
                 'evidence_ids':[f'fact-{index}']} for index in range(3)]
        class LocalPreparation:
            def research(self,context):
                return {'fixture':True,'sources':['offline fixture']}
            def materials(self,context):
                return {'photos':photos,'assets':assets}
            def story(self,context):
                return {'scenes':scenes,
                        'script':' '.join(s['narration'] for s in scenes),
                        'review':{'native_language_quality':True}}
            def revise_story(self,*args):
                raise AssertionError('fitting first attempt must not rewrite')
        def local_alignment(context):
            measured=context['outputs']['voice']
            original=context['outputs']['story']
            duration=measured['duration_ms']
            segments=original['scenes']
            return {'audio_sha256':measured['sha256'],'timings':[
                {'start_ms':duration*i/len(segments),
                 'end_ms':duration*(i+1)/len(segments)}
                for i in range(len(segments))]}
        voice.alignment=local_alignment
        adapters=FactoryNextAdapters(LocalPreparation(),voice,MediaStages(self.root))
        job=str(uuid4())
        checkpoints=self.root/'pipeline-state'
        pipeline=Pipeline(checkpoints,adapters,'d'*40)
        pipeline.create(job,'Controlled photo topic','pl',15)
        for _ in range(8):
            # A newly constructed Pipeline must resume the preceding output
            # without re-sending the provider side effect.
            state=Pipeline(checkpoints,adapters,'d'*40).step(job)
        self.assertEqual(state['status'],'complete')
        self.assertEqual(len(state['receipts']),8)
        self.assertEqual(provider.calls,1)
        self.assertEqual(len(quota.operations),2)
        self.assertTrue(all(state['outputs']['audit']['gates'].values()))
        self.assertEqual(state['outputs']['audit']['duration_ms'],15000)
        result=self.root/'renders'/job/'final.mp4'
        self.assertEqual(sha(result),state['outputs']['render']['sha256'])
        self.assertEqual(sha(audio),state['outputs']['voice']['sha256'])
        self.assertEqual(len({s['material_id'] for s in state['outputs']['edit']['shots']}),
                         len(state['outputs']['edit']['shots']))


if __name__=='__main__': unittest.main()

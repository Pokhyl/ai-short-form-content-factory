"""At most three separately metered natural TTS attempts; store only the measured winner.

No retry after uncertain sends. The Pipeline running checkpoint blocks any
replay of a partly executed voice stage. Each attempt has a distinct quota key,
an exclusive local archive, and measured audio identity.
"""
import base64
import os
from pathlib import Path
from uuid import UUID

from factory_v3.worker_adapters import WorkerAdapters
from material_first.rendering import sha
from .duration import duration_fits, require_reviewed_revision, NaturalDurationRejected


class VoiceStages:
    def __init__(self, root, voice_provider, worker_http, quota_ledger):
        self.root=Path(root)
        self.provider=voice_provider
        self.http=worker_http
        self.quota=quota_ledger
        self.worker=WorkerAdapters(root,voice_provider,'http://shorts-v2-media-worker-1:3001',None,http=worker_http)

    def _synthesize_once(self, job, language, script, attempt):
        if attempt not in (1,2,3):raise ValueError('unbudgeted TTS attempt')
        key='next:'+job+':voice:'+str(attempt)
        sku='wavenet' if language=='ru' else 'chirp3_hd'
        self.quota._call("SELECT factory.reserve_provider_usage(%s,'google_cloud_tts',%s,'characters',"
            "date_trunc('month',CURRENT_DATE)::date,%s,%s,"
            "jsonb_build_object('stage','next_voice','attempt',%s))",
            (key,sku,len(script),job,attempt))
        # Commit the reservation before the uncertain external send.
        self.quota._call('SELECT factory.commit_provider_usage(%s,NULL)',(key,))
        encoded,expected=self.provider.synthesize(language,script)
        measured=self.worker._post('/voiceover-probe',{'audio_base64':encoded})
        if measured.get('status')!='ready' or measured.get('sha256')!=expected:
            raise ValueError('measured audio differs from synthesized audio')
        raw=base64.b64decode(encoded,validate=True)
        if not raw or sha_bytes(raw)!=expected:
            raise ValueError('synthesized byte hash mismatch')
        attempt_dir=self.root/'voiceover-attempts'/job
        attempt_dir.mkdir(parents=True,exist_ok=True)
        path=attempt_dir/('attempt-'+str(attempt)+'.mp3')
        # O_EXCL means a second send may never silently overwrite this attempt.
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o640)
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if sha(path)!=expected:
            raise ValueError('voice attempt archive differs from measured bytes')
        return encoded,measured,expected

    def voice(self, context, *, revision_builder=None):
        request=context['request']
        original=context['outputs']['story']
        job=str(UUID(str(context['id'])))
        script=original['script']
        if not isinstance(script,str) or not script.strip():
            raise ValueError('empty reviewed narration')
        selected_story=original
        for selected_attempt in (1,2,3):
            if selected_attempt>1:
                if revision_builder is None:
                    raise NaturalDurationRejected('reviewed natural-duration correction unavailable')
                # A distinct approved rewrite and ledger namespace is required
                # for each *new* measured MP3. Never resend earlier audio.
                correction_context={**context,
                    'outputs':{**context['outputs'],'story':selected_story},
                    '_voice_correction_round':selected_attempt}
                selected_story=require_reviewed_revision(
                    selected_story,revision_builder(correction_context,measurement['duration_ms']))
                script=selected_story['script']
            encoded,measurement,expected=self._synthesize_once(
                job,request['language'],script,selected_attempt)
            if duration_fits(measurement['duration_ms'],request['seconds']):
                break
        else:
            raise NaturalDurationRejected('three measured natural-voice attempts exhausted')
        # Never upload rejected audio to the final-job namespace.
        staged=self.worker._post('/voiceover-candidates/'+job,
                                 {'audio_base64':encoded})
        if staged.get('status')!='ready' or staged.get('sha256')!=expected or staged.get('duration_ms')!=measurement['duration_ms']:
            raise ValueError('candidate differs from measured voice')
        result=self.worker._post('/voiceover-candidates/'+job+'/promote',
                                  {'expected_sha256':expected,
                                   'expected_duration_ms':measurement['duration_ms']})
        path=self.root/'voiceovers'/job/'final.mp3'
        if result.get('status')!='ready' or result.get('sha256')!=expected or result.get('duration_ms')!=measurement['duration_ms'] or sha(path)!=expected:
            raise ValueError('promoted final voice differs from measured audio')
        return {**result,'storage_path':str(path),'audio_tempo_factor':1.0,
                'attempt_count':selected_attempt,'reviewed_story':selected_story}

    def alignment(self, context):
        voice=context['outputs']['voice']
        story=voice.get('reviewed_story',context['outputs']['story'])
        result=self.worker.align(context['id'],{**context['request'],**story},{'voice':voice})
        return {**result,'timings':result['scene_timings']}


def sha_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()

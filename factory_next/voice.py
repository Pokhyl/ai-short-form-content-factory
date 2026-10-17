"""Natural speech adapter; reserve free-tier quota before the only send."""
from pathlib import Path
from factory_v3.worker_adapters import WorkerAdapters
from material_first.rendering import sha


class VoiceStages:
    def __init__(self, root, voice_provider, worker_http, quota_ledger):
        self.root=Path(root);self.provider=voice_provider;self.http=worker_http;self.quota=quota_ledger
        self.worker=WorkerAdapters(root,voice_provider,'http://shorts-v2-media-worker-1:3001',None,http=worker_http)

    def voice(self, context):
        request=context['request'];script=context['outputs']['story']['script'];job=context['id']
        if not script.strip():raise ValueError('empty reviewed narration')
        key='next:'+job+':voice:1'
        sku='wavenet' if request['language']=='ru' else 'chirp3_hd'
        self.quota._call("SELECT factory.reserve_provider_usage(%s,'google_cloud_tts',%s,'characters',"
            "date_trunc('month',CURRENT_DATE)::date,%s,%s,"
            "jsonb_build_object('stage','next_voice','single_attempt',true))",
            (key,sku,len(script),job))
        self.quota._call('SELECT factory.commit_provider_usage(%s,NULL)',(key,))
        encoded,expected=self.provider.synthesize(request['language'],script)
        result=self.worker._post('/voiceovers/'+job,{'audio_base64':encoded})
        path=self.root/'voiceovers'/job/'final.mp3'
        if result.get('status')!='ready' or result.get('sha256')!=expected or sha(path)!=expected:
            raise ValueError('stored voice differs from synthesized audio')
        return {**result,'storage_path':str(path),'audio_tempo_factor':1.0}

    def alignment(self, context):
        story=context['outputs']['story'];voice=context['outputs']['voice']
        result=self.worker.align(context['id'],{**context['request'],**story},{'voice':voice})
        return {**result,'timings':result['scene_timings']}

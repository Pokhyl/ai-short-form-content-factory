"""Actual whole-photo rendering and independent byte-level media audit."""
import json
from pathlib import Path

from factory_v3.preflight import asset_path, validate_asset
from material_first.presentation import TOPIC_POLICY, render_whole_photos
from material_first.rendering import sha
from material_first.qa import audit_whole


class MediaStages:
    def __init__(self, media_root):
        self.root=Path(media_root).resolve()

    def render(self, context):
        outputs=context['outputs'];job_id=context['id'];edit=outputs['edit']
        voice=outputs['voice'];alignment=outputs['alignment']
        source=self.root/'voiceovers'/job_id/'final.mp3'
        if sha(source)!=voice['sha256'] or alignment['audio_sha256']!=voice['sha256']:
            raise ValueError('measured audio identity changed')
        assets={a['id']:a for a in outputs['materials']['assets']}
        photos=[];segments=[]
        for shot in edit['shots']:
            asset=assets[shot['material_id']]
            validate_asset(self.root,asset)
            path=asset_path(self.root,asset['path'])
            photos.append(path)
            segments.append({**shot,'asset_path':str(path),'asset_sha256':asset['sha256']})
        directory=self.root/'renders'/job_id
        proof=render_whole_photos(directory,source,photos,context['request']['seconds'],
            policy=TOPIC_POLICY,timeline=[{k:s[k] for k in ('start_frame','end_frame')} for s in edit['shots']])
        if proof['source_audio_duration_ms']!=voice['duration_ms']:
            raise ValueError('measured duration changed')
        manifest={'sha256':proof['video_sha256'],'input_audio_sha256':voice['sha256'],
                  'fitted_audio_sha256':proof['fitted_audio_sha256'],
                  'audio_duration_ms':voice['duration_ms'],'audio_tempo_factor':1.0,
                  'duration_policy':TOPIC_POLICY,'segments':segments}
        (directory/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False))
        return {**manifest,'path':str(directory/'final.mp4')}

    def audit(self, context):
        outputs=context['outputs'];shots=outputs['edit']['shots']
        selected={s['material_id'] for s in shots}
        payload={**context['request'],'presentation_policy':TOPIC_POLICY,
                 'visuals':shots,'assets':[a for a in outputs['materials']['assets'] if a['id'] in selected]}
        return audit_whole(self.root,context['id'],payload,outputs['render']['sha256'],
                           outputs['voice']['sha256'],timings=outputs['alignment']['timings'])

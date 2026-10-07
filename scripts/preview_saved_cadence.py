"""Separate cached editing preview: no new request, model, source or TTS calls."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
from uuid import UUID
from factory_v3.runtime import Runtime, load_settings
from material_first.presentation import CALM_POLICY, render_whole_photos
from material_first.rendering import sha
from material_first.visuals import make_visuals, ordered_visuals

parser=argparse.ArgumentParser()
parser.add_argument('--id',required=True)
args=parser.parse_args()
identity=str(UUID(args.id))
runtime=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
state=runtime.ledger.snapshot(identity)
if state['status']!='qa_pass': raise ValueError('preview requires an existing completed video')
payload=deepcopy(state['frozen']['payload'])
payload['presentation_policy']=CALM_POLICY
payload['visuals']=make_visuals(payload['seconds'],payload['observations'],payload['scenes'],CALM_POLICY)
selected={v['material_id'] for v in payload['visuals']}
payload['assets']=[a for a in payload['assets'] if a['id'] in selected]
payload['observations']=[m for m in payload['observations'] if m['id'] in selected]
voice,alignment=state['outputs']['voice'],state['outputs']['align']
original=Path(state['outputs']['render']['storage_path'])
source=Path('/data/voiceovers')/identity/'final.mp3'
if sha(original)!=state['outputs']['render']['sha256'] or sha(source)!=voice['sha256']:
    raise ValueError('original media changed')
ordered=ordered_visuals(payload,alignment['scene_timings'],voice['duration_ms'])
original_segments={s['material_id']:s for s in state['outputs']['render']['segments']}
photos=[original_segments[v['material_id']]['asset_path'] for v in ordered]
timeline=[{k:v[k] for k in ('start_frame','end_frame')} for v in ordered]
directory=Path('/data/checks/cadence-v2')/identity
directory.parent.mkdir(parents=True,exist_ok=True)
proof=render_whole_photos(directory,source,photos,payload['seconds'],policy=CALM_POLICY,timeline=timeline)
assert sha(original)==state['outputs']['render']['sha256'] and sha(source)==voice['sha256']
frames=[(c['start_frame']+c['end_frame'])//2 for c in timeline]
selection='+'.join(f'eq(n,{i})' for i in frames)
subprocess.run(['ffmpeg','-nostdin','-v','error','-n','-i',str(directory/'final.mp4'),
 '-vf',f"select='{selection}',scale=180:320,tile=6x{(len(frames)+5)//6}",'-frames:v','1','-threads','1',str(directory/'contact.jpg')],check=True,timeout=60)
receipt={'kind':'cached_editing_preview','original_id':identity,'runtime_revision':runtime.revision,
 'requested_seconds':payload['seconds'],'image_count':len(ordered),'hold_seconds':[(c['end_frame']-c['start_frame'])/30 for c in timeline],
 'new_model_calls':0,'new_tts_calls':0,'database_writes':0,'original_video_unchanged':True,
 'source_audio_unchanged':True,'policy':CALM_POLICY,'proof':proof,'human_pass':False,
 'quality_limits':'Original narration and photo inspection quality retained; this preview only changes editing pace.'}
(directory/'preview.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='proof'}))

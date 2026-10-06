"""Isolated PhotoWorker stage/render/QA on saved real media, zero provider calls.

Mount saved media read-only at /saved-data, an empty writable directory at
/fixture, and the checkout at /checkout. Not a production job/model review.
"""
import json
import shutil
import sys
import uuid
from pathlib import Path
from material_first.worker import PhotoWorker
from material_first.visuals import POLICY
from material_first.rendering import probe, sha

case, identity = sys.argv[1:3]
uuid.UUID(identity)
root, saved = Path('/fixture'), Path('/saved-data')
plan = json.loads((Path('/checkout/acceptance/factory-v3') / f'whole-photo-{case}-plan-20261006.json').read_text())
proof = json.loads(Path('/checkout/acceptance/factory-v3/whole-photo-previews-20261006.json').read_text())
previous = next(p for p in proof['preview_cases'] if p['case'] == case)
original = root / 'originals';original.mkdir(exist_ok=False)
assets, observations, visuals = [], [], []
for i,entry in enumerate(plan['photos']):
    source = saved / entry['path'];assert sha(source) == entry['sha256']
    file = original / (str(i) + source.suffix);shutil.copyfile(source,file)
    metadata = entry['asset']
    assets.append({**metadata,'id':'fixture-'+str(i),'path':str(file.relative_to(root)),
        'sha256':entry['sha256'],'framing':'original-whole','media_type':'photo'})
    observations.append({'id':'fixture-'+str(i),'supported_fact_ids':['source-fact'],
                         'matched_visual_targets':{}})
    visuals.append({'id':'photo-'+str(i+1),'material_id':'fixture-'+str(i)})
voice = root / 'voiceovers' / identity;voice.mkdir(parents=True,exist_ok=False)
source = saved / plan['audio']['path'];assert sha(source) == plan['audio']['sha256']
shutil.copyfile(source,voice/'final.mp3')
duration = round(float(probe(voice/'final.mp3')['format']['duration'])*1000)
scenes = [{'id':'paragraph-'+str(i),'material_id':assets[i]['id'],
           'narration':'Controlled alignment paragraph '+str(i),'evidence_ids':['source-fact']} for i in range(5)]
payload = {'schema':'material-first','presentation_policy':POLICY,'seconds':plan['seconds'],
           'scenes':scenes,'visuals':visuals,'assets':assets,'observations':observations}
worker = PhotoWorker(root,None,'http://localhost:3001',None)
worker._validate_scene_count(payload)
staged = worker._stage_photos(identity,payload)
outputs = {'voice':{'sha256':plan['audio']['sha256'],'duration_ms':duration,'staged_photos':staged},
           'align':{'audio_sha256':plan['audio']['sha256'],'scene_timings':[
               {'start_ms':duration*i//5,'end_ms':duration*(i+1)//5} for i in range(5)]}}
outputs['render'] = worker.render(identity,payload,outputs)
outputs['qa'] = worker.qa(identity,payload,outputs)
assert outputs['qa']['machine_pass'] is True and outputs['qa']['human_pass'] is False
assert sha(source)==plan['audio']['sha256']
receipt={'isolated':True,'provider_calls':0,'automatic_product':False,'human_pass':False,
         'fixture_id':identity,'case':case,'outputs':outputs}
(root/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'case':case,'fixture_id':identity,'duration_ms':outputs['qa']['duration_ms'],
                  'photos':outputs['qa']['scene_count'],'audio_correlation':outputs['qa']['audio_correlation'],
                  'sha256':outputs['qa']['sha256'],'passed':True}),flush=True)

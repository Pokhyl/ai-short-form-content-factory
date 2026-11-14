#!/usr/bin/env python3
"""Collect existing acceptance jobs and midpoint frames; never create or retry jobs."""
import io,json,sqlite3,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw

root=Path('/data/factory-universal')
plan=json.loads((root/'acceptance-20261114.json').read_text())
conn=sqlite3.connect(root/'jobs.sqlite3');conn.row_factory=sqlite3.Row
out=root/'reviews';out.mkdir(exist_ok=True)
results=[]
for case in plan['jobs']:
 row=conn.execute('SELECT status,stage,error,manifest FROM jobs WHERE id=?',(case['id'],)).fetchone()
 result=case|{'status':row['status'],'stage':row['stage'],'error':row['error']}
 if row['status']=='ready':
  manifest=json.loads(row['manifest']);video=Path(manifest['render']['storage_path']);segments=manifest['render']['segments']
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate,duration','-of','json',str(video)],text=True))['streams'][0]
  result.update({'script':manifest['script'],'audit':manifest['audit'],'render':manifest['render'],'frame_count':int(probe['nb_frames']),'exact_frames':int(probe['nb_frames'])==case['duration_s']*30,'exact_duration':abs(float(probe['duration'])-case['duration_s'])<.001})
  result['llm_calls']=manifest['llm_calls'];result['speech_voice']=manifest['narration']['voice']
  result['hash_matches']=hashlib.sha256(video.read_bytes()).hexdigest()==manifest['render']['sha256']
  cached=out/(case['id']+'-manifest.json');same=cached.exists() and json.loads(cached.read_text())['render']['sha256']==manifest['render']['sha256']
  for offset in ([] if same else range(0,len(segments),12)):
   part=segments[offset:offset+12];cols=3 if len(part)<=9 else 4;canvas=Image.new('RGB',(270*cols,500*((len(part)+cols-1)//cols)),'#17202c')
   for index,segment in enumerate(part):
    sec=(segment['start_ms']+segment['end_ms'])/2000
    raw=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-ss',str(sec),'-i',str(video),'-frames:v','1','-vf','scale=270:480','-f','image2pipe','-vcodec','png','-'],timeout=20)
    frame=Image.open(io.BytesIO(raw));x=(index%cols)*270;y=(index//cols)*500;canvas.paste(frame,(x,y));ImageDraw.Draw(canvas).text((x+5,y+481),str(offset+index+1),fill='white')
   filename=case['id']+'-'+str(offset//12+1)+'.jpg';canvas.save(out/filename,quality=90)
  (out/(case['id']+'-manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 results.append(result)
 print(json.dumps({key:value for key,value in result.items() if key not in {'script','audit','render'}},ensure_ascii=False),flush=True)
plan['results']=results;plan['technical_pass']=all(result['status']=='ready' and result.get('exact_frames') and result.get('exact_duration') and result.get('hash_matches') and result.get('llm_calls')==0 and result.get('audit',{}).get('full_decode') and result['audit']['unique_assets']==result['audit']['shots_required'] and result['audit']['all_images_pixel_checked'] and result['audit']['all_visuals_have_provenance'] and result['audit']['minimum_two_images_per_beat'] and all(result['audit']['renderer_gates'].values()) for result in results)
(root/'acceptance-20261114-results.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))

"""Separate viewing artifacts; never changes or approves a failed production job."""
import hashlib,json,os,shutil,subprocess,sys,uuid,math
from pathlib import Path
from factory_v3.runtime import Runtime,load_settings
from material_first.engine import verify
from material_first.rendering import probe,sha
from scripts.audit_final_media import pcm
r=Runtime(load_settings('/run/factory-v3/settings.json'),'/data',os.environ['FACTORY_V3_REVISION'])
case,source,preview=sys.argv[1:4]
source,preview=str(uuid.UUID(source)),str(uuid.UUID(preview))
state=r.ledger.snapshot(source);p=verify('/data',state['frozen'])
root=Path('/data/manual-previews')/preview
root.mkdir(parents=True,exist_ok=False)
audio_source=Path('/data/voiceovers')/source/'final.mp3'
audio=root/'voice.mp3';shutil.copyfile(audio_source,audio)
assert sha(audio)==sha(audio_source)
duration_ms=round(float(probe(audio)['format']['duration'])*1000)
assets={a['id']:a for a in p['assets']}
word_counts=[len(s['narration'].split()) for s in p['scenes']]
word_total=sum(word_counts);cursor=0;segments=[];manifest=[]
def run(args,timeout=180):
 return subprocess.run(args,check=True,capture_output=True,text=True,timeout=timeout)
for i,scene in enumerate(p['scenes']):
 start=round(duration_ms*cursor/word_total);cursor+=word_counts[i];end=round(duration_ms*cursor/word_total)
 asset=assets[scene['material_id']];file=Path('/data')/asset['path'];assert sha(file)==asset['sha256']
 segment=root/f'segment-{i:02d}.mp4'
 run(['ffmpeg','-nostdin','-v','error','-n','-loop','1','-framerate','30','-i',str(file),
  '-vf','scale=1080:1920,setsar=1,fps=30,format=yuv420p','-an','-c:v','libx264','-threads','1','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-t',f'{(end-start)/1000:.3f}',str(segment)])
 segments.append(segment);manifest.append({'asset_id':asset['id'],'sha256':asset['sha256'],'start_ms':start,'end_ms':end,'narration':scene['narration']})
(root/'concat.txt').write_text(''.join(f"file '{s}'\n" for s in segments))
silent=root/'silent.mp4';final=root/'final.mp4'
run(['ffmpeg','-nostdin','-v','error','-n','-f','concat','-safe','0','-i',str(root/'concat.txt'),'-c','copy',str(silent)])
run(['ffmpeg','-nostdin','-v','error','-n','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',f'{duration_ms/1000:.3f}','-movflags','+faststart',str(final)])
run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(final),'-f','null','-'])
actual=probe(final);video=[s for s in actual['streams'] if s['codec_type']=='video'];sound=[s for s in actual['streams'] if s['codec_type']=='audio']
assert len(actual['streams'])==2 and len(video)==len(sound)==1
assert (video[0]['width'],video[0]['height'],video[0]['codec_name'],video[0]['pix_fmt'],video[0]['r_frame_rate'])==(1080,1920,'h264','yuv420p','30/1')
assert sound[0]['codec_name']=='aac'
encoded_ms=round(float(actual['format']['duration'])*1000);assert abs(encoded_ms-duration_ms)<=100
original_pcm,final_pcm=pcm(audio),pcm(final);n=min(len(original_pcm),len(final_pcm))
correlation=sum(x*y for x,y in zip(original_pcm[:n],final_pcm[:n]))/math.sqrt(sum(x*x for x in original_pcm[:n])*sum(x*x for x in final_pcm[:n]))
assert correlation>=.99 and abs(len(original_pcm)-len(final_pcm))<=1600
indices=[int((s['start_ms']+s['end_ms'])*30/2000) for s in manifest]
select='+'.join('eq(n\\,'+str(i)+')' for i in indices)
run(['ffmpeg','-nostdin','-v','error','-n','-i',str(final),'-vf','select='+select+',scale=180:320,tile='+str(math.ceil(len(indices)/2))+'x2','-frames:v','1','-threads','1',str(root/'contact.jpg')])
proof={'mode':'manual_cached_assembly','automatic_product':False,'production_job_pass':False,'human_pass':False,'audio_listening_claim':False,'source_job':source,'preview_id':preview,'runtime_revision':os.environ['FACTORY_V3_REVISION'],'topic':p['topic'],'language':p['language'],'requested_seconds':p['seconds'],'actual_duration_ms':encoded_ms,'scene_count':len(manifest),'script':p['script'],'scene_timing':'approximate proportional word allocation, not ASR alignment','timing_request_pass':p['seconds']*.8*1000<=duration_ms<=p['seconds']*1.2*1000,'new_provider_calls':0,'new_tts_calls':0,'audio_sha256':sha(audio),'video_sha256':sha(final),'audio_correlation':correlation,'full_decode_pass':True,'format':'1080x1920 H264 yuv420p 30fps AAC','segments':manifest,'output':str(final)}
(root/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
for segment in segments:segment.unlink()
silent.unlink()
print(json.dumps({k:proof[k] for k in ('preview_id','source_job','language','actual_duration_ms','scene_count','video_sha256','audio_correlation','timing_request_pass','output')}),flush=True)

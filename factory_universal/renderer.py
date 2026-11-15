"""Project-owned still-card renderer. No provider calls and no speech tempo changes."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

def digest(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def probe(path):
 result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],check=True,capture_output=True,text=True,timeout=15)
 return json.loads(result.stdout)

def render(jid,payload,data=Path('/data')):
 jid=str(uuid.UUID(jid));data=Path(data).resolve()
 requested=payload['requested_duration_ms'];actual=payload['audio_duration_ms'];target=payload['target_duration_ms']
 if requested not in {15000,30000,45000,60000} or target!=requested or not requested*.90<=actual<=requested:raise ValueError('natural audio does not fit requested duration')
 audio=data/'voiceovers'/jid/'final.mp3'
 if digest(audio)!=payload['input_audio_sha256']:raise ValueError('input narration hash changed')
 if abs(round(float(probe(audio)['format']['duration'])*1000)-actual)>1:raise ValueError('input narration duration changed')
 scenes=payload['scenes'];cursor=0;hashes=set();segments=[];lines=['ffconcat version 1.0']
 if len(scenes)!=requested//2500:raise ValueError('incorrect number of image scenes')
 for order,scene in enumerate(scenes,1):
  start=scene['segment_start_ms'];end=scene['segment_end_ms']
  path=Path(scene['asset_path']).resolve()
  if not path.is_relative_to(data/'visuals'/jid) or not path.is_file():raise ValueError('image is outside job-owned directory')
  if "'" in str(path) or '\n' in str(path):raise ValueError('invalid image path')
  if scene['media_type']!='photo' or start!=cursor or end<=start or start%100 or end%100:raise ValueError('image timeline is invalid')
  sha=digest(path)
  if sha!=scene['asset_sha256'] or sha in hashes:raise ValueError('image hash changed or duplicated')
  if scene['asset_width']!=1080 or scene['asset_height']!=1920:raise ValueError('card dimensions changed')
  hashes.add(sha)
  lines.extend(["file '"+str(path)+"'","option framerate 30",'duration '+format((end-start)/1000,'.3f')])
  segments.append({'scene_uuid':scene['scene_uuid'],'shot_uuid':scene['shot_uuid'],'visual_asset_id':scene['visual_asset_id'],'segment_order':order,'start_ms':start,'end_ms':end,'duration_ms':end-start,'asset_sha256':sha,'media_type':'photo'})
  cursor=end
 if cursor!=requested:raise ValueError('image timeline does not cover requested duration')
 lines.extend(["file '"+str(path)+"'","option framerate 30"])
 directory=data/'renders'/jid;directory.mkdir(parents=True,exist_ok=True)
 timeline=directory/'timeline.ffconcat';timeline.write_text('\n'.join(lines)+'\n')
 output=directory/'final.mp4';draft=directory/'rendering.mp4'
 command=['ffmpeg','-nostdin','-y','-v','error','-f','concat','-safe','0','-i',str(timeline),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-vf','fps=30,scale=in_range=full:out_range=tv,format=yuv420p','-af','apad=whole_dur='+str(requested/1000),'-c:v','libx264','-pix_fmt','yuv420p','-color_range','tv','-threads','2','-preset','veryfast','-crf','20','-c:a','aac','-b:a','192k','-t',str(requested/1000),'-frames:v',str(requested*30//1000),'-movflags','+faststart',str(draft)]
 try:
  result=subprocess.run(command,capture_output=True,text=True,timeout=240)
  if result.returncode:raise ValueError('FFmpeg render failed: '+result.stderr[-600:])
  meta=probe(draft);videos=[s for s in meta['streams'] if s['codec_type']=='video'];audios=[s for s in meta['streams'] if s['codec_type']=='audio']
  if len(videos)!=1 or len(audios)!=1:raise ValueError('render stream count is invalid')
  video=videos[0];sound=audios[0];duration=round(float(video['duration'])*1000)
  gates={'exact_frames':int(video.get('nb_frames',0))==requested*30//1000,'exact_duration':duration==requested,'portrait_dimensions':(video['width'],video['height'])==(1080,1920),'h264':video['codec_name']=='h264','aac':sound['codec_name']=='aac','yuv420p':video['pix_fmt']=='yuv420p','fps_30':video['r_frame_rate']=='30/1','unique_images':len(hashes)==len(scenes),'continuous_timeline':cursor==requested,'unchanged_source_audio':digest(audio)==payload['input_audio_sha256'],'natural_audio_fits':requested*.90<=actual<=requested}
  if not all(gates.values()):raise ValueError('render QA failed: '+','.join(k for k,v in gates.items() if not v))
  draft.replace(output)
  receipt={'status':'ready','job_id':jid,'engine':'project FFmpeg renderer','storage_path':str(output),'manifest_path':str(directory/'manifest.json'),'sha256':digest(output),'bytes':output.stat().st_size,'width':video['width'],'height':video['height'],'video_codec':video['codec_name'],'audio_codec':sound['codec_name'],'pix_fmt':video['pix_fmt'],'fps_num':30,'fps_den':1,'duration_ms':duration,'muxed_audio_duration_ms':round(float(sound['duration'])*1000),'video_stream_count':1,'audio_stream_count':1,'frame_count':int(video['nb_frames']),'audio_duration_ms':actual,'requested_duration_ms':requested,'target_duration_ms':target,'duration_delta_ms':duration-requested,'input_audio_sha256':payload['input_audio_sha256'],'segments':segments,'qa_passed':True,'qa_gates':gates}
  (directory/'manifest.json').write_text(json.dumps(receipt,indent=2))
  return receipt
 finally:
  timeline.unlink(missing_ok=True);draft.unlink(missing_ok=True)

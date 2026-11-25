"""Real renderer regression: accepted natural narration must produce exactly 450 frames."""
from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import subprocess
import uuid
from PIL import Image
from renderer import digest,probe,render

def check():
 with TemporaryDirectory(prefix='factory-render-check-') as temp:
  data=Path(temp);jid=str(uuid.uuid4());voice=data/'voiceovers'/jid;voice.mkdir(parents=True)
  audio=voice/'final.mp3'
  subprocess.run(['ffmpeg','-nostdin','-y','-v','error','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t','13.416','-c:a','libmp3lame',str(audio)],check=True,timeout=15)
  actual=round(float(probe(audio)['format']['duration'])*1000)
  assert 13450<=actual<13500,actual
  scenes=[];images=data/'visuals'/jid;images.mkdir(parents=True)
  for index in range(6):
   path=images/(str(index)+'.jpg');Image.new('RGB',(1080,1920),(30+index*30,40,60)).save(path)
   scenes.append({'scene_uuid':str(uuid.uuid4()),'shot_uuid':str(uuid.uuid4()),'visual_asset_id':str(uuid.uuid4()),'asset_path':str(path),'asset_sha256':digest(path),'media_type':'photo','asset_width':1080,'asset_height':1920,'segment_start_ms':index*2500,'segment_end_ms':(index+1)*2500})
  payload={'requested_duration_ms':15000,'target_duration_ms':15000,'audio_duration_ms':actual,'input_audio_sha256':digest(audio),'scenes':scenes,'attribution':{'adaptation_license':{'name':'CC BY-SA 4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/'},'text':[{'authors':'Example contributors','source_url':'https://example.org/source','changes':'Selected excerpts.'}]}}
  bad=copy.deepcopy(payload);bad['scenes'][1]['asset_path']=bad['scenes'][0]['asset_path'];bad['scenes'][1]['asset_sha256']=bad['scenes'][0]['asset_sha256']
  try:render(jid,bad,data);raise AssertionError('duplicate image accepted')
  except ValueError as error:assert 'duplicated' in str(error)
  receipt=render(jid,payload,data)
  assert receipt['frame_count']==450 and receipt['duration_ms']==15000 and all(receipt['qa_gates'].values())
  subprocess.run(['ffmpeg','-nostdin','-v','error','-i',receipt['storage_path'],'-f','null','-'],check=True,capture_output=True,timeout=30)
  assert (data/'renders'/jid/'credits.txt').is_file()
  assert 'Example contributors' in probe(receipt['storage_path'])['format']['tags']['comment']
  assert receipt['qa_gates']['attribution_embedded']
  assert digest(audio)==payload['input_audio_sha256']
  print('PASS real FFmpeg: 450 frames, 15000 ms, complete decode, unchanged input audio, repeated assets rejected',flush=True)
if __name__=='__main__':check()

import app

def check():
 assert app.tokens('Volcanoes cats dogs species series')==['volcano','cat','dog','species','series']
 parser=app.WikiHTML('en',paragraphs_only=True)
 parser.feed('<h2>History</h2><div>Fragment</div><p>A complete paragraph.</p><ul><li>A list fragment.</li></ul><table><tr><td>Table fragment.</td></tr></table>')
 assert parser.text()=='A complete paragraph.'
 assert app.sentences('Energia zapobiega tzw. letnim blackoutom. Kolejne zdanie.')==['Energia zapobiega tzw. letnim blackoutom.','Kolejne zdanie.']
 for shots,beats in [(6,2),(6,3),(12,5),(18,6),(24,8)]:
  layout=app.shot_beats(shots,beats)
  assert len(layout)==shots and sorted(layout)==layout
  assert all(layout.count(i)>=2 for i in range(beats))
 anchor={'title':'Volcano','text':'Volcanoes emit lava ash magma gas from the crust of Earth.'}
 film={'title':'Volcano (1997 film)','text':'A film about lava ash magma gas in the crust of Earth.'}
 assert app.relevant_sources([film,anchor],'Volcano','en')==[anchor]
 slot={'text':'Solar thermal conversion produces heat.','visual_title':'Solar thermal collector'}
 fossil={'alt':'Chimneys, thermal power station, energy','height':1000,'width':800}
 solar={'alt':'Solar panels for thermal heating on a house','height':1000,'width':800}
 assert app.photo_score(fossil,slot,'Solar energy')<0
 assert app.photo_score(solar,slot,'Solar energy')>=0
 assert app.unsupported_qualifier('The largest mud volcanoes are enormous.','Volcano',[{'title':'Volcano'}])
 assert not app.unsupported_qualifier('The largest mud volcanoes are enormous.','Volcano',[{'title':'Volcano'},{'title':'Mud volcano'}])
 contexts=[{'title':'Lunar eclipse','visual_title':'Lunar eclipse','text':'The Moon moves through the shadow of Earth.'},{'title':'August 2009 lunar eclipse','visual_title':'August 2009 lunar eclipse','text':'The Moon moves through the shadow of Earth.'}]
 assert app.visual_context_title({'text':'The Moon moves through the shadow of Earth.'},contexts,'en')=='Lunar eclipse'
 assert app.photo_score({'alt':'Total solar eclipse of the sun','height':1000,'width':800},{'text':'A lunar eclipse occurs when the Moon enters the shadow of Earth.','visual_title':'Eclipse'},'Lunar eclipse')<0
 assert app.photo_score({'alt':'Total lunar eclipse showing the red Moon','height':1000,'width':800},{'text':'A lunar eclipse occurs when the Moon enters the shadow of Earth.','visual_title':'Lunar eclipse'},'Lunar eclipse')>=0
 assert app.photo_score({'provider':'pixabay','alt':'solar eclipse, eclipse, sun, lunar, moon','height':1000,'width':800},{'text':'A lunar eclipse darkens the Moon.','visual_title':'Eclipse'},'Lunar eclipse')<0
 assert app.photo_score({'provider':'pixabay','alt':'lunar eclipse, fantasy, sci-fi','height':1000,'width':800},{'text':'A lunar eclipse darkens the Moon.','visual_title':'Lunar eclipse'},'Lunar eclipse')<0
 from pathlib import Path
 import json
 fixture_path=Path('/app/fixtures/mixed-language-uk.json')
 if fixture_path.exists():
  fixture=json.loads(fixture_path.read_text())
  slots=app.plan_script(fixture['sources'],fixture['input_topic'],fixture['output_language'],fixture['duration_s'])
  assert len(slots)>=4 and all(slot['language']=='uk' for slot in slots)
  assert all(slot.get('resolved_topic')==fixture['sources'][0]['title'] for slot in slots)
 expected={'en':'en-US-Chirp3-HD-Algenib','pl':'pl-PL-Chirp3-HD-Enceladus','ru':'ru-RU-Wavenet-D','uk':'uk-UA-Chirp3-HD-Enceladus'}
 for lang,name in expected.items():
  request=app.selected_voice_request(lang,'Test text.')
  assert request['voice']['name']==name
  assert request['audioConfig']=={'audioEncoding':'MP3'}
  assert set(request)=={'input','voice','audioConfig'}
 assert app.selected_voice_request('uk','гала́ктики')['input']['text']=='галактики'

 # Regression: the real measured sequence changes text, preserves selected voice, and stops after three sends.
 from unittest.mock import patch
 from tempfile import TemporaryDirectory
 import io,hashlib,uuid
 with TemporaryDirectory() as temp:
  directory=Path(temp);job_id=str(uuid.uuid4());calls=[];plans=[]
  def fake_plan(sources,topic,lang,seconds,max_beats=None):
   plans.append(seconds);return [{'text':'Complete source sentence number '+str(len(plans))+'.','language':lang}]
  def fake_voice(lang,text,jid,attempt):
   calls.append((lang,text,attempt));path=directory/('attempt-'+str(attempt));path.write_bytes(b'unchanged natural voice')
   return path,{'audio_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration_ms':[30384,49056,43176][attempt-1]}
  def fake_alignment(request,timeout):
   payload=json.loads(request.data);scene=payload['scenes'][0]
   return io.BytesIO(json.dumps({'status':'ready','audio_sha256':payload['audio_sha256'],'global_coverage':1.0,'scene_timings':[{'scene_uuid':scene['scene_uuid'],'scene_key':'0','start_ms':0,'end_ms':43150}]}).encode())
  with patch.multiple(app,ROOT=directory,VOICE=directory/'voice',plan_script=fake_plan,google_voice_once=fake_voice,update=lambda *a,**kw:None):
   with patch.object(app.urllib.request,'urlopen',fake_alignment):
    result=app.prepare_selected_narration([], 'topic','uk',job_id,45)
   assert len(calls)==3 and len({text for _,text,_ in calls})==3
   assert result[-1]['voice']=='uk-UA-Chirp3-HD-Enceladus' and result[-1]['audio_tempo_factor']==1.0
   assert result[1].read_bytes()==b'unchanged natural voice'
   with patch.object(app,'google_voice_once',side_effect=TimeoutError('uncertain send')) as failed:
    try:app.prepare_selected_narration([], 'topic','uk',str(uuid.uuid4()),45)
    except TimeoutError:pass
    else:raise AssertionError('uncertain TTS timeout did not stop')
    assert failed.call_count==1


 for text in ['Нарешті, серед взаємодіючих галактик багато систем з активними ядрами.','Такі взаємодіючі системи були виявлені серед відомих галактик.','Імовірно ці галактики розташовані неподалік одна від одної.','Його слабке гравітаційне поле не здатне витримати тиск.','Finally, the stars form a galaxy.','Наконец, галактики сближаются.','Wreszcie galaktyki zderzają się ze sobą.']:
  assert app.context_dependent_sentence(text),text
 assert not app.context_dependent_sentence('Зіткнення галактик є звичайним явищем в еволюції Всесвіту.')
 if fixture_path.exists():
  for duration in (15,30,45,60):
   plan=app.plan_script(fixture['sources'],fixture['input_topic'],'uk',duration)
   assert plan
   positions=[slot['source_position'] for slot in plan];assert positions==sorted(positions)
   for slot in plan:
    assert not app.context_dependent_sentence(slot['text'])
    source=fixture['sources'][slot['source_index']]['text'];start=slot['source_position']
    assert source[start:start+len(slot['source_sentence'])]==slot['source_sentence']

 assert app.sentences('Дослідження проводив Б. А. Воронцов. Наступне речення.')==['Дослідження проводив Б. А. Воронцов.','Наступне речення.']
 assert app.sentences('Це сталося 100 млн. років тому. Інша подія.')==['Це сталося 100 млн. років тому.','Інша подія.']
 assert app.safe_id('../unrelated') is None
 print('PASS: plural normalization, paragraph extraction, complete abbreviations, five shot layouts, homonym exclusion, owned UUID validation')

if __name__=='__main__':check()

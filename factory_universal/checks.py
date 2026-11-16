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
    guard_counts=[]
    result=app.prepare_selected_narration([], 'topic','uk',job_id,45,before_send=lambda slots:guard_counts.append(len(calls)))
    assert guard_counts==[0,1,2]
   assert len(calls)==3 and len({text for _,text,_ in calls})==3
   assert result[-1]['voice']=='uk-UA-Chirp3-HD-Enceladus' and result[-1]['audio_tempo_factor']==1.0
   assert result[1].read_bytes()==b'unchanged natural voice'
   with patch.object(app,'google_voice_once',side_effect=TimeoutError('uncertain send')) as failed:
    try:app.prepare_selected_narration([], 'topic','uk',str(uuid.uuid4()),45)
    except TimeoutError:pass
    else:raise AssertionError('uncertain TTS timeout did not stop')
    assert failed.call_count==1

   def no_images(slots):raise ValueError('no verified images')
   with patch.object(app,'google_voice_once') as unused:
    try:app.prepare_selected_narration([], 'topic','uk',str(uuid.uuid4()),45,before_send=no_images)
    except ValueError as error:assert str(error)=='no verified images'
    else:raise AssertionError('missing images did not stop narration')
    assert unused.call_count==0



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

 # Human identity must come from Commons structured data or the exact Wikidata-linked category.
 from unittest.mock import patch
 profile={'id':'Q123','kind':'human','commons_category':'Example Person','source_url':'https://www.wikidata.org/wiki/Q123'}
 photos=[{'provider':'commons','id':str(i),'source_url':'https://commons.wikimedia.org/?curid='+str(i),'categories':(['Category:Example Person'] if i==4 else [])} for i in range(1,5)]
 response={'entities':{'M1':{'statements':{'P180':[{'mainsnak':{'datavalue':{'value':{'id':'Q123'}}}}]}},'M2':{'statements':{'P180':[{'mainsnak':{'datavalue':{'value':{'id':'Q999'}}}}]}}}}
 with patch.object(app,'cache_fetch',lambda key,fetch:fetch()),patch.object(app,'http_json',lambda *args,**kwargs:response):
  bound=app.bind_human_images(photos,profile)
 assert bound[0]['identity_verification']['entity_id']=='Q123'
 assert 'identity_verification' not in bound[1] and 'identity_verification' not in bound[2]
 assert bound[3]['identity_verification']['basis']=='Wikidata-linked Commons category'
 slot={'entity_profile':profile,'text':'Example Person is a public figure.'}
 portrait={'alt':'Official portrait of Example Person','width':900,'height':1200,'identity_verification':bound[0]['identity_verification']}
 assert app.photo_score(portrait,slot,'Example Person')>=0
 assert app.photo_score(portrait|{'identity_verification':{'entity_id':'Q999'}},slot,'Example Person')<0
 assert app.photo_score(portrait|{'alt':'A letter signed by Example Person'},slot,'Example Person')<0
 assert app.omit_parenthetical_asides('Subject (a date (and an aside)) is a person.')=='Subject is a person.'
 parser=app.WikiHTML('ru',paragraphs_only=True)
 parser.feed('<p>Масса равна 2,5⋅10<sup>16</sup> кг.<sup class="reference">[1]</sup></p>')
 assert '10^16' in parser.text() and '[1]' not in parser.text()
 # Decorative source links are not mathematical exponents.
 parser=app.WikiHTML('uk',paragraphs_only=True)
 parser.feed('<p>Предмет є темою<sup><a href="#section">[⇨]</a></sup> речення.</p>')
 assert parser.text()=='Предмет є темою речення.' or parser.text()=='Предмет є темоюречення.'
 assert '^' not in parser.text()
 # Compound process title survives retrieval; generic process search contains no glass-specific furnace stages.
 def wiki_fixture(url,**kwargs):
  query=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(url).query)
  if query.get('list')==['search']:
   assert 'furnace' not in query['srsearch'][0]
   return {'query':{'search':[{'title':'Paper','pageid':1},{'title':'Papermaking','pageid':2},{'title':'Paper cup','pageid':3}]}}
  if query.get('action')==['parse']:
   title=query['page'][0]
   return {'parse':{'title':title,'text':{'*':'<p>'+('Paper is produced from fibres and water. '*10)+'</p>'},'langlinks':[]}}
  raise AssertionError('unexpected retrieval')
 with patch.object(app,'http_json',wiki_fixture):
  retrieved=app.wikipedia('How paper is made','en')
 assert retrieved[0]['title']=='Papermaking'
 # Ranker must retain the process anchor selected by discovery.
 assert app.relevant_sources(retrieved,'How paper is made','en')[0]['title']=='Papermaking'


 # A role-related document cannot pass the separate photographic human-content gate.
 from visual_verifier import VisualVerifier
 verifier=VisualVerifier.__new__(VisualVerifier)
 def role_only(image,descriptions):
  return [.19 if 'President of' not in label else .9 for label in descriptions]
 with patch.object(verifier,'compare',role_only):
  assert not verifier.check_person('unused',{'entity_id':'Q123','basis':'fixture'},'President of Example')['passed']


 assert app.sentences('W jej skład wchodzi 18 dzielnic m.st. Warszawy. Następne zdanie.')==['W jej skład wchodzi 18 dzielnic m.st. Warszawy.','Następne zdanie.']
 # Resolve the process anchor before binding its structured identity.
 captured=[]
 def profile_fixture(sources,language):
  captured.append(sources[0]['title'])
  return {'id':'Q123','kind':'concept','native_name':'Papermaking','native_description':'process of making paper','source_url':'https://www.wikidata.org/wiki/Q123','labels':{'en':'papermaking'}}
 with patch.object(app,'cache_fetch',lambda key,fetch:list(retrieved)),patch.object(app,'entity_profile',profile_fixture):
  enriched=app.load_sources('How paper is made','en')
 assert captured==['Papermaking']
 assert enriched[-1]['source_type']=='structured definition'
 assert app.relevant_sources(enriched,'How paper is made','en')[-1]['source_type']=='structured definition'
 # A rejected meaning stays rejected; another meaning of the same topic remains selectable.
 with TemporaryDirectory() as temp:
  with patch.object(app,'DB',Path(temp)/'decisions.sqlite3'):
   with app.connect() as c:c.execute("CREATE TABLE source_decisions(topic_key TEXT,language TEXT,entity_id TEXT,decision TEXT,note TEXT,created_at TEXT,PRIMARY KEY(topic_key,language,entity_id))")
   app.reject_subject(' Example topic ','en','Q123')
   assert app.subject_rejected('EXAMPLE TOPIC','en','Q123')
   assert not app.subject_rejected('EXAMPLE TOPIC','en','Q456')


 # Staged stock imagery cannot establish a named astronomical body's identity.
 astronomical={'id':'Q123','kind':'entity','visual_description':'fourth planet from the Sun'}
 assert app.named_astronomical_subject(astronomical)
 assert not app.named_astronomical_subject({'kind':'human','visual_description':'film star'})
 astro_slot={'text':'The planet has a thin atmosphere.','entity_profile':astronomical,'source_driven':True,'visual_title':'Mars'}
 assert app.photo_score({'provider':'pexels','alt':'An astronaut in a Mars landscape','creator':'Photographer','width':1200,'height':1800},astro_slot,'Mars')<0
 assert not app.photographic_metadata({'alt':'Photosynthesis chart','depiction':'File:Photosynthesis.svg'})
 assert app.photographic_metadata({'alt':'A photograph of green leaves','depiction':''})
 # Request whole stock photos, never the provider's portrait crop.
 fixture_photo={'id':123,'width':2400,'height':1600,'src':{'original':'https://images.pexels.com/photos/123/photo.jpeg','portrait':'https://images.pexels.com/photos/123/photo.jpeg?fit=crop&h=1200'}}
 with patch.object(app,'PROVIDERS',{'Pexels API':{'value':'fixture-only'}}),patch.object(app,'cache_fetch',lambda key,fetch:fetch()),patch.object(app,'http_json',lambda *args,**kwargs:{'photos':[fixture_photo]}):
  photo=app.photo_search('example','en')[0]
 query=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(photo['url']).query)
 assert query['w']==['1600'] and not any(key in query for key in ['crop','fit','h'])

 assert app.photo_origin({'provider':'commons','depiction':'File:Planet Valles.jpeg'})==app.photo_origin({'provider':'commons','depiction':'File:Planet Valles EDIT.jpg'})
 assert app.context_dependent_sentence('The outcome often weighs several tons.')
 process_slot={'text':'Paper is made in a factory.','source_driven':True,'process_intent':True,'entity_profile':{}}
 assert app.photo_score({'provider':'pexels','id':'wrong','alt':'Hands working on paper patterns for dressmaking in a workshop','width':1000,'height':1000},process_slot,'paper manufacturing')<0
 place={'kind':'entity','name':'Example City','native_name':'Example City','visual_description':'capital and largest city of a country'}
 assert app.named_place_subject(place)
 assert not app.place_identity({'provider':'pexels','alt':'Example City'},place)
 assert app.place_identity({'provider':'commons','categories':['Category:Buildings in Example City']},place)

 # Retention accounts for ASR records and never selects unrelated shared UUIDs.
 with TemporaryDirectory() as temp:
  base=Path(temp);owned=str(app.uuid.uuid4());unrelated=str(app.uuid.uuid4())
  with patch.multiple(app,DATA=base,ROOT=base/'factory-universal',DB=base/'factory-universal/jobs.sqlite3',RENDER=base/'renders',VISUAL=base/'visuals',VOICE=base/'voiceovers',RENDER_MAX_BYTES=100):
   app.ROOT.mkdir();app.init_db();ts=app.now()
   with app.connect() as db:db.execute("INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message) VALUES(?,?,?,?,?,?,'ready','review',100,'fixture')",(owned,ts,ts,'fixture','en',15))
   for jid in [owned,unrelated]:
    directory=base/'alignments'/jid;directory.mkdir(parents=True);(directory/'whisper.json').write_text('x'*200)
   app.cleanup()
   assert not (base/'alignments'/owned).exists()
   assert (base/'alignments'/unrelated/'whisper.json').exists()
   assert app.get_job(owned)['status']=='expired'

 assert not app.photographic_metadata({'depiction':'File:Example City location map.png','alt':'City location'})
 assert not app.photographic_metadata({'depiction':'File:City.png','alt':'Wikivoyage locator maps','creator':''})
 assert not app.photographic_metadata({'depiction':'File:City.png','alt':'City','creator':'original.svg derivative work'})
 assert app.safe_id('../unrelated') is None
 print('PASS: plural normalization, paragraph extraction, complete abbreviations, five shot layouts, homonym exclusion, owned UUID validation')

if __name__=='__main__':check()

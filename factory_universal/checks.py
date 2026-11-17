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
 with patch.object(app,'cache_fetch',lambda key,fetch:list(retrieved)),patch.object(app,'entity_profile',profile_fixture),patch('storyboard.ensure_source',lambda sources,lang,api:None):
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

 # A person search must use licensed result pools within the same three-query bound.
 person_queries=[]
 def person_search(query,limit=20):
  person_queries.append((query,limit))
  return [{'provider':'commons','id':str(len(person_queries))}]
 with patch.object(app,'SEARCH_QUERIES',{'stock':set(),'commons':set()}),patch.object(app,'DISCOVERED_PHOTOS',{}),patch.object(app,'commons_search',person_search),patch.object(app,'photo_search',side_effect=AssertionError('unverified stock identity')):
  app.discover_photos('Example Person','en',[{'text':'Example Person is an engineer.','source_driven':True,'entity_profile':{'kind':'human','id':'Q123','name':'Example Person','commons_category':'Example Person'}}])
 assert len(person_queries)==3 and all(limit==50 for _,limit in person_queries)
 assert person_queries[0][0]=='haswbstatement:P180=Q123'
 assert 'incategory:"CC-BY-2.0"' in person_queries[1][0] and 'incategory:"CC-BY-4.0"' in person_queries[2][0]
 assert app.context_dependent_sentence('Згодом переїхав до іншого міста.')


 # Personal category ancestry can establish identity; family categories cannot.
 parent_fixture={'Category:Example Person in 2024':['Category:Example Person by year'],'Category:Example Person by year':['Category:Example Person'],'Category:Family of Example Person':['Category:Example Person']}
 def category_http(url,*args,**kwargs):
  titles=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(url).query)['titles'][0].split('|')
  return {'query':{'pages':{str(i):{'title':title,'categories':[{'title':parent} for parent in parent_fixture.get(title,[])]} for i,title in enumerate(titles)}}}
 people=[{'categories':['Category:Example Person in 2024']},{'categories':['Category:Family of Example Person']},{'categories':['Category:Other Person in 2024']}]
 with patch.object(app,'http_json',category_http),patch.object(app,'cache_fetch',lambda key,fetch:fetch()):
  verified=app.verified_human_categories(people,{'name':'Example Person','commons_category':'Example Person'})
 assert verified=={'Category:Example Person in 2024'}


 # Renamed portrait crops retain the same specific Commons description.
 original={'provider':'commons','id':'1','depiction':'File:Official portrait.jpg','alt':'File:Official portrait.jpg Official photographic portrait of the president standing in the office beside a flag, photographed in January.','identity_verification':{'entity_id':'Q123'}}
 derivative={**original,'id':'2','depiction':'File:Unrelated filename (4x5).png'}
 derivative['alt']=derivative['depiction']+' '+original['alt'].removeprefix(original['depiction']).strip()
 assert app.photo_origins(original)&app.photo_origins(derivative)
 distinct={**derivative,'alt':derivative['depiction']+' A photograph of the president giving a public speech at a separate official ceremony on the following day.'}
 assert not app.photo_origins(original)&app.photo_origins(distinct)


 # A verified portrait cannot stand in for the linked object of a later fact.
 from storyboard import target_score,shot_slots,build,SceneUnavailable
 target={'id':'Q987','name':'Example Rockets','native_name':'Ракети Приклад','description':'aerospace manufacturer','commons_category':'Example Rockets'}
 scene={'text':'The founder established Example Rockets.','visual_target':target}
 portrait={'provider':'commons','id':'p','depiction':'File:Example Person portrait.jpg','alt':'Example Person portrait','identity_verification':{'entity_id':'Q123'}}
 rocket={'provider':'commons','id':'r','depiction':'File:Example Rockets launch.jpg','alt':'Example Rockets rocket launching','width':1000,'height':1000}
 assert target_score(portrait,scene,app)<0 and target_score(rocket,scene,app)>0
 assert app.photo_score(portrait,{**scene,'entity_profile':{'kind':'human','id':'Q123'}},'Example Person')<0
 rotated=shot_slots([{'text':'Two linked objects','visual_targets':[target,{**target,'id':'Q988'}]}],[0,0,0])
 assert [row['visual_target']['id'] for row in rotated]==['Q987','Q988','Q987']
 assert len(app.sentences('In 2004 he joined Example, Inc. as an early investor. A new sentence follows.'))==2


 # Reused anchor labels in other paragraphs cannot change a scene's subject.
 import storyboard
 parser=storyboard.ArticleLinks()
 parser.feed('<p>A <a href="/wiki/River_One">river</a> feeds the lake.</p><p>The <a href="/wiki/Unrelated_Fiction">river</a> is a fictional character.</p>')
 first='A river feeds the lake.'
 local_sources=[{'text':first+'\nThe river is a fictional character.','url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'concept','id':'Q123'}}]
 local_slots=[{'text':'An introduction.','source_index':0,'source_sentence':'An introduction.'},{'text':first,'source_index':0,'source_sentence':first}]
 entities={'River One':{'id':'Q901','name':'River One','kind':'entity','description':'river','native_name':'River One'},'Unrelated Fiction':{'id':'Q902','name':'Unrelated Fiction','kind':'entity','description':'fictional character','native_name':'Unrelated Fiction'}}
 with patch.object(storyboard,'source_links',return_value=parser.links),patch.object(storyboard,'resolve_links',return_value=entities):
  storyboard.build(local_slots,local_sources,'en',app)
 assert [x['id'] for x in local_slots[1]['visual_targets']]==['Q901']


 # Context beats a broad shared keyword: treatment is not a nuclear test.
 medical={'id':'Q900','name':'radioactivity','description':'physical phenomenon'}
 medical['intent']=storyboard.scene_intent('Research on cancer treatment using radioactivity.',medical)
 atomic={'provider':'commons','depiction':'File:Radioactivity nuclear test.jpg','alt':'radioactivity from an atomic bomb explosion'}
 therapy={'provider':'commons','depiction':'File:Radioactivity cancer therapy.jpg','alt':'radioactivity cancer therapy in a hospital'}
 assert storyboard.target_score(atomic,{'visual_target':medical},app)<0
 assert storyboard.target_score(therapy,{'visual_target':medical},app)>0
 organization={**target,'description':'aerospace manufacturer'}
 organization['intent']=storyboard.scene_intent('The founder established Example Rockets.',organization)
 conference={**rocket,'depiction':'File:Example Rockets press conference.jpg','alt':'Example Rockets press conference'}
 assert storyboard.target_score(conference,{'visual_target':organization},app)<0
 weighted=app.storyboard_beats(12,[{'text':'An introduction.','visual_role':'establishing'},{'text':'A detailed process description. '*5},{'text':'A shorter fact.'}])
 assert weighted.count(0)==2 and weighted.count(1)>weighted.count(2)>=2


 # A reusable landing relation must not turn an aircraft into a rocket.
 plane=storyboard.scene_intent('The aircraft landed.',{'name':'Example Airliner','description':'commercial aircraft'})
 assert plane['name']=='landing' and 'aircraft' in plane['visual'] and 'rocket' not in plane['visual']
 water=storyboard.scene_intent('The company treats wastewater.',{'name':'water','description':'chemical substance'})
 assert water['name']!='medical treatment'


 # Exact text and scene links share the existing article parser, including br.
 snapshot=storyboard.extract_article('<p>A <a href="/wiki/River_One">river</a> flows.<br>Another <a href="/wiki/Lake_One">lake</a> follows.</p>','en',app)
 assert len(snapshot['visual_links'])==2
 for row,line in zip(snapshot['visual_links'],snapshot['text'].splitlines()):
  assert row['paragraph_key']==storyboard.paragraph_key(line)


 # Extra shots can use either illustrated subject, while both first appearances
 # remain mandatory. A scarce subject never forces duplicate photographs.
 rare={'id':'Q990','name':'Example Rare Material'}
 rich={'id':'Q991','name':'Example Common Material'}
 body={'text':'Two explicitly linked materials.','visual_targets':[rare,rich]}
 expanded=storyboard.shot_slots([body],[0]*6)
 assert not expanded[0]['visual_target_optional'] and not expanded[1]['visual_target_optional']
 fixtures=[{'provider':'commons','id':'rare','depiction':'File:Example Rare Material.jpg','alt':'Example Rare Material','width':1000,'height':1000}]+[{'provider':'commons','id':'common'+str(i),'depiction':'File:Example Common Material '+str(i)+'.jpg','alt':'Example Common Material','width':1000,'height':1000} for i in range(5)]
 assigned=app.allocate_photos(fixtures,[body],'Example',6,scene_slots=expanded)
 assert len({row['id'] for row in assigned})==6
 assert assigned[0]['id']=='rare'


 # Wikipedia often links a name only at its first mention. Unambiguous aliases
 # remain usable later; an ambiguous label still requires its local link.
 only=storyboard.ArticleLinks();only.feed('<p><a href="/wiki/Example_City">Example City</a> is introduced.</p>')
 alias_sources=[{'text':'Example City is introduced.\nThe scientist was born in Example City.','url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 alias_slots=[{'text':'An introduction.','source_index':0,'source_sentence':'An introduction.'},{'text':'The scientist was born in Example City.','source_index':0,'source_sentence':'The scientist was born in Example City.'}]
 with patch.object(storyboard,'source_links',return_value=only.links),patch.object(storyboard,'resolve_links',return_value={'Example City':{'id':'Q995','name':'Example City','kind':'entity','description':'city','native_name':'Example City'}}):
  storyboard.build(alias_slots,alias_sources,'en',app)
 assert alias_slots[1]['visual_targets'][0]['id']=='Q995'
 assert alias_slots[1]['visual_targets'][0]['binding']=='unambiguous article alias'


 # Metadata may use a sourced former or short organization name.
 renamed={'id':'Q996','name':'Example Vehicles, Inc.','aliases':['Example Motors'],'description':'automotive manufacturer'}
 renamed['intent']=storyboard.scene_intent('The founder joined Example Vehicles, Inc.',renamed)
 vehicle={'provider':'commons','depiction':'File:Example Motors factory.jpg','alt':'Example Motors automotive factory'}
 assert storyboard.target_score(vehicle,{'visual_target':renamed},app)>0


 # An incidental mention in a photographer's description is not object identity.
 unrelated={'provider':'commons','depiction':'File:Unrelated museum room.jpg','alt':'Unrelated museum room. Originally posted via Example Motors.','categories':['Category:Images from Example Motors']}
 assert storyboard.target_score(unrelated,{'visual_target':renamed},app)<0
 assert not app.photographic_metadata({'depiction':'File:Company advertisement.jpg','alt':'A company product'})


 # Scene subjects retain astronomical provenance gates.
 moon={'id':'Q997','kind':'entity','name':'Example Moon','description':'natural satellite'}
 lunar={'provider':'commons','id':'moon','depiction':'File:Example Moon.jpg','alt':'Example Moon','creator':'Unverified uploader','width':1000,'height':1000}
 assert app.photo_score(lunar,{'visual_target':moon},'Example planet')<0
 assert app.photo_score({**lunar,'creator':'NASA'},{'visual_target':moon},'Example planet')>0


 # A possessive can have an explicit antecedent in the same complete sentence.
 assert not app.context_dependent_sentence('У 2002 році Приклад заснував компанію Альфа і став її керівником.')
 assert app.context_dependent_sentence('Її керівник отримав нагороду.')
 assert app.context_dependent_sentence('Był on odkrywcą nowego zjawiska.')


 # A 503 thumbnail may fall back to the bounded original of that same file.
 import io,tempfile
 png=io.BytesIO();app.Image.new('RGB',(2,2),'white').save(png,format='PNG');png_bytes=png.getvalue()
 class ImageResponse:
  headers={'Content-Type':'image/png'}
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def read(self,limit):return png_bytes
 picture={'url':'https://thumb.wikimedia.org/a.jpg','original_url':'https://upload.wikimedia.org/a.jpg','original_size':len(png_bytes),'original_pixels':4}
 with tempfile.TemporaryDirectory() as folder:
  error=app.urllib.error.HTTPError(picture['url'],503,'temporary',{},None)
  with patch.object(app.urllib.request,'urlopen',side_effect=[error,ImageResponse()]) as opening:
   app.download_photo(picture,app.Path(folder)/'source.png')
   assert opening.call_count==2
   assert opening.call_args_list[1].args[0].full_url==picture['original_url']
  with patch.object(app.urllib.request,'urlopen',side_effect=TimeoutError('read timeout')) as opening:
   try:app.download_photo(picture,app.Path(folder)/'timeout.png')
   except TimeoutError:pass
   else:raise AssertionError('Timeout did not propagate')
   assert opening.call_count==1
  rate=app.urllib.error.HTTPError(picture['url'],429,'rate limited',{},None)
  with patch.object(app.urllib.request,'urlopen',side_effect=rate) as opening:
   try:app.download_photo(picture,app.Path(folder)/'rate.png')
   except app.ImageServiceError as error:assert error.status==429
   else:raise AssertionError('429 did not propagate')
   assert opening.call_count==1

 # Temporary image-service failures keep the same facts and have a global cap.
 same_slots=[{'text':'A complete source-backed fact.'}]
 calls=[]
 def temporarily_unavailable(slots):
  calls.append(slots);raise app.ImageServiceError(503)
 with patch.object(app,'IMAGE_SERVICE_RETRIES',0),patch.object(app.time,'sleep') as delay,patch.object(app,'plan_script',side_effect=AssertionError('Network failures must not discard facts')):
  try:app.prepare_illustrated_slots([], 'Example','en',15,15,same_slots,temporarily_unavailable)
  except app.ImageServiceError:pass
  else:raise AssertionError('Persistent 503 did not stop after the cap')
  assert len(calls)==3 and delay.call_count==2 and all(row is same_slots for row in calls)


 # A search-rate response stops the provider sequence immediately.
 rate=app.urllib.error.HTTPError('https://images.example/',429,'rate limited',{},None)
 with patch.object(app,'SEARCH_QUERIES',{'stock':set(),'commons':set()}),patch.object(app,'DISCOVERED_PHOTOS',{}),patch.object(app,'photo_search',side_effect=rate) as search,patch.object(app,'commons_search',side_effect=AssertionError('Do not continue after rate limiting')):
  try:app.discover_photos('Example topic','en',[{'text':'Example topic','process_intent':False}])
  except app.urllib.error.HTTPError as error:assert error.code==429
  else:raise AssertionError('Search rate limit was swallowed')
  assert search.call_count==1


 # Awards use the actual award object, not a similarly named parody or a winner portrait.
 award={'id':'Q999','name':'Example Prize','description':'international award','aliases':['Example']}
 award['intent']=storyboard.scene_intent('The scientist won the Example Prize.',award)
 medal={'provider':'commons','depiction':'File:Example Prize medal.jpg','alt':'A medal','categories':['Category:Example Prize medals']}
 parody={'provider':'commons','depiction':'File:Parody Example Prize trophy.jpg','alt':'A trophy','categories':['Category:Parody Example Prize trophies']}
 winner={'provider':'commons','depiction':'File:Example Prize laureate portrait.jpg','alt':'A prize winner'}
 assert storyboard.target_score(medal,{'visual_target':award},app)>0
 assert storyboard.target_score(parody,{'visual_target':award},app)<0
 assert storyboard.target_score(winner,{'visual_target':award},app)<0

 # Texture from the same source remains a duplicate after a crop and resize.
 import numpy as np
 from photo_duplicates import fingerprint,duplicate
 with tempfile.TemporaryDirectory() as folder:
  rng=np.random.default_rng(42)
  original=app.Image.fromarray(rng.integers(0,256,(150,200,3),dtype=np.uint8)).resize((800,600))
  first=app.Path(folder)/'first.png';crop=app.Path(folder)/'crop.png';different=app.Path(folder)/'different.png'
  original.save(first);original.crop((120,80,700,520)).resize((870,660)).save(crop)
  app.Image.fromarray(np.random.default_rng(43).integers(0,256,(600,800,3),dtype=np.uint8)).save(different)
  assert duplicate(fingerprint(first),fingerprint(crop))['duplicate']
  assert not duplicate(fingerprint(first),fingerprint(different))['duplicate']

 # Generic stage matching must reject a factory exterior and a cutting machine during pressing.
 slot={'text':'The paper is pressed to remove water, sometimes assisted by heating.','source_driven':True,'process_intent':True}
 assert app.scene_actions(slot['text'])=={'press'}
 photo={'provider':'commons','alt':'paper factory machinery','height':800,'width':1200}
 assert app.photo_score({**photo,'depiction':'Paper mill exterior at night'},slot,'How paper is made')<0
 assert app.photo_score({**photo,'depiction':'Paper mill cutting and slitting machinery'},slot,'How paper is made')<0
 assert app.photo_score({**photo,'depiction':'Paper mill pressing machinery'},slot,'How paper is made')>=0
 assert app.scene_actions('Wet paper fibers drain through a sieve.')=={'drain'}
 assert app.safe_id('../unrelated') is None
 print('PASS: plural normalization, paragraph extraction, complete abbreviations, five shot layouts, homonym exclusion, owned UUID validation')

if __name__=='__main__':check()

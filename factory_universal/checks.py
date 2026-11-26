import app
import storyboard

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
 drying={'text':'The wet sheets of paper are air dried.','process_intent':True}
 after={'alt':'File:Paper mill.jpg A worker collects dry paper sheets after drying.',
        'depiction':'File:Paper mill.jpg','width':1200,'height':900}
 on_rack={**after,'alt':'Drying handmade paper sheets on racks.','depiction':'File:Drying handmade paper.jpg'}
 assert app.photo_score(after,drying,'How paper is made')<0
 assert app.photo_score(on_rack,drying,'How paper is made')>=0
 assert not app.photographic_metadata({'depiction':'File:Before After Specimen Washing.jpg'})
 for depiction,description in [
  ('File:Infographic- evolution of a star.jpg','A team of researchers reports a discovery.'),
  ('File:Eccentric star (closeup-labeled).jpg','An observation of the source.'),
  ('File:Stellar merger.jpg','Simulation frames from this NASA animation.'),
  ('File:Double star.jpg','A still frame from the planetarium show.'),
  ('File:Neutron star.jpg','A star done in Blender using procedural textures.'),
  ('File:Neutron star and companion.jpg','Done with PlanetMaker'),
 ]:
  assert not app.photographic_metadata({'depiction':depiction,'alt':depiction+' '+description})
 observation=lambda title:app.photo_origins({'provider':'commons','creator':'ESO','depiction':title})
 assert observation('File:Hubble view (eso1810b).jpg')&observation('File:MUSE view (eso1810c).jpg')
 assert not observation('File:Hubble view (eso1810b).jpg')&observation('File:An independent exposure (eso1811a).jpg')
 assert not app.photographic_metadata({'alt':'Specimen preparation. (A) Photograph of the insect. (B) Close-up of the wing. (C) View under magnification.'})
 assert not app.photographic_metadata({'depiction':'File:Volcano from an orbiter.jpg',
                                        'creator':'The contributor modified the image with labels.'})
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
 for duration in app.DURATIONS:
  minimum,maximum=app.natural_voice_window(duration)
  assert minimum==duration*900-50 and maximum==duration*1000

 # Regression: the real measured sequence changes text, preserves selected voice, and stops after three sends.
 from unittest.mock import patch
 from tempfile import TemporaryDirectory
 import io,hashlib,uuid
 with TemporaryDirectory() as temp:
  directory=Path(temp);job_id=str(uuid.uuid4());calls=[];plans=[]
  def fake_plan(sources,topic,lang,seconds,max_beats=None,excluded_narrations=()):
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
 with TemporaryDirectory() as temp,patch.multiple(app,ROOT=Path(temp),DB=Path(temp)/'jobs.sqlite3'):
  app.init_db()
  voice=app.SELECTED_VOICES['en'][1];jid=str(uuid.uuid4());now=app.now()
  cases=[('too short',26496,True),('fits duration',28800,True),('too long and no cache',30936,False)]
  excluded=[]
  with app.connect() as db:
   db.execute("INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message) VALUES(?,?,?,?,?,?,'failed','voice',100,'fixture')",(jid,now,now,'Example','en',30))
   for attempt,(script,milliseconds,save) in enumerate(cases,1):
    digest=hashlib.sha256(script.encode()).hexdigest()
    db.execute("INSERT INTO voice_attempts(job_id,attempt,text_sha256,voice,state) VALUES(?,?,?,?,'measured')",(jid,attempt,digest,voice))
    if save:
     path=app.voice_cache_path(voice,digest);path.parent.mkdir(exist_ok=True)
     audio=b'fixture audio'
     path.write_text(app.json.dumps({'audio_base64':app.base64.b64encode(audio).decode(),
       'audit':{'voice':voice,'text_sha256':digest,'audio_sha256':hashlib.sha256(audio).hexdigest(),'duration_ms':milliseconds}}))
    if attempt==1:excluded.append(digest)
  assert app.out_of_window_narrations('Example','en',30)==set(excluded)
  assert app.out_of_window_narrations('Another topic','en',30)==set()
  assert app.out_of_window_narrations('Example','en',45)==set()



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
 # A verified joined-title redirect outranks a qualified homonym.
 def split_title_fixture(url,**kwargs):
  query=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(url).query)
  if query.get('list')==['search']:
   return {'query':{'search':[{'title':'Супер Нова (футбольний клуб)','pageid':2}]}}
  if query.get('titles')==['супернова']:
   assert query['redirects']==['1']
   return {'query':{'pages':[{'pageid':1,'title':'Наднова'}]}}
  if query.get('action')==['parse']:
   return {'parse':{'title':query['page'][0],'text':{'*':'<p>'+('Підтверджений факт з енциклопедичного джерела. '*10)+'</p>'}}}
  raise AssertionError(query)
 with patch.object(app,'http_json',split_title_fixture):
  split_retrieved=app.wikipedia('супер нова','uk')
 assert app.relevant_sources(split_retrieved,'супер нова','uk')[0]['title']=='Наднова'
 def inflected_title_fixture(url,**kwargs):
  query=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(url).query)
  if query.get('action')==['query']:
   return {'query':{'search':[{'title':'Корабельня','pageid':1}]}}
  assert query['page']==['Корабельня']
  return {'parse':{'title':'Корабельня','text':{'*':'<p>'+('На корабельні будують і ремонтують судна. '*10)+'</p>'}}}
 with patch.object(app,'http_json',inflected_title_fixture):
  assert app.wikipedia('Робота на корабельні','uk')[0]['title']=='Корабельня'
 # Match a verified product in a multilingual brief without substituting an unrelated source.
 assert app.topic_identifier('7-Zip для архівів')=='7-Zip'
 assert app.topic_identifier('1987 спостереження')==''
 assert app.topic_identifier('Made with 7-Zip')=='7-Zip'
 assert app.topic_identifier('Автоматизация процессов n8n')=='n8n'
 assert app.topic_identifier('Автоматизация фирмы с помощью (n8n).')=='n8n'
 assert app.topic_identifier('n8n или N8N')=='n8n'
 assert app.topic_identifier('Сравнить 7-Zip и H44')==''
 def identifier_fixture(url,**kwargs):
  parsed=app.urllib.parse.urlsplit(url)
  query=app.urllib.parse.parse_qs(parsed.query)
  if query.get('action')==['parse']:
   assert query['page']==['Архіватор H44']
   return {'parse':{'title':'Архіватор H44','text':{'*':'<p>'+('Архіватор H44 пакує файли. '*20)+'</p>'}}}
  assert query['titles']==['H44'] and query['redirects']==['1']
  page={'title':'H44','missing':True} if parsed.hostname.startswith('uk.') else {'title':'H44 Archiver','pageid':1}
  return {'query':{'pages':[page]}}
 brief='Для резервних копій через H44'
 import source_translation
 with patch.object(app,'http_json',identifier_fixture),patch.object(app,'cache_fetch',lambda key,fetch:fetch()),patch.object(source_translation,'configured_for',return_value=False):
  assert app.wikipedia(brief,'uk')==[]
  reference=app.identifier_article('H44','uk')
  assert reference['language']=='en' and reference['native_title']==''
  writes=[]
  with patch.object(app,'get_job',return_value={'topic':brief,'language':'uk','duration_s':45}),patch.object(app,'update',side_effect=lambda jid,**values:writes.append(values)),patch.object(app,'google_connection_status',return_value={'ready':True}):
   app.run_job('fixture')
  assert writes[-1]['status']=='needs_input'
  assert app.json.loads(writes[-1]['manifest'])['input_reason']=='source_language_unavailable'
 native_reference={**reference,'native_title':'Архіватор H44'}
 with patch.object(app,'http_json',identifier_fixture),patch.object(app,'identifier_article',return_value=native_reference):
  native=app.wikipedia(brief,'uk')
 assert native[0]['scoped_identifier']=='H44'
 with patch.object(app,'source_slots',side_effect=lambda sources,topic,count,lang,**kwargs:[{'text':'Архіватор пакує файли.'}]*count):
  assert app.plan_script(native,brief,'uk',45)==[]
 with patch.object(app,'source_slots',side_effect=lambda sources,topic,count,lang,**kwargs:[{'text':'Архіватор створює архіви резервних копій.'}]*count):
  assert app.plan_script(native,brief,'uk',45)
 # A better-scoring overview of the same length must not hide the scoped plan.
 rows=[
  (30,0,'The instrument measures temperature.',[]),
  (20,0,'An engineer designed the instrument.',[]),
  (5,0,'The instrument records ocean conditions.',[]),
 ]
 with patch.object(app,'measured_sentence_ms',return_value=3000):
  fitted=app.fit_narration(rows,2,'en',duration_ms=8000,required_sentence=rows[0][2],scope={'ocean'})
 assert [slot['text'] for slot in fitted]==[rows[0][2],rows[2][2]]
 # A Russian brief can match the equivalent Ukrainian wording in the source.
 assert app.script_covers_identifier_scope([{'scoped_identifier':'X20'}],
  'X20 автоматизация для фирм','uk',[{'text':'Компанії можуть використовувати X20 для автоматизації.'}])
 assert app.script_covers_identifier_scope([{'scoped_identifier':'X20'}],
  'Автоматизация вашей фирмы с помощью X20','uk',[{'text':'Компанії можуть використовувати X20 для автоматизації.'}])
 assert not app.script_covers_identifier_scope([{'scoped_identifier':'X20'}],
  'X20 автоматизация для фирм','uk',[{'text':'Компанія створила X20 у 2020 році.'}])
 city={'kind':'entity','visual_description':'capital city of a country'}
 assert app.incidental_place_event('W 1339 odbył się proces sądowy w mieście.','Warszawa',city)
 assert app.incidental_place_event('Z 1427 pochodzą pierwsze udokumentowane wiadomości o Żydach mieszkających w Starej Warszawie.','Warszawa',city)
 assert app.incidental_place_event('The earliest records come from 1427.','Example City',city)
 assert not app.incidental_place_event('The trail climbs from 1427 metres above sea level.','Example City',city)
 assert app.incidental_place_event('Pierwsza wzmianka o Warszawie pochodzi z 23 kwietnia 1313.','Warszawa',city)
 assert app.incidental_place_event('W 1526 została włączona do Korony Królestwa Polskiego.','Warszawa',city)
 assert app.incidental_place_event('W Warszawie odbyło się 145 sejmów walnych.','Warszawa',city)
 assert app.incidental_place_event('Nazwa miasta zmieniła się w XVI wieku.','Warszawa',city)
 assert app.incidental_place_event('In 1812 an army occupied the city.','Example City',city)
 assert not app.incidental_place_event('W 1339 odbył się proces sądowy w mieście.','Historia Warszawy',city)
 assert not app.incidental_place_event('In 2020 the city had a population of a million.','Example City',city)
 # A cut before an example list must preserve the following predicate.
 complete='This is a method by which several workers, such as librarians, preserve old records.'
 assert app.complete_clause_variants(complete,'en')==[complete]
 assert app.truncated_dependent_clause('This is a method by which several workers.',complete,'en')
 assert not app.truncated_dependent_clause(complete,complete,'en')
 assert app.context_dependent_sentence('In small cells, they are embedded in the membrane.')
 assert app.context_dependent_sentence('Поскольку неизвестно, является ли такая сила тяжести достаточной, рассматриваются другие варианты.')
 assert app.context_dependent_sentence('За цими рухами інші бджоли дізнаються про місце збору.')
 assert app.context_dependent_sentence('Since water is used here, the equation for the process is.')
 assert not app.context_dependent_sentence('In small cells, pigments are embedded in the membrane.')

 # Specific catalog designations need that object, not generic space photography.
 astro={'entity_profile':{'kind':'concept','visual_description':'an astronomical explosion of a star'},'text':'У 1987 році спостерігали SN 1987A.','source_driven':True,'visual_title':'Supernova'}
 sky={'provider':'commons','alt':'Supernova photograph','depiction':'File:Supernova SN1987A.jpg','height':1280,'width':1280}
 assert app.photo_score(sky,astro,'Supernova')>=0
 assert app.photo_score({**sky,'depiction':'File:Supernova SN 1006.jpg'},astro,'Supernova')<0
 assert not app.photographic_metadata({**sky,'depiction':'File:Supernova (CGI).jpg'})
 assert not app.photographic_metadata({'depiction':'File:Instrument.png','alt':'3d model using Blender'})
 assert not app.photographic_metadata({'depiction':'File:Instrument - Fig. 59.png'})
 assert not app.photographic_metadata({'depiction':'File:Data.png','alt':'This image shows the spectrum of the object.'})
 assert not app.photographic_metadata({'depiction':'File:Target (annotated).png'})
 assert not app.photographic_metadata({'depiction':'File:Target (Compass Image).png','alt':'This detailed image has been annotated to highlight structures.'})
 relation={'provider':'commons','creator':'ESA','alt':'The telescope frame was obtained by Telescope X in 1992, with 10 minutes exposure in H-alpha.'}
 original={**relation,'depiction':'File:SN 1987A view.jpg'}
 crop={**relation,'depiction':'File:Detail of SN 1987A image.jpg'}
 assert any(key[0]=='commons-observation-exposure' for key in app.photo_origins(original)&app.photo_origins(crop))

 assert app.photographic_metadata({'depiction':'File:Target composite.png','alt':'Combined visible and infrared observations of the target.'})

 microscope_slot={'text':'A microscope magnifies small objects.','visual_title':'Microscope','source_driven':True}
 microscope={**sky,'depiction':'File:Microscope toy.jpg','alt':'A children’s microscope toy'}
 assert app.photo_score(microscope,microscope_slot,'Microscope')<0
 assert app.photo_score(microscope,microscope_slot,'Microscope toy')>=0
 instrument_history={**microscope_slot,'text':'Przyrząd opracowano w XVII wieku.','entity_profile':{'visual_description':'A microscope is an optical instrument.'}}
 historical={**sky,'depiction':'File:Microscope from 1670.jpg','alt':'Microscope from 1670'}
 assert app.photo_score(historical,instrument_history,'Microscope')>=0
 assert app.photo_score({**historical,'depiction':'File:Microscope 1870.jpg'},instrument_history,'Microscope')<0
 assert app.photo_score({**historical,'depiction':'File:Modern Microscope.jpg','alt':'The microscope, invented in the 17th century, has evolved considerably today.'},instrument_history,'Microscope')<0

 assert app.century_labels('XVII столітті and 18th century')=={17,18}


 assert app.astronomical_identifiers('NGC 224 and SN 1987A')=={'NGC 224','SN 1987A'}
 # A verified spelling repair never outranks an exact requested title.
 exact={'title':'Супер Нова','text':'Independent exact match.'}
 assert app.relevant_sources(split_retrieved+[exact],'супер нова','uk')[0]==exact
 assert app.exact_source_title('light house','Lighthouse')==1
 assert app.exact_source_title('light house','Lighthouse (album)')==0



 # A role-related document cannot pass the separate photographic human-content gate.
 from visual_verifier import VisualVerifier
 verifier=VisualVerifier.__new__(VisualVerifier)
 def role_only(image,descriptions,use_cache=True):
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
 # Snapshot links and the exact text must point to the same revision.
 from storyboard import ensure_source
 source={'url':'https://en.wikipedia.org/wiki/Papermaking'}
 def snapshot_fixture(url,**kwargs):
  params=app.urllib.parse.parse_qs(app.urllib.parse.urlsplit(url).query)
  assert params['page']==['Papermaking'] and 'revid' in params['prop'][0].split('|')
  return {'parse':{'revid':12345,'text':{'*':'<p>'+('Papermaking uses <a href="/wiki/Pulp_(paper)">pulp</a>. '*15)+'</p>'}}}
 with patch.object(app,'cache_fetch',lambda key,fetch:fetch()),patch.object(app,'http_json',snapshot_fixture):
  ensure_source([source],'en',app)
 assert source['revision_id']==12345
 assert source['revision_url']=='https://en.wikipedia.org/w/index.php?oldid=12345'
 assert any(link['title']=='Pulp (paper)' for link in source['visual_links'])
 from source_translation import article_view,usable_translation
 english={'title':'H44','url':'https://en.wikipedia.org/wiki/H44','revision_id':12345,
          'revision_url':'https://en.wikipedia.org/w/index.php?oldid=12345',
          'text':'H44 packs files into one compressed archive.\nH44 checks 20 files every day.'}
 def translated_fixture(sentences,language):
  assert language=='uk' and sentences==english['text'].splitlines()
  return ['H44 пакує файли в один стиснений архів.','H44 перевіряє 30 файлів щодня.']
 translated=article_view(english,'uk',app.sentences,translate=translated_fixture)
 assert translated['text']=='H44 пакує файли в один стиснений архів.'
 slot={'source_position':0,'source_sentence':translated['text']}
 proof=app.beat_source(slot,translated)
 assert proof['source_span']==english['text'].splitlines()[0]
 assert proof['source_revision_url']==english['revision_url']
 assert proof['translated_span']==translated['text']
 assert not app.article_supports_query({'title':'Model yachting','text':'Work in yacht production is mentioned here.'},
                                         'Work in yacht production')
 assert not app.article_supports_query({'title':'Engineering','text':'Work is undertaken in Gdańsk.\nYacht production happens elsewhere.'},
                                         'Work in yacht production in Gdańsk')
 assert app.article_supports_query({'title':'Shipyard','text':'Work in yacht production in Gdańsk includes hull assembly.'},
                                     'Work in yacht production in Gdańsk')
 assert app.article_supports_query({'title':'Model yachting','text':'Model yachting is a recreational activity.'},
                                     'Model yachting')
 scoped={'strict_translated_scope':True}
 assert app.script_covers_identifier_scope([scoped],'Виробництво човнів в Одесі','uk',[
  {'text':'Виробництво човнів в Одесі охоплює кілька етапів.'}])
 assert not app.script_covers_identifier_scope([scoped],'Виробництво човнів в Одесі','uk',[
  {'text':'Виробництво човнів охоплює кілька етапів.'}])
 with patch.multiple(source_translation,configured_for=lambda lang:True,
                     query_configured_for=lambda lang:True,
                     english_query=lambda topic,lang:'Boat manufacturing in Odesa'), \
      patch.object(app,'cache_fetch',side_effect=lambda key,fetch:fetch()), \
      patch.object(app,'wikipedia',return_value=[
       {'title':'Boat manufacturing','text':'Boat manufacturing spans different materials.'},
       {'title':'Shipyard','text':'Boat manufacturing in Odesa uses composite materials.'}]), \
      patch.object(app,'translated_article',return_value=[translated]) as research:
  assert app.translated_research_sources('Виробництво човнів в Одесі','uk')==[translated]
  assert research.call_count==1
  assert research.call_args.args[0]['title']=='Shipyard'
 assert not usable_translation('About 12, then about 35.','Спочатку близько 35, потім близько 12.')
 assert not usable_translation('The system uses H-264 codec.','Система використовує кодек H.264.')
 assert 'machine-translated' in app.output_credits([translated],[])['text'][0]['changes']
 try:
  app.beat_source({**slot,'source_sentence':'Інше речення.'},translated)
 except ValueError:
  pass
 else:
  raise AssertionError('Mismatched translation lost its exact origin')
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
 assert app.place_scene_features('The most populous city in the region.','en')==[]
 assert app.place_scene_features('Skarpa biegnie w pobliżu Wisły.','pl')==['river','escarpment']
 assert app.place_scene_features('Most nad Wisłą.','pl')==['river','bridge']
 feature_slot={'entity_profile':place,'text':'The escarpment slopes down to the river.',
               'place_features':['river','escarpment'],'place_detail_query':'Example City river escarpment'}
 skyline={'provider':'commons','alt':'Example City skyline','query':feature_slot['place_detail_query'],
          'categories':['Category:Buildings in Example City'],'width':1200,'height':900}
 assert app.photo_score(skyline,feature_slot,'Example City')<0
 assert app.photo_score({**skyline,'alt':'Escarpment above the river in Example City'},feature_slot,'Example City')>=0
 assert app.insect_scene_features('Бджола виконує певні умовні рухи — танцює.')==['waggle dance']
 assert app.insect_scene_features('У кожної бджоли є дві пари крил та вусики.')==['antennae','wings']
 assert app.insect_scene_features('Бджолина матка відкладає яйця, з яких виходять личинки.')==['brood','queen']
 assert app.insect_scene_features('Пилок потрібен для годування личинок.')==['brood','pollen']
 assert app.insect_scene_features('Довгий хоботок потрібен для висмоктування нектару.')==['proboscis']
 insect={'text':'A bee performs a waggle dance.','insect_features':['waggle dance']}
 flowers={'provider':'commons','alt':'A bee on a flower','width':1200,'height':900}
 assert app.photo_score(flowers,insect,'Bee')<0
 assert app.photo_score({**flowers,'alt':'Honey bee performing a waggle dance on the comb'},insect,'Bee')>=0
 live_insect={'text':'A bee collects pollen.','entity_profile':{'visual_description':'clade of insects'}}
 fossil_bee={**flowers,'alt':'Fossilized stingless bee preserved in amber.'}
 assert app.photo_score(fossil_bee,live_insect,'Bee')<0
 hoverfly={**flowers,'depiction':'File:Eristalis tenax and flowers.jpg',
           'alt':'File:Eristalis tenax and flowers.jpg Drone fly on ragwort; a bee mimic.'}
 bee_slot={**live_insect,'entity_profile':{'name':'bee','visual_description':'clade of insects'}}
 assert app.photo_score(hoverfly,bee_slot,'Bee')<0
 assert app.photo_score(flowers,bee_slot,'Bee')>=0
 target_slot={**bee_slot,'visual_target':{'name':'Bee','kind':'animal'}}
 for title in ('Amber color ant with wings like bee','Bee or wasp','Crab spider with bee prey','Ant lifting dead bee','Greater Bee Fly - Bombylius major'):
  assert app.photo_score({**flowers,'depiction':f'File:{title}.jpg','alt':title},target_slot,'Bee')<0
 honey_slot={**bee_slot,'text':'Бджоли перероблюють нектар на мед.'}
 honey_slot['insect_features']=app.insect_scene_features(honey_slot['text'])
 assert honey_slot['insect_features']==['honey production']
 assert app.insect_scene_features('Бджоли перероблюють його в мед.')==['honey production']
 assert app.insect_scene_features('З нектару виробляється мед.')==['honey production']
 assert app.insect_scene_features('Існують у різноманітних колективних утвореннях.')==['insect colony']
 assert app.insect_scene_features('Молоді робочі бджоли годують молодняк.')==['brood']
 assert app.photo_score(flowers,honey_slot,'Bee')<0
 assert app.photo_score({**flowers,'alt':'Honey bees on honeycomb'},honey_slot,'Bee')>=0
 assert app.insect_scene_features('Бджоли як запилювачі важливі в сільському господарстві.')==['pollination']
 assert app.insect_scene_features('Бджолу-матір називають маткою.')==['queen']
 assert app.insect_scene_features('Один вид бджіл є обпилювачем цієї рослини.')==['pollination']
 assert app.insect_scene_features('Група бджіл пристосувалася до поїдання падалі.')==['carrion feeding']
 assert app.insect_scene_features('Бджола може стати жертвою павуків.')==['predation']
 assert app.insect_scene_features('Одиночні бджоли трапляються у саду.')==['solitary insects']
 prey={**flowers,'alt':'Crab spider with bee prey','depiction':'File:Crab spider with bee prey.jpg'}
 termite={**flowers,'alt':'Winged termites swarming','depiction':'File:Winged termites swarming.jpg'}
 wing_scene={**bee_slot,'insect_features':['wings']}
 assert app.photo_score(termite,wing_scene,'Bee')<0
 assert app.photo_score({**flowers,'alt':'Honeybee with wings extended'},wing_scene,'Bee')>=0
 assert app.photo_score(prey,bee_slot,'Bee')<0
 assert app.photo_score(prey,{**bee_slot,'insect_features':['predation']},'Bee')>=0
 assert app.photo_score({**flowers,'depiction':'File:Honey bee comb.jpg','alt':'Honey bee comb and an explanation of pollination'},
                        {**bee_slot,'insect_features':['pollination']},'Bee')<0
 assert app.volcanic_features('Під час виверження побачили потік лави.')==['eruption','lava flow']
 assert not app.volcanic_subject({'name':'Volcano Town','visual_description':'a town near a volcano'})
 assert app.volcanic_subject({'visual_description':'Sunda Strait volcanic island caldera'})
 volcano_slot={'text':'Під час виверження утворився шлейф попелу.','volcanic_features':['eruption'],
               'entity_profile':{'kind':'concept','name':'volcano'},'source_driven':True}
 quiet={**flowers,'alt':'A quiet volcano with a snow-covered cone','depiction':'File:Volcano in winter.jpg'}
 assert app.photo_score(quiet,volcano_slot,'volcano')<0
 assert app.photo_score({**quiet,'alt':'An ash cloud from the erupting volcano'},volcano_slot,'volcano')>=0
 mars_crater={**quiet,'depiction':'File:Mars volcano and impact crater.jpg','alt':'A volcanic caldera on Mars.'}
 crater_slot={**volcano_slot,'volcanic_features':['crater']}
 assert app.photo_score(mars_crater,crater_slot,'volcano')<0
 assert app.photo_score(mars_crater,crater_slot,'Mars volcano')>=0
 assert app.photo_score({**quiet,'alt':'A natural volcano stone'}, {**volcano_slot,'volcanic_features':[]},'volcano')<0
 audit_context=app.photo_audit_context('volcano',volcano_slot)
 assert app.photo_audit_context('volcano',{**volcano_slot,'text':'Інше речення про виверження.'})==audit_context
 assert app.photo_audit_context('volcano',{**volcano_slot,'volcanic_features':['crater']})!=audit_context
 natural={'text':'A plume rose from Example Peak.','volcanic_features':['eruption']}
 volcanic_source={'entity_profile':{'id':'Q1','kind':'concept','name':'volcano'}}
 example={'id':'Q2','name':'Example Peak','description':'active volcano','commons_category':'Example Peak'}
 link={'label':'Example Peak','title':'Example Peak'}
 with patch.object(storyboard,'source_links',return_value=[link]),patch.object(storyboard,'resolve_links',return_value={'Example Peak':example}):
  storyboard.build([natural],[volcanic_source],'en',app)
 assert natural['visual_targets'][0]['id']=='Q2'
 assert 'Example Peak eruption' in storyboard.query_plan([natural])
 grounded={**volcano_slot,'visual_target':natural['visual_targets'][0]}
 assert app.photo_score({**quiet,'alt':'An ash cloud from an erupting volcano.'},grounded,'volcano')<0
 assert app.photo_score({**quiet,'depiction':'File:Example Peak eruption.jpg','alt':'An ash cloud from the erupting volcano.'},grounded,'volcano')>=0
 dated_scene={**natural,'text':'A plume rose from Example Peak in 1883.'}
 with patch.object(storyboard,'source_links',return_value=[link]),patch.object(storyboard,'resolve_links',return_value={'Example Peak':example}):
  storyboard.build([dated_scene],[volcanic_source],'en',app)
 dated_target=dated_scene['visual_targets'][0]
 assert dated_target['intent']['event_years']==['1883']
 assert storyboard.target_score({**quiet,'depiction':'File:Example Peak eruption 2020.jpg','alt':'First erupted in 1883'},{'visual_target':dated_target},app)<0
 region={'id':'Q3','name':'Example Mountains','description':'mountain range'}
 context={'text':'Old volcanoes are found in the Example Mountains.'}
 with patch.object(storyboard,'source_links',return_value=[{'title':region['name'],'label':region['name']}]),patch.object(storyboard,'resolve_links',return_value={region['name']:region}):
  storyboard.build([context],[volcanic_source],'en',app)
 attached=context['visual_targets'][0]
 assert storyboard.target_score({**quiet,'depiction':'File:Example Mountains panorama.jpg','alt':'Mountain panorama'},{'visual_target':attached},app)<0
 assert storyboard.target_score({**quiet,'depiction':'File:Example Mountains volcanic outcrop.jpg'},{'visual_target':attached},app)>=0
 assert storyboard.linked_alias_in({'label':'Везувій','title':'Везувій'},'Виверження Везувію.', 'uk')
 assert not storyboard.linked_alias_in({'label':'Везувій','title':'Везувій'},'Виверження іншого вулкана.', 'uk')

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
 parser=storyboard.ArticleLinks()
 parser.feed('<p>A <a href="/wiki/River_One">river</a> feeds the lake.</p><p>The <a href="/wiki/Unrelated_Fiction">river</a> is a fictional character.</p>')
 first='A river feeds the lake.'
 local_sources=[{'text':first+'\nThe river is a fictional character.','url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
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
 with patch.object(app,'photo_score',wraps=app.photo_score) as scoring:
  options,edges=app.rank_storyboard_photos(fixtures,expanded,[0]*6,'Example')
  assert scoring.call_count==2*len(fixtures)
 assert app.allocate_photos(fixtures,[body],'Example',6,scene_slots=expanded,edges=edges)==assigned
 assert len(options[0])==1 and len(options[2])==2


 # Wikipedia often links a name only at its first mention. Unambiguous aliases
 # remain usable later; an ambiguous label still requires its local link.
 only=storyboard.ArticleLinks();only.feed('<p><a href="/wiki/Example_City">Example City</a> is introduced.</p>')
 alias_sources=[{'text':'Example City is introduced.\nThe scientist was born in Example City.','url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 alias_slots=[{'text':'An introduction.','source_index':0,'source_sentence':'An introduction.'},{'text':'The scientist was born in Example City.','source_index':0,'source_sentence':'The scientist was born in Example City.'}]
 with patch.object(storyboard,'source_links',return_value=only.links),patch.object(storyboard,'resolve_links',return_value={'Example City':{'id':'Q995','name':'Example City','kind':'entity','description':'city','native_name':'Example City'}}):
  storyboard.build(alias_slots,alias_sources,'en',app)
 assert alias_slots[1]['visual_targets'][0]['id']=='Q995'
 assert alias_slots[1]['visual_targets'][0]['binding']=='unambiguous article alias'


 # A specifically linked landmark outranks an inferred city elsewhere in the article.
 scoped=storyboard.ArticleLinks();scoped.feed('<p><a href="/wiki/Example_City">Example City</a> is introduced.</p><p>The scientist rests in the <a href="/wiki/Example_Mausoleum">Example Mausoleum</a> in Example City.</p>')
 sentence='The scientist rests in the Example Mausoleum in Example City.'
 scoped_sources=[{'text':'Example City is introduced.\n'+sentence,'url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 scoped_slots=[{'text':'Introduction.','source_index':0},{'text':sentence,'source_sentence':sentence,'source_index':0}]
 with patch.object(storyboard,'source_links',return_value=scoped.links),patch.object(storyboard,'resolve_links',return_value={'Example City':{'id':'Q995','name':'Example City','kind':'entity','description':'city'},'Example Mausoleum':{'id':'Q996','name':'Example Mausoleum','kind':'entity','description':'mausoleum'}}):
  storyboard.build(scoped_slots,scoped_sources,'en',app)
 assert [target['id'] for target in scoped_slots[1]['visual_targets']]==['Q996']

 # Abstract academic qualifications cannot illustrate a person's research with someone else's graduation.
 degree_parser=storyboard.ArticleLinks();degree_parser.feed('<p>The scientist researched radiation for a <a href="/wiki/Doctorate">doctorate</a>.</p>')
 degree_sentence='The scientist researched radiation for a doctorate.'
 degree_sources=[{'text':degree_sentence,'url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 with patch.object(storyboard,'source_links',return_value=degree_parser.links),patch.object(storyboard,'resolve_links',return_value={'Doctorate':{'id':'Q997','name':'doctorate','kind':'entity','description':'academic or professional degree'}}):
  try:storyboard.build([{'text':'Introduction.','source_index':0},{'text':degree_sentence,'source_sentence':degree_sentence,'source_index':0}],degree_sources,'en',app)
  except storyboard.SceneUnavailable:pass
  else:raise AssertionError('An abstract degree became visual evidence for research')

 # A scarce scene keeps its facts and minimum two photos; surplus shots move to other beats.
 limited=[{'text':'A long physical process fact. '*5,'visual_shot_cap':3},{'text':'Another physical stage.'},{'text':'A final physical stage.'}]
 layout=app.storyboard_beats(12,limited)
 assert len(layout)==12 and layout.count(0)==3 and all(layout.count(i)>=2 for i in range(3))
 try:app.storyboard_beats(12,[{**slot,'visual_shot_cap':3} for slot in limited])
 except app.ShotCapacityError:pass
 else:raise AssertionError('A bounded layout exceeded verified image capacity')
 scarce=storyboard.SceneUnavailable({'source_index':0,'source_sentence':'A complete fact.'},'No fourth distinct image')
 scarce.beat_index=0;scarce.verified_in_beat=3
 with TemporaryDirectory() as folder:
  test_slots=[{'text':'A complete fact.'},{'text':'Another complete fact.'}]
  with patch.object(app,'VISUAL',app.Path(folder)),patch.object(app,'_prepare_visuals',side_effect=[scarce,{'complete':True}]) as prepare:
   assert app.prepare_visuals('owned-test',[],'Example','en',30,test_slots)=={'complete':True}
   assert prepare.call_count==2 and test_slots[0]['visual_shot_cap']==3
   assert test_slots[0]['text']=='A complete fact.'
 with patch.object(app,'_prepare_visuals',side_effect=[app.PhotoPoolTooSmall(8,6),{'complete':True}]) as prepare:
  assert app.prepare_visuals('owned-test',[],'Example','en',30,test_slots)=={'complete':True}
  assert [call.args[-2:] for call in prepare.call_args_list]==[(12,6),(8,6)]
 with patch.object(app,'_prepare_visuals',side_effect=app.PhotoPoolTooSmall(5,6)) as prepare:
  try:app.prepare_visuals('owned-test',[],'Example','en',30,test_slots)
  except app.PhotoPoolTooSmall:pass
  else:raise AssertionError('An undersized photo pool was accepted')
  assert prepare.call_count==1

 # Differently worded sentences must not repeat the same founding event.
 events=storyboard.ArticleLinks();events.feed('<p>In 2002 the founder established <a href="/wiki/Example_Rockets">Example Rockets</a>.</p><p>In June 2002 the founder founded <a href="/wiki/Example_Rockets">Example Rockets</a>.</p>')
 first_event='In 2002 the founder established Example Rockets.';second_event='In June 2002 the founder founded Example Rockets.'
 event_sources=[{'text':first_event+'\n'+second_event,'url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 event_slots=[{'text':'Introduction.','source_index':0},{'text':first_event,'source_sentence':first_event,'source_index':0},{'text':second_event,'source_sentence':second_event,'source_index':0}]
 with patch.object(storyboard,'source_links',return_value=events.links),patch.object(storyboard,'resolve_links',return_value={'Example Rockets':{'id':'Q998','name':'Example Rockets','kind':'entity','description':'aerospace company'}}):
  try:storyboard.build(event_slots,event_sources,'en',app)
  except storyboard.SceneUnavailable as error:assert error.source_sentence==second_event and error.visual_target is None
  else:raise AssertionError('The same founding event was narrated twice')
 company={'id':'Q998','name':'Example Rockets','description':'spaceflight company'}
 company['intent']=storyboard.scene_intent('The founder established Example Rockets.',company)
 assert company['intent']['visual_objects'][0]=='rocket'
 ceremony={'provider':'commons','depiction':'File:Example Rockets welcome home ceremony.jpg','alt':'Spacecraft returned safely to the factory.'}
 assert storyboard.target_score(ceremony,{'visual_target':company},app)<0

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
 with patch.object(app,'SEARCH_QUERIES',{'stock':set(),'commons':set()}),patch.object(app,'DISCOVERED_PHOTOS',{}),patch.object(app,'media_aliases',return_value=['Example topic']),patch.object(app,'photo_search',side_effect=AssertionError('Stock sources must not be mixed into the share-alike adaptation')),patch.object(app,'commons_search',side_effect=rate) as search:
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

 # An organization cannot inherit a namesake person's identity or generic podium portrait.
 company={'id':'Q998','name':'Example, Inc.','aliases':['Example'],'description':'automotive manufacturer'}
 company['intent']=storyboard.scene_intent('The founder invested in Example, Inc.',company)
 def org_photo(title,alt=''):return {'provider':'commons','depiction':'File:'+title+'.jpg','alt':alt,'categories':[]}
 assert storyboard.target_score(org_photo('Inventor Example laboratory'),{'visual_target':company},app)<0
 assert storyboard.target_score(org_photo('Example automobile factory'),{'visual_target':company},app)>0
 assert storyboard.target_score(org_photo('Example founder at podium'),{'visual_target':company},app)<0

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
 salvage={**photo,'depiction':'Salvage drive. Scrap paper hydraulic press.jpg',
          'alt':'Scrap paper, packed in hydraulic presses and tied into bales.'}
 assert app.photo_score(salvage,slot,'How paper is made')<0
 assert app.photo_score(salvage,{**slot,'text':'The factory presses scrap paper into bales.'},'How paper is made')>=0
 assert app.scene_actions('Wet paper fibers drain through a sieve.')=={'drain'}
 assert 'drain' not in app.scene_actions('The phone screen is assembled in the factory.')
 assert app.process_definition('Papermaking is the process of manufacturing paper and cardboard.')
 assert not app.process_definition('Papermaking — economic sector.')
 assert not app.process_definition('Glass is a non-crystalline solid.')
 # Duration fitting must preserve different manufacturing stages instead of repeating pressing.
 stage_rows=[(40,0,'The manufacturing process makes the material.',['lead']),(14,0,'Press rollers squeeze the wet sheet.',['press']),(13,0,'Hydraulic pressing removes the remaining water.',['press']),(12,0,'Fibers drain through a sieve screen.',['drain']),(12,0,'Finished sheets dry on open racks.',['dry'])]
 with patch.object(app,'measured_sentence_ms',return_value=1000):
  fitted=app.fit_narration(stage_rows,4,'en',True,5000,required_sentence=stage_rows[0][2])
 assert len(fitted)==4 and sum(app.scene_actions(slot['text'])=={'press'} for slot in fitted)==1
 assert any(app.scene_actions(slot['text'])=={'dry'} for slot in fitted)
 # Keep the named physical model needed for source-to-image binding, while omitting bare date asides.
 model_sentence='The inventor bought a computer (Example ZX-80) and learned programming (1971).'
 clean=app.omit_parenthetical_asides(app.retain_named_model_asides(model_sentence))
 assert 'Example ZX-80' in clean and '1971' not in clean
 # A scientific award is not illustrated with a different disciplinary prize.
 field_award={'id':'Q999','name':'Example Prize','description':'international award'}
 field_award['intent']=storyboard.scene_intent('The scientist received the Example Prize in physics.',field_award)
 peace_medal={'provider':'commons','depiction':'File:Example Prize peace medal.jpg','alt':'A physical medal'}
 physics_medal={'provider':'commons','depiction':'File:Example Prize physics medal.jpg','alt':'A physical medal'}
 assert storyboard.target_score(peace_medal,{'visual_target':field_award},app)<0
 assert storyboard.target_score(physics_medal,{'visual_target':field_award},app)>0
 assert storyboard.award_domains('Nagrodę otrzymała z fizyki.')=={'physics'}
 # A concrete instrument outranks a broad company mentioned in the same factual scene.
 specificity=storyboard.ArticleLinks();specificity.feed('<p><a href="/wiki/Example_Device">Example Device</a> is introduced.</p><p>The engineer demonstrated Example Device at <a href="/wiki/Example_Corporation">Example Corporation</a>.</p>')
 specific_sentence='The engineer demonstrated Example Device at Example Corporation.'
 specific_sources=[{'text':'Example Device is introduced.\n'+specific_sentence,'url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 specific_slots=[{'text':'Introduction.','source_index':0},{'text':specific_sentence,'source_sentence':specific_sentence,'source_index':0}]
 with patch.object(storyboard,'source_links',return_value=specificity.links),patch.object(storyboard,'resolve_links',return_value={'Example Device':{'id':'Q112','name':'Example Device','kind':'entity','description':'laboratory instrument'},'Example Corporation':{'id':'Q113','name':'Example Corporation','kind':'entity','description':'technology company'}}):
  storyboard.build(specific_slots,specific_sources,'en',app)
 assert [target['id'] for target in specific_slots[1]['visual_targets']]==['Q112']
 # Establishing views cannot consume the only photos that verify a later physical stage.
 beat_map=[0,0,0,1,1,1,2,2,2]
 scene_rows=[{'text':'Factory production overview.','process_intent':True}]*3+[{'text':'Wet fibres drain through a sieve.','process_intent':True}]*3+[{'text':'Rollers press the sheet.','process_intent':True}]*3
 eligible=[set(range(10))]*3+[set(range(3))]*3+[set(range(5))]*3
 ordering=app.photo_selection_order(beat_map,scene_rows,eligible)
 assert sorted(ordering)==list(range(9))
 assert ordering[:2]==[3,4] and ordering.index(0)>ordering.index(6)
 assert max(ordering.index(i) for i in (0,1,3,4,6,7))<min(ordering.index(i) for i in (2,5,8))
 # A matching head noun does not turn food into a cellulose manufacturing image.
 food_photo={'provider':'pexels','alt':'Vietnamese food production, rice paper drying on woven mats','height':1000,'width':1500}
 assert app.photo_score(food_photo,{'text':'The paper dries on racks.','process_intent':True,'source_driven':True},'Paper')<0
 wet_mesh={'provider':'pixabay','alt':'paper manufacturing, paper mesh, papermaking mould','height':1000,'width':1500}
 assert app.photo_score(wet_mesh,{'text':'The paper dries on racks.','process_intent':True,'source_driven':True},'How paper is made')<0
 assert 'drain' in app.visual_actions('papermaking paper mesh')
 # Share-alike material is admitted with explicit author/licence data; NC/ND remain excluded.
 assert app.COMMONS_ONLY
 assert app.supported_commons_license('CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/','Example Author')
 assert app.supported_commons_license('CC BY-SA 3.0','https://creativecommons.org/licenses/by-sa/3.0/','Example Author')
 assert not app.supported_commons_license('CC BY-SA 4.0','https://example.org/wrong-license','Example Author')
 assert not app.supported_commons_license('CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/','')
 assert not app.supported_commons_license('CC BY-NC 4.0','https://creativecommons.org/licenses/by-nc/4.0/','Example Author')
 assert not app.supported_commons_license('CC BY-ND 4.0','https://creativecommons.org/licenses/by-nd/4.0/','Example Author')
 # Commons publishes official licence URIs both with and without the trailing slash.
 assert app.supported_commons_license('CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0','Example Author')
 assert app.supported_commons_license('CC BY-SA 3.0','http://creativecommons.org/licenses/by-sa/3.0/','Example Author')
 assert not app.supported_commons_license('CC BY-SA 4.0','https://creativecommons.org.evil.example/licenses/by-sa/4.0','Example Author')
 info={'url':'https://upload.wikimedia.org/wikipedia/commons/test.jpg','width':1000,'height':800,'size':2000,
       'extmetadata':{'LicenseShortName':{'value':'CC BY-SA 4.0'},'LicenseUrl':{'value':'https://creativecommons.org/licenses/by-sa/4.0/'},'Artist':{'value':'Example Author'}}}
 restricted={**info,'extmetadata':{**info['extmetadata'],'LicenseShortName':{'value':'CC BY-NC 4.0'}}}
 pages={'1':{'pageid':1,'title':'File:Example photo.jpg','imageinfo':[info]},
        '2':{'pageid':2,'title':'File:Restricted.jpg','imageinfo':[restricted]}}
 with patch.object(app,'cache_fetch',side_effect=lambda key,fetch:fetch()),patch.object(app,'http_json',side_effect=[{'parse':{'images':['Icon.svg','Example photo.jpg','Restricted.jpg']}},{'query':{'pages':pages}}]) as http:
  matches=app.article_photo_candidates({'url':'https://uk.wikipedia.org/wiki/Example','revision_id':1234})
  assert [photo['id'] for photo in matches]==['1']
  assert matches[0]['article_media_revision']=='https://uk.wikipedia.org/w/index.php?oldid=1234'
  assert 'oldid=1234' in http.call_args_list[0].args[0]
  assert 'Icon' not in http.call_args_list[1].args[0]
  assert not app.article_photo_candidates({'url':'https://example.org/wiki/Example','revision_id':1234})
  assert http.call_count==2
 # General Cyrillic overviews avoid foreign-name catalogues the selected native voice cannot align reliably.
 catalogue='Исследователи используют Alpha Mission, Beta Orbiter, Gamma Explorer, Delta Probe и другие аппараты.'
 assert app.foreign_name_catalogue(catalogue,'ru','Планета')
 assert app.foreign_name_catalogue(catalogue,'uk','Планета')
 assert not app.foreign_name_catalogue(catalogue,'ru','Список аппаратов')
 assert not app.foreign_name_catalogue('Он приобрёл компьютер Example ZX-80, и научился программировать.','ru','Учёный')
 assert not app.foreign_name_catalogue('A long, complete, ordinary, English sentence.','en','Science')
 # Duration correction chooses complete supported clauses, never noun fragments.
 long_fact='Water is further removed from the wet sheet by pressing, sometimes aided by suction or heating.'
 assert 'Water is further removed from the wet sheet by pressing.' in app.complete_clause_variants(long_fact,'en')
 assert app.complete_clause_variants('Photosynthesis, which is a biological process, converts energy.','en')==['Photosynthesis, which is a biological process, converts energy.']
 polish='Badacz Jan Kowalski otrzymał międzynarodową nagrodę za badania nad roślinami.'
 assert 'Badacz Jan Kowalski otrzymał międzynarodową nagrodę.' in app.complete_clause_variants(polish,'pl')
 assert app.semantic_categories({'categories':['Category:Press photographs','Category:Paper presses']})==['Category:Paper presses']
 mould={'provider':'commons','depiction':'File:Paper mould.jpg','alt':'A wooden paper mould with mesh','categories':['Category:Paper moulds'],'height':900,'width':1200}
 assert app.photo_score(mould,{'text':'Wet paper drains through a sieve.','process_intent':True},'Paper manufacturing')>=0
 assert app.photo_score(mould,{'text':'The paper dries on racks.','process_intent':True},'Paper manufacturing')<0
 # A material's industrial production is not a substitute for a biological phenomenon.
 concept_slots=[{'text':'Photosynthesis converts light energy.','source_index':0},{'text':'Photosynthesis releases oxygen.','source_index':0}]
 with patch.object(storyboard,'source_links',side_effect=AssertionError('Do not substitute associated ingredients for a concept')):
  storyboard.build(concept_slots,[{'entity_profile':{'kind':'concept','name':'Photosynthesis'}}],'en',app)
 assert all(not slot['visual_targets'] for slot in concept_slots)
 # Native inflections identify the same physical stage in all supported narration languages.
 assert app.scene_actions('Papier jest wysuszany na stojakach.')=={'dry'}
 assert app.scene_actions('Бумагу высушивают на стеллажах.')=={'dry'}
 assert app.scene_actions('Папір висушують на стелажах.')=={'dry'}
 assert app.scene_actions('Волокна зневоднюють через сито.')=={'drain'}
 assert app.scene_actions('Смесь расплавляют в печи.')=={'melt'}
 conference={'provider':'commons','depiction':'File:White paper press conference.jpg','alt':'A press conference about a white paper','categories':['Category:Paper industry'],'height':1000,'width':1400}
 assert app.photo_score(conference,{'text':'The paper is pressed.','process_intent':True},'Paper manufacturing')<0
 # Scene identity must also retain the stated place or physical work context.
 city={'id':'Q991','name':'Sample City','description':'city in Europe'}
 city['intent']=storyboard.scene_intent('The scientist was born in Sample City.',city)
 school={'provider':'commons','depiction':'File:Sample City school.jpg','alt':'A school in Sample City','categories':['Category:Sample City']}
 panorama={**school,'depiction':'File:Sample City panorama.jpg'}
 assert storyboard.target_score(school,{'visual_target':city},app)<0
 assert storyboard.target_score(panorama,{'visual_target':city},app)>0
 tunnel={'id':'Q992','name':'Sample Construction','description':'infrastructure and tunneling company'}
 tunnel['intent']=storyboard.scene_intent('The founder established Sample Construction.',tunnel)
 prop={'provider':'commons','depiction':'File:Sample Construction watchtower.jpg','alt':'A sentry tower at the tunnel opening event'}
 assert storyboard.target_score(prop,{'visual_target':tunnel},app)<0
 press_photo={**conference,'depiction':'File:Paper Dolls press photo.jpg','alt':'Publicity photograph from a television series'}
 assert app.photo_score(press_photo,{'text':'The paper is pressed.','process_intent':True},'Paper manufacturing')<0
 # Reserve broad process discovery: stage refinements must not evict it.
 process_slots=[{'text':text,'source_driven':True,'process_intent':True,'entity_profile':{'name':'Papermaking','commons_category':'Papermaking'}} for text in ['Water drains through a paper screen.','Paper is pressed.','Paper dries.']]
 with patch.object(app,'SEARCH_QUERIES',{'stock':set(),'commons':set()}),patch.object(app,'DISCOVERED_PHOTOS',{}),patch.object(app,'commons_search',return_value=[{'provider':'commons','id':'1'}]) as search:
  app.discover_photos('paper manufacturing','en',process_slots)
  queries=[call.args[0] for call in search.call_args_list]
  assert len(queries)<=12 and 'incategory:"Papermaking"' in queries
  assert 'paper handmade' in queries and 'paper mould' in queries
 capital={**city,'description':'administrative capital of a country'}
 assert storyboard.scene_intent('Born in the capital.',capital)['name']=='city context'
 ruin={**panorama,'alt':'A ruin of the former Panorama building','depiction':'File:Sample City panorama building.jpg'}
 assert storyboard.target_score(ruin,{'visual_target':city},app)<0
 interior={**panorama,'depiction':'File:Sample City spherical interior panorama.jpg'}
 assert storyboard.target_score(interior,{'visual_target':city},app)<0
 interface={'id':'Q993','name':'brain-computer interface','description':'connection between brain and computer'}
 interface['intent']=storyboard.scene_intent('Research on a brain-computer interface.',interface)
 tissue={'provider':'commons','depiction':'File:Brain computer interface tissue construct.jpg','alt':'A microscope view of glial cells','categories':[]}
 headset={'provider':'commons','depiction':'File:Brain computer interface electrode headset.jpg','alt':'An electrode headset connected to a computer','categories':[]}
 assert storyboard.target_score(tissue,{'visual_target':interface},app)<0
 assert storyboard.target_score(headset,{'visual_target':interface},app)>0
 # A high-scoring short source pair must not defeat the native duration window.
 facts=[(100,0,'The instrument records a complete measurement each morning with its original source clock.',[]),(100,0,'The recorded measurements are stored in the laboratory with their original source dates.',[]),(10,0,'The instrument measures the material with a calibrated sensor before every experimental session begins.',[]),(10,0,'The laboratory stores each complete measurement with its original date and its source instrument identifier.',[])]
 with patch.object(app,'natural_char_rate',return_value=140),patch.object(app,'natural_internal_rate',return_value=None):
  selected=app.fit_narration(facts,2,'en',duration_ms=30000,natural=True)
  predicted=sum((len(app.selected_voice_request('en',row['text'])['input']['text'])+1)*140 for row in selected)
  assert 27000<=predicted<=30000,predicted
 # Feasible fact counts compete on measured duration; the preferred count is a tie-breaker.
 short=' '.join(['word']*81)+'.'
 fitted=' '.join(['word']*89)+'.'
 def count_plan(sources,topic,count,lang,duration_s):
  text=short if count==3 else fitted
  return [{'text':text,'score':100 if count==3 else 1}]+[{'text':'','score':0} for _ in range(count-1)] if count in {2,3} else []
 with patch.object(app,'source_overview_mode',return_value=True),patch.object(app,'source_slots',side_effect=count_plan),patch.object(app,'expand_source_blocks',side_effect=lambda rows,limit:rows),patch.object(app,'natural_char_rate',return_value=64),patch.object(app,'natural_internal_rate',return_value=None):
  selected=app.plan_script([{}],'A process','en',30,max_beats=6)
  assert len(selected)==2
 # Expanding a multi-stage source block must not repeat its physical stages.
 block='The pulp drains through a screen and then the sheet is pressed.'
 repeat='A screen drains additional water from the pulp.'
 with patch.object(app,'natural_char_rate',return_value=100),patch.object(app,'natural_internal_rate',return_value=None):
  assert not app.fit_narration([(100,0,block,[]),(100,0,repeat,[])],2,'en',process_intent=True,duration_ms=12000,natural=True)
 ordered=app.order_process_slots([{'text':'The sheet is pressed.'},{'text':'Wet pulp drains through a screen.'},{'text':'The sheet dries on racks.'},{'text':'Papermaking is a manufacturing process.'}])
 assert [next(iter(app.scene_actions(row['text']))) for row in ordered]==['production','drain','press','dry']
 landing_target={'id':'Q994','name':'Example Rocket','description':'partially reusable orbital launch vehicle'}
 landing_target['intent']=storyboard.scene_intent('The Example Rocket landed on its landing pad.',landing_target)
 leg={'provider':'commons','depiction':'File:Example Rocket landing leg in headquarters.jpg','alt':'A displayed component at company headquarters'}
 descent={**leg,'depiction':'File:Example Rocket landing.jpg','alt':'The rocket lands on its launch landing pad'}
 assert storyboard.target_score(leg,{'visual_target':landing_target},app)<0
 assert storyboard.target_score(descent,{'visual_target':landing_target},app)>0
 # Homonyms are typed: an appointment to office is never a vehicle landing.
 office={'id':'Q9001','name':'President of Example','description':'head of state of Example'}
 for sentence in ['Обраний на посаду президента.','Избран на пост президента.','Elected to the office of president.','Wybrany na urząd prezydenta.']:
  assert storyboard.scene_intent(sentence,office)['name']!='landing'
 profile={'id':'Q9002','name':'Example Person','native_name':'Приклад','commons_category':'Example Person'}
 event=storyboard.person_event_target(office,profile,'Обраний на посаду президента.')
 assert event['intent']['event']=='inauguration' and event['linked_context']['id']==office['id']
 inauguration={'provider':'commons','depiction':'File:Example Person inauguration.jpg','alt':'Taking the oath of office','identity_verification':{'entity_id':profile['id']}}
 portrait={**inauguration,'depiction':'File:Example Person portrait.jpg'}
 other={**inauguration,'identity_verification':{'entity_id':'Q9999'}}
 assert storyboard.target_score(inauguration,{'visual_target':event},app)>0
 assert storyboard.target_score(portrait,{'visual_target':event},app)<0
 assert storyboard.target_score(other,{'visual_target':event},app)<0
 assert any('inauguration' in query for query in storyboard.query_plan([{'visual_targets':[event]}]))
 studio={'id':'Q9003','name':'Example Studio','description':'television production company'}
 performance=storyboard.person_event_target(studio,profile,'An actor and comedian performed with Example Studio.')
 assert performance['intent']['event']=='performance'
 assert storyboard.person_event_target(studio,profile,'The company was acquired.')==studio
 assert storyboard.person_event_target({'description':'automotive manufacturer'},profile,'The founder established a company.')=={'description':'automotive manufacturer'}
 # Explicit campaign context also works without a linked physical object.
 direct=storyboard.person_event_target(profile,profile,'Під час передвиборчої кампанії кандидат представив програму.')
 assert direct['intent']['event']=='campaign'
 dated=storyboard.person_event_target(profile,profile,'The candidate joined the 2019 election campaign.')
 photo={'provider':'commons','depiction':'File:Candidate voting 2019.jpg','identity_verification':{'entity_id':profile['id']}}
 assert storyboard.target_score(photo,{'visual_target':dated},app)>0
 summit={**photo,'depiction':'File:Candidate at 2023 summit.jpg','alt':'Previously won the 2019 election'}
 assert storyboard.target_score(summit,{'visual_target':dated},app)<0
 assert storyboard.target_score(summit,{'visual_target':direct},app)<0
 assert storyboard.target_score(photo,{'visual_target':direct},app)>0
 assert all('2019' in query for query in storyboard.query_plan([{'visual_targets':[dated]}]))

 assert storyboard.person_event_target(profile,profile,'Виступив проти наміру міністерства змінити правила.')==profile
 query_variants=storyboard.query_plan([{'visual_targets':[direct]}])
 assert any('election' in query for query in query_variants) and any('campaign' in query for query in query_variants)
 assert any('Example Studio' in query for query in storyboard.query_plan([{'visual_targets':[performance]}]))
 # Missing photos for one event must not blacklist the person's entire biography.
 bad_text='Example Person took part in an election campaign.'
 good_text='Example Person took the oath of office at the inauguration.'
 event_source=[{'text':bad_text+'\n'+good_text}]
 bad_slot={'text':bad_text,'source_sentence':bad_text,'source_index':0,'visual_target':event}
 good_slot={'text':good_text,'source_sentence':good_text,'source_index':0}
 calls=[]
 def missing_campaign(rows):
  calls.append(rows)
  if len(calls)==1:raise storyboard.SceneUnavailable(bad_slot,'No verified campaign photographs')
 with patch.object(app,'plan_script',return_value=[good_slot]):
  assert app.prepare_illustrated_slots(event_source,'Example Person','en',30,30,[bad_slot],missing_campaign)==[good_slot]
 assert event_source[0]['excluded_visual_sentences']==[bad_text]
 first='Wind turbines are machines that convert wind into electricity.'
 other='Wind turbines generate electricity when moving air turns the blades attached to each rotor.'
 overview=[{'title':'Wind turbines','text':first+'\n'+other,'entity_profile':{'id':'Q1'},'excluded_visual_sentences':[first]}]
 overview_slots=app.source_slots(overview,'Wind turbines',1,'en',duration_s=15)
 assert [slot['source_sentence'] for slot in overview_slots]==[other],overview_slots
 already_spoken={'text':'Example Person was elected in a national vote.','source_index':0}
 calls.clear()
 event_source=[{'text':bad_text+'\n'+already_spoken['text']+'\n'+good_text}]
 seen={app.narration_digest('en',[already_spoken])}
 with patch.object(app,'plan_script',side_effect=[[already_spoken],[good_slot]]):
  assert app.prepare_illustrated_slots(event_source,'Example Person','en',30,30,[bad_slot],missing_campaign,seen,-1)==[good_slot]
 assert calls==[[bad_slot],[good_slot]]
 # Historical event photos must depict the event, not later anniversary exhibitions.
 revolution={'id':'Q9003','name':'Example Revolution','description':'2014 revolution in Example','commons_category':'Example protests'}
 revolution['intent']=storyboard.scene_intent('The election followed the Example Revolution.',revolution)
 actual={'provider':'commons','depiction':'File:Example Revolution 2014 street protest.jpg','alt':'Protesters at the Example Revolution in 2014'}
 assert storyboard.target_score(actual,{'visual_target':revolution},app)>0
 for title,description in [('Example Revolution anniversary 2022','A commemoration of the 2014 revolution'),('Example Revolution photoexhibition 2019','Відкриття фотовиставки до п’ятої річниці подій 2014 року'),('Example Revolution 2016','Вшанування загиблих у 2014 році')]:
  assert storyboard.target_score({**actual,'depiction':'File:'+title+'.jpg','alt':description},{'visual_target':revolution},app)<0
 assert any('2014' in query for query in storyboard.query_plan([{'visual_targets':[revolution]}]))
 named_event={'id':'Q9004','name':'The Assembly','commons_category':'The Assembly','description':'2014 mass protest in Example'}
 named_event['intent']=storyboard.scene_intent('The Assembly followed the election.',named_event)
 assert storyboard.target_score({'provider':'commons','depiction':'File:The Assembly 2014 public square.jpg','alt':'The Assembly in 2014'},{'visual_target':named_event},app)>0
 # A completed recording from a failed downstream stage needs exact source/text/voice binding.
 first='Перший повний факт.';second='Другий повний факт.';spoken=first+' '+second
 evidence={'voice':app.SELECTED_VOICES['uk'][1],'spoken_text':spoken,'sources':[{'url':'https://uk.wikipedia.org/wiki/Example'}],'beats':[{'text':first,'source_index':0,'source_sentence':first,'source_position':0},{'text':second,'source_index':0,'source_sentence':second,'source_position':len(first)+1}]}
 receipt={'voice':evidence['voice'],'duration_ms':28000,'text_sha256':hashlib.sha256(spoken.encode()).hexdigest()}
 source=[{'url':evidence['sources'][0]['url'],'text':spoken}]
 assert len(app.source_verified_native_plan(evidence,receipt,source,'Example','uk',30))==2
 assert app.source_verified_native_plan(evidence,{**receipt,'voice':'unselected'},source,'Example','uk',30) is None
 assert app.source_verified_native_plan(evidence,{**receipt,'text_sha256':'0'*64},source,'Example','uk',30) is None
 assert app.source_verified_native_plan(evidence,receipt,[{**source[0],'text':'Changed '+spoken}],'Example','uk',30) is None
 assert app.source_verified_native_plan(evidence,{**receipt,'duration_ms':32000},source,'Example','uk',30) is None
 # A named family requires a visible family group, not any image of its famous member.
 family_target={'id':'Q9002','name':'family of Example Person','description':'First Family of Example from 2009 to 2017'}
 family_intent=storyboard.scene_intent('The official spoke about the extended family.',family_target)
 assert family_intent['name']=='family group'
 assert 'alone' in ' '.join(family_intent['negative_descriptions'])
 assert 'large crowd' in ' '.join(family_intent['negative_descriptions'])
 with patch.object(app,'get_pixel_verifier') as factory:
  factory.return_value.check.side_effect=[{'passed':True},{'passed':False}]
  audit=app.pixel_check('unused','Example Person',{'visual_target':{**family_target,'intent':family_intent}})
  assert not audit['passed'] and not audit['family_group_verification']['passed']
  assert factory.return_value.check.call_args_list[1].args[1]=='members of a family photographed together'
 # A distinct script alone is insufficient after a miss: compare complete
 # alternatives against the original delivery window in either direction.
 prior=[{'text':'Previously measured script.'}]
 short=[{'text':'Distinct but too short.'}]
 fits=[{'text':'Distinct and close to the target.'}]
 seen={app.narration_digest('uk',prior)}
 for duration in app.DURATIONS:
  for lang in app.LANGS:
   def candidate(sources,topic,language,budget,max_beats=None,excluded_narrations=()):
    assert max_beats==duration//5 and excluded_narrations==seen
    return fits if budget==duration-1.5 else short
   with patch.object(app,'source_overview_mode',return_value=True),patch.object(app,'plan_script',side_effect=candidate),patch.object(app,'natural_duration_ms',side_effect=lambda text,language:duration*(950 if text==fits[0]['text'] else 780)):
    assert app.distinct_narration_plan([], 'topic',lang,duration,duration,seen,1)==(fits,duration-1.5)
 # Recorded native UK timings: character-only calibration misses number-rich text.
 # Predict two held-out complete recordings using only the first completed sample.
 calibration=(526,51025,35136)
 for characters,internal_ms,actual_ms in [(639,72530,46728),(610,58067,39984)]:
  with patch.object(app,'selected_voice_request',return_value={'input':{'text':'x'*characters}}),patch.object(app,'natural_char_rate',return_value=calibration[2]/calibration[0]),patch.object(app,'natural_internal_rate',return_value=calibration[2]/calibration[1]),patch.object(app,'measured_sentence_ms',return_value=internal_ms):
   predicted=app.natural_duration_ms('source sentence','uk')
  assert abs(predicted-actual_ms)/actual_ms<.025,(predicted,actual_ms)
 # A biography's academic field cannot select arbitrary museums bearing that field's name.
 field_sentence='The mother began anthropology field work.'
 field_parser=storyboard.ArticleLinks();field_parser.feed('<p>The mother began <a href="/wiki/Anthropology">anthropology</a> field work.</p>')
 field_entity={'id':'Q23404','name':'anthropology','kind':'entity','description':'scientific study of humans, human behavior, and societies'}
 field_sources=[{'text':field_sentence,'url':'https://en.wikipedia.org/wiki/Example','entity_profile':{'kind':'human','id':'Q123'}}]
 with patch.object(storyboard,'source_links',return_value=field_parser.links),patch.object(storyboard,'resolve_links',return_value={'Anthropology':field_entity}):
  try:storyboard.build([{'text':'Introduction.','source_index':0},{'text':field_sentence,'source_sentence':field_sentence,'source_index':0}],field_sources,'en',app)
  except storyboard.SceneUnavailable:pass
  else:raise AssertionError('Abstract discipline selected as a physical scene subject')
 for description in ['scientific study of life','academic discipline','branch of science','social science']:
  assert storyboard.abstract_visual_subject({'description':description})
 for description in ['anthropology museum','scientific instrument used to study humans','university in Canada','city in Ukraine']:
  assert not storyboard.abstract_visual_subject({'description':description})
 # The complete genre vocabulary exceeds one encoder batch; tail negatives still veto.
 from visual_verifier import VisualVerifier
 verifier=VisualVerifier.__new__(VisualVerifier);genre_batches=[]
 def genre_scores(path,descriptions,use_cache=True):
  assert 0<len(descriptions)<=32
  genre_batches.append(descriptions)
  return [.9 if 'painting, woodcut' in text else .8 if 'casting votes' in text else .1 for text in descriptions]
 with patch.object(verifier,'compare',side_effect=genre_scores):
  assert not verifier.check_photograph('unused')['passed']
 assert len(genre_batches)==2 and any('painting, woodcut' in text for text in genre_batches[-1])
 def photo_scores(path,descriptions,use_cache=True):
  assert 0<len(descriptions)<=32
  return [.8 if 'casting votes' in text else .1 for text in descriptions]
 with patch.object(verifier,'compare',side_effect=photo_scores):
  assert verifier.check_photograph('unused')['passed']
 # Adding a sourced person description must not overflow the encoder batch.
 def person_scores(path,descriptions,use_cache=True):
  assert 0<len(descriptions)<=32
  return [.8 if text=='A photograph of a man.' else .1 for text in descriptions]
 with patch.object(verifier,'compare',side_effect=person_scores):
  human=verifier.check_person('unused',{'entity_id':'Q123','basis':'fixture'},'a public official')
  assert human['passed'] and len(human['descriptions'])>32
 assert app.safe_id('../unrelated') is None
 print('PASS: plural normalization, paragraph extraction, complete abbreviations, five shot layouts, homonym exclusion, owned UUID validation')

if __name__=='__main__':check()

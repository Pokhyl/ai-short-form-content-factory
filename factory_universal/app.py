#!/usr/bin/env python3
import base64, hashlib, hmac, json, os, re, shutil, sqlite3, subprocess, time, urllib.parse, urllib.request, uuid, wave
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

DATA=Path('/data'); ROOT=DATA/'factory-universal'; DB=ROOT/'jobs.sqlite3'
RENDER=DATA/'renders'; VISUAL=DATA/'visuals'; VOICE=DATA/'voiceovers'
SETTINGS=json.load(open(os.getenv('FACTORY_SETTINGS','/run/secrets/settings.json')))
PROVIDERS=json.load(open(os.getenv('VISUAL_CREDENTIALS','/run/secrets/visual-providers.json')))
PROJECT=json.load(open(os.getenv('PROJECT_SETTINGS','/run/secrets/n8n-project-settings.json')))
BASE_PATH=urllib.parse.urlparse(PROJECT.get('STUDIO_PUBLIC_ORIGIN','')).path.rstrip('/')
WORKER=os.getenv('MEDIA_WORKER_URL','http://shorts-v2-media-worker-1:3001').rstrip('/')
LANGS={'en':'en','pl':'pl','ru':'ru','uk':'uk'}; DURATIONS={15,30,45,60}
STOP=set('the and for with from that this are was were have has into its which their about when where what how why over under after before through between each more most some than then they them these those there here because while also such many much very just often can could will would been being who whose your you our not but all one two three first second new used made make use using known called include including during according part parts people роки років який яка яке які цей ця це ці того для про при після перед між через також може має було були його її їх свої свій вони він все усі більш менш дуже інші один одна одно дві два три что это как для при после перед между через также может имеет было его ее их свои он она все более менее очень другие אחד'.split())
ROOT.mkdir(parents=True,exist_ok=True)
POOL=ThreadPoolExecutor(max_workers=1)

def now(): return datetime.now(timezone.utc).isoformat()
def connect():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row
 c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=20000')
 return c
def init_db():
 with connect() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS jobs(\n   id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,\n   topic TEXT NOT NULL, language TEXT NOT NULL, duration_s INTEGER NOT NULL,\n   status TEXT NOT NULL, stage TEXT NOT NULL, progress INTEGER NOT NULL,\n   message TEXT NOT NULL, error TEXT, manifest TEXT,\n   review_status TEXT NOT NULL DEFAULT 'pending', review_note TEXT)""")
  c.execute("UPDATE jobs SET status='failed',stage='interrupted',message='Process restarted before completion',error='interrupted' WHERE status IN ('queued','running')")
def update(jid,**fields):
 fields['updated_at']=now()
 with connect() as c:c.execute('UPDATE jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),jid))
def get_job(jid):
 with connect() as c:r=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
 if not r:return None
 d=dict(r);d['manifest']=json.loads(d['manifest']) if d['manifest'] else None;return d
def public_job(j):
 if not j:return None
 return {k:j[k] for k in ('id','created_at','updated_at','topic','language','duration_s','status','stage','progress','message','error','review_status','review_note')}|{'manifest':j['manifest']}
def safe_id(x):
 try:return str(uuid.UUID(x))
 except Exception:return None
def tokens(s):
 out=[]
 for x in re.findall(r'[^\W_]+',s or '',re.UNICODE):
  x=x.lower()
  if len(x)<=2 or x in STOP:continue
  if x.isascii() and x.isalpha():
   if len(x)>4 and x.endswith('ies'):x=x[:-3]+'y'
   elif len(x)>4 and x.endswith(('ches','shes','xes','zes')):x=x[:-2]
   elif len(x)>4 and x.endswith('s') and not x.endswith(('ss','us','is')):x=x[:-1]
  out.append(x)
 return out
def topic_terms(text,lang):
  stop={
   'pl':set('jak sie się jest są oraz dla który która które tych tego lub w na od do z ze o po przy przez jakimi jakie ich może nie aby że ten ta to jest bylo było ich'.split()),
   'ru':set('как это для что где когда который которая которые этот эта эти из в во на по с со от при между после перед как не и а или чтобы'.split()),
   'uk':set('як це для що де коли який яка яке які цей ця ці із зі з в у на по при між після перед не і та або щоб'.split())
  }
  actions={
   'pl':r'^(rob\w*|zrob\w*|wytwarz\w*|produk\w*|powst\w*|tworz\w*|proces\w*|wykon\w*)$',
   'ru':r'^(дел\w*|сдел\w*|изготов\w*|производ\w*|созда\w*|получ\w*|процесс\w*)$',
   'uk':r'^(роб\w*|зроб\w*|виготов\w*|виробля\w*|створ\w*|отрим\w*|процес\w*)$'
  }
  if lang=='en':return [x for x in tokens(text) if x not in {'make','made','manufacture','manufacturing','produce','production','process','how'}]
  suffixes={
   'pl':('owego','owej','owym','owych','ami','ach','ania','enie','owa','owe','owy','owi','ów','om','em','ie','ki','ka','ek','y','i','a','e','u'),
   'ru':('иями','ями','ами','ого','ему','ому','ыми','ими','ая','яя','ое','ее','ые','ие','ых','их','ой','ый','ий','ую','юю','ам','ям','ах','ях','ов','ев','а','я','ы','и','е','о','у','ю'),
   'uk':('ями','ами','ого','ому','ими','ими','ими','ая','яя','еє','іє','их','ій','ий','ою','єю','ам','ям','ах','ях','ів','ев','а','я','и','і','е','о','у','ю')
  }
  out=[]
  for word in re.findall(r'[^\W_]+',(text or '').lower(),re.UNICODE):
   if word in STOP or word in stop.get(lang,set()) or re.fullmatch(actions.get(lang,r'(?!)'),word):continue
   for suffix in suffixes.get(lang,()):
    if len(word)-len(suffix)>=4 and word.endswith(suffix):word=word[:-len(suffix)];break
   if len(word)>2:out.append(word)
  return out

def process_signal(text,lang):
  patterns={
   'en':r'\b(melt\w*|form\w*|blow\w*|anneal\w*|cool\w*|inspect\w*|furnace\w*|batch|gob|press\w*|feed\w*)\b',
   'pl':r'(top\w*|form\w*|wydmuch\w*|chłodz\w*|chlodz\w*|wyżarz\w*|wyzarz\w*|inspekc\w*|piec\w*|wsad\w*|kropl\w*)',
   'ru':r'(плав\w*|форм\w*|выдув\w*|охлажд\w*|отжиг\w*|провер\w*|печ\w*|смес\w*|капл\w*)',
   'uk':r'(плав\w*|форм\w*|видув\w*|охолодж\w*|відпал\w*|перевір\w*|печ\w*|шихт\w*|крап\w*)'
  }
  return len(re.findall(patterns.get(lang,patterns['en']),text or '',re.I|re.UNICODE))
def http_json(url,headers=None,timeout=20):
 h={'User-Agent':'UniversalShortFactory/1.0','Accept':'application/json'};h.update(headers or {})
 with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=timeout) as r:return json.loads(r.read(8_000_000).decode('utf-8'))
class WikiHTML(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 SKIP_TAGS={'script','style','table','figure','gallery','sup'}
 SKIP_CLASSES={'mw-editsection','reference','navbox','metadata','mw-references-wrap','toc','sidebar','hatnote','ambox','vertical-navbox','reflist'}
 SKIP_SECTIONS={
  'en':{'references','notes','see also','further reading','external links','bibliography','works cited','sources'},
  'pl':{'przypisy','bibliografia','zobacz też','zobacz takze','dalsza lektura','linki zewnętrzne','źródła'},
  'ru':{'примечания','источники','литература','см. также','ссылки','внешние ссылки'},
  'uk':{'примітки','джерела','література','див. також','посилання','зовнішні посилання'}
 }
 def __init__(self,lang='en'):
  super().__init__(convert_charrefs=True);self.lang=lang;self.skip=0;self.skip_section=False;self.heading=None;self.heading_text=[];self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag in {'h2','h3'}:
   if tag=='h2' and self.skip_section:self.skip_section=False
   self.heading=tag;self.heading_text=[];return
  if self.heading or self.skip_section:return
  if self.skip:
   if tag not in self.VOID:self.skip+=1
   return
  classes=set(dict(attrs).get('class','').split())
  if tag in self.SKIP_TAGS or classes&self.SKIP_CLASSES:
   if tag not in self.VOID:self.skip=1
   return
  if tag in {'p','h4','li','br'}:self.parts.append('\n')
 def handle_endtag(self,tag):
  if self.heading:
   if tag==self.heading:
    name=re.sub(r'\s+',' ',' '.join(self.heading_text)).strip().lower();skip=self.SKIP_SECTIONS.get(self.lang,set())
    if tag=='h2' and name in skip:self.skip_section=True
     # Headings label structure but are not narration.
    self.heading=None;self.heading_text=[]
   return
  if self.skip_section:return
  if self.skip:
   if tag not in self.VOID:self.skip-=1
   return
  if tag in {'p','h4','li'}:self.parts.append('\n')
  elif tag in {'a','b','strong','i','em','span'}:self.parts.append(' ')
 def handle_data(self,data):
  if self.heading:self.heading_text.append(data)
  elif not self.skip and not self.skip_section:self.parts.append(data)
 def text(self):
  raw=''.join(self.parts)
  raw=re.sub(r'[\t\f\v ]+',' ',raw)
  raw=re.sub(r' *\n+ *','\n',raw)
  return raw.strip()

def cache_fetch(key,fetch):
 cache=ROOT/'cache';cache.mkdir(exist_ok=True);path=cache/(hashlib.sha256(key.encode()).hexdigest()+'.json')
 try:
  if time.time()-path.stat().st_mtime<86400:return json.loads(path.read_text())
 except (OSError,ValueError):pass
 data=fetch();path.write_text(json.dumps(data,ensure_ascii=False));return data
def wikipedia(topic,lang):
  queries=[(topic,6)]
  made=bool(re.search(r'\b(make|made|manufactur\w*|produc\w*|fabricat\w*|build|create|zrobi\w*|produk\w*|wytwarz\w*|изготов\w*|производ\w*|виробля\w*|виготов\w*)\b',topic,re.I))
  core=list(dict.fromkeys(topic_terms(topic,lang)))
  suffix={'en':'manufacturing process','pl':'proces produkcji','ru':'процесс производства','uk':'процес виробництва'}
  stage={'en':'furnace forming annealing machine','pl':'piec formowanie wyzarzanie maszyna','ru':'печь формование отжиг машина','uk':'піч формування відпал машина'}
  if made and core:
   queries.insert(0,(' '.join(core)+' '+suffix[lang],8));queries.append((' '.join(core)+' '+stage[lang],8))
  hits=[];seen=set()
  for query,limit in queries:
   q=urllib.parse.urlencode({'action':'query','list':'search','srsearch':query,'srlimit':str(limit),'srnamespace':'0','format':'json','formatversion':'2'})
   data=http_json('https://'+lang+'.wikipedia.org/w/api.php?'+q,timeout=22)
   for hit in (data.get('query') or {}).get('search') or []:
    title=str(hit.get('title') or '').strip();key=str(hit.get('pageid') or title)
    if title and key not in seen:seen.add(key);hits.append(title)
  core_set=set(core);method_terms=set(topic_terms({'en':'furnace forming annealing glassblowing container glass production line','pl':'piec formowanie wyzarzanie szklo pojemnik linia produkcyjna','ru':'печь формование отжиг стекло тара производственная линия','uk':'піч формування відпал скло тара виробнича лінія'}[lang],lang))
  hits=[title for title in hits if (set(topic_terms(title,lang))&core_set) or (made and bool(set(topic_terms(title,lang))&method_terms))]
  if made and len(core_set)>1:
   hits=[title for title in hits if core_set<=set(topic_terms(title,lang)) or bool((set(topic_terms(title,lang))-core_set)&method_terms)]
  hits=sorted(hits,key=lambda title:(-len(set(topic_terms(title,lang))&core_set),hits.index(title)))
  out=[]
  for title in hits[:10]:
   try:
    q=urllib.parse.urlencode({'action':'parse','page':title,'prop':'text','disableeditsection':'1','disablelimitreport':'1','format':'json'})
    parsed=http_json('https://'+lang+'.wikipedia.org/w/api.php?'+q,timeout=22).get('parse') or {}
    actual=str(parsed.get('title') or title).strip();html=((parsed.get('text') or {}).get('*') or '')
    parser=WikiHTML(lang);parser.feed(html);text=parser.text()
    if actual and len(text)>220 and 'may refer to:' not in text[:600].lower():out.append({'title':actual,'url':'https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(actual.replace(' ','_')),'text':text})
   except Exception:continue
  return out
def source_slots(sources,topic,count,lang='en'):
  object_terms=set(topic_terms(topic,lang))
  process_intent=bool(re.search(r'\b(make|made|manufactur\w*|produc\w*|fabricat\w*|build|create|zrobi\w*|produk\w*|wytwarz\w*|изготов\w*|производ\w*|виробля\w*|виготов\w*)\b',topic,re.I))
  bottle_words=set(topic_terms('bottle bottles бутылка пляшка пляшки butelka butelki',lang))
  container_words=set(topic_terms('container containers packaging jar pojemnik pojemniki opakowanie тара контейнер контейнери',lang))
  rows=[]
  for si,src in enumerate(sources):
   title_terms=set(topic_terms(src['title'],lang))
   for paragraph in src['text'].splitlines():
    for sentence in re.split(r'(?<=[.!?])\s+',paragraph.strip()):
     sentence=re.sub(r'\[[^\]]{1,24}\]','',sentence).strip();words=sentence.split()
     if not sentence.endswith(('.', '!', '?')) or not 9<=len(words)<=18:continue
     sentence_terms=set(topic_terms(sentence,lang));combined=sentence_terms|title_terms
     topic_hits=len(combined&object_terms);needed=min(2,len(object_terms))
     if object_terms&bottle_words and combined&container_words:topic_hits=max(topic_hits,min(2,len(object_terms)))
     direct_topic=bool(sentence_terms&object_terms);process_overlap=process_signal(sentence,lang)
     if needed and topic_hits<needed:continue
     if process_intent and (not process_overlap or not direct_topic):continue
     score=topic_hits*4+len(sentence_terms&object_terms)*3+process_overlap*2+min(len(words),15)/15
     rows.append((score,si,sentence,words))
  rows.sort(key=lambda x:(-x[0],x[1],abs(len(x[3])-13)))
  chosen=[];seen=set();used=set();source_counts={}
  while rows and len(chosen)<count:
   best_i=max(range(len(rows)),key=lambda i:rows[i][0]+.3*len(set(topic_terms(rows[i][2],lang))-used)+2/(1+source_counts.get(rows[i][1],0)))
   score,si,sentence,words=rows.pop(best_i);norm=re.sub(r'\W+','',sentence.lower())
   if norm in seen:continue
   seen.add(norm);chosen.append({'text':sentence,'source_index':si,'source_sentence':sentence,'score':score})
   used.update(topic_terms(sentence,lang));source_counts[si]=source_counts.get(si,0)+1
  if len(chosen)!=count:return []
  return sorted(chosen,key=lambda x:(x['source_index'],sources[x['source_index']]['text'].find(x['source_sentence'])))
def photo_search(topic,lang):
 found=[];errors=[];pex=(PROVIDERS.get('Pexels API') or {}).get('value','').strip();pix=(PROVIDERS.get('Pixabay API') or {}).get('value','').strip()
 if pex:
  try:
   locale={'en':'en-US','pl':'pl-PL','ru':'ru-RU','uk':'uk-UA'}[lang];q=urllib.parse.urlencode({'query':topic,'per_page':80,'orientation':'portrait','locale':locale})
   data=cache_fetch('pexels|'+lang+'|'+topic,lambda:http_json('https://api.pexels.com/v1/search?'+q,{'Authorization':pex},25))
   for x in data.get('photos') or []:
    src=x.get('src') or {};url=src.get('portrait') or src.get('large') or src.get('original')
    if url:found.append({'provider':'pexels','id':str(x.get('id')),'alt':x.get('alt') or '','url':url,'source_url':x.get('url') or '','creator':x.get('photographer') or '','creator_url':x.get('photographer_url') or '','width':int(x.get('width') or 0),'height':int(x.get('height') or 0)})
  except Exception as e:errors.append('Pexels unavailable (HTTP '+str(getattr(e,'code','request error'))+')')
 if pix:
  try:
   q=urllib.parse.urlencode({'key':pix,'q':topic,'lang':lang if lang in {'en','pl','ru'} else 'en','image_type':'photo','orientation':'vertical','safesearch':'true','per_page':200})
   data=cache_fetch('pixabay|'+lang+'|'+topic,lambda:http_json('https://pixabay.com/api/?'+q,timeout=25))
   for x in data.get('hits') or []:
    url=x.get('largeImageURL') or x.get('webformatURL')
    if url:found.append({'provider':'pixabay','id':str(x.get('id')),'alt':x.get('tags') or '','url':url,'source_url':x.get('pageURL') or '','creator':x.get('user') or '','creator_url':'https://pixabay.com/users/'+urllib.parse.quote(str(x.get('user') or ''))+'/','width':int(x.get('imageWidth') or x.get('webformatWidth') or 0),'height':int(x.get('imageHeight') or x.get('webformatHeight') or 0)})
  except Exception as e:errors.append('Pixabay unavailable (HTTP '+str(getattr(e,'code','request error'))+')')
 unique={}
 for x in found:
  key=(x['provider'],x['id'])
  if key not in unique and x['width']>=640 and x['height']>=640:unique[key]=x
 if not unique:raise ValueError('; '.join(errors) if errors else 'photo search returned no usable results')
 return list(unique.values())
def dhash(im):
 im=ImageOps.grayscale(im).resize((9,8));p=list(im.getdata());n=0
 for y in range(8):
  for x in range(8):n=(n<<1)|(1 if p[y*9+x]>p[y*9+x+1] else 0)
 return n
def photo_score(p,slot,topic):
 terms=set(tokens(topic+' '+slot['text']));meta=set(tokens(p['alt']+' '+p['creator']))
 return 2*len(terms&meta)+.8*len(set(tokens(topic))&meta)+(.5 if p['height']>=p['width'] else 0)
def font(size,bold=False):
 paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
 for p in paths:
  try:return ImageFont.truetype(p,size)
  except OSError:pass
 return ImageFont.load_default()
def wrap(text):
 lines=[];cur=''
 for word in text.split():
  if cur and len(cur)+len(word)+1>29:lines.append(cur);cur=word
  else:cur=(cur+' '+word).strip()
 if cur:lines.append(cur)
 return lines[:4] if len(lines)<=4 else lines[:3]+[' '.join(lines[3:])[:27]+'…']
def make_card(raw,caption,dest):
 with Image.open(raw) as src:
  im=ImageOps.exif_transpose(src).convert('RGB')
  if min(im.size)<320:raise ValueError('photo resolution too small')
  bg=ImageOps.fit(im,(1080,1920),method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
  bg=Image.blend(bg,Image.new('RGB',bg.size,(7,13,23)),.48)
  fg=ImageOps.contain(im,(1040,1420),method=Image.Resampling.LANCZOS)
  bg.paste(fg,((1080-fg.width)//2,95+(1420-fg.height)//2))
  layer=Image.new('RGBA',(1080,1920),(0,0,0,0));d=ImageDraw.Draw(layer)
  d.rounded_rectangle((42,1510,1038,1880),radius=38,fill=(7,13,23,224),outline=(255,255,255,50),width=2)
  d.text((82,1540),'SOURCE-GROUNDED',font=font(25,True),fill=(120,205,255,255))
  y=1600
  for line in wrap(caption):d.text((82,y),line,font=font(40,True),fill='white');y+=54
  Image.alpha_composite(bg.convert('RGBA'),layer).convert('RGB').save(dest,'JPEG',quality=88,optimize=True)
def download_photo(c,dest):
 host=(urllib.parse.urlparse(c['url']).hostname or '').lower()
 if urllib.parse.urlparse(c['url']).scheme!='https' or not(host=='images.pexels.com' or host.endswith('.pixabay.com')):raise ValueError('photo host not allowed')
 with urllib.request.urlopen(urllib.request.Request(c['url'],headers={'User-Agent':'UniversalShortFactory/1.0'}),timeout=25) as r:
  data=r.read(20_000_001);ct=r.headers.get('Content-Type','').split(';')[0].lower()
 if len(data)>20_000_000 or ct not in {'image/jpeg','image/png','image/webp'}:raise ValueError('photo payload invalid')
 Path(dest).write_bytes(data)
 with Image.open(dest) as im:im.verify()
def write_audio(slots,lang,jid,duration):
 voice={'en':'en-us','pl':'pl','ru':'ru','uk':'uk'}[lang];tmp=ROOT/'tmp'/jid;tmp.mkdir(parents=True,exist_ok=True)
 slot_ms=duration*1000//len(slots);targets=[slot_ms]*(len(slots)-1)+[duration*1000-slot_ms*(len(slots)-1)]
 wavs=[];speech=[]
 for i,slot in enumerate(slots):
  path=tmp/('line-%02d.wav'%i);words=max(1,len(slot['text'].split()))
  speed=max(105,min(220,round(60*words/((targets[i]-35)/1000))))
  used=None
  for _ in range(12):
   subprocess.run(['espeak-ng','-v',voice,'-s',str(speed),'-w',str(path),'--',slot['text']],check=True,capture_output=True,timeout=20)
   with wave.open(str(path),'rb') as f:used=round(f.getnframes()*1000/f.getframerate())
   if used<=targets[i]-15:break
   speed=min(280,speed+15)
  if used is None or used>targets[i]:raise ValueError('spoken sentence does not fit its five-second narration beat')
  wavs.append(path);speech.append(used)
 joined=tmp/'joined.wav'
 with wave.open(str(wavs[0]),'rb') as f:params=f.getparams()
 with wave.open(str(joined),'wb') as out:
  out.setparams(params);silence=b'\0'*(params.nchannels*params.sampwidth)
  for i,path in enumerate(wavs):
   with wave.open(str(path),'rb') as f:
    if f.getparams()[:3]!=params[:3]:raise ValueError('voice sample format changed')
    frames=f.readframes(f.getnframes())
   sample_frames=len(frames)//(params.nchannels*params.sampwidth);target_frames=round(targets[i]*params.framerate/1000)
   if sample_frames>target_frames:raise ValueError('narration exceeded its visual slot by '+str(round((sample_frames-target_frames)*1000/params.framerate))+' ms')
   out.writeframes(frames);out.writeframes(silence*(target_frames-sample_frames))
 mp3=VOICE/jid/'final.mp3';mp3.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(joined),'-codec:a','libmp3lame','-q:a','3',str(mp3)],check=True,capture_output=True,timeout=45)
 p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(mp3)],check=True,capture_output=True,text=True,timeout=10)
 return mp3,round(float(p.stdout.strip())*1000),speech,targets
def post_render(jid,payload):
 req=urllib.request.Request(WORKER+'/renders/'+jid,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=240) as r:return json.loads(r.read().decode())
def scrub_error(e):
 if hasattr(e,'code'):return 'provider returned HTTP '+str(e.code)
 s=str(e)
 for group in PROVIDERS.values():
  if isinstance(group,dict):
   for v in group.values():
    if isinstance(v,str) and len(v)>6:s=s.replace(v,'[redacted]')
 return s[:500]
def run_job(jid):
 j=get_job(jid);topic=j['topic'];lang=j['language'];duration=j['duration_s'];visual_count=duration*2//5;beat_count=duration//5
 try:
  update(jid,status='running',stage='research',progress=5,message='Finding cited facts in the selected language')
  sources=wikipedia(topic,lang)
  if len(sources)<2:raise ValueError('fewer than two usable source articles; try a more specific topic or another language')
  slots=source_slots(sources,topic,beat_count,lang)
  if len(slots)!=beat_count:raise ValueError('not enough complete, topic-grounded sentences for '+str(beat_count)+' narration beats')
  update(jid,stage='visuals',progress=20,message='Searching a bounded photo pool; requiring unique relevant assets')
  candidates=photo_search(topic,lang)
  if len(candidates)<visual_count:raise ValueError('photo search found '+str(len(candidates))+' distinct candidates; '+str(visual_count)+' are required')
  topic_terms=set(tokens(topic));selected=[];used_ids=set();hashes=[];visual_rows=[]
  for i in range(visual_count):
   slot=slots[i//2]
   ranked=sorted(candidates,key=lambda p:(photo_score(p,slot,topic),hashlib.sha1((jid+p['provider']+p['id']).encode()).hexdigest()),reverse=True)
   found=None
   for p in ranked:
    key=(p['provider'],p['id'])
    if key in used_ids:continue
    meta=set(tokens(p['alt']))
    if topic_terms and meta and not topic_terms&meta:continue
    shot=str(uuid.uuid4());folder=VISUAL/jid/shot;folder.mkdir(parents=True,exist_ok=False)
    raw=folder/'source.download';final=folder/'selected.jpg'
    try:
     download_photo(p,raw)
     with Image.open(raw) as im:ph=dhash(im.convert('RGB'))
     if any((ph^old).bit_count()<=4 for old in hashes):raw.unlink(missing_ok=True);shutil.rmtree(folder);continue
     make_card(raw,slot['text'],final);raw.unlink(missing_ok=True)
    except Exception:shutil.rmtree(folder,ignore_errors=True);continue
    row=dict(p);row.update({'caption':slot['text'],'article_title':sources[slot['source_index']]['title'],'article_url':sources[slot['source_index']]['url'],'asset_sha256':hashlib.sha256(final.read_bytes()).hexdigest()})
    found={'provider':p,'shot':shot,'path':final,'hash':row['asset_sha256'],'phash':ph,'row':row};break
   if found is None:raise ValueError('no distinct topic-matched photo for visual '+str(i+1)+'; repeats are disabled')
   hashes.append(found['phash']);used_ids.add((found['provider']['provider'],found['provider']['id']));selected.append(found);visual_rows.append(found['row'])
   update(jid,progress=20+int((i+1)*25/visual_count),message='Prepared '+str(i+1)+' of '+str(visual_count)+' unique photos')
  update(jid,stage='voice',progress=50,message='Creating narration locally; no text-generation API')
  mp3,audio_ms,speech_ms,slot_targets=write_audio(slots,lang,jid,duration)
  lo={15:14208,30:28464,45:42864,60:58176}[duration];hi={15:15768,30:34000,45:46128,60:61656}[duration]
  if not lo<=audio_ms<=hi:raise ValueError('measured voice is outside the accepted '+str(duration)+' second window')
  audio_sha=hashlib.sha256(mp3.read_bytes()).hexdigest();target=max(duration*1000,audio_ms);step=target//visual_count;beat_step=target//beat_count;cursor=0;scenes=[]
  for i,item in enumerate(selected):
   end=target if i==visual_count-1 else cursor+step;beat=i//2;beat_start=beat*beat_step;spoken_end=min(target,beat_start+speech_ms[beat]);speech_start=max(cursor,beat_start);speech_end=min(end,spoken_end,audio_ms)
   if speech_end<=speech_start:speech_start=cursor;speech_end=min(end,cursor+1)
   scenes.append({'scene_uuid':str(uuid.uuid4()),'shot_uuid':item['shot'],'visual_asset_id':str(uuid.uuid4()),'media_type':'photo','asset_sha256':item['hash'],'asset_path':str(item['path']),'asset_width':1080,'asset_height':1920,'scene_order':i+1,'segment_start_ms':cursor,'segment_end_ms':end,'speech_start_ms':speech_start,'speech_end_ms':speech_end})
   cursor=end
  update(jid,stage='render',progress=80,message='Rendering 1080×1920 MP4 and decoding the complete file')
  rendered=post_render(jid,{'input_audio_sha256':audio_sha,'audio_duration_ms':audio_ms,'target_duration_ms':target,'requested_duration_ms':duration*1000,'scenes':scenes})
  video=Path(rendered['storage_path'])
  full=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=150)
  if full.returncode:raise ValueError('full MP4 decode failed')
  if not rendered.get('qa_passed'):raise ValueError('media-worker render QA failed')
  manifest={'version':'universal-1','job_id':jid,'topic':topic,'language':lang,'requested_duration_s':duration,'created_at':now(),'script':' '.join(x['text'] for x in slots),'script_mode':'source-grounded extractive','llm_calls':0,'sources':[{'title':x['title'],'url':x['url']} for x in sources],'beats':[{'order':i+1,'caption':s['text'],'source_span':s['source_sentence'],'source_title':sources[s['source_index']]['title'],'source_url':sources[s['source_index']]['url']} for i,s in enumerate(slots)],'visuals':[{'order':i+1,'provider':x['provider'],'provider_id':x['id'],'alt':x['alt'],'creator':x['creator'],'creator_url':x['creator_url'],'provider_page':x['source_url'],'search_query':topic,'caption':x['caption'],'source_article':x['article_url'],'source_title':x['article_title'],'asset_sha256':x['asset_sha256']} for i,x in enumerate(visual_rows)],'narration':{'engine':'eSpeak NG local','voice':{'en':'en-us','pl':'pl','ru':'ru','uk':'uk'}[lang],'audio_duration_ms':audio_ms,'sha256':audio_sha},'render':rendered,'audit':{'shots_required':visual_count,'narration_beats':beat_count,'unique_assets':len({x['asset_sha256'] for x in visual_rows}),'two_unique_photos_per_five_seconds':len(visual_rows)==visual_count,'source_count':len(sources),'all_visuals_have_provenance':all(x['source_url'] and x['article_url'] for x in visual_rows),'full_decode':True,'renderer_gates':rendered.get('qa_gates',{})},'retention_days':30}
  (RENDER/jid/'universal-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
  shutil.rmtree(VISUAL/jid,ignore_errors=True);shutil.rmtree(VOICE/jid,ignore_errors=True);shutil.rmtree(ROOT/'tmp'/jid,ignore_errors=True)
  update(jid,status='ready',stage='review',progress=100,message='MP4 ready for review',manifest=json.dumps(manifest,ensure_ascii=False),error=None)
 except Exception as e:
  for p in (VISUAL/jid,VOICE/jid,ROOT/'tmp'/jid):shutil.rmtree(p,ignore_errors=True)
  stage=(get_job(jid) or {}).get('stage','unknown')
  update(jid,status='failed',stage='failed',progress=100,message='Stopped at '+stage,error=scrub_error(e))
def cleanup():
 cutoff=time.time()-30*86400
 with connect() as c:rows=c.execute("SELECT id FROM jobs WHERE status='ready'").fetchall()
 for r in rows:
  p=RENDER/r['id']
  try:
   if p.exists() and p.stat().st_mtime<cutoff:shutil.rmtree(p);update(r['id'],status='expired',stage='expired',progress=100,message='MP4 expired after 30 days')
  except OSError:pass
 cache=ROOT/'cache'
 if cache.exists():
  for p in cache.glob('*.json'):
   try:
    if time.time()-p.stat().st_mtime>86400:p.unlink()
   except OSError:pass
  files=list(cache.glob('*.json'));total=sum(p.stat().st_size for p in files if p.exists())
  for p in sorted(files,key=lambda x:x.stat().st_mtime):
   if total<=512*1024*1024:break
   try:total-=p.stat().st_size;p.unlink()
   except OSError:pass
HTML=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Universal Video Factory</title><style>:root{color-scheme:dark;font:16px system-ui;background:#0b1020;color:#edf2ff}body{margin:0 auto;max-width:1100px;padding:32px 20px}h1{font-size:32px;margin:0}p{color:#aab6d3}form,.job{background:#141c31;border:1px solid #2b3858;border-radius:16px;padding:20px;margin:22px 0}form{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:end}label{display:grid;gap:6px;color:#bdc9e5}input,select,button{font:inherit;border-radius:9px;padding:12px;border:1px solid #3b4b70;background:#0b1020;color:#fff}button{cursor:pointer;background:#4b72ea;border:0;font-weight:700}button.secondary{background:#26344f}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.job h2{font-size:19px}.job video{width:100%;max-height:680px;background:#05070c}.bar{height:8px;background:#283653;border-radius:5px;overflow:hidden}.bar span{display:block;height:8px;background:#79a6ff}.sources a{color:#90b5ff}.error{color:#ff9e9e}.pill{display:inline-block;border-radius:99px;background:#283653;padding:4px 9px;font-size:12px}@media(max-width:760px){form,.grid{grid-template-columns:1fr}}</style><body><h1>Universal Video Factory</h1><p>Topic → cited script → unique photos → local voice → vertical MP4. No Gemini. Two distinct photos every five seconds.</p><form id="new"><label>Topic<input name="topic" minlength="3" maxlength="180" required placeholder="How glass bottles are made"></label><label>Language<select name="language"><option value="en">English</option><option value="pl">Polski</option><option value="ru">Русский</option><option value="uk">Українська</option></select></label><label>Length<select name="duration_s"><option>15</option><option>30</option><option>45</option><option>60</option></select></label><button>Create MP4</button></form><div id="status"></div><div id="jobs" class="grid"></div><script>
var base=location.pathname.replace(/\/$/,'');if(base==='/')base='';function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}function api(p,o){return fetch(base+p,o||{}).then(function(r){return r.json().then(function(x){if(!r.ok)throw Error(x.error||r.status);return x})})}function draw(){api('/api/jobs').then(function(d){document.getElementById('jobs').innerHTML=(d.jobs||[]).map(function(j){var m=j.manifest||{};var video=j.status==='ready'?'<video controls preload="metadata" src="'+base+'/api/jobs/'+j.id+'/video"></video><p><a href="'+base+'/api/jobs/'+j.id+'/manifest">Manifest and media audit</a></p>':'';var script=m.script?'<details><summary>Script and cited sources</summary><p>'+esc(m.script)+'</p><div class="sources">'+(m.sources||[]).map(function(s){return '<p><a target="_blank" rel="noreferrer" href="'+esc(s.url)+'">'+esc(s.title)+'</a></p>'}).join('')+'</div></details>':'';var err=j.error?'<p class="error">'+esc(j.error)+'</p>':'';var review=j.status==='ready'?'<p><span class="pill">Review: '+esc(j.review_status)+'</span> <button class="secondary" onclick="reviewJob(\''+j.id+'\',\'approved\')">Approve</button> <button class="secondary" onclick="reviewJob(\''+j.id+'\',\'changes_requested\')">Request changes</button></p>':'';return '<article class="job"><h2>'+esc(j.topic)+' · '+j.duration_s+'s · '+esc(j.language)+'</h2><p>'+esc(j.stage)+' — '+esc(j.message)+'</p><div class="bar"><span style="width:'+j.progress+'%"></span></div>'+err+video+script+review+'</article>'}).join('')||'<p>No videos yet.</p>'}).catch(function(e){document.getElementById('status').textContent=e.message})}function reviewJob(id,state){api('/api/jobs/'+id+'/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:state})}).then(draw).catch(function(e){alert(e.message)})}document.getElementById('new').addEventListener('submit',function(e){e.preventDefault();var f=new FormData(e.target);api('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:f.get('topic'),language:f.get('language'),duration_s:Number(f.get('duration_s'))})}).then(function(){e.target.reset();draw()}).catch(function(x){document.getElementById('status').textContent=x.message})});draw();setInterval(draw,4000);
</script></body></html>'''
class Handler(BaseHTTPRequestHandler):
 def auth(self):
  expected=base64.b64encode((PROJECT.get('STUDIO_AUTH_USERNAME','')+':'+PROJECT.get('STUDIO_AUTH_PASSWORD','')).encode()).decode()
  if hmac.compare_digest(self.headers.get('Authorization',''),'Basic '+expected):return True
  self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="Universal Video Factory"');self.send_header('Content-Length','0');self.end_headers();return False
 def route(self):
  p=urllib.parse.urlsplit(self.path).path
  return (p[len(BASE_PATH):] or '/') if BASE_PATH and p.startswith(BASE_PATH) else p
 def json_out(self,status,obj):
  b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n<=0 or n>32768:raise ValueError('invalid request size')
  x=json.loads(self.rfile.read(n))
  if not isinstance(x,dict):raise ValueError('JSON object required')
  return x
 def do_GET(self):
  if self.route()=='/healthz':return self.json_out(200,{'status':'ok','service':'factory-universal','llm_calls':0})
  if not self.auth():return
  p=self.route()
  if p in ('/','/index.html'):
   b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  if p=='/api/jobs':
   with connect() as c:rows=c.execute('SELECT id FROM jobs ORDER BY created_at DESC LIMIT 50').fetchall()
   return self.json_out(200,{'jobs':[public_job(get_job(x['id'])) for x in rows]})
  m=re.fullmatch(r'/api/jobs/([0-9a-fA-F-]{36})(?:/(video|manifest))?',p)
  if m:
   jid=safe_id(m.group(1));j=get_job(jid) if jid else None
   if not j:return self.json_out(404,{'error':'job_not_found'})
   if m.group(2)=='video':
    f=RENDER/jid/'final.mp4'
    if not f.is_file():return self.json_out(404,{'error':'video_not_found'})
    size=f.stat().st_size;rg=self.headers.get('Range','');start=0;end=size-1;status=200
    if rg.startswith('bytes='):
     try:
      a,b=rg[6:].split('-',1);start=int(a or 0);end=min(int(b),size-1) if b else size-1
      if start<0 or start>=size or end<start:raise ValueError()
      status=206
     except Exception:self.send_response(416);self.send_header('Content-Range','bytes */'+str(size));self.end_headers();return
    self.send_response(status);self.send_header('Content-Type','video/mp4');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1));self.send_header('Content-Disposition','inline; filename="'+jid+'.mp4"')
    if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    self.end_headers()
    with f.open('rb') as src:
     src.seek(start);remaining=end-start+1
     while remaining:
      b=src.read(min(1024*1024,remaining))
      if not b:break
      self.wfile.write(b);remaining-=len(b)
    return
   if m.group(2)=='manifest':
    f=RENDER/jid/'universal-manifest.json'
    if not f.is_file():return self.json_out(404,{'error':'manifest_not_found'})
    b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
   return self.json_out(200,public_job(j))
  return self.json_out(404,{'error':'not_found'})
 def do_POST(self):
  if not self.auth():return
  p=self.route()
  try:b=self.body()
  except Exception as e:return self.json_out(400,{'error':str(e)})
  if p=='/api/jobs':
   topic=re.sub(r'\s+',' ',str(b.get('topic') or '')).strip();lang=str(b.get('language') or '')
   try:duration=int(b.get('duration_s'))
   except Exception:duration=0
   if len(topic)<3 or len(topic)>180:return self.json_out(400,{'error':'topic must contain 3–180 characters'})
   if lang not in LANGS:return self.json_out(400,{'error':'language must be en, pl, ru or uk'})
   if duration not in DURATIONS:return self.json_out(400,{'error':'duration must be 15, 30, 45 or 60 seconds'})
   jid=str(uuid.uuid4());ts=now()
   with connect() as c:c.execute('INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message) VALUES(?,?,?,?,?,?,?,?,?,?)',(jid,ts,ts,topic,lang,duration,'queued','queued',0,'Waiting for the single worker'))
   cleanup();POOL.submit(run_job,jid);return self.json_out(202,{'id':jid,'status':'queued'})
  m=re.fullmatch(r'/api/jobs/([0-9a-fA-F-]{36})/review',p)
  if m:
   jid=safe_id(m.group(1));j=get_job(jid) if jid else None
   if not j:return self.json_out(404,{'error':'job_not_found'})
   state=str(b.get('status') or '')
   if state not in {'approved','changes_requested'}:return self.json_out(400,{'error':'review status must be approved or changes_requested'})
   update(jid,review_status=state,review_note=str(b.get('note') or '')[:500]);return self.json_out(200,{'ok':True})
  return self.json_out(404,{'error':'not_found'})
 def log_message(self,*args):return
init_db()
ThreadingHTTPServer(('0.0.0.0',3000),Handler).serve_forever()

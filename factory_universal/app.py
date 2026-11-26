#!/usr/bin/env python3
import base64, hashlib, threading, json, os, re, shutil, sqlite3, subprocess, time, urllib.parse, urllib.request, uuid, wave, unicodedata, sys, signal, math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from visual_verifier import VisualVerifier

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

def implementation_hashes():
 base=Path(__file__).parent
 return {name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ('app.py','storyboard.py','visual_verifier.py','photo_duplicates.py','renderer.py','alignment_core.py','source_translation.py')}

def now(): return datetime.now(timezone.utc).isoformat()
def connect():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row
 c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=20000')
 return c
def init_db():
 with connect() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS jobs(\n   id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,\n   topic TEXT NOT NULL, language TEXT NOT NULL, duration_s INTEGER NOT NULL,\n   status TEXT NOT NULL, stage TEXT NOT NULL, progress INTEGER NOT NULL,\n   message TEXT NOT NULL, error TEXT, manifest TEXT,\n   review_status TEXT NOT NULL DEFAULT 'pending', review_note TEXT)""")
  if 'origin' not in {row['name'] for row in c.execute('PRAGMA table_info(jobs)')}:c.execute("ALTER TABLE jobs ADD COLUMN origin TEXT NOT NULL DEFAULT 'user'")
  c.execute('CREATE TABLE IF NOT EXISTS source_decisions(topic_key TEXT NOT NULL,language TEXT NOT NULL,entity_id TEXT NOT NULL,decision TEXT NOT NULL,note TEXT,created_at TEXT NOT NULL,PRIMARY KEY(topic_key,language,entity_id))')
  c.execute("CREATE TABLE IF NOT EXISTS voice_attempts(job_id TEXT NOT NULL,attempt INTEGER NOT NULL,text_sha256 TEXT NOT NULL,voice TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT,PRIMARY KEY(job_id,attempt))")
  c.execute("UPDATE jobs SET status='failed',stage='interrupted',message='Process restarted before completion',error='interrupted' WHERE status IN ('queued','running')")
def update(jid,**fields):
 fields['updated_at']=now()
 with connect() as c:c.execute('UPDATE jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),jid))
def get_job(jid):
 with connect() as c:r=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
 if not r:return None
 d=dict(r);d['manifest']=json.loads(d['manifest']) if d['manifest'] else None;return d
def subject_rejected(topic,lang,entity_id):
 if not entity_id:return False
 try:
  with connect() as c:row=c.execute("SELECT decision FROM source_decisions WHERE topic_key=? AND language=? AND entity_id=?",(' '.join(topic.casefold().split()),lang,entity_id)).fetchone()
  return bool(row and row['decision']=='rejected')
 except sqlite3.OperationalError:return False
def reject_subject(topic,lang,entity_id,note='Owner rejected this source interpretation'):
 if not re.fullmatch(r'Q[1-9][0-9]*',str(entity_id)):raise ValueError('missing resolved subject identity')
 with connect() as c:c.execute("INSERT OR REPLACE INTO source_decisions(topic_key,language,entity_id,decision,note,created_at) VALUES(?,?,?,'rejected',?,?)",(' '.join(topic.casefold().split()),lang,entity_id,note,now()))

def public_job(j):
 if not j:return None
 return {k:j[k] for k in ('id','created_at','updated_at','topic','language','duration_s','status','stage','progress','message','error','review_status','review_note')}|{'manifest':j['manifest'],'origin':j.get('origin','user')}
def safe_id(x):
 try:return str(uuid.UUID(x))
 except Exception:return None
def tokens(s):
 s=unicodedata.normalize('NFC',s or '').replace(chr(0x301),'')
 out=[]
 for x in re.findall(r'[^\W_]+',s or '',re.UNICODE):
  x=x.lower()
  if len(x)<=2 or x in STOP:continue
  if x.isascii() and x.isalpha():
   if len(x)>4 and x.endswith('ies') and x not in {'species','series'}:x=x[:-3]+'y'
   elif len(x)>4 and x.endswith('oes') and x not in {'shoes','canoes','oboes'}:x=x[:-2]
   elif len(x)>4 and x.endswith(('ches','shes','xes','zes')):x=x[:-2]
   elif len(x)>3 and x.endswith('s') and not x.endswith(('ss','us','is')) and x not in {'mars','news','lens','bias','species','series'}:x=x[:-1]
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
   'pl':('owego','owej','owym','owych','ego','emu','ych','ymi','ej','ami','ach','ania','enie','owa','owe','owy','owi','ów','om','em','ie','ki','ka','ek','y','i','a','e','u'),
   'ru':('иями','ями','ами','ого','ему','ому','ыми','ими','ая','яя','ое','ее','ые','ие','ых','их','ой','ый','ий','ую','юю','ам','ям','ах','ях','ов','ев','а','я','ы','и','е','о','у','ю'),
   'uk':('ями','ами','ого','ому','ої','ими','ими','ими','ая','яя','еє','іє','их','ій','ий','ою','єю','ам','ям','ах','ях','ів','ев','а','я','и','і','ї','е','о','у','ю')
  }
  out=[]
  for word in re.findall(r'[^\W_]+',unicodedata.normalize('NFC',text or '').replace(chr(0x301),'').lower(),re.UNICODE):
   if word in STOP or word in stop.get(lang,set()) or re.fullmatch(actions.get(lang,r'(?!)'),word):continue
   for suffix in suffixes.get(lang,()):
    if len(word)-len(suffix)>=4 and word.endswith(suffix):word=word[:-len(suffix)];break
   if len(word)>2:out.append(word)
  return out

def process_signal(text,lang):
  patterns={
   'en':r'\b(melt(?:s|ed|ing)?|molten|form(?:s|ed|ing)?|blow(?:s|n|ing|pipe)?|anneal(?:s|ed|ing)?|cool(?:s|ed|ing)|inspect(?:s|ed|ing|ion|ions)?|furnaces?|batch|gobs?|press(?:es|ed|ing)?|feed(?:s|ing)?)\b',
   'pl':r'(top\w*|form\w*|wydmuch\w*|chłodz\w*|chlodz\w*|wyżarz\w*|wyzarz\w*|inspekc\w*|piec\w*|wsad\w*|kropl\w*)',
   'ru':r'(плав\w*|форм\w*|выдув\w*|охлажд\w*|отжиг\w*|провер\w*|печ\w*|смес\w*|капл\w*)',
   'uk':r'(плав\w*|форм\w*|видув\w*|охолодж\w*|відпал\w*|перевір\w*|печ\w*|шихт\w*|крап\w*)'
  }
  return len(re.findall(patterns.get(lang,patterns['en']),text or '',re.I|re.UNICODE))+len(re.findall({'en':r'\b(?:mix\w*|separat\w*|clean\w*|wash\w*|grind\w*|crush\w*|cook\w*|drain\w*|dry\w*|dri\w*|filter\w*|remov\w*|layer\w*|laid|add\w*|pour\w*|roll\w*|cut\w*|assembl\w*|bake\w*|stir\w*)','pl':r'\b(?:miesza\w*|rozdziel\w*|oczyszcz\w*|sus\w*|pras\w*|miel\w*|dodaj\w*|walc\w*|filtrow\w*)','ru':r'\b(?:смеш\w*|раздел\w*|очищ\w*|измельч\w*|дроб\w*|суш\w*|пресс\w*|фильтр\w*|добавля\w*|удаля\w*)','uk':r'\b(?:зміш\w*|розділ\w*|очищ\w*|подрібн\w*|прес\w*|суш\w*|фільтр\w*|дода\w*|видаля\w*)'}.get(lang,r'(?!)'),text or '',re.I|re.UNICODE))
WIKI_LAST_REQUEST=0.0
def http_json(url,headers=None,timeout=20):
 global WIKI_LAST_REQUEST
 host=(urllib.parse.urlparse(url).hostname or '').lower()
 if host.endswith('.wikipedia.org') or host=='commons.wikimedia.org':
  pause=1.1-(time.monotonic()-WIKI_LAST_REQUEST)
  if pause>0:time.sleep(pause)
  WIKI_LAST_REQUEST=time.monotonic()
 h={'User-Agent':'UniversalShortFactory/1.0 (https://studio.hodor.com.pl/; educational video research)','Accept':'application/json'};h.update(headers or {})
 with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=timeout) as r:return json.loads(r.read(8_000_000).decode('utf-8'))
class WikiHTML(HTMLParser):
 VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
 SKIP_TAGS={'script','style','table','figure','gallery'}
 SKIP_CLASSES={'mw-editsection','reference','navbox','metadata','mw-references-wrap','toc','sidebar','hatnote','ambox','vertical-navbox','reflist'}
 SKIP_SECTIONS={
  'en':{'references','notes','see also','further reading','external links','bibliography','works cited','sources'},
  'pl':{'przypisy','bibliografia','zobacz też','zobacz takze','dalsza lektura','linki zewnętrzne','źródła'},
  'ru':{'примечания','источники','литература','см. также','ссылки','внешние ссылки'},
  'uk':{'примітки','джерела','література','див. також','посилання','зовнішні посилання'}
 }
 def __init__(self,lang='en',paragraphs_only=False):
  self.paragraphs_only=paragraphs_only;self.paragraph_depth=0
  super().__init__(convert_charrefs=True);self.lang=lang;self.sup_level=0;self.sup_text=[];self.skip=0;self.skip_section=False;self.heading=None;self.heading_text=[];self.parts=[]
 def handle_starttag(self,tag,attrs):
  if self.sup_level:
   if tag not in self.VOID:self.sup_level+=1
   return
  if tag in {'h2','h3'}:
   if tag=='h2' and self.skip_section:self.skip_section=False
   self.heading=tag;self.heading_text=[];return
  if self.heading or self.skip_section:return
  if self.skip:
   if tag not in self.VOID:self.skip+=1
   return
  classes=set(dict(attrs).get('class','').split())
  if tag in self.SKIP_TAGS or classes&self.SKIP_CLASSES or (self.paragraphs_only and tag=='li'):
   if tag not in self.VOID:self.skip=1
   return
  if tag=='sup':self.sup_level=1;self.sup_text=[];return
  if tag=='sub':self.parts.append('_')
  if tag=='p':self.paragraph_depth+=1
  if tag in {'p','h4','li','br'}:self.parts.append('\n')
 def handle_endtag(self,tag):
  if self.sup_level:
   if tag not in self.VOID:self.sup_level-=1
   if not self.sup_level:
    value=''.join(self.sup_text).strip()
    if value and not re.fullmatch(r'\[[^\]]*\]|[⇨↗↑↓•*†‡]+',value):self.parts.append('^'+value)
    self.sup_text=[]
   return
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
  if tag=='p':self.paragraph_depth=max(0,self.paragraph_depth-1)
  if tag in {'p','h4','li'}:self.parts.append('\n')
  elif tag in {'a','b','strong','i','em','span'}:self.parts.append(' ')
 def handle_data(self,data):
  if self.sup_level:self.sup_text.append(data)
  elif self.heading:self.heading_text.append(data)
  elif not self.skip and not self.skip_section and (not self.paragraphs_only or self.paragraph_depth>0):self.parts.append(data)
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
def measured_sentence_ms(text,lang):
 def measure():
  folder=ROOT/'tmp'/('speech-plan-'+str(uuid.uuid4()));folder.mkdir(parents=True,exist_ok=True)
  try:
   path=folder/'speech.wav';voice={'en':'en-us','pl':'pl','ru':'ru','uk':'uk'}[lang]
   subprocess.run(['espeak-ng','-v',voice,'-s','155','-w',str(path),'--',text],check=True,capture_output=True,timeout=15)
   with wave.open(str(path),'rb') as audio:return (audio.getnframes()*1000+audio.getframerate()-1)//audio.getframerate()
  finally:shutil.rmtree(folder,ignore_errors=True)
 return cache_fetch('speech-plan-natural-estimate-v2|'+lang+'|155|'+text,measure)
NATURAL_RATE_CACHE={}
def natural_char_rate(lang):
 if lang in NATURAL_RATE_CACHE:return NATURAL_RATE_CACHE[lang]
 from statistics import median
 try:
  with connect() as c:rows=c.execute("SELECT receipt FROM voice_attempts WHERE voice=? AND state='measured' AND receipt IS NOT NULL ORDER BY rowid DESC LIMIT 12",(SELECTED_VOICES[lang][1],)).fetchall()
  data=[json.loads(row['receipt']) for row in rows]
  values=[item['duration_ms']/item['characters'] for item in data if item.get('characters',0)>=120]
  if values:
   NATURAL_RATE_CACHE[lang]=median(values);return NATURAL_RATE_CACHE[lang]
 except (sqlite3.Error,ValueError,KeyError):pass
 NATURAL_RATE_CACHE[lang]={'en':65.0,'pl':65.0,'ru':70.0,'uk':70.0}[lang]
 return NATURAL_RATE_CACHE[lang]

NATURAL_INTERNAL_RATE_CACHE={}
def natural_internal_rate(lang):
 if lang in NATURAL_INTERNAL_RATE_CACHE:return NATURAL_INTERNAL_RATE_CACHE[lang]
 from statistics import median
 values=[]
 with connect() as db:rows=db.execute("SELECT job_id,receipt FROM voice_attempts WHERE voice=? AND state='measured' AND receipt IS NOT NULL ORDER BY rowid DESC LIMIT 12",(SELECTED_VOICES[lang][1],)).fetchall()
 for row in rows:
  try:
   receipt=json.loads(row['receipt']);digest=receipt['text_sha256']
   if not safe_id(row['job_id']) or not re.fullmatch('[a-f0-9]{64}',digest):continue
   evidence=json.loads((RENDER/row['job_id']/('verified-input-'+digest[:16]+'.json')).read_text())
   text=evidence['spoken_text']
   if hashlib.sha256(text.encode()).hexdigest()!=digest or evidence['voice']!=SELECTED_VOICES[lang][1]:continue
   estimate=measured_sentence_ms(text,lang)
   if estimate>0:values.append(receipt['duration_ms']/estimate)
  except (OSError,ValueError,KeyError):continue
 NATURAL_INTERNAL_RATE_CACHE[lang]=median(values) if values else None
 return NATURAL_INTERNAL_RATE_CACHE[lang]

def natural_duration_ms(text,lang):
 # Characters miss spoken numbers and punctuation. Blend two independently calibrated
 # estimates; eSpeak remains a silent internal measurement, never output audio.
 spoken=selected_voice_request(lang,text)['input']['text']
 characters=len(spoken)*natural_char_rate(lang);internal_rate=natural_internal_rate(lang)
 if internal_rate is None:return round(characters)
 return round((characters+measured_sentence_ms(spoken,lang)*internal_rate)/2)

def fit_narration(rows,count,lang,process_intent=False,duration_ms=None,required_sentence=None,natural=False,scope=()):
 # Exact-count duration-constrained selection over source sentences, measured in the selected voice.
 rate=natural_char_rate(lang) if natural else None
 cost_ms=lambda text:natural_duration_ms(text,lang)+round(rate) if natural else measured_sentence_ms(text,lang)
 step=10 if natural else 25
 budget=((duration_ms if duration_ms is not None else count*5000)-(0 if natural else 100))//step;states=[{} for _ in range(count+1)];states[0][(0,0)]=(0.0,())
 seen=set();candidates=[]
 for row in rows:
  norm=re.sub(r'\W+','',row[2].lower())
  if norm in seen:continue
  seen.add(norm);candidates.append(row)
  if len(candidates)>=240:break
 if len(candidates)>60:
  mandatory=next((row for row in candidates if row[2]==required_sentence),None)
  candidates=candidates[:40]+sorted(candidates[40:],key=lambda row:cost_ms(row[2]))[:20]
  if mandatory is not None and mandatory not in candidates:candidates[-1]=mandatory
 # Remember which scope terms a partial narration already covers. This
 # prevents a higher-ranked overview from replacing a topical plan of
 # the same length before the final scope check.
 scope_bits={term:1<<i for i,term in enumerate(sorted(scope))}
 full_scope=(1<<len(scope_bits))-1
 masks=[sum(scope_bits[term] for term in identifier_scope_terms(row[2],lang)&scope_bits.keys())
        for row in candidates] if scope_bits else [0]*len(candidates)
 present=0
 for mask in masks:present|=mask
 if present!=full_scope:return []
 normalized=[re.sub(r'\W+','',row[2].casefold()) for row in candidates] if natural else []
 actions=[visual_actions(row[2])-{'production'} for row in candidates]
 terms=[set(topic_terms(row[2],lang)) for row in candidates]
 penalties=[]
 conflicts=[]
 for i in range(len(candidates)):
  pair=[]
  blocked=set()
  for j in range(len(candidates)):
   if (process_intent and actions[i]&actions[j]) or (natural and (normalized[i] in normalized[j] or normalized[j] in normalized[i])):
    blocked.add(j)
   overlap=len(terms[i]&terms[j])/max(1,len(terms[i]|terms[j]))
   pair.append((8*len(actions[i]&actions[j]) if process_intent else 0)+(10*overlap if overlap>.35 else 0))
  penalties.append(pair)
  conflicts.append(blocked)
 required=next((i for i,row in enumerate(candidates) if row[2]==required_sentence),None)
 if required_sentence and required is None:return []
 if required is not None:
  cost=(cost_ms(candidates[required][2])+step-1)//step
  if cost>budget:return []
  states[0].clear();states[1][(cost,masks[required])]=(candidates[required][0],(required,))
 for index,(score,source_index,sentence,words) in enumerate(candidates):
  if index==required:continue
  cost=(cost_ms(sentence)+step-1)//step
  if cost>budget:continue
  for selected in range(min(count,index+1+(required is not None)),0,-1):
   for (used,covered),(total,chosen) in list(states[selected-1].items()):
    target=used+cost
    if target>budget:continue
    if not conflicts[index].isdisjoint(chosen):continue
    candidate=(total+score-sum(penalties[index][old] for old in chosen),chosen+(index,))
    key=(target,covered|masks[index])
    if key not in states[selected] or candidate[0]>states[selected][key][0]:states[selected][key]=candidate
 if not states[count]:return []
 options=[(used,value) for (used,covered),value in states[count].items()
          if covered==full_scope and (not natural or used*step >= (duration_ms or count*5000)*.85)]
 if not options:return []
 # Natural speech must occupy the requested window; relevance breaks timing ties.
 if natural:
  target=(duration_ms or count*5000)*.95
  chosen=max(options,key=lambda item:(-abs(item[0]*step-target),item[1][0]))[1][1]
 else:chosen=max(options,key=lambda item:(item[1][0],item[0]))[1][1]
 return [{'text':candidates[index][2],'language':lang,'source_index':candidates[index][1],'source_sentence':candidates[index][2],'score':candidates[index][0]} for index in chosen]

def source_title_key(text):
 return unicodedata.normalize('NFKC',text).casefold().strip()

def joined_topic_title(topic):
 # Candidate for accidental word splitting, never a loose search synonym.
 parts=source_title_key(topic).split()
 if len(parts)!=2 or not all(part.isalpha() and len(part)>=2 for part in parts):return ''
 joined=''.join(parts)
 return joined if len(joined)>=7 else ''

def exact_source_title(topic,title):
 requested=source_title_key(topic)
 actual=source_title_key(title)
 if requested==actual:return 2
 return int(bool(joined_topic_title(topic)) and joined_topic_title(topic)==actual)

def source_match_rank(topic,source):
 return max(exact_source_title(topic,source.get('title','')),int(bool(joined_topic_title(topic)) and joined_topic_title(topic)==source.get('joined_title_alias')))

def topic_identifier(topic):
 candidates={}
 for match in re.finditer(r'(?<!\w)[A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)*(?!\w)',topic):
  name=match[0]
  if 3<=len(name)<=40 and re.search('[A-Za-z]',name) and re.search('[0-9]',name):
   candidates.setdefault(name.casefold(),name)
 return next(iter(candidates.values())) if len(candidates)==1 else ''

def identifier_article(identifier,lang):
 def fetch():
  for query_lang in dict.fromkeys((lang,'en','pl','ru','uk')):
   params={'action':'query','titles':identifier,'redirects':1,'prop':'langlinks|pageprops','lllang':lang,'format':'json','formatversion':2}
   query=http_json('https://'+query_lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params),timeout=12).get('query',{})
   pages=query.get('pages',[])
   if not pages or not pages[0].get('pageid') or 'disambiguation' in pages[0].get('pageprops',{}):continue
   page=pages[0]
   # Treat acronym redirects to a section as references, not entity identities.
   if any(row.get('tofragment') for row in query.get('redirects',[])):continue
   native=page['title'] if query_lang==lang else next((link['title'] for link in page.get('langlinks',[]) if link['lang']==lang),'')
   return {'title':page['title'],'language':query_lang,'native_title':native,
           'url':'https://'+query_lang+'.wikipedia.org/wiki/'+urllib.parse.quote(page['title'].replace(' ','_'))}
  return {}
 return cache_fetch('identifier-article-v1|'+lang+'|'+source_title_key(identifier),fetch)

def wikipedia(topic,lang):
  identifier=topic_identifier(topic)
  reference=identifier_article(identifier,lang) if identifier else {}
  if reference and not reference['native_title']:return []
  native_title=reference.get('native_title','')
  scoped_identifier=bool(native_title and source_title_key(topic)!=source_title_key(identifier))
  queries=[(topic,6)]
  made=bool(re.search(r'\b(make|made|manufactur\w*|produc\w*|fabricat\w*|build|create|zrobi\w*|produk\w*|wytwarz\w*|изготов\w*|производ\w*|виробля\w*|виготов\w*)\b',topic,re.I))
  core=list(dict.fromkeys(topic_terms(topic,lang)))
  suffix={'en':'manufacturing process','pl':'proces produkcji','ru':'процесс производства','uk':'процес виробництва'}
  stage={'en':'production method materials equipment','pl':'metoda produkcji materiały urządzenia','ru':'способ производства материалы оборудование','uk':'спосіб виробництва матеріали обладнання'}
  if made and core:
   queries.insert(0,(' '.join(core)+' '+suffix[lang],8));queries.append((' '.join(core)+' '+stage[lang],8))
  hits=[];seen=set()
  for query,limit in ([] if native_title else queries):
   q=urllib.parse.urlencode({'action':'query','list':'search','srsearch':query,'srlimit':str(limit),'srnamespace':'0','format':'json','formatversion':'2'})
   data=http_json('https://'+lang+'.wikipedia.org/w/api.php?'+q,timeout=22)
   for hit in (data.get('query') or {}).get('search') or []:
    title=str(hit.get('title') or '').strip();key=str(hit.get('pageid') or title)
    if title and key not in seen:seen.add(key);hits.append(title)
  # A qualified homonym can dominate the search for a broken compound.
  # Try the joined spelling while retaining priority for any valid exact article.
  joined=joined_topic_title(topic)
  joined_target=''
  if joined and not native_title and not made and not any(exact_source_title(topic,title)==1 for title in hits):
   q=urllib.parse.urlencode({'action':'query','titles':joined,'redirects':1,'prop':'pageprops','format':'json','formatversion':'2'})
   pages=(http_json('https://'+lang+'.wikipedia.org/w/api.php?'+q,timeout=22).get('query') or {}).get('pages',[])
   page=pages[0] if len(pages)==1 else {}
   if page.get('pageid') and 'disambiguation' not in page.get('pageprops',{}):
    joined_target=page['title']
    if joined_target not in hits:hits.append(joined_target)
  core_set=set(core);method_terms=set(topic_terms({'en':'manufacturing making production process materials equipment','pl':'produkcja wytwarzanie proces materiały urządzenia','ru':'производство изготовление процесс материалы оборудование','uk':'виробництво виготовлення процес матеріали обладнання'}[lang],lang))
  def core_matches(title):
   words=set(topic_terms(title,lang))
   if lang!='en':
    roots=grounding_terms(title,lang)
    return {term for term in core_set if term[:4] in roots}
   return {term for term in core_set if term in words or (made and len(term)>=4 and any(word.startswith(term) and word[len(term):] in {'making','manufacturing','production','blowing'} for word in words))}
  hits=[title for title in hits if title==joined_target or exact_source_title(topic,title) or core_matches(title) or (made and bool(set(topic_terms(title,lang))&method_terms))]
  if made and len(core_set)>1:
   hits=[title for title in hits if core_matches(title)==core_set or bool((set(topic_terms(title,lang))-core_set)&method_terms) or (core_matches(title) and re.search(r'manufactur|produc|fabricat|process|produk|wytwarz|proces|производ|изготов|процесс|виробниц|виготов|процес',title,re.I))]
  hits=sorted(hits,key=lambda title:(-max(int(title==joined_target),exact_source_title(topic,title)),-len(core_matches(title)),-int(made and bool(re.search(r'making|manufactur|production|produk|wytwarz|производ|изготов|виробниц|виготов',title,re.I))),hits.index(title)))
  if native_title:hits=[native_title]
  if not hits:
   hints=['uk','ru','en','pl'] if re.search('[іїєґІЇЄҐ]',topic) else ['ru','uk','en','pl'] if re.search('[А-Яа-яЁё]',topic) else ['pl','en','ru','uk'] if re.search('[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]',topic) else ['en','pl','ru','uk']
   for query_lang in hints:
    if query_lang==lang:continue
    q=urllib.parse.urlencode({'action':'query','list':'search','srsearch':topic,'srlimit':'6','srnamespace':'0','format':'json','formatversion':'2'})
    foreign=(http_json('https://'+query_lang+'.wikipedia.org/w/api.php?'+q,timeout=22).get('query') or {}).get('search') or []
    if not foreign:continue
    query_terms=grounding_terms(topic,query_lang)
    def foreign_rank(hit):
     title_terms=grounding_terms(hit['title'],query_lang)
     return (bool(query_terms&title_terms) and (len(title_terms)>1 or len(query_terms)==1),len(query_terms&title_terms)/max(1,len(title_terms)),-len(title_terms))
    foreign.sort(key=foreign_rank,reverse=True)
    q=urllib.parse.urlencode({'action':'parse','page':foreign[0]['title'],'prop':'langlinks','format':'json'})
    links=(http_json('https://'+query_lang+'.wikipedia.org/w/api.php?'+q,timeout=22).get('parse') or {}).get('langlinks') or []
    translated=next((link.get('*') or link.get('title') for link in links if link.get('lang')==lang),'')
    if translated:hits=[translated];break
  out=[]
  for title in hits[:10]:
   try:
    q=urllib.parse.urlencode({'action':'parse','page':title,'prop':'text|langlinks','disableeditsection':'1','disablelimitreport':'1','format':'json'})
    parsed=http_json('https://'+lang+'.wikipedia.org/w/api.php?'+q,timeout=22).get('parse') or {}
    actual=str(parsed.get('title') or title).strip();html=((parsed.get('text') or {}).get('*') or '')
    parser=WikiHTML(lang,paragraphs_only=True);parser.feed(html);text=parser.text()
    if actual and len(text)>220 and 'may refer to:' not in text[:600].lower():out.append({'title':actual,'joined_title_alias':joined if title==joined_target else '','url':'https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(actual.replace(' ','_')),'text':text,'visual_title':actual if lang=='en' else next((str(link.get('*') or link.get('title') or '') for link in parsed.get('langlinks',[]) if link.get('lang')=='en'),''),'scoped_identifier':identifier if scoped_identifier else ''})
   except Exception as e:
    if getattr(e,'code',None)==429:raise
    continue
   if len(out)>=6:break
  return out
def sentences(paragraph):
 abbreviations=r'\b(?:e\.g|i\.e|U\.S|U\.K|Mr|Mrs|Dr|Prof|Inc|Ltd|Corp|Co|im|np|m\.in|m\.st|нар|род|itp|itd|tj|tzn|tzw|ok|godz|proc|por|rys|św|млн|млрд|тис|тыс|т\.е|т\.д|т\.п|гг|рис|ім|ст)\.'
 protected=re.sub(abbreviations,lambda match:match.group(0).replace('.',chr(0x2024)),paragraph,re.I)
 protected=re.sub(r'(?<!\w)([A-ZА-ЯІЇЄҐ])\.(?=\s+[A-ZА-ЯІЇЄҐ])',lambda match:match.group(1)+chr(0x2024),protected)
 return [part.replace(chr(0x2024),'.') for part in re.split(r'(?<=[.!?])\s+',protected.strip())]

def unsupported_qualifier(sentence,topic,sources):
 # An article about a broad class does not establish photos for an unrepresented subtype.
 core=set(topic_terms(topic,'en'));represented=set().union(*(set(tokens(source['title'])) for source in sources))
 grammar=STOP|set('around near within without throughout against among like unlike than onto into larger smaller largest smallest longest shortest numerous several certain various different remaining potential potentially another other such these those total overall individual particular single multiple large small great higher lower historical modern'.split())
 words=re.findall(r'[^\W_]+',sentence.lower(),re.UNICODE)
 for index,word in enumerate(words):
  if not index or not set(tokens(word))&core:continue
  qualifier=words[index-1]
  if len(qualifier)<3 or not qualifier.isalpha() or qualifier in grammar or qualifier in core:continue
  if not set(tokens(qualifier))<=represented:return True
 return False

def entity_profile(sources,lang):
 if not sources:return {}
 title=sources[0].get('visual_title') or sources[0]['title']
 def retrieve():
  query=urllib.parse.urlencode({'action':'query','titles':title,'prop':'pageprops','format':'json','formatversion':'2','redirects':'1'})
  pages=http_json('https://en.wikipedia.org/w/api.php?'+query,timeout=20).get('query',{}).get('pages',[])
  qid=next((page.get('pageprops',{}).get('wikibase_item') for page in pages if page.get('pageprops',{}).get('wikibase_item')),None)
  if not qid:return {}
  entity=http_json('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json',timeout=20).get('entities',{}).get(qid,{})
  claims=entity.get('claims',{})
  values=lambda prop:[item.get('mainsnak',{}).get('datavalue',{}).get('value') for item in claims.get(prop,[])]
  types={value.get('id') for value in values('P31') if isinstance(value,dict)}
  labels=entity.get('labels',{});name=labels.get('en',{}).get('value') or title
  native=labels.get(lang,{}).get('value') or sources[0]['title']
  descriptions=entity.get('descriptions',{})
  aliases=[name]+[value['value'] for value in entity.get('aliases',{}).get('en',[]) if len(value.get('value','').split())<=4]
  categories=[value for value in values('P373') if isinstance(value,str)]
  kind='human' if 'Q5' in types else 'concept' if name[:1].islower() else 'entity'
  english_text=sources[0]['text'] if lang=='en' else ''
  if kind=='concept' and not english_text:
   try:
    query=urllib.parse.urlencode({'action':'parse','page':title,'prop':'text','format':'json'})
    parsed=http_json('https://en.wikipedia.org/w/api.php?'+query,timeout=20).get('parse',{})
    parser=WikiHTML('en',paragraphs_only=True);parser.feed(parsed.get('text',{}).get('*',''))
    english_text=parser.text()[:5000]
   except Exception:pass
  vocabulary=sorted(set(tokens(english_text[:5000]+' '+descriptions.get('en',{}).get('value',''))))[:350]
  visual_lead=sentences(english_text.splitlines()[0])[0][:400] if kind=='concept' and english_text.strip() else ''
  return {'id':qid,'kind':kind,'name':name,'native_name':native,
          'native_description':descriptions.get(lang,{}).get('value',''),'visual_vocabulary':vocabulary,
          'labels':{language:labels.get(language,{}).get('value','') for language in LANGS},
          'aliases':list(dict.fromkeys(aliases))[:8],
          'commons_category':categories[0] if categories else '',
          'visual_description':visual_lead or re.sub(r'\s+since\b.*$','',descriptions.get('en',{}).get('value',''),flags=re.I).strip(),
          'visual_description_source':('https://en.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))) if visual_lead else 'https://www.wikidata.org/wiki/'+qid,
          'source_url':'https://www.wikidata.org/wiki/'+qid}

 try:return cache_fetch('subject-profile-v5|'+lang+'|'+title,retrieve)
 except urllib.error.HTTPError as error:
  if error.code in {429,503}:raise
  return {}
 except Exception:return {}
def omit_parenthetical_asides(text):
 depth=0;out=[]
 for char in text:
  if char=='(':depth+=1;continue
  if char==')':
   if depth:depth-=1;continue
  if not depth:out.append(char)
 return re.sub(r'\s+',' ',''.join(out)).strip()
def verified_human_categories(candidates,profile):
 root='Category:'+profile.get('commons_category','')
 if root=='Category:':return set()
 names=list(dict.fromkeys([profile.get('commons_category',''),profile.get('name','')]))
 def personal(category):
  value=category.removeprefix('Category:')
  return any(re.match(r'^(?:Portraits of |Photographs of |Cropped portraits of )?'+re.escape(name)+r'(?:$| (?:in|at|wearing|speaking|visiting|by)\b)',value,re.I) for name in names if name)
 wanted={category for p in candidates for category in p.get('categories',[]) if category!=root and personal(category)}
 wanted=set(sorted(wanted)[:50]);parents={};frontier=set(wanted)
 for _ in range(3):
  if not frontier:break
  titles='|'.join(sorted(frontier))
  def retrieve():
   params={'action':'query','titles':titles,'prop':'categories','cllimit':'max','format':'json'};found={}
   for _page in range(4):
    data=http_json('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params),timeout=20)
    for page in data.get('query',{}).get('pages',{}).values():
     found.setdefault(page['title'],[]).extend(category['title'] for category in page.get('categories',[]))
    if not data.get('continue'):break
    params.update(data['continue'])
   return found
  parents.update(cache_fetch('commons-person-category-parents-v1|'+titles,retrieve))
  frontier={parent for category in frontier for parent in parents.get(category,[]) if parent!=root and parent not in parents and personal(parent)}
 def reaches(category,seen):
  if category==root:return True
  if category in seen:return False
  return any(reaches(parent,seen|{category}) for parent in parents.get(category,[]) if parent==root or personal(parent))
 return {category for category in wanted if reaches(category,set())}

def bind_human_images(candidates,profile):
 candidates=bind_place_images(candidates,profile)
 commons=[p for p in candidates if p.get('provider')=='commons'];entities={}
 verified_categories=verified_human_categories(commons,profile)
 for start in range(0,len(commons),50):
  batch=commons[start:start+50];ids='|'.join('M'+p['id'] for p in batch)
  if not ids:continue
  def retrieve():
   query=urllib.parse.urlencode({'action':'wbgetentities','ids':ids,'props':'claims','format':'json'})
   return http_json('https://commons.wikimedia.org/w/api.php?'+query,timeout=25).get('entities',{})
  try:entities.update(cache_fetch('commons-depicts-v1|'+ids,retrieve))
  except urllib.error.HTTPError as error:
   if error.code in {429,503}:raise
  except Exception:pass
 for p in commons:
  entity=entities.get('M'+p['id'],{});statements=entity.get('statements') or entity.get('claims') or {}
  depicts={claim.get('mainsnak',{}).get('datavalue',{}).get('value',{}).get('id') for claim in statements.get('P180',[])}
  category='Category:'+profile.get('commons_category','')
  if profile['id'] in depicts:basis='Commons structured depicts statement'
  elif profile.get('commons_category') and category in p.get('categories',[]):basis='Wikidata-linked Commons category'
  elif verified_categories.intersection(p.get('categories',[])):basis='Verified personal subcategory of Wikidata-linked Commons category'
  else:continue
  p['identity_verification']={'entity_id':profile['id'],'basis':basis,'file_page':p['source_url'],'entity_source':profile['source_url']}
 return candidates

def grounding_terms(text,lang):
 return {term[:4] if lang!='en' else term for term in topic_terms(text,lang)}

def context_dependent_sentence(text):
 # Source paragraphs may refer to material omitted from a short video.
 leading=r'^(?:pozostał\w* częś\w*|поверх (?:цієї |такої )?маси|поверх (?:этой |такой )?массы|решта|остальн\w* часть|the remaining part|był on|była ona|byli oni|były one|ось чому|вот почему|that is why|that.s why|dlatego|згодом|пізніше|затем|впоследствии|subsequently|later|potem|następnie|the (?:outcome|result|wooden frame)\b|finally|lastly|unfortunately|according to some|according to many|furthermore|moreover|however|another|other|therefore|thus|in addition|for example|examples? include|another example|нарешті|на жаль|за оцінкою|по мнению|według niektórych|наостанок|крім того|однак|але|проте|зрештою|інше|інша|інший|отже|таким чином|наприклад|наконец|кроме того|однако|другое|другой|другая|следовательно|таким образом|например|wreszcie|ponadto|jednak|zatem|na przykład|na koniec)\b'
 references=r'\b(?:цього|цієї|цих|цим|цими|цій|этими|цей|ця|цю|ці|їх|її|його|такі|таких|такого|такої|така|такою|этой|этого|этих|такие|таких|такая|такой|такую|такое|tych|tej|tego|takie|takich|this|these|those|such)\b'
 pronouns=r'^(?:he|she|it|they|their|its|он|она|оно|они|его|ее|её|их|він|вона|воно|вони|це|його|її|їх|one|ona|ono|oni|jej|jego|ich)\b'
 reference=re.search(references,text,re.I)
 dangling=bool(reference and len(text[:reference.start()].split())<5)
 intro=re.match(r'^(?:in|on|at|during|among|for|under|within)\s+[^,]{1,65},\s*',text,re.I)
 unresolved=bool(intro and re.search(pronouns,text[intro.end():],re.I))
 omitted_expression=bool(re.search(r'\b(?:equation|formula|expression)\b[^.!?]{0,120}\b(?:is|are|was|were|becomes?)\s*[.!?]$',text,re.I))
 return bool(re.search(leading,text,re.I) or dangling or re.search(pronouns,text,re.I) or unresolved or omitted_expression)


def attach_native_aliases(sources,lang):
 if not sources or len(topic_terms(sources[0]['title'],lang))!=2:return sources
 title=sources[0]['title']
 def retrieve():
  query=urllib.parse.urlencode({'action':'query','titles':title,'prop':'redirects','rdlimit':'20','format':'json','formatversion':'2'})
  data=http_json('https://'+lang+'.wikipedia.org/w/api.php?'+query,timeout=20)
  return [r['title'] for page in data.get('query',{}).get('pages',[]) for r in page.get('redirects',[]) if r.get('ns',0)==0]
 try:sources[0]['native_aliases']=cache_fetch('native-topic-aliases-v1|'+lang+'|'+title,retrieve)
 except Exception:sources[0]['native_aliases']=[]
 return sources
def narrative_focus(sources,topic,lang):
 if not sources:return set()
 if sources[0].get('translation_model'):
  return grounding_terms(sources[0]['text'].splitlines()[0],lang)&grounding_terms(topic,lang)
 title=sources[0]['title'];terms=topic_terms(title,lang)
 if len(terms)!=2:return set()
 root=lambda term:term[:4] if lang!='en' else term
 head=root(terms[-1]);focus={root(terms[0])}
 for alias in sources[0].get('native_aliases',[]):
  words=topic_terms(alias,lang)
  if len(words)==2 and root(words[-1])==head:focus.add(root(words[0]))
 return focus

def source_overview_mode(sources):
 return bool(sources and sources[0].get('entity_profile',{}).get('id')) or any(source.get('source_type')=='structured definition' for source in sources)

def biography_signal(text):
 # Prefer work and achievements over incidental short family anecdotes.
 return int(bool(re.search(r'\b(?:found(?:ed|er)|cofound\w*|establish\w*|invent\w*|discover\w*|research\w*|award\w*|prize|laureate|scientific|published|elected|founded|założy\w*|założyciel\w*|odkry\w*|bada\w*|nobla|nagrod\w*|wynal\w*|wybran\w*|zasnu\w*|засну\w*|основа\w*|винайш\w*|изобр\w*|відкри\w*|откры\w*|дослідж\w*|исслед\w*|нагород\w*|премі\w*|преми\w*|обран\w*)',text,re.I)))

def retain_named_model_asides(text):
 def retain(match):
  value=match.group(1)
  if len(value.split())<=4 and any(c.isupper() for c in value) and any(c.isdigit() for c in value) and any(c.isalpha() for c in value):return ' '+value+' '
  return match.group(0)
 return re.sub(r'\(([^()]*)\)',retain,text)

def process_definition(text):
 parts=re.split(r'\s[—–]\s|\b(?:is|are|jest|są|це|это|є)\b',text or '',maxsplit=1,flags=re.I)
 return len(parts)>1 and bool(re.search(r'manufactur|making|made from|made by|process of|wytwarz|produk|виготов|виробниц|изготов|производ',parts[1],re.I))

def foreign_name_catalogue(text,lang,topic):
 if lang not in {'ru','uk'} or re.search(r'list|catalog|список|перелік|каталог',topic,re.I):return False
 return len(re.findall(r'[A-Za-z]{2,}',text))>=3 and len(re.findall(r'[,;]',text))>=3

DEPENDENT_RELATIVE = {
  'en':r'\b(?:by|through|in|from|under|for|to|with|of) which\b',
  'pl':r'\b(?:w|przez|dzięki|za pomocą) któr\w*',
  'ru':r'\b(?:в|при|с помощью|посредством) котор\w*',
  'uk':r'\b(?:в|у|за допомогою|під час|через) як\w*',
 }

def truncated_dependent_clause(text,source,lang):
 if not re.search(DEPENDENT_RELATIVE.get(lang,r'(?!)'),text,re.I):return False
 def canonical(value):
  return re.sub(r'[^\w]+','',value.casefold())
 prefix=canonical(text)
 original=canonical(source)
 return prefix!=original and original.startswith(prefix)

def complete_clause_variants(text,lang):
 variants=[text]
 separators={
  'en':r',\s+(?:which|while|sometimes|such as|for example)\b|:',
  'pl':r',\s+(?:który|która|które|którzy)\b|\s+za\s+(?:badani\w*|odkry\w*|prac\w*)|:',
  'ru':r',\s+(?:который|которая|которое|которые)\b|\s+за\s+(?:исследован\w*|открыти\w*|работ\w*)|:',
  'uk':r',\s+(?:який|яка|яке|які)\b|\s+за\s+(?:дослідженн\w*|відкритт\w*|прац\w*)|:',
 }
 verbs={
  'en':r'\b(?:is|are|was|were|has|have|had|can|may|involves|consists|received|won|founded|discovered)\b',
  'pl':r'\b(?:jest|są|był|była|byli|były|został|została|otrzymał|otrzymała|otrzymali|odkrył|odkryła)\b',
  'ru':r'\b(?:является|имеет|составляет|насчитывает|получил|получила|получили|открыл|открыла|основал|основала|был|была|были)\b',
  'uk':r'\b(?:є|має|становить|налічує|отримав|отримала|отримали|відкрив|відкрила|заснував|заснувала|був|була|були)\b',
 }
 for match in re.finditer(separators.get(lang,r'(?!)'),text,re.I):
  prefix=text[:match.start()].strip().rstrip(',;: .')
  if len(prefix.split())<6 or not re.search(verbs.get(lang,r'(?!)'),prefix,re.I):continue
  if re.match(r'^(?:while|although|because|when|if|after|before|whereas|gdy|kiedy|chociaż|ponieważ|jeśli|aby|когда|хотя|поскольку|если|чтобы|коли|хоча|оскільки|якщо|щоб)\b',prefix,re.I):continue
  if re.search(r'following|следующ|наступн|następując',prefix,re.I):continue
  if prefix.count('(')!=prefix.count(')'):continue
  # A copula in the main clause does not complete a following relative clause.
  # Keep the original when a cut might leave its subject without a predicate.
  if truncated_dependent_clause(prefix,text,lang):continue
  variants.append(prefix+'.')
 return list(dict.fromkeys(variants))[:4]

def source_slots(sources,topic,count,lang='en',duration_s=None):
  target_ms=(duration_s if duration_s is not None else count*5)*1000
  object_terms=grounding_terms(topic,lang)
  scope=identifier_scope(sources,topic,lang)
  translated_focus=(scope-{'company'}) if sources and sources[0].get('translation_model') else set()
  process_intent=bool(re.search(r'\b(make|made|manufactur\w*|produc\w*|fabricat\w*|build|create|zrobi\w*|produk\w*|wytwarz\w*|изготов\w*|производ\w*|виробля\w*|виготов\w*)\b',topic,re.I))
  focus=set() if process_intent else narrative_focus(sources,topic,lang)
  bottle_words=grounding_terms('bottle bottles бутылка пляшка пляшки butelka butelki',lang)
  container_words=grounding_terms('container containers packaging jar pojemnik pojemniki opakowanie тара контейнер контейнери',lang)
  human=bool(sources and sources[0].get('entity_profile',{}).get('kind')=='human')
  rows=[];source_positions={};source_spans={}
  definition_index=next((i for i,source in enumerate(sources) if source.get('source_type')=='structured definition'),None)
  definition=sources[definition_index]['text'] if definition_index is not None else None
  if human and definition:
   original_definition=definition;definition=omit_parenthetical_asides(retain_named_model_asides(definition))
   source_positions[(definition_index,definition)]=0;source_spans[(definition_index,definition)]=original_definition
  vernacular=lang in {'ru','uk'} and bool(sources) and bool(re.search(r'\b(?:insects?|animals?|plants?|birds?|mammals?|fish)\b',sources[0].get('entity_profile',{}).get('visual_description',''),re.I))
  if vernacular and definition and re.search(r'\b[A-Z][a-z]{2,}\b',definition):
   safe_lead=next((sentence for paragraph in sources[0]['text'].splitlines()[:5] for sentence in sentences(paragraph) if sentence.endswith(('.', '!', '?')) and 5<=len(sentence.split())<=60 and not re.search(r'[A-Za-z]{3,}',sentence) and not context_dependent_sentence(sentence)),None)
   if safe_lead:
    definition_index=0;definition=safe_lead
    source_positions[(0,safe_lead)]=sources[0]['text'].find(safe_lead);source_spans[(0,safe_lead)]=safe_lead

  if not definition and source_overview_mode(sources):
   paragraph=next((p for p in sources[0]['text'].splitlines() if p.strip()),'')
   original=sentences(paragraph)[0] if paragraph else ''
   lead=original if sources[0].get('translation_model') else re.sub(r'\s+([,.;:!?])',r'\1',omit_parenthetical_asides(original)).strip()
   if lead.endswith(('.', '!', '?')) and 5<=len(lead.split())<=90 and len(lead)<=650 and not re.search(r'\^|(?<=\w)_(?=\w)|[⋅×➤]',lead) and not incidental_place_event(lead,topic,sources[0].get('entity_profile',{})):
    definition_index=0;definition=lead
    source_positions[(0,lead)]=sources[0]['text'].find(original);source_spans[(0,lead)]=original
  if definition:
   original_definition=source_spans.get((definition_index,definition),definition)
   if any(excluded in original_definition for excluded in sources[definition_index].get('excluded_visual_sentences',[])):
    definition_index=None;definition=None
  if definition:
   rows.append((40,definition_index,definition,definition.split()))
   source_positions.setdefault((definition_index,definition),0);source_spans.setdefault((definition_index,definition),definition)
  for si,src in enumerate(sources):
   if definition and si!=0:continue
   title_text=src['text'].splitlines()[0] if src.get('translation_model') else src['title']
   title_terms=grounding_terms(title_text,lang)
   for paragraph_index,paragraph in enumerate(src['text'].splitlines()):
    if definition and paragraph_index>31:continue
    if human and (si>0 or paragraph_index>31):continue
    if human and not re.search(r'critic|scandal|controvers|corrupt|критик|скандал|корупц|коррупц|kryty|afer',topic,re.I) and re.search(r'critic|scandal|controvers|corrupt|критик|скандал|корупц|коррупц|kryty|afer',paragraph,re.I):continue
    if definition and process_intent and not re.search(r'histor|ancient|истори|істор|dziej|handmade|manual|traditional|ручн|ręczn|традиц',topic,re.I) and re.search(r'ancient|centur|etymolog|invention|invented|traditional|originally|истори|древн|стародав|wynalezion|starożytn',paragraph,re.I):continue
    paragraph_start=src['text'].find(paragraph)
    units=sentences(paragraph)
    if definition and not src.get('translation_model') and len(units)>1 and (process_signal(paragraph,lang)>=2 or any(context_dependent_sentence(unit) for unit in units[1:])):units=units+[paragraph]
    variants=[(paragraph,paragraph)] if src.get('translation_model') else [(original,variant) for original in units for variant in complete_clause_variants(original,lang)]
    for original_sentence,sentence in variants:
     connected_block=original_sentence==paragraph and len(sentences(paragraph))>1
     source_position=paragraph_start+paragraph.find(original_sentence)
     if foreign_name_catalogue(sentence,lang,topic):continue
     if any(excluded in original_sentence for excluded in src.get('excluded_visual_sentences',[])):continue
     if incidental_place_event(sentence,topic,sources[0].get('entity_profile',{})):continue
     if human:sentence=retain_named_model_asides(sentence)
     if human or definition:sentence=omit_parenthetical_asides(sentence)
     sentence=re.sub(r'\[[^\]]{1,240}\]','',sentence).strip();sentence=re.sub(r'\s+([,.;:!?])',r'\1',sentence);words=sentence.split()
     scope_hits=scope&identifier_scope_terms(sentence,lang) if scope else set()
     if translated_focus and not translated_focus&scope_hits:continue
     if vernacular and re.search(r'[A-Za-z]{3,}',sentence):continue
     first=re.search(r'[^\W_]',sentence,re.UNICODE)
     named_lead=bool(src.get('translation_model') and src.get('scoped_identifier') and re.match(re.escape(src['scoped_identifier'])+r'\b',sentence,re.I))
     if not first or not (first.group().isupper() or first.group().isdigit() or named_lead):continue
     context_text=sentences(sentence)[0] if connected_block else sentence
     if context_dependent_sentence(context_text):continue
     if not sentence.endswith(('.', '!', '?')) or not (5 if process_intent else 8)<=len(words)<=(90 if definition and process_intent else 60 if definition else 24 if process_intent else 36):continue
     if re.search(r'\^|(?<=\w)_(?=\w)|[⋅×➤]',sentence):continue
     if re.search(r'[:;]\s*[\"”\u0027]?[.!?]$',sentence):continue
     if sentence.count('(')!=sentence.count(')') or re.search(r'\bIPA\s*:|U\+[0-9A-F]{4}|Unicode',sentence):continue
     if re.match(r'^(?:examples? include|another example|for example|such)\b',sentence,re.I):continue
     history_requested=bool(re.search(r'histor|ancient|истори|істор|dziej',topic,re.I))
     research_requested=bool(re.search(r'research|scientist|computer|дослід|дослiд|исслед|комп.ютер|учен|nauk|badani',topic,re.I))
     if not research_requested and re.search(r'humanity|supercomputer|людству|суперкомп|систематично спостерігати|systematically observ',sentence,re.I):continue
     if process_intent and not history_requested and re.search(r'\b(?:invention|invented|ancient|century|centuries|were|was)\b|древн|стародав|wynalezion|starożytn',sentence,re.I):continue
     sentence_terms=grounding_terms(sentence,lang);combined=sentence_terms|title_terms
     topic_hits=len(combined&object_terms);needed=min(2,len(object_terms))
     if object_terms&bottle_words and combined&container_words:topic_hits=max(topic_hits,min(2,len(object_terms)))
     if focus and not human and not (sentence_terms&focus or src.get('strict_translated_scope') and scope_hits):continue
     direct_topic=(human or bool(definition)) and si==0 and paragraph_index<5 or bool(sentence_terms&object_terms);process_overlap=process_signal(sentence,lang) if process_intent else 0
     if definition and si==0:topic_hits=max(topic_hits,needed)
     if needed and topic_hits<needed:continue
     if not process_intent and object_terms and (not direct_topic or (lang=='en' and not definition and not grounding_terms(' '.join(words[:6]),lang)&object_terms)):continue
     if lang=='en' and not human and not definition and not process_intent and unsupported_qualifier(sentence,topic,sources):continue
     if process_intent and not definition and (not process_overlap or not direct_topic or not visual_actions(sentence)):continue
     if process_intent and not (visual_actions(sentence)-{'production'}) and not (si==0 and source_position<4 and process_definition(sentence)):continue
     score=((5 if process_intent else 30)/(1+paragraph_index) if definition else 0)+(8*process_overlap if definition and process_intent else 0)+topic_hits*4+len(sentence_terms&object_terms)*3+process_overlap*2+min(len(words),15)/15-.25*max(0,len(words)-15)+(3 if paragraph_index<2 and not process_intent else 0)+(4 if si==0 and not process_intent else 0)+(8 if si==0 and paragraph_index==0 and not process_intent else 0)
     score+=12*len(scope_hits)
     if human:
      profile_terms=r'profile|account|username|logo|обліков\w* запис|уч[её]тн\w* запис|профил|профіл|логотип|profil\w*|konto'
      if not biography_signal(sentence) and re.search(profile_terms,sentence,re.I) and not re.search(profile_terms,topic,re.I):continue
      score+=12*biography_signal(sentence)
     rows.append((score,si,sentence,words));source_positions.setdefault((si,sentence),source_position);source_spans.setdefault((si,sentence),original_sentence)
  rows.sort(key=lambda x:(-x[0],x[1],abs(len(x[3])-13)))
  if definition:
   candidate=next((row for row in rows if row[1]==0 and source_positions[(row[1],row[2])]<4 and re.search(r'—|\b(?:is|are|jest|są|є|это)\b',row[2],re.I) and natural_duration_ms(row[2],lang)<=target_ms*.8),None)
   if process_intent and not (candidate and process_definition(candidate[2])):
    procedural=[row for row in rows if row[1]==0 and process_signal(row[2],lang)>=2 and grounding_terms(row[2],lang)&grounding_terms(sources[0]['title'],lang) and natural_duration_ms(row[2],lang)<=target_ms]
    if procedural:candidate=min(procedural,key=lambda row:(source_positions[(0,row[2])],-len(row[2])))
   if candidate and (definition_index!=0 or candidate[2]!=definition):
    rows=[row for row in rows if not (row[1]==definition_index and row[2]==definition)]
    definition_index=0;definition=candidate[2]
  all_rows=list(rows)
  opening=min((row for row in rows if row[1]==0 and source_positions[(row[1],row[2])]<len('\n'.join(sources[0]['text'].splitlines()[:2])) and measured_sentence_ms(row[2],lang)<=target_ms*.6),key=lambda row:source_positions[(row[1],row[2])],default=None) if not process_intent else None
  if definition:opening=next(row for row in rows if row[1]==definition_index and row[2]==definition)
  chosen=[];seen=set();used=set();source_counts={};action_counts={}
  while rows and len(chosen)<count:
   best_i=max(range(len(rows)),key=lambda i:rows[i][0]+.3*len(set(topic_terms(rows[i][2],lang))-used)+2/(1+source_counts.get(rows[i][1],0))-(8 if process_intent else 0)*sum(action_counts.get(action,0) for action in visual_actions(rows[i][2]) if action!='production'))
   score,si,sentence,words=rows.pop(best_i);norm=re.sub(r'\W+','',sentence.lower())
   if norm in seen:continue
   seen.add(norm);chosen.append({'text':sentence,'language':lang,'process_intent':process_intent,'source_index':si,'source_sentence':sentence,'score':score})
   used.update(topic_terms(sentence,lang));source_counts[si]=source_counts.get(si,0)+1
   for action in visual_actions(sentence):action_counts[action]=action_counts.get(action,0)+1
  if len(chosen)!=count:return []
  if opening is not None and not any(slot['text']==opening[2] for slot in chosen):
   chosen[-1]={'text':opening[2],'language':lang,'process_intent':process_intent,'source_index':opening[1],'source_sentence':opening[2],'score':opening[0]}
  if definition or scope or sum(measured_sentence_ms(slot['text'],lang) for slot in chosen)>target_ms-100:
   chosen=fit_narration(all_rows,count,lang,process_intent,target_ms,required_sentence=opening[2] if opening else None,natural=bool(definition),scope=scope if len(scope)<=4 else ())
   if len(chosen)!=count:return []
   for slot in chosen:slot['process_intent']=process_intent
  for slot in chosen:
   key=(slot['source_index'],slot['text']);slot['source_position']=source_positions[key];slot['source_sentence']=source_spans[key]
  if process_intent and not definition and not re.search(r'histor|ancient|истори|істор|dziej',topic,re.I):
   stage_order={'heat':0,'shape':1,'cool':2,'inspect':3}
   return sorted(chosen,key=lambda x:(max((stage_order[action] for action in visual_actions(x['text']) if action in stage_order),default=0),x['source_index'],x['source_position']))
  return sorted(chosen,key=lambda x:(0 if definition and x['source_index']==definition_index else 1,x['source_index'],x['source_position']))
def source_cache_key(topic,lang):
 return 'wikipedia-v14|'+lang+'|'+topic

def article_supports_query(article,query):
 required=grounding_terms(query,'en')
 if not required:return False
 title=article['title']
 # Model making and simulations describe a different subject from the
 # corresponding real-world activity unless that qualifier was requested.
 qualifiers=r'\b(?:scale models?|toys?|miniatures?|simulat\w*)\b'
 if re.search(r'^models?\b|'+qualifiers,title,re.I) and not re.search(r'\bmodels?\b|'+qualifiers,query,re.I):return False
 manufacture=r'\b(?:manufactur\w*|produc\w*|fabricat\w*|build\w*|built|assembl\w*|mak(?:e|es|ing))\b'
 needs_manufacture=bool(re.search(manufacture,query,re.I))
 return any(required<=grounding_terms(title+' '+paragraph,'en') and
            (not needs_manufacture or re.search(manufacture,title+' '+paragraph,re.I))
            for paragraph in article['text'].splitlines())

def translated_article(reference,lang,query=''):
 from source_translation import MODEL,article_view
 from storyboard import ensure_source
 title=reference['title']
 source={**reference,'visual_title':title}
 ensure_source([source],'en',sys.modules[__name__])
 if query and not article_supports_query(source,query):return []
 profile=entity_profile([source],'en')
 # Translated personal names need the native biography link resolver.
 if not profile.get('id') or profile.get('kind')=='human':return []
 source['entity_profile']=profile
 key='article-translation-v1|'+MODEL+'|'+lang+'|'+source['revision_url']
 def translate():
  view=article_view(source,lang,sentences)
  return {name:view[name] for name in ('text','source_language','translation_model','translated_spans')} if view else {}
 view=cache_fetch(key,translate)
 return [source|view] if view else []

def translated_research_sources(topic,lang,duration=None):
 from source_translation import QUERY_MODEL,configured_for,english_query,query_configured_for
 if not configured_for(lang):return []
 identifier=topic_identifier(topic)
 reference=identifier_article(identifier,lang) if identifier else {}
 if reference.get('language')=='en' and not reference.get('native_title'):
  return translated_article({**reference,'scoped_identifier':identifier},lang)
 if not query_configured_for(lang):return []
 query=cache_fetch('search-query-en|'+QUERY_MODEL+'|'+lang+'|'+topic,lambda:english_query(topic,lang))
 if not query:return []
 candidates=cache_fetch(source_cache_key(query,'en'),lambda:wikipedia(query,'en'))
 for candidate in candidates:
  if not article_supports_query(candidate,query):continue
  sources=translated_article({**candidate,'strict_translated_scope':True,'english_search_topic':query},lang,query)
  if sources and (duration is None or plan_script(sources,topic,lang,duration)):return sources
 return []

def load_sources(topic,lang,duration=None):
 current=ROOT/'cache'/(hashlib.sha256(source_cache_key(topic,lang).encode()).hexdigest()+'.json')
 try:
  sources=attach_native_aliases(relevant_sources(cache_fetch(source_cache_key(topic,lang),lambda:wikipedia(topic,lang)),topic,lang),lang)
  if not sources:return translated_research_sources(topic,lang,duration)
  if sources:
   from storyboard import ensure_source
   ensure_source(sources,lang,sys.modules[__name__])
   profile=entity_profile(sources,lang);sources[0]['entity_profile']=profile
   description=profile.get('native_description','').strip().rstrip('.')
   if description:description=sentences(description)[0].rstrip('.!?')
   label=profile.get('native_name','').strip()
   original=grounding_terms(topic,lang)
   known=' '.join([sources[0]['title']]+list(profile.get('labels',{}).values()))
   grounded=bool(source_match_rank(topic,sources[0]) or original&grounding_terms(known,lang)) or (lang=='en' and any(len(term)>=4 and any(word.startswith(term) and word[len(term):] in {'making','manufacturing','production','blowing'} for word in tokens(known)) for term in original))
   if description and label and grounded and 15<=len(description)<=220:
    definition=label[:1].upper()+label[1:]+' — '+description+'.'
    sources.append({'title':label+' — Wikidata','url':profile['source_url'],'text':definition,
                    'visual_title':sources[0].get('visual_title',''),
                    'source_type':'structured definition','label':label,'description':description})
  return sources
 except urllib.error.HTTPError as error:
  if error.code!=429:raise
  raise ValueError('Wikipedia temporarily rate-limited (HTTP 429); no saved sources for this topic') from error

def relevant_sources(sources,topic,lang):
 definitions=[source for source in sources if source.get('source_type')=='structured definition']
 sources=[source for source in sources if source.get('source_type')!='structured definition']
 terms=topic_terms(topic,lang)
 def stem(word):return word[:4] if not word.isascii() else word
 process_intent=bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 def title_rank(source):
  title=topic_terms(source['title'],lang)
  matched=sum(any(stem(a)==stem(b) or (process_intent and lang=='en' and len(a)>=4 and b.startswith(a) and b[len(a):] in {'making','manufacturing','production','blowing'}) for b in title) for a in terms)
  method=bool(process_intent and re.search(r'making|manufactur|production|produk|wytwarz|производ|изготов|виробниц|виготов',source['title'],re.I))
  return (source_match_rank(topic,source),matched,int(method),-len(title))
 ranked=sorted(sources,key=title_rank,reverse=True)
 if not ranked:return []
 anchor=ranked[0]
 topic_words={stem(word) for word in terms}
 def vocabulary(source):return {stem(word) for word in topic_terms(source['text'][:1800],lang) if len(word)>3}-topic_words
 basis=vocabulary(anchor)
 def same_name_other_sense(source):
  base=lambda title:re.sub(r'\s*\([^)]*\)\s*','',title).strip().casefold()
  return base(source['title'])==base(anchor['title']) and source['title'].casefold()!=anchor['title'].casefold()
 return [anchor]+[source for source in ranked[1:] if not same_name_other_sense(source) and len(basis&vocabulary(source))>=3]+definitions
def expand_source_blocks(slots,max_beats):
 expanded=[]
 for slot in slots:
  for text in sentences(slot['text']):
   row=dict(slot);row['text']=text;expanded.append(row)
 return expanded if len(expanded)<=max_beats else []

def order_process_slots(slots):
 # Preserve source claims while presenting physical stages in their causal order.
 stages={'production':-1,'mix':0,'heat':1,'melt':1,'shape':2,'drain':3,'press':4,'dry':5,'cool':6,'cut':7,'inspect':8}
 return sorted(slots,key=lambda slot:(min((stages[action] for action in scene_actions(slot['text'])),default=99),slot.get('source_index',0),slot.get('source_position',0)))

def identifier_scope_terms(text,lang):
 root_length=5 if lang in {'uk','ru'} else 4
 return {('company' if lang in {'uk','ru'} and re.match(r'^(?:ф[іи]рм|компан|підприєм|предприят)',term)
          else term if lang=='en' else term[:root_length]) for term in topic_terms(text,lang)}

def identifier_scope(sources,topic,lang):
 identifier=sources[0].get('scoped_identifier','') if sources else ''
 if not identifier and not (sources and sources[0].get('strict_translated_scope')):return set()
 scope=re.sub(r'\b(?:с помощью|за допомогою|za pomocą|by means of|using|ваш(?:а|ей|ої|у|е|его|ого|им|ими|их|і)?)\b',' ',topic,flags=re.I)
 return identifier_scope_terms(scope,lang)-identifier_scope_terms(identifier,lang)

def script_covers_identifier_scope(sources,topic,lang,slots):
 return identifier_scope(sources,topic,lang)<=identifier_scope_terms(' '.join(slot['text'] for slot in slots),lang)

def plan_script(sources,topic,lang,duration,max_beats=None,excluded_narrations=()):
 identifier=sources[0].get('scoped_identifier','') if sources else ''
 if sources and not sources[0].get('strict_translated_scope') and source_match_rank(topic,sources[0])==1:
  topic=sources[0]['title']
 process_intent=bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 structured=source_overview_mode(sources)
 limit=int(min(max_beats or 100,max(2,duration//5)))
 preferred=min(limit,max(2,int((max_beats*5 if max_beats else duration)//10)))
 counts=list(range(preferred,0,-1))+list(range(preferred+1,limit+1)) if structured else range(int(min(max_beats or 100,max(2,duration//(5 if process_intent else 7)))),1,-1)
 plans=[]
 for count in counts:
  slots=source_slots(sources,topic,count,lang,duration_s=duration)
  if len(slots)==count:
   if structured:
    expanded=expand_source_blocks(slots,int(max_beats or duration//5))
    if process_intent:expanded=order_process_slots(expanded)
    if expanded and script_covers_identifier_scope(sources,topic,lang,expanded) and (
        not excluded_narrations or narration_digest(lang,expanded) not in excluded_narrations):
     spoken=selected_voice_request(lang,' '.join(slot['text'] for slot in expanded))['input']['text']
     predicted=natural_duration_ms(spoken,lang)
     plans.append((abs(predicted-duration*950),abs(count-preferred),-sum(slot.get('score',0) for slot in expanded),expanded))
   elif script_covers_identifier_scope(sources,topic,lang,slots) and (
       not excluded_narrations or narration_digest(lang,slots) not in excluded_narrations):return slots
 if plans:return min(plans,key=lambda row:row[:3])[3]
 if sources and not process_intent and not identifier and not sources[0].get('strict_translated_scope'):
  canonical=sources[0]['title']
  if canonical.casefold()!=topic.casefold():
   slots=plan_script(sources,canonical,lang,duration,max_beats=max_beats,excluded_narrations=excluded_narrations)
   for slot in slots:slot['resolved_topic']=canonical
   return slots
 return []

def shot_beats(shot_count,beat_count):
 if beat_count<1 or shot_count<2*beat_count:raise ValueError('storyboard requires at least two images per narration beat')
 return [index*beat_count//shot_count for index in range(shot_count)]

class ShotCapacityError(ValueError):pass

def storyboard_beats(shot_count,slots):
 counts=[2]*len(slots)
 if sum(counts)>shot_count:raise ValueError('At least two scene images are required per narration beat')
 weights=[0 if slot.get('visual_role')=='establishing' else max(1,len(slot['text'])) for slot in slots]
 for _ in range(shot_count-sum(counts)):
  eligible=[i for i,slot in enumerate(slots) if counts[i]<slot.get('visual_shot_cap',2 if slot.get('visual_role')=='establishing' and slot.get('entity_profile',{}).get('kind')=='human' else shot_count)]
  if not eligible:raise ShotCapacityError('Verified scene capacity cannot cover all required images')
  index=max(eligible,key=lambda i:weights[i]/max(1,counts[i]-1))
  counts[index]+=1
 return [i for i,count in enumerate(counts) for _ in range(count)]

def photo_search(topic,lang):
 found=[];errors=[];pex=(PROVIDERS.get('Pexels API') or {}).get('value','').strip();pix=(PROVIDERS.get('Pixabay API') or {}).get('value','').strip()
 if pex:
  try:
   locale={'en':'en-US','pl':'pl-PL','ru':'ru-RU','uk':'uk-UA'}[lang];q=urllib.parse.urlencode({'query':topic,'per_page':80,'locale':locale})
   data=cache_fetch('pexels-all-v2|'+lang+'|'+topic,lambda:http_json('https://api.pexels.com/v1/search?'+q,{'Authorization':pex},25))
   for x in data.get('photos') or []:
    src=x.get('src') or {};url=src.get('original') or src.get('large2x') or src.get('large')
    if url and src.get('original'):
     parsed=urllib.parse.urlsplit(url);query=dict(urllib.parse.parse_qsl(parsed.query));query.update({'auto':'compress','cs':'tinysrgb','w':'1600'})
     for key in ('h','fit','crop'):query.pop(key,None)
     url=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urllib.parse.urlencode(query),''))
    if url:found.append({'provider':'pexels','id':str(x.get('id')),'alt':x.get('alt') or '','query':topic,'url':url,'source_url':x.get('url') or '','creator':x.get('photographer') or '','creator_url':x.get('photographer_url') or '','width':int(x.get('width') or 0),'height':int(x.get('height') or 0)})
  except Exception as e:errors.append('Pexels unavailable (HTTP '+str(getattr(e,'code','request error'))+')')
 if pix:
  try:
   q=urllib.parse.urlencode({'key':pix,'q':topic,'lang':lang if lang in {'en','pl','ru'} else 'en','image_type':'photo','safesearch':'true','per_page':200})
   data=cache_fetch('pixabay-all-v2|'+lang+'|'+topic,lambda:http_json('https://pixabay.com/api/?'+q,timeout=25))
   for x in data.get('hits') or []:
    url=x.get('largeImageURL') or x.get('webformatURL')
    if url:found.append({'provider':'pixabay','id':str(x.get('id')),'alt':x.get('tags') or '','query':topic,'url':url,'source_url':x.get('pageURL') or '','creator':x.get('user') or '','creator_url':'https://pixabay.com/users/'+urllib.parse.quote(str(x.get('user') or ''))+'/','width':int(x.get('imageWidth') or x.get('webformatWidth') or 0),'height':int(x.get('imageHeight') or x.get('webformatHeight') or 0)})
  except Exception as e:errors.append('Pixabay unavailable (HTTP '+str(getattr(e,'code','request error'))+')')
 unique={}
 for x in found:
  key=(x['provider'],x['id'])
  if key not in unique and x['width']>=640 and x['height']>=640:unique[key]=x
 if not unique:raise ValueError('; '.join(errors) if errors else 'photo search returned no usable results')
 return list(unique.values())
def plain_metadata(value):
 parser=WikiHTML();parser.feed(str(value or ''))
 return re.sub(r'\s+',' ',parser.text()).strip()
OUTPUT_LICENSE={'name':'CC BY-SA 4.0','url':'https://creativecommons.org/licenses/by-sa/4.0/'}
COMMONS_ONLY=True

def supported_commons_license(name,url,artist):
 allowed={'Public domain','CC0','CC BY 2.0','CC BY 2.5','CC BY 3.0','CC BY 4.0','CC BY-SA 3.0','CC BY-SA 4.0'}
 if name not in allowed:return False
 if name.startswith('CC BY') and (not url or not artist):return False
 if name.startswith('CC BY-SA'):
  parsed=urllib.parse.urlsplit(url);expected='/licenses/by-sa/'+name.rsplit(' ',1)[-1]
  if parsed.scheme not in {'http','https'} or parsed.hostname!='creativecommons.org' or not (parsed.path.rstrip('/')==expected or parsed.path.startswith(expected+'/')):return False
 return True

def output_credits(sources,visuals):
 text=[]
 for source in sources:
  structured=source.get('source_type')=='structured definition'
  text.append({'title':source['title'],'source_url':source.get('revision_url') or source['url'],'authors':'Wikidata contributors' if structured else 'Wikipedia contributors','license':'CC0' if structured else 'CC BY-SA 4.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/' if structured else OUTPUT_LICENSE['url'],'changes':'Selected source excerpts; parentheses and punctuation may be normalized; narrated and captioned.'})
  if source.get('translation_model'):text[-1]['changes']='Selected source sentences, machine-translated, narrated and captioned.'
 media=[{'title':row.get('depiction') or row['alt'],'author':row['creator'],'source_url':row['source_url'],'license':row['license'],'license_url':row.get('license_url'),'changes':row.get('changes','Resized and captioned.')} for row in visuals]
 return {'adaptation_license':OUTPUT_LICENSE,'text':text,'media':media,'scope':'Factory contributions to this video adaptation; original component licence notices remain applicable.'}

COMMONS_IMAGE_FIELDS={'action':'query','prop':'imageinfo|categories','cllimit':'50','iiprop':'url|size|extmetadata','iiurlwidth':1280,'format':'json'}

def commons_photo_candidates(data,query):
 found=[]
 for page in sorted((data.get('query') or {}).get('pages',{}).values(),key=lambda x:x.get('index',999)):
  for im in page.get('imageinfo',[]):
   meta=im.get('extmetadata') or {}
   get=lambda key:plain_metadata((meta.get(key) or {}).get('value',''))
   license_name=get('LicenseShortName');license_url=get('LicenseUrl')
   if not supported_commons_license(license_name,license_url,get('Artist')):continue
   original_url=im.get('url','');original_size=int(im.get('size') or 0);pixels=int(im.get('width') or 0)*int(im.get('height') or 0)
   prefer_original=0<original_size<=4_000_000 and 0<pixels<=20_000_000 and urllib.parse.urlsplit(original_url).path.lower().endswith(('.jpg','.jpeg','.png','.webp'))
   url=original_url if prefer_original else im.get('thumburl') or original_url;host=urllib.parse.urlparse(url).hostname
   if host not in {'upload.wikimedia.org','thumb.wikimedia.org'}:continue
   width=int(im.get('thumbwidth') or im.get('width') or 0);height=int(im.get('thumbheight') or im.get('height') or 0)
   if min(width,height)<640:continue
   source='https://commons.wikimedia.org/w/index.php?curid='+str(page['pageid'])
   found.append({'provider':'commons','categories':[category['title'] for category in page.get('categories',[])],'id':str(page['pageid']),'alt':plain_metadata(page.get('title',''))+' '+get('ImageDescription'),'depiction':plain_metadata(page.get('title','')),'query':query,'url':url,'original_url':original_url,'original_size':original_size,'original_pixels':pixels,'source_url':source,'creator':get('Artist') or get('Credit') or 'Wikimedia Commons','creator_url':im.get('descriptionurl') or source,'width':width,'height':height,'license':license_name,'license_url':license_url,'changes':'resized and composited with narration captions'})
 return found

def commons_search(query,limit=20):
 params=urllib.parse.urlencode({**COMMONS_IMAGE_FIELDS,'generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':max(1,min(50,int(limit)))})
 data=cache_fetch('commons-v4|'+str(limit)+'|'+query,lambda:http_json('https://commons.wikimedia.org/w/api.php?'+params,timeout=25))
 return commons_photo_candidates(data,query)

def article_photo_candidates(source):
 url=urllib.parse.urlsplit(source['url']);revision=source.get('revision_id')
 language=(url.hostname or '').removesuffix('.wikipedia.org')
 if url.scheme!='https' or url.hostname!=language+'.wikipedia.org' or not re.fullmatch('[a-z][a-z-]{0,15}',language) or not isinstance(revision,int) or revision<1:return []
 reference='https://'+url.hostname+'/w/index.php?oldid='+str(revision)
 def retrieve():
  params=urllib.parse.urlencode({'action':'parse','oldid':revision,'prop':'images','format':'json'})
  files=http_json('https://'+url.hostname+'/w/api.php?'+params,timeout=15).get('parse',{}).get('images',[])
  titles=list(dict.fromkeys('File:'+filename for filename in files if re.search(r'\.(?:jpe?g|png|webp)$',filename,re.I)))[:36]
  if not titles:return []
  params=urllib.parse.urlencode({**COMMONS_IMAGE_FIELDS,'titles':'|'.join(titles),'redirects':1})
  data=http_json('https://commons.wikimedia.org/w/api.php?'+params,timeout=20)
  # Commons resolves every file's license and attribution independently.
  return [{**row,'article_media_revision':reference} for row in commons_photo_candidates(data,reference)]
 return cache_fetch('article-commons-v1|'+reference,retrieve)

def visual_context_title(slot,sources,lang):
 # Match the native-language fact to article introductions, then use their English titles.
 mapped=[source for source in sources if source.get('visual_title') and all(year in slot['text'] for year in re.findall(r'\b\d{4}\b',source['title']))]
 if not mapped:return slot.get('visual_title','')
 corpus=[set(topic_terms(source['title']+' '+source['text'][:1800],lang)) for source in mapped]
 weights={term:math.log(1+len(corpus)/(1+sum(term in doc for doc in corpus))) for doc in corpus for term in doc}
 query=set(topic_terms(slot['text'],lang))
 scores=[sum(weights.get(term,0)**2 for term in query&doc)/max(1,sum(weights[term]**2 for term in doc))**.5 for doc in corpus]
 return mapped[max(range(len(mapped)),key=lambda index:scores[index])]['visual_title']
def scoped_visual_title(slot,sources,lang):
 primary=sources[0]
 base=grounding_terms(primary['title'],lang);words=grounding_terms(slot['text'],lang)
 choices=[]
 for source in sources[1:]:
  if source.get('source_type')=='structured definition' or not source.get('visual_title'):continue
  extra=grounding_terms(source['title'],lang)-base
  if 1<=len(extra)<=2 and extra<=words:choices.append((len(extra),source['visual_title']))
 return max(choices,key=lambda item:item[0])[1] if choices else primary.get('visual_title','')

def media_search_topic(topic,lang,sources):
 structured=source_overview_mode(sources)
 process=bool(re.search(r'made|making|manufactur|produc|дела|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 if structured:
  if process and lang=='en':return ' '.join(dict.fromkeys(topic_terms(topic,'en')))+' manufacturing'
  title=sources[0].get('visual_title') or (sources[0]['title'] if lang=='en' else '')
  if title:
   if process and re.search(r'making$',title,re.I):return re.sub(r'making$','',title,flags=re.I).strip()+' manufacturing'
   return title
 if lang=='en':
  if sources and not set(topic_terms(topic,'en'))&set(topic_terms(sources[0]['title'],'en')):return sources[0].get('visual_title') or sources[0]['title']
  return topic
 terms=topic_terms(topic,lang)
 def relevance(source):
  title_terms=topic_terms(source['title'],lang)
  matched=sum(any(a==b or (len(a)>=4 and len(b)>=4 and a[:4]==b[:4]) for b in title_terms) for a in terms)
  return (matched,-len(title_terms))
 mapped=sorted([source for source in sources if source.get('visual_title')],key=relevance,reverse=True)
 title=mapped[0]['visual_title'] if mapped else ''
 if not title:raise ValueError('source articles have no English interlanguage title for visual discovery')
 if re.search(r'made|making|manufactur|produc|дела|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I):title+=' manufacturing'
 return title

def visual_queries(topic,lang,slots):
 core=list(dict.fromkeys(topic_terms(topic,lang)));queries=[topic]
 if slots and slots[0].get('source_driven'):
  titles=[slot.get('visual_title') for slot in slots if slot.get('visual_title')]
  if slots[0].get('process_intent'):
   subject=slots[0].get('entity_profile',{}).get('name') or ' '.join(core)
   industry=[subject+' mill'] if 'mill' in slots[0].get('entity_profile',{}).get('visual_vocabulary',[]) else []
   stages=[subject+' '+STAGE_QUERIES[next(iter(scene_actions(slot['text'])))] for slot in slots if scene_actions(slot['text'])!={'production'}]
   return list(dict.fromkeys(stages+[topic]+titles+industry+[subject+' '+term for term in ['factory','manufacturing','handmade','workshop','production machinery']]))[:7]
  return list(dict.fromkeys([topic]+titles))[:7]
 labels={'heat':'melting furnace','shape':'forming molding','cool':'annealing','inspect':'quality inspection','production':'manufacturing'}
 needed=set().union(*(visual_actions(slot['text']) if slot.get('process_intent',True) else set() for slot in slots))
 for action in ('inspect','cool','shape','heat','production'):
  if action not in needed:continue
  query=' '.join(core[:6]+[labels[action]])[:100]
  if query.casefold() not in {item.casefold() for item in queries}:queries.append(query)
 for slot in slots:
  if len(queries)>=7:break
  title=slot.get('visual_title','').strip()
  if title and title.casefold() not in {query.casefold() for query in queries}:queries.append(title)
 return queries[:7]

def media_aliases(topic):
 def retrieve():
  q=urllib.parse.urlencode({'action':'query','titles':topic,'prop':'redirects','rdlimit':'20','format':'json','formatversion':'2'})
  data=http_json('https://en.wikipedia.org/w/api.php?'+q,timeout=22)
  pages=(data.get('query') or {}).get('pages') or []
  names=[redirect['title'] for page in pages for redirect in page.get('redirects',[]) if redirect.get('ns',0)==0]
  result=[topic];seen={frozenset(tokens(topic))}
  for name in sorted(names,key=lambda text:(len(tokens(text)),text)):
   key=frozenset(tokens(name))
   if key and key not in seen and 1<=len(key)<=4 and '(' not in name:result.append(name);seen.add(key)
   if len(result)>=3:break
  return result
 try:return cache_fetch('visual-aliases-v1|'+topic,retrieve)
 except Exception:return [topic]
SEARCH_QUERIES={'stock':set(),'commons':set()}
DISCOVERED_PHOTOS={}
def named_astronomical_subject(profile):
 if profile.get('kind')!='entity':return False
 description=profile.get('visual_description','').strip().lower()
 pattern=r'^(?:(?:the|a|an|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|dwarf|minor|terrestrial|spiral|barred|elliptical|binary|variable|red|blue|yellow|white|giant|natural|main-sequence)\s+){0,5}(?:planet|star|galaxy|moon|satellite|nebula|asteroid|comet)\b'
 return bool(re.search(pattern,description) or re.match(r"^[\w-]+['’]s (?:only )?natural satellite\b",description))

def astronomical_identifiers(text):
 # Catalog designations are language-independent and can identify the
 # particular object discussed in an otherwise broad astronomy overview.
 pattern=r'(?<!\w)(SN)[ -]?(\d{4}[a-z]{1,3})(?!\w)|(?<!\w)(NGC|IC|Messier)[ -]?(\d{1,5})(?!\w)'
 return {' '.join(part.upper() for part in match.groups() if part) for match in re.finditer(pattern,text,re.I)}

def scene_astronomical_identifiers(slot):
 profile=slot.get('entity_profile',{})
 description=profile.get('visual_description','')
 if named_astronomical_subject(profile) or re.search(r'\b(?:astronomical|stellar|galax(?:y|ies)|star|nebula|supernova|constellation)\b',description,re.I):
  return astronomical_identifiers(slot.get('text',''))
 return set()

def century_labels(text):
 from alignment_core import _roman_numeral_to_int
 matches=re.findall(r'(?<!\w)([IVXLC]{1,6}|\d{1,2})(?:st|nd|rd|th|[-–.]?[йяийго]{1,2})?\.?\s*(?:centur(?:y|ies)|wiek\w*|століт\w*|столет\w*|век\w*)(?!\w)',text,re.I)
 return {int(value) if value.isdigit() else _roman_numeral_to_int(value.upper()) for value in matches}

def artifact_scene_centuries(slot):
 description=slot.get('entity_profile',{}).get('visual_description','')
 if re.search(r'\b(?:instrument|device|machine|tool|apparatus)\b',description,re.I):
  return century_labels(slot.get('text',''))
 return set()

def artifact_photo_centuries(photo):
 title=photo.get('depiction','')
 description=photo.get('alt','').removeprefix(title).strip()
 # Prefer the file title when it dates the object. The first caption sentence
 # is the archival description rather than an arbitrary year elsewhere.
 first=next(iter(sentences(description)),'')
 dated_description=re.search(r'\b(?:made|built|manufactured|crafted|produced|constructed|dates?) (?:in|to|from) (.{1,32})',first,re.I)
 context=title if century_labels(title) or re.search(r'\b[12]\d{3}\b',title) else dated_description.group(1) if dated_description else ''
 return century_labels(context)|{(int(year)-1)//100+1 for year in re.findall(r'\b[12]\d{3}\b',context)}

def named_place_subject(profile):
 return profile.get('kind')=='entity' and bool(re.search(r'\b(?:city|town|village|capital|municipality|country|island|mountain|national park|palace|castle|cathedral|monument)\b',profile.get('visual_description',''),re.I))

def incidental_place_event(text,topic,profile):
 # Present-day views can illustrate geography, but cannot establish a
 # dated trial, battle or other incidental historical event.
 event=r'\b(?:trials?|battles?|sieges?|uprisings?|treaties|treaty|wars?|occup\w*|founded|first mention\w*|proces\w*|bitw\w*|oblęż\w*|powstan\w*|traktat\w*|wojn\w*|założ\w*|wzmiank\w*|суд\w*|битв\w*|осад\w*|облог\w*|восстан\w*|повстан\w*|войн\w*|війн\w*|окупац\w*|оккупац\w*|заснув\w*|основан\w*|згадк\w*|упоминани\w*)\b'
 date=r'\b(?:[1-9]\d{2}|[12]\d{3})\b'
 early_year=r'\b(?:in|from|since|until|w|we|z|od|do|в|у|з|с|до)\s+(?:(?:the year|roku|року|года)\s+)?1[0-8]\d{2}\b(?![.,]\d|\s*(?:(?:km|mi|m|metres?|meters?|metr\w*|км|м|метр\w*)\b|м²))'
 historical_brief=r'\b(?:histor\w*|ancient|medieval|dziej\w*|średniowiecz\w*|истори\w*|істор\w*|древн\w*|середньовіч\w*)\b'
 historic_assembly=r'\b(?:general sejm|sejm\w* waln\w*|вальн\w* сейм\w*)\b'
 return bool(named_place_subject(profile) and not re.search('|'.join((event,date,historical_brief,historic_assembly)),topic,re.I)
             and not century_labels(topic)
             and (re.search(early_year,text,re.I) or re.search(historic_assembly,text,re.I)
                  or any(century<20 for century in century_labels(text))
                  or (re.search(date,text) and re.search(event,text,re.I))))

PLACE_FEATURES={
 'river':r'\b(?:rivers?|riverbank\w*|Vistula|Wisł\w*|Wisla|rzek\w*|річк\w*|рек\w*|рік[аиу])\b',
 'escarpment':r'\b(?:escarpments?|bluffs?|steep slope\w*|skarp\w*|урвищ\w*|круч\w*|обрыв\w*|откос\w*)\b',
 'bridge':r'\b(?:bridges?|most(?:u|y|em|ów|ach|ami)|міст(?:ок|ки)|мост\w*)\b',
}

def place_scene_features(text,lang=None):
 features=[feature for feature,pattern in PLACE_FEATURES.items() if re.search(pattern,text,re.I)]
 if lang=='pl' and 'bridge' not in features and re.search(r'\bmost\b',text,re.I):features.append('bridge')
 return features

INSECT_SCENE_FEATURES={
 'antennae':r'\b(?:antenna(?:e|s)?|antennal|czułk\w*|вусик\w*|усик\w*)\b',
 'wings':r'\b(?:wings?|winged|skrzydł\w*|крил\w*|крыл\w*)\b',
 'stinger':r'\b(?:sting(?:er|ers|ing)?|żądł\w*|жал[аоу]|жалом)\b',
 'waggle dance':r'\b(?:waggle dance|bee dance|dance of (?:the )?bees|taniec pszcz\w*|танц\w*|танок)\b',
 'fossil':r'\b(?:fossils?|fossilized|skamieniałoś\w*|скам[’\x27]яніл\w*|окаменел\w*)\b',
 'brood':r'\b(?:brood|larv\w*|eggs?|czerw(?:iu|ia|ie|iem)?|larw\w*|jaj(?:a|ka|ek|ko)|личин(?:ок|к\w*)|яйц\w*|молодняк\w*)\b',
 'queen':r'\b(?:queen(?: bee)?|queen ant|queen wasp|królow\w*|matk\w* pszczel\w*|матк\w*|бджол[ауиі]-мат[іе]\w*)\b',
 'pollen':r'\b(?:pollen|pollen basket\w*|pył(?:ek|ku|kiem)|пил(?:ок|ку|ком)|пыльц\w*)\b',
 'proboscis':r'\b(?:proboscis|proboscides|trąbk\w*|хобот\w*)\b',
 'honey production':r'\b(?:honeycomb\w*|honey (?:extraction|production|processing|stores?)|(?:make|produce|store|extract|harvest)\w* honey|produkcj\w* miodu|plastry miodu|переробл\w*\b.{0,40}\b(?:на|в|у) мед|виробля\w* мед|виробництв\w* меду|пчелиные соты|производ(?:ств\w* м[её]да|ится м[её]д)|кг меду)\b',
 'pollination':r'\b(?:pollinat\w*|foraging|(?:drinking|collecting) nectar|on (?:a |the )?flower\w*|zapyl\w*|(?:за|об)пил\w*|опыл\w*)\b',
 'carrion feeding':r'\b(?:carrion|vulture bees?|padlin\w*|падал(?:ь|і|лю|ью))\b',
 'predation':r'\b(?:predat\w*|prey|eating a (?:bee|wasp|fly)|drapież\w*|ofiar\w*|жертв\w*|здобич\w*|прогодуван\w* птах\w*|хищн\w*|павук\w*)\b',
 'solitary insects':r'\b(?:solitary (?:bees?|wasps?|insects?)|samotnicz\w*|одиночн\w*)\b',
 'insect colony':r'\b(?:hive|beehive|insect colony|colony of bees|swarm of bees|kolektyw\w*|колективн\w* утворенн\w*|колони\w* пч[её]л|бджолин\w* колоні\w*)\b',
}

def insect_scene_features(text):
 return [feature for feature,pattern in INSECT_SCENE_FEATURES.items() if re.search(pattern,text,re.I)]

def insect_subject(profile):
 return bool(re.search(r'\binsects?\b',profile.get('visual_description',''),re.I))

def insect_photo_identity(candidate,profile):
 names=[profile.get('name',''),profile.get('native_name',''),*profile.get('aliases',[])]
 groups=[set(tokens(name)) for name in names if tokens(name)]
 if not groups:return True
 title=candidate.get('depiction','')
 description=candidate.get('alt','').removeprefix(title).strip()
 fields=[title,description[:150],*semantic_categories(candidate)]
 for field in fields:
  words=set(tokens(field))
  # A compound common name still identifies its parent insect group.
  if words&{'honeybee','bumblebee','stinglessbee','carpenterbee'}:words.add('bee')
  if any(group<=words for group in groups):return True
 return False

VOLCANIC_FEATURES={
 'eruption':(r'\b(?:erupt\w*|ash plume|ash cloud|erupcj\w*|wybuch\w*|виверж\w*|изверж\w*|вулканічн\w* поп[іе]л\w*|вулканическ\w* пепел\w*)\b','an erupting volcano with a visible ash plume or lava fountain'),
 'lava flow':(r'\b(?:lava flows?|molten lava|law[ayę] (?:płyn\w*|spływ\w*)|(?:потік|поток\w*) лав[иы]|лавов\w* (?:потік|поток\w*))\b','a lava flow or its solidified channel in a volcanic landscape'),
 'crater':(r'\b(?:craters?|calderas?|kratery?|krater\w*|kalder\w*|кратер\w*|кальдер\w*)\b','a volcanic crater or caldera seen from above or from its rim'),
 'fumarole':(r'\b(?:fumarol\w*|фумарол\w*)\b','a visible steam vent on a volcanic slope'),
}

def volcanic_subject(profile):
 landform=r'(?:(?:strato|super)?volcano(?:es)?|volcanism|calderas?|volcanic (?:landform|island|crater lake))'
 if re.fullmatch(landform,profile.get('name',''),re.I):return True
 modifiers=r'(?:(?:an?|the|active|inactive|extinct|dormant|submarine|underwater|shield|ancient|small|large|quaternary|complex|composite)\s+)*'
 description=profile.get('visual_description','')
 return bool(re.match(modifiers+landform+r'\b',description,re.I) or re.search(r'\bvolcanic (?:island )?caldera\b',description))

def volcanic_features(text):
 return [feature for feature,(pattern,_) in VOLCANIC_FEATURES.items() if re.search(pattern,text,re.I)]

def conflicting_insect_identity(candidate,profile,features=()):
 # Hoverflies are often photographed on the same flowers as bees. Use the
 # named subject in the caption, before keyword and category lists.
 if not re.fullmatch(r'bees?',profile.get('name',''),re.I):return False
 title=candidate.get('depiction','')
 description=candidate.get('alt','').removeprefix(title).lstrip()
 identity=title+' '+description[:110]
 different_species=r'\b(?:hoverfl(?:y|ies)|(?:drone|bee)[ -]fl(?:y|ies)|Eristalis|Syrphidae|Bombyliidae|Bombylius|bee mimics?|bee or wasp|(?:it is|possibly|probably) a wasp|ant with wings)\b'
 incidental_bee=r'\b(?:ant lifting|dead bee|spider with (?:bee )?prey)\b'
 return bool(re.search(different_species,identity,re.I) or ('predation' not in features and re.search(incidental_bee,identity,re.I)))

def place_detail_query(slot,profile):
 if slot.get('place_features'):
  return ' '.join([profile.get('native_name') or profile['name'],*slot['place_features']])
 words=re.findall(r"[^\W\d_]+",slot['text'],re.UNICODE)
 names={name.casefold() for name in list(profile.get('labels',{}).values())+[profile.get('name','')]}
 for index in range(1,len(words)-1):
  pair=words[index:index+2]
  if all(word.istitle() for word in pair) and not any(word.casefold() in names for word in pair):
   return ' '.join(pair)+' '+(profile.get('native_name') or profile['name'])
 return ''

def place_identity(p,profile):
 if p.get('provider')!='commons':return False
 names=[profile.get('name',''),profile.get('native_name','')]+list(profile.get('labels',{}).values())
 categories=' | '.join(p.get('categories',[]))
 return any(name and re.search(r'(?<!\w)'+re.escape(name)+r'(?!\w)',categories,re.I) for name in names)

def bind_place_images(candidates,profile):
 commons=[p for p in candidates if p.get('provider')=='commons']
 for start in range(0,len(commons),50):
  batch=commons[start:start+50];ids='|'.join(p['id'] for p in batch)
  def retrieve():
   params={'action':'query','pageids':ids,'prop':'categories','cllimit':'max','format':'json'}
   found={}
   for _ in range(4):
    data=http_json('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params),timeout=20)
    for page in data.get('query',{}).get('pages',{}).values():
     found.setdefault(str(page['pageid']),[]).extend(c['title'] for c in page.get('categories',[]))
    continuation=data.get('continue')
    if not continuation:break
    params.update(continuation)
   return found
  categories=cache_fetch('commons-place-categories-v1|'+ids,retrieve)
  for p in batch:p['categories']=list(dict.fromkeys(p.get('categories',[])+categories.get(p['id'],[])))
 return candidates

def semantic_categories(candidate):
 return [category for category in candidate.get('categories',[]) if not re.search(r'\b(?:from|via|uploaded|taken with|photographs by|images by|files by|press photographs?|press photos?|published in)\b',category,re.I)]

def photographic_metadata(p):
 title=p.get('depiction','')
 description=p.get('alt','').removeprefix(title).strip()
 overlays=r'\b(?:added (?:text |color(?:ed)? )?(?:labels|arrows)|(?:modified|marked|overlaid) (?:the )?(?:image |photo(?:graph)? )?with (?:text |color(?:ed)? )?(?:labels|arrows))\b'
 if re.search(overlays,description+' '+p.get('creator',''),re.I):return False
 if re.search(r'\b(?:annotated|labeled|labelled|infographic|montage|multi.panel|before(?:[ _-]+and)?[ _-]+after)\b',title,re.I):return False
 nonphoto=r'\b(?:shows?|showing|displays?|plots?|depicts?) (?:a |an |the )?(?:spectrum|(?:light.?curve|spectral|intensity) plot|graph)\b|\b(?:inset(?: [a-z-]+){0,2} images?|series of [a-z]+ panels)\b|\[(?:top|bottom) (?:left|right)\]'
 if re.search(nonphoto,description[:950],re.I):return False
 # Match creator disclosures about this asset, including scientific archives
 # whose titles describe the subject but omit the production method.
 if re.search(r'\b(?:simulation (?:frames?|still|image)|still(?: frame)? from (?:a |an |the )?(?:planetarium show|animation|simulation)|(?:done|made|created|rendered|model(?:l)?ed) (?:in|with|using) (?:Blender|PlanetMaker|Cinema 4D|3ds Max|Maya)|procedural textures)\b',description[:950],re.I):return False
 if re.search(r'\b(?:image (?:has been |is )annotated|annotated to highlight|comparison star|(?:two|three|four) images (?:of .*? )?(?:are (?:shown|seen)|show)|multiple panels)\b',description[:750],re.I):return False
 if len(set(re.findall(r'(?:^|[.!?]\s+)\(([A-H])\)\s+[A-Z]',description[:950])))>=3:return False
 text=p.get('depiction','')+' '+p.get('alt','')+' '+p.get('creator','')+' '+' '.join(p.get('categories',[]))
 if re.search(r'\bfig(?:ure)?[. ]+\s*\d+\b',p.get('depiction',''),re.I):return False
 return not re.search(r'\.svg\b|\b(?:logos?|wordmarks?|icons?|calendars?|scrapbooks?|advertisements?|advertising banners?|promotional graphics?|flyers?|fliers?|brochures?|signatures?|autographs?|handwriting|diagrams?|charts?|graphs?|graphique|caricatures?|cartoons?|source code|maps?|mapa|mapy|plan|карта|мапа|document|letterhead|billhead|invoice|certificate|patent|schematic|collage|montage|topographic map|drawing|illustration|woodcut|engraving|lithograph|painting|poster|computer.generated|CGI|artist[’\x27]?s? (?:impression|concept|rendering)|(?:3d|3-d|3 d) (?:render\w*|model\w*)|digital art\w*|ai.generated|wykres|schemat|rysunek|график|схема|діаграма|малюнок)\b',text,re.I)

def discover_photos(topic,lang,slots):
 pool=dict(DISCOVERED_PHOTOS);errors=[]
 profile=slots[0].get('entity_profile',{}) if slots else {}
 aliases=list(dict.fromkeys(alias for slot in slots for alias in slot.get('topic_aliases',[])))
 for query in ([] if COMMONS_ONLY or profile.get('kind')=='human' or named_astronomical_subject(profile) or named_place_subject(profile) else list(dict.fromkeys(visual_queries(topic,lang,slots)+aliases))[:7]):
  key=query.casefold().strip()
  if key not in SEARCH_QUERIES['stock'] and len(SEARCH_QUERIES['stock'])>=7:continue
  SEARCH_QUERIES['stock'].add(key)
  try:
   for candidate in photo_search(query,lang):pool.setdefault((candidate['provider'],candidate['id']),candidate)
  except Exception as e:
   if getattr(e,'code',None) in {429,503}:raise
   errors.append(str(e))
 # Commons supplements source-backed technical images, with a separate three-query bound.
 core_terms=list(dict.fromkeys(topic_terms(topic,lang)))
 core=' '.join(core_terms[:1])
 actions=set() if slots and slots[0].get('source_driven') else set().union(*(visual_actions(slot['text']) if slot.get('process_intent',True) else set() for slot in slots))
 labels={'heat':'furnace','shape':'forming','cool':'annealing','inspect':'inspection','production':'manufacturing'}
 queries=[((' '.join(core_terms) if action=='inspect' else core)+' '+labels[action]).strip() for action in ('cool','inspect','heat','shape','production') if action in actions][:3]
 if named_astronomical_subject(profile):
  terrain=bool(re.search(r'\b(?:planet|moon|satellite)\b',profile.get('visual_description',''),re.I))
  queries=([('incategory:"'+profile['commons_category']+'"')] if profile.get('commons_category') else [topic+' NASA'])+[topic+' rover panorama NASA',topic+' ESA photograph'] if terrain else [topic+' NASA',topic+' ESA',topic+' ESO']
 if slots and slots[0].get('source_driven') and slots[0].get('process_intent'):
  category=profile.get('commons_category')
  queries=([('incategory:"'+category+'"')] if category else [])+[topic+' machinery',' '.join(core_terms)+(' mill interior' if 'mill' in profile.get('visual_vocabulary',[]) else ' handmade')]
  stages=[(profile.get('name') or ' '.join(core_terms))+' '+STAGE_QUERIES[next(iter(scene_actions(slot['text'])))] for slot in slots if scene_actions(slot['text'])!={'production'}]
  actions_needed=list(dict.fromkeys(next(iter(scene_actions(slot['text']))) for slot in slots if scene_actions(slot['text'])!={'production'}))
  stages += [' '.join(core_terms)+' '+STAGE_QUERY_TOOLS[action][index] for index in range(2) for action in actions_needed]
  queries=list(dict.fromkeys(queries[:3]+stages))[:12]
 if named_place_subject(profile):
  name=profile['name']
  details=list(dict.fromkeys(slot.get('place_detail_query') for slot in slots if slot.get('place_detail_query')))
  queries=([name+' panorama incategory:"CC-BY-3.0"']+details+[name+' panorama incategory:"CC-BY-4.0"'])[:8]
 if profile.get('kind')=='concept' and slots and not slots[0].get('process_intent'):
  queries=([('incategory:"'+profile['commons_category']+'"')] if profile.get('commons_category') else [])+[topic+' photograph',topic]
 if insect_subject(profile):
  details=list(dict.fromkeys(feature for slot in slots for feature in slot.get('insect_features',[])))
  queries=[topic+' '+feature for feature in details]+queries
 if volcanic_subject(profile):
  details=list(dict.fromkeys(feature for slot in slots for feature in slot.get('volcanic_features',[])))
  queries=[topic+' '+feature for feature in details]+queries
 if profile.get('kind')=='human':
  name=profile['name'];category=profile.get('commons_category') or name
  exclude=' -intitle:Caricature -intitle:graph'
  subject='haswbstatement:P180='+profile['id'] if re.fullmatch(r'Q[1-9][0-9]*',profile.get('id','')) else name+' portrait'
  queries=[subject,name+' incategory:"CC-BY-2.0"'+exclude,'intitle:"'+name+'" incategory:"CC-BY-4.0"'+exclude]
 from storyboard import query_plan
 scene_queries=query_plan(slots)
 if scene_queries:queries=list(dict.fromkeys(queries[:8 if volcanic_subject(profile) else 2]+scene_queries))[:48]
 commons_limit=3
 if scene_queries:commons_limit=48
 elif slots and slots[0].get('process_intent'):commons_limit=12
 elif named_place_subject(profile) or insect_subject(profile) or volcanic_subject(profile):commons_limit=8
 elif slots and slots[0].get('source_driven') and slots[0].get('requested_shots',0)>=18:
  # Long overviews need a wider pool of separately licensed photographs.
  commons_limit=8
 if slots and slots[0].get('english_search_topic') and not (scene_queries or named_place_subject(profile) or named_astronomical_subject(profile)):
  # Search the verified article title and the original scoped research query.
  # A translated technical title alone may miss common names in image metadata.
  scoped=slots[0]['english_search_topic']
  commons_limit=max(commons_limit,5)
  keywords=' '.join(topic_terms(scoped,'en'))
  queries=list(dict.fromkeys([scoped,keywords,topic,*queries,scoped+' photograph']))[:commons_limit]
 if slots and slots[0].get('source_driven') and slots[0].get('requested_shots',0)>=18 and commons_limit==8 and not named_place_subject(profile):
  variants=[topic+' '+term for term in ('closeup','in nature','photography')]
  queries=list(dict.fromkeys(queries+[topic+' intitle:"'+topic+'"']+variants))[:commons_limit]
 if not queries:queries=list(dict.fromkeys([slot.get('visual_title') for slot in slots if slot.get('visual_title')]+[topic]+aliases))[:3]
 catalog_queries=list(dict.fromkeys(name for slot in slots for name in sorted(scene_astronomical_identifiers(slot))))
 periods=set().union(*(artifact_scene_centuries(slot) for slot in slots))
 dated_queries=[]
 for century in sorted(periods.intersection(range(4,22))):
  suffix={1:'st',2:'nd',3:'rd'}.get(century%10,'th') if century not in {11,12,13} else 'th'
  dated_queries.append(f'{topic} {century}{suffix} century')
 if (catalog_queries or dated_queries) and not (scene_queries or slots[0].get('process_intent')):
  queries=list(dict.fromkeys(queries[:1]+catalog_queries+dated_queries+queries[1:]))[:commons_limit]
 for query in queries:
  key=query.casefold().strip()
  if key not in SEARCH_QUERIES['commons'] and len(SEARCH_QUERIES['commons'])>=commons_limit:continue
  SEARCH_QUERIES['commons'].add(key)
  try:
   for candidate in commons_search(query,limit=50 if profile.get('kind')=='human' or (slots and slots[0].get('source_driven')) else 20):pool.setdefault((candidate['provider'],candidate['id']),candidate)
  except Exception as e:
   if getattr(e,'code',None) in {429,503}:raise
   errors.append('Commons: '+str(e))
 if not pool:raise ValueError('; '.join(errors) or 'no photo candidates')
 DISCOVERED_PHOTOS.update(pool)
 return list(pool.values())

def photo_origin(p):
 if p.get('provider')!='commons':return (p.get('provider'),p.get('id'))
 title=re.sub(r'^File:','',p.get('depiction') or '',flags=re.I)
 title=re.sub(r'\.[a-z0-9]{2,5}$','',title,flags=re.I)
 title=re.sub(r'\b(?:edit(?:ed)?|cropped|crop|retouched|restored|enhanced|version|derivative)\b',' ',title,flags=re.I)
 return ('commons-original',re.sub(r'[\W_]+','',title.casefold())) if title else ('commons',p.get('id'))


def photo_origins(p):
 origins={photo_origin(p)}
 # Commons derivatives can have unrelated filenames but retain the original
 # descriptive caption. Prefer diversity over multiple crops from that source.
 if p.get('provider')=='commons' and p.get('identity_verification'):
  description=p.get('alt','').removeprefix(p.get('depiction','')).strip()
  description=re.sub(r'\s+',' ',description).casefold()
  if len(description)>=80 and len(set(description.split()))>=10:
   origins.add(('commons-person-description',description))
 if p.get('provider')=='commons' and institutional_astronomical_photo(p):
  # Telescope archives may publish multiple crops or color mappings of one exposure.
  description=p.get('alt','').removeprefix(p.get('depiction','')).strip()
  signature=' '.join(token for token in tokens(' '.join(sentences(description)[:2])) if token not in STOP)
  if len(signature)>=100:origins.add(('commons-observation-description',signature))
  publication_id=re.search(r'\(((?:19|20)\d{2}-\d{2,4}(?:-\d{2,5})?)\)\.[a-z]+$',p.get('depiction',''),re.I)
  if publication_id:origins.add(('commons-observation-publication',publication_id.group(1)))
  release_id=re.search(r'\b((?:opo|eso|noirlab|noaoann)\d{4,})[a-z](?:\)|[ _-]|\.)',p.get('depiction',''),re.I)
  if release_id:origins.add(('commons-observation-release',release_id.group(1).casefold()))
  exposure=re.search(r'\bobtained by (.{4,100}?) in ((?:19|20)\d{2}), with (\d+) minutes? exposure in ([a-z-]+)',description,re.I)
  if exposure:
   subjects='|'.join(sorted(astronomical_identifiers(p.get('depiction',''))))
   if subjects:origins.add(('commons-observation-exposure',subjects,*[part.casefold() for part in exposure.groups()]))
 return origins

def dhash(im):
 im=ImageOps.grayscale(im).resize((9,8));p=list(im.getdata());n=0
 for y in range(8):
  for x in range(8):n=(n<<1)|(1 if p[y*9+x]>p[y*9+x+1] else 0)
 return n
def visual_actions(text):
 patterns={
  'melt':r'\b(?:melt\w*|molten|(?:roz|s)?topi\w*|(?:с|рас|пере|роз)?плав\w*)',
  'drain':r'\b(?:drain\w*|siev\w*|deckle\w*|paper mesh|paper mou?lds?|papermaking mou?lds?|wire mesh|(?:mesh|forming|wire|mould|mold|pulp) screens?\b|dewater\w*|odwad\w*|(?:od|prze)?sącz\w*|осуш\w*|обезвож\w*|зневод\w*|процідж\w*|відцідж\w*|сито\w*)',
  'press':r'\b(?:press\w*|squeez\w*|(?:s|wy)?pras\w*|(?:с|пере)?пресс\w*|(?:с|пере)?прес\w*)',
  'dry':r'\b(?:dry\w*|dried|dries|dryer\w*|(?:wy|do|po)?susz\w*|(?:вы|ви|по|під|до)?суш\w*)',
  'cut':r'\b(?:cut\w*|slit\w*|trim\w*|cię\w*|рез\w*|різ\w*)',
  'mix':r'\b(?:mix\w*|stirr\w*|blend\w*|miesz\w*|смеш\w*|зміш\w*)',
  'heat':r'\b(?:furnace\w*|heat(?:ed|ing)|kiln\w*|topi\w*|piec\w*|плав\w*|печ\w*|нагр\w*)',
  'shape':r'\b(?:blow(?:n|ing|pipe)?|blows|glassblow\w*|form(?:ed|ing)|mold\w*|mould\w*|shap(?:ed|ing)|wydmuch\w*|formow\w*|wyduw\w*|выдув\w*|формов\w*|видув\w*|формув\w*)',
  'cool':r'\b(?:cool(?:ed|ing)|anneal\w*|lehr|leer|chłodz\w*|wyżarz\w*|охлажд\w*|отжиг\w*|охолодж\w*|відпал\w*)',
  'inspect':r'\b(?:inspect\w*|quality control|quality check\w*|test(?:ed|ing)|kontrol\w*|sprawdz\w*|провер\w*|контрол\w*|перевір\w*)',
  'production':r'\b(?:factor(?:y|ies)|mill(?:ing)?|refiner\w*|manufactur\w*|\w{3,}making|production|assembly|automat\w*|machine\w*|fabryk\w*|produkc\w*|zakład\w*|завод\w*|производств\w*|виробниц\w*)'
 }
 return {key for key,pattern in patterns.items() if re.search(pattern,text or '',re.I)}
def scene_actions(text):
 actions=visual_actions(text)
 # The main operation takes precedence over auxiliary heat/vacuum in a clause.
 for action in ('press','drain','cut','mix','melt','dry','inspect','cool','shape','heat'):
  if action in actions:return {action}
 return {'production'}

STAGE_QUERIES={'press':'press','drain':'screen','cut':'cutting slitting','mix':'mixing raw materials','melt':'melting furnace','dry':'drying','inspect':'quality inspection','cool':'annealing','shape':'forming molding','heat':'heating','production':'manufacturing'}
STAGE_QUERY_TOOLS={'drain':['mould','sieve'],'press':['pulp press','hydraulic press'],'dry':['drying sheets','drying racks'],'shape':['mould','forming'],'heat':['furnace','kiln'],'melt':['furnace','molten'],'cool':['annealing','cooling'],'inspect':['inspection','quality control'],'mix':['mixer','mixing'],'cut':['cutter','slitting'],'production':['machinery','factory']}


def visual_competitors(topic,candidates):
 core=topic_terms(topic,'en');generic={'energy','power','system','process','technology','science','history','type','method','production','manufacturing'}
 anchors=[term for term in core if term not in generic]
 if len(anchors)<2 or any(word.endswith(('ing','ed')) for word in anchors[:-1]):return []
 head=anchors[-1];counts={};grammar=STOP|set('partial total full complete great large small closeup stunning dramatic beautiful captivating breathtaking detailed mesmerizing amazing during before after'.split())
 for candidate in candidates:
  words=re.findall(r'[a-z]+',(candidate.get('depiction') or candidate['alt']).lower());found=set()
  for index,word in enumerate(words):
   if not index or tokens(word)!=[head]:continue
   modifier=words[index-1]
   if len(modifier)>2 and modifier not in grammar and modifier not in core:found.add(modifier+' '+head)
  for phrase in found:counts[phrase]=counts.get(phrase,0)+1
 return ['A photograph of a '+phrase+'.' for phrase,count in sorted(counts.items(),key=lambda item:(-item[1],item[0])) if count>=3][:2]
def institutional_astronomical_photo(candidate):
 text=candidate.get('creator','')+' '+candidate.get('alt','')
 return candidate.get('provider')=='commons' and bool(re.search(r'\b(?:NASA|ESA|JPL|Hubble|STScI|ESO|USGS|NOIRLab|NAOJ|JAXA|ISRO|CNSA)\b',text,re.I)) and not re.search(r'\b(?:astronaut|cosmonaut|spacesuit|space suit|simulation|simulated|concept|analogue|analog|rendering)\b',candidate.get('alt',''),re.I)

def photo_score(p,slot,topic):
 if not photographic_metadata(p):return -1
 toy_pattern=r'\b(?:toys?|toy model|playset|Spielzeug|zabawk\w*|іграш\w*|игруш\w*)\b'
 if re.search(toy_pattern,p.get('depiction') or p.get('alt',''),re.I) and not re.search(toy_pattern,topic,re.I):return -1
 periods=artifact_scene_centuries(slot)
 if periods and not periods&artifact_photo_centuries(p):return -1
 identifiers=scene_astronomical_identifiers(slot)
 if identifiers:
  observed=astronomical_identifiers(p.get('depiction','')+' '+' '.join(semantic_categories(p)))
  if not observed&identifiers:return -1
 profile=slot.get('entity_profile',{})
 insect_profile=insect_subject(profile)
 insect_features=slot.get('insect_features',[])
 if insect_profile or insect_features:
  if conflicting_insect_identity(p,profile,insect_features):return -1
  if insect_profile and not insect_photo_identity(p,profile):return -1
  depicted_features=set(insect_scene_features(p.get('alt','')+' '+' '.join(semantic_categories(p))))
  if not set(insect_features)<=depicted_features:return -1
  title=p.get('depiction','')
  if 'pollination' in insect_features:
   if re.search(r'\b(?:hive|comb|frames?|honeycomb|beeswax)\b',title,re.I) and not re.search(r'\b(?:pollinating|on (?:a |the )?flower|orchard)\b',title,re.I):return -1
   if re.search(r'\b(?:queen marking|bee marked in|marking a queen)\b',p.get('alt',''),re.I):return -1
  if 'fossil' in depicted_features and 'fossil' not in insect_features and 'fossil' not in insect_scene_features(topic):return -1
 features=slot.get('volcanic_features',[])
 if volcanic_subject(profile):
  alien_terrain=r'\b(?:on (?:mars|venus|mercury|the moon|io|titan)|martian (?:surface|crater|volcano|landscape)|lunar (?:surface|crater)|venusian (?:surface|crater|volcano))\b'
  if re.search(alien_terrain,p.get('alt',''),re.I) and not re.search(r'\b(?:mars|venus|mercury|moon|io|titan|martian|lunar|venusian)\b',topic,re.I):return -1
  material_sample=r'\b(?:volcan(?:o|ic) stones?|volcanic rock specimens?|volcanic rock samples?)\b'
  if not features and re.search(material_sample,p.get('alt',''),re.I) and not re.search(material_sample,topic,re.I):return -1
 if features:
  observed=volcanic_features(p.get('alt','')+' '+' '.join(semantic_categories(p)))
  if not set(features).intersection(observed):return -1
 if slot.get('visual_target'):
  target=slot['visual_target']
  if named_astronomical_subject({'kind':target.get('kind'),'visual_description':target.get('description','')}) and not institutional_astronomical_photo(p):return -1
  from storyboard import target_score
  return target_score(p,slot,sys.modules[__name__])
 if named_place_subject(profile):
  if not place_identity(p,profile):return -1
  detail=slot.get('place_detail_query')
  features=slot.get('place_features',[])
  if not features and detail and p.get('query')!=detail:return -1
  if features and not set(features)<=set(place_scene_features(p.get('alt','')+' '+' '.join(semantic_categories(p)))):return -1
  return 2*len(set(tokens(slot['text']+' '+slot.get('visual_title','')))&set(tokens(p.get('alt',''))))+(.5 if p['height']>=p['width'] else 0)
 if named_astronomical_subject(profile):
  if p.get('provider')!='commons':return -1
  if not re.search(r'\b(?:NASA|ESA|JPL|Hubble|STScI|ESO|USGS|NOIRLab|NAOJ|JAXA|ISRO|CNSA)\b',p.get('creator','')+' '+p.get('alt',''),re.I):return -1
  if re.search(r'\b(?:astronaut|cosmonaut|spacesuit|space suit|simulation|simulated|concept|analogue|analog|rendering)\b',p.get('alt',''),re.I):return -1
 if slot.get('entity_profile',{}).get('kind')=='human':
  if re.search(r'\b(?:signature|autograph|letter|document|certificate|poster|propaganda|graffiti|mural|banner|caricature|billboard|stamp|statue|bust|sculpture)\b',p.get('depiction') or p['alt'],re.I):return -1
  return (20+(10 if re.search(r'portrait|cropped',p['alt'],re.I) else 0)+(3 if p['height']>=p['width'] else 0)) if p.get('identity_verification',{}).get('entity_id')==slot['entity_profile']['id'] else -1
 depiction=p.get('depiction') or p['alt']
 if slot.get('process_intent'):depiction+=' '+' '.join(semantic_categories(p))
 terms=set(tokens(topic+' '+slot['text']+' '+slot.get('visual_title','')));meta=set(tokens(depiction))
 for word in list(meta):
  if len(word)>8 and word.endswith('making'):meta.add(word[:-6])
 process_topic=bool(slot.get('process_intent') or re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 anchors=set(topic_terms(topic,'en'))-{'energy','power','system','process','technology','science','history','type','method','production','manufacturing'}
 if process_topic and anchors and not anchors&meta:return -1
 if not process_topic and anchors:
  concept=slot.get('source_driven') and slot.get('entity_profile',{}).get('kind')=='concept'
  supported_concept=concept and bool(meta&set(slot['entity_profile'].get('visual_vocabulary',[])))
  names=[topic]+slot.get('topic_aliases',[])
  groups=[set(topic_terms(name,'en'))-{'energy','power','system','process','technology','science','history','type','method','production','manufacturing'} for name in names]
  category_identity=concept and any(group and group<=set(tokens(category)) for category in semantic_categories(p) for group in groups)
  if not any(group and group<=meta for group in groups) and not supported_concept and not category_identity and not insect_profile:return -1
 if not process_topic and not slot.get('source_driven') and p.get('provider')=='pixabay' and len(anchors)>1 and not any(group and group<=set(tokens(tag)) for group in groups for tag in depiction.split(',')):return -1
 if p.get('provider') in {'pixabay','pexels'} and re.search(r'\b(?:fantasy|sci[ -]?fi|digital art|3d render|ai[ -]generated)\b',depiction,re.I):return -1
 work_context=r'\b(?:factor(?:y|ies)|mill(?:ing)?|refiner\w*|manufactur\w*|production|assembly|machine\w*|workshop|artisan\w*|craftsman|glassblow\w*|furnace\w*|kiln\w*|industrial|anneal\w*|lehr|leer|oven|inspection box|final inspection|glass works|laborator\w*|\w{3,}making|handmade|bakery|kitchen|brewery|fabryk\w*|warsztat\w*|завод\w*|цех\w*|мастерск\w*|майстер\w*|виробниц\w*)'
 if process_topic and not re.search(work_context,depiction,re.I) and not (visual_actions(depiction+' '+p.get('alt','')[:300])-{'production'}):return -1
 if process_topic:
  if re.search(r'press.conference|news.conference|press[ _-]photo(?:graph)?|publicity[ _-]photo',depiction,re.I) and not re.search(r'press.conference|news.conference',topic,re.I):return -1
  food=r'\b(?:food|rice paper|rice flour|spring rolls?|edible|pancakes?|tortillas?|noodles?|chocolate|cakes?|bread|potato)\b'
  if re.search(food,p.get('alt','')+' '+' '.join(p.get('categories',[])),re.I) and not re.search(food,topic,re.I):return -1
  uses=set(re.findall(r'\b(?:printing press|letter press|letterpress|paper printing|book printing|printing machine|dressmaking|origami|wrapping|writing|drawing|typewriter|paper bags|paper sacks)\b',depiction,re.I))
  if any(use.casefold() not in topic.casefold() for use in uses):return -1
  compounds=[word[:-6] for word in meta if len(word)>8 and word.endswith('making')]
  if compounds and not any(root in anchors for root in compounds):return -1
 if not process_topic:
  qualifiers={term for term in tokens(slot.get('visual_title','')) if term not in tokens(topic) and term.isalpha() and len(term)>=3}-{'energy','power','system','plant','factory','production','manufacturing','process','industry','technology','list','century'}
  if qualifiers and not qualifiers&meta:return -1
 required=scene_actions(slot['text']) if process_topic else set()
 action_description=(p.get('alt','').removeprefix(p.get('depiction','')) or '')[:300]
 action_metadata=depiction+' '+action_description
 if 'press' in required:
  wet_material=r'\b(?:wet|water|damp|moist|dewater\w*|wilgo\w*|mokr\w*|wod\w*|вод\w*|волог\w*|мокр\w*|влаг\w*)\b'
  dry_packing=r'\b(?:baling|baling press|baled|packed(?: in)? bales|scrap paper|waste paper|scrap metal|salvage drive|makulatur\w*|макулатур\w*|пресування відходів)\b'
  if re.search(wet_material,slot['text'],re.I) and re.search(dry_packing,action_metadata,re.I) and not re.search(wet_material,action_metadata,re.I):return -1
 if 'dry' in required:
  # A photo of handling an already dried item does not show the drying step.
  action_metadata=re.sub(r'\b(?:after (?:the )?drying|already dried|dry (?:paper|sheets?|cardboard|fibres?|fibers?))\b',' ',action_metadata,flags=re.I)
 depicted=visual_actions(action_metadata)
 specific=required-{'production'}
 if specific and not specific&depicted:return -1
 if specific and re.search(r'\b(?:exterior|outside|panorama|skyline)\b',depiction,re.I):return -1
 if required and not required&depicted and 'production' not in depicted:return -1
 return 2*len(terms&meta)+.8*len(set(tokens(topic))&meta)+8*len(required&depicted)+(5 if p.get('article_media_revision') else 0)+(6 if slot.get('visual_title') and slot['visual_title'].casefold()==p.get('query','').casefold() else 0)+(.5 if p['height']>=p['width'] else 0)
def scene_photo_score(candidate,slot,topic):
 if slot.get('visual_target_optional'):
  return max((photo_score(candidate,{**slot,'visual_target':target},topic) for target in slot.get('visual_targets',[])),default=-1)
 return photo_score(candidate,slot,topic)
PIXEL_VERIFIER=None
def get_pixel_verifier():
 global PIXEL_VERIFIER
 if PIXEL_VERIFIER is None:PIXEL_VERIFIER=VisualVerifier()
 return PIXEL_VERIFIER
def pixel_check(raw,topic,slot,candidate=None):
 if slot.get('visual_target'):
  target=slot['visual_target'];intent=target.get('intent',{});display_name=target['name']
  if len(display_name)<3 and target.get('anchor','').isascii() and len(target.get('anchor',''))>=3:display_name=target['anchor']
  subject=display_name+' — '+intent.get('visual',target.get('description',''))
  negatives=intent.get('negative_descriptions',[])+['A close-up portrait photograph of a person with no visible scene object.','A screenshot of a website, app interface or social media profile.','A standalone corporate logo or wordmark on a plain background.','A generic photograph of people at an unrelated meeting.','A flat digital advertisement or promotional text banner.']
  positives=['A photograph of '+display_name+' '+obj+'.' for obj in intent.get('visual_objects',[])[:3]]
  audit=get_pixel_verifier().check(raw,subject,set(),'',[],topic,extra_negatives=negatives,extra_positives=positives)
  if intent.get('name')=='person event':
   human=get_pixel_verifier().check_person(raw,(candidate or {}).get('identity_verification') or {})
   audit['human_content_verification']=human; audit['passed']=audit['passed'] and human['passed']
  if intent.get('name')=='family group':
   # A famous surname must not make a solo portrait or distant crowd a family scene.
   group=get_pixel_verifier().check(raw,'members of a family photographed together',set(),extra_positives=['A photograph of a family posing together.','A photograph of parents with their children.','A photograph of several family members walking together.'],extra_negatives=['A photograph of a man standing alone.','A photograph of a woman standing alone.','A photograph of only one person.','A wide view of a large crowd at a rally.'])
   audit['family_group_verification']=group;audit['passed']=audit['passed'] and group['passed']
  audit['scene_target']=target;return audit

 if slot.get('entity_profile',{}).get('kind')=='human':
  identity=(candidate or {}).get('identity_verification') or {}
  if identity.get('entity_id')!=slot['entity_profile']['id']:raise ValueError('portrait lacks source-backed subject identity')
  audit=get_pixel_verifier().check_person(raw,identity,slot['entity_profile'].get('visual_description',''))
  audit['identity_verification']=identity;return audit
 if slot.get('source_driven'):
  profile=slot.get('entity_profile',{})
  if volcanic_subject(profile):
   features=slot.get('volcanic_features',[])
   if features:
    subject=VOLCANIC_FEATURES[features[0]][1]
    positives=['A photograph of '+VOLCANIC_FEATURES[feature][1]+'.' for feature in features]
    negatives=['A quiet mountain panorama with no volcanic activity.','A town, storefront, or street sharing a volcano name.'] if 'crater' not in features else ['A town, storefront, or street sharing a volcano name.']
   else:
    subject='a volcano in a natural landscape'
    positives=['A photograph of a volcanic cone rising above the surrounding landscape.','A natural volcanic crater or a volcanic eruption.']
    negatives=['A photograph of a town or storefront sharing a volcano name.']
   return get_pixel_verifier().check(raw,subject,set(),'',[],topic,extra_positives=positives,extra_negatives=negatives)
  features=slot.get('place_features') or slot.get('insect_features')
  if features:
   if slot.get('insect_features')==['pollination']:
    name=profile['name']
    return get_pixel_verifier().check(raw,name+' collecting nectar on a flower',set(),'',[],topic,
      extra_positives=['A close photograph of a '+name+' carrying pollen and feeding on a flower.','A '+name+' pollinating the center of a flower.'],
      extra_negatives=['An insect walking on the ground or on wood.','A flower with no insect on it.','A fly with large compound eyes hovering near a flower.'])
   if 'predation' in slot.get('insect_features',[]):
    name=profile['name']
    return get_pixel_verifier().check(raw,'a predator holding a '+name+' as prey',set(),'',[],topic,
      extra_positives=['A spider holding a '+name+' in its legs.','A bird holding a '+name+' in its beak.'],
      extra_negatives=['A single insect feeding on a flower with no predator nearby.','A beehive or a group of bees on a honeycomb.'])
   feature=' and '.join(features)
   subject=profile['name']+' — '+feature
   return get_pixel_verifier().check(raw,subject,set(),'',[],topic,
     extra_positives=['A photograph of the '+feature+' in '+profile['name']+'.'],
     extra_negatives=['A generic photograph of '+profile['name']+' without visible evidence of '+feature+'.'])
  if named_astronomical_subject(profile):
   name=profile['name']
   positive=['A photograph of '+name+' in space.']
   if re.search(r'\b(?:planet|moon|satellite)\b',profile.get('visual_description',''),re.I):
    positive+=['A photograph of the rocky surface of '+name+' taken by a rover.','An orbital photograph of the surface of '+name+'.']
   return get_pixel_verifier().check(raw,name,set(),'',[],name,extra_positives=positive,extra_negatives=['A photograph of a spacecraft being built in a laboratory.','A person wearing an astronaut costume on Earth.','A collage of multiple labeled satellite images.','A topographic map with a color legend.','A small irregular moon or asteroid above a planet.','An artists concept or simulated view of a planet.'])
  if slot.get('process_intent'):
   subject=' '.join(dict.fromkeys(topic_terms(topic,'en'))) or topic
   return get_pixel_verifier().check(raw,subject,scene_actions(slot['text']),slot['text'] if slot.get('language')=='en' else '',slot.get('visual_competitors',[]),topic,extra_negatives=['A person writing or drawing on finished '+subject+'.','A typewriter, office printer or a person wrapping a parcel.'],extra_positives=[])
  visual_subject=slot.get('visual_title') or topic
  description=profile.get('visual_description','') if visual_subject.casefold() in {profile.get('name','').casefold(),topic.casefold()} else ''
  subject=visual_subject+(' — '+description if description else '')
  extras=['A wide landscape photograph of a flower garden.'] if re.search(r'\binsects?\b',profile.get('visual_description',''),re.I) else []
  plain_subject=['A photograph of '+visual_subject+'.'] if description and profile.get('kind')=='concept' else []
  return get_pixel_verifier().check(raw,subject,set(),'',slot.get('visual_competitors',[]),topic,extra_negatives=extras,extra_positives=plain_subject)
 visual_subject=(slot.get('visual_title') or topic) if not slot.get('process_intent',True) else topic
 subject=' '.join(dict.fromkeys(topic_terms(visual_subject,'en')))
 return get_pixel_verifier().check(raw,subject or topic,visual_actions(slot['text']) if slot.get('process_intent',True) else set(),slot['text'] if slot.get('language','en')=='en' else '',slot.get('visual_competitors',[]),topic)

def photo_audit_context(topic,slot):
 target=slot.get('visual_target') or {};profile=slot.get('entity_profile',{})
 context={'topic':topic,'target':{key:target.get(key) for key in ('id','name','anchor','description','intent')},
          'profile':{key:profile.get(key) for key in ('id','kind','name','visual_description')},
          'visual_title':slot.get('visual_title'),'competitors':slot.get('visual_competitors',[]),
          'source_driven':slot.get('source_driven'),'process_intent':slot.get('process_intent'),'language':slot.get('language'),
          'features':{key:slot.get(key) for key in ('place_features','insect_features','volcanic_features')}}
 if not target and (slot.get('process_intent') or not slot.get('source_driven')):context['caption']=slot['text']
 return hashlib.sha256(json.dumps(context,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def allocate_photos(candidates,slots,topic,shot_count=None,scene_slots=None,edges=None):
 # Assign the entire storyboard before downloads, preserving scarce assets for scenes that need them.
 if edges is None:
  choices=scene_slots if scene_slots is not None else [slots[beat] for beat in shot_beats(shot_count if shot_count is not None else len(slots)*2,len(slots))]
  edges=[]
  for slot in choices:
   scored=[(scene_photo_score(candidate,slot,topic),index) for index,candidate in enumerate(candidates)]
   edges.append([index for score,index in sorted(scored,key=lambda entry:-entry[0]) if score>=0])
 owner={}
 def assign(scene,seen):
  for candidate in edges[scene]:
   if candidate in seen:continue
   seen.add(candidate)
   if candidate not in owner or assign(owner[candidate],seen):owner[candidate]=scene;return True
  return False
 for scene in sorted(range(len(edges)),key=lambda index:len(edges[index])):
  if not assign(scene,set()):
   from storyboard import SceneUnavailable
   raise SceneUnavailable(scene_slots[scene] if scene_slots else slots[shot_beats(len(edges),len(slots))[scene]],'not enough scene-matched images for the storyboard; shot '+str(scene+1))
 allocated=[None]*len(edges)
 for candidate,scene in owner.items():allocated[scene]=candidates[candidate]
 return allocated

def rank_storyboard_photos(candidates,scene_slots,beat_for_shot,topic):
 # The same caption and target often span several shots. Score each pair once.
 scores={};shot_options=[];edges=[]
 for slot,beat in zip(scene_slots,beat_for_shot):
  choices=[slot]
  if slot.get('visual_target_optional'):
   choices.extend({**slot,'visual_target':target} for target in slot['visual_targets'] if target['id']!=slot['visual_target']['id'])
  options=[];eligible={}
  for choice in choices:
   key=(beat,(choice.get('visual_target') or {}).get('id'))
   if key not in scores:
    scored={index:score for index,candidate in enumerate(candidates) if (score:=photo_score(candidate,choice,topic))>=0}
    scores[key]=(scored,sorted(scored,key=scored.get,reverse=True))
   scored,ranked=scores[key]
   options.append((choice,ranked))
   for index,score in scored.items():eligible[index]=max(score,eligible.get(index,-1))
  shot_options.append(options)
  edges.append(sorted(eligible,key=lambda index:(-eligible[index],index)))
 return shot_options,edges

def font(size,bold=False):
 paths=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
 for p in paths:
  try:return ImageFont.truetype(p,size)
  except OSError:pass
 return ImageFont.load_default()
def wrap(text,face,width=916):
 lines=[];cur=''
 for word in text.split():
  candidate=(cur+' '+word).strip()
  if cur and face.getlength(candidate)>width:lines.append(cur);cur=''
  if face.getlength(word)>width:
   if cur:lines.append(cur);cur=''
   for char in word:
    if cur and face.getlength(cur+char)>width:lines.append(cur);cur=''
    cur+=char
  else:cur=(cur+' '+word).strip()
 if cur:lines.append(cur)
 return lines
def make_card(raw,caption,dest,credit=None):
 with Image.open(raw) as src:
  im=ImageOps.exif_transpose(src).convert('RGB')
  if min(im.size)<320:raise ValueError('photo resolution too small')
  bg=Image.new('RGB',(1080,1920),(7,13,23))
  fg=ImageOps.contain(im,(1040,1400),method=Image.Resampling.LANCZOS)
  bg.paste(fg,((1080-fg.width)//2,95+(1400-fg.height)//2))
  layer=Image.new('RGBA',(1080,1920),(0,0,0,0));d=ImageDraw.Draw(layer)
  if credit and credit.get('provider')=='commons':
   attribution='Media: '+credit['creator']+' | '+credit['license']+' | '+credit['source_url']
   if credit.get('license_url'):attribution+=' | '+credit['license_url']
   attribution+=' | Resized, captioned'
   credit_lines=wrap(attribution,font(16),996)
   if len(credit_lines)>4:raise ValueError('photo credit is too long for complete readable attribution')
   d.rectangle((32,4,1048,92),fill=(7,13,23,235))
   for index,line in enumerate(credit_lines):d.text((42,8+index*20),line,font=font(16),fill='white')
  d.rounded_rectangle((42,1510,1038,1880),radius=38,fill=(7,13,23,224),outline=(255,255,255,50),width=2)
  for size in range(40,23,-2):
   face=font(size,True);lines=wrap(caption,face);line_height=size+12
   if len(lines)*line_height<=300:break
  else:raise ValueError('complete caption cannot fit in the readable caption area')
  y=1545
  for line in lines:d.text((82,y),line,font=face,fill='white');y+=line_height
  d.text((42,1882),'Adaptation: CC BY-SA 4.0 | https://creativecommons.org/licenses/by-sa/4.0/',font=font(15),fill='white')
  d.text((42,1900),'Text: Wikimedia contributors. Full authors, sources and changes are embedded in MP4 credits.',font=font(15),fill='white')
  Image.alpha_composite(bg.convert('RGBA'),layer).convert('RGB').save(dest,'JPEG',quality=88,optimize=True)
class ImageServiceError(RuntimeError):
 def __init__(self,status):
  super().__init__('Image service returned HTTP '+str(status))
  self.status=status

IMAGE_SERVICE_RETRIES=0
def download_photo(c,dest):
 def fetch(url):
  parsed=urllib.parse.urlparse(url);host=(parsed.hostname or '').lower()
  if parsed.scheme!='https' or not(host in {'images.pexels.com','pixabay.com'} or host.endswith('.pixabay.com') or host in {'upload.wikimedia.org','thumb.wikimedia.org'}):raise ValueError('photo host not allowed')
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UniversalShortFactory/1.0 (https://studio.hodor.com.pl/; educational video research)'}),timeout=25) as response:
   data=response.read(20_000_001);content_type=response.headers.get('Content-Type','').split(';')[0].lower()
  if len(data)>20_000_000 or content_type not in {'image/jpeg','image/png','image/webp'}:raise ValueError('photo payload invalid')
  return data
 try:data=fetch(c['url'])
 except urllib.error.HTTPError as error:
  # The original is the same licensed Commons file, not a replacement image.
  original=c.get('original_url')
  usable=original and original!=c['url'] and 0<c.get('original_size',0)<=8_000_000 and 0<c.get('original_pixels',0)<=20_000_000
  if error.code==503 and usable:
   error.close()
   try:data=fetch(original)
   except urllib.error.HTTPError as second:
    if second.code in {429,503}:raise ImageServiceError(second.code) from second
    raise
  elif error.code in {429,503}:raise ImageServiceError(error.code) from error
  else:raise
 Path(dest).write_bytes(data)
 with Image.open(dest) as image:image.verify()

SELECTED_VOICES={'en':('en-US','en-US-Chirp3-HD-Algenib'),'pl':('pl-PL','pl-PL-Chirp3-HD-Enceladus'),'ru':('ru-RU','ru-RU-Wavenet-D'),'uk':('uk-UA','uk-UA-Chirp3-HD-Enceladus')}
def selected_voice_request(lang,text):
 locale,voice=SELECTED_VOICES[lang]
 text=unicodedata.normalize('NFC',text).replace(chr(0x301),'')
 return {'input':{'text':text},'voice':{'languageCode':locale,'name':voice},'audioConfig':{'audioEncoding':'MP3'}}
GOOGLE_STATUS_LOCK=threading.Lock()
def google_connection_status(force=False):
 path=ROOT/'google-connection-status.json'
 with GOOGLE_STATUS_LOCK:
  try:
   saved=json.loads(path.read_text())
   if time.time()-saved.get('checked_at',0)<(5 if force else 60):return saved
  except (OSError,ValueError,TypeError):pass
  result={'ready':False,'code':'GOOGLE_UNAVAILABLE','message':'The Google voice connection is unavailable. Check the connection again.','reconnect_url':'https://publisher.hodor.com.pl/home/credentials'}
  project=(SETTINGS.get('free_tier_proof') or {}).get('project_id')
  try:
   payload={'provider':'google_metadata','request':{'operation':'billing','body':{'project_id':project}}}
   request=urllib.request.Request('http://ai-short-form-n8n:5678/webhook/factory-v3-internal-provider',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-Factory-V3-Broker':SETTINGS['broker_token']})
   with urllib.request.urlopen(request,timeout=8) as response:receipt=json.loads(response.read(1000000))
   result['gateway_execution_id']=receipt.get('gateway_execution_id')
   if receipt.get('error_reason')=='OAUTH_GRANT_REJECTED':
    result.update(code='GOOGLE_RECONNECT_REQUIRED',message='Reconnect Google account to restore narration.')
   elif receipt.get('error_reason')=='ACCESS_TOKEN_SCOPE_INSUFFICIENT':
    result.update(code='GOOGLE_RECONNECT_REQUIRED',message='Reconnect Google account with the required Cloud access.')
   elif isinstance(receipt.get('status'),int) and 200<=receipt['status']<500:
    result.update(ready=True,code='READY',message='')
  except (OSError,ValueError,TypeError):pass
  result['checked_at']=time.time()
  draft=path.with_suffix('.tmp');draft.write_text(json.dumps(result));draft.replace(path)
  return result

def voice_cache_path(voice,digest):
 return ROOT/'cache'/(hashlib.sha256(('selected-voice-audio-v1|'+voice+'|'+digest).encode()).hexdigest()+'.json')

def cached_native_voice(voice,digest):
 cache=voice_cache_path(voice,digest)
 try:
  stat=cache.stat()
  if time.time()-stat.st_mtime>=86400 or stat.st_size>=10_000_000:return None
  saved=json.loads(cache.read_text());audit=saved.get('audit',{});audio=base64.b64decode(saved.get('audio_base64',''),validate=True)
  if audio and audit.get('voice')==voice and audit.get('text_sha256')==digest and audit.get('audio_sha256')==hashlib.sha256(audio).hexdigest():
   return audio,audit
 except (OSError,ValueError,TypeError,AttributeError):pass
 return None

def google_voice_once(lang,text,jid,attempt):
 import psycopg
 body=selected_voice_request(lang,text);spoken=body['input']['text'];voice=body['voice']['name']
 if not spoken.strip() or len(spoken.encode())>4800:raise ValueError('narration exceeds the selected voice request size')
 key='universal:'+jid+':voice:'+str(attempt);digest=hashlib.sha256(spoken.encode()).hexdigest()
 # A durable claim precedes quota accounting and the uncertain send; an interrupted attempt cannot replay.
 with connect() as c:
  c.execute('INSERT INTO voice_attempts(job_id,attempt,text_sha256,voice,state) VALUES(?,?,?,?,?)',(jid,attempt,digest,voice,'claimed'))
 cache=voice_cache_path(voice,digest)
 saved=cached_native_voice(voice,digest)
 if saved:
  audio,audit=saved
  folder=ROOT/'tmp'/jid;folder.mkdir(parents=True,exist_ok=True);path=folder/('voice-attempt-'+str(attempt)+'.mp3')
  with path.open('xb') as stream:stream.write(audio)
  audit={**audit,'attempt':attempt,'reused_completed_audio':True,'provider_send':False}
  with connect() as c:c.execute("UPDATE voice_attempts SET state='measured',receipt=? WHERE job_id=? AND attempt=?",(json.dumps(audit),jid,attempt))
  return path,audit
 sku='wavenet' if lang=='ru' else 'chirp3_hd'
 try:
  with psycopg.connect(SETTINGS['database_url'],connect_timeout=5,options='-c statement_timeout=5000') as pg:
   with pg.cursor() as cur:
    cur.execute("SELECT factory.reserve_provider_usage(%s,'google_cloud_tts',%s,'characters',date_trunc('month',CURRENT_DATE)::date,%s,%s,%s::jsonb)",(key,sku,len(spoken),jid,json.dumps({'stage':'universal_selected_voice','attempt':attempt,'voice':voice})))
    cur.execute('SELECT factory.commit_provider_usage(%s,NULL)',(key,))
  with connect() as c:c.execute("UPDATE voice_attempts SET state='sent' WHERE job_id=? AND attempt=?",(jid,attempt))
  request=urllib.request.Request('http://ai-short-form-n8n:5678/webhook/factory-v3-internal-provider',data=json.dumps({'provider':'google_tts','request':{'query':{},'body':body}},ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-Factory-V3-Broker':SETTINGS['broker_token']})
  with urllib.request.urlopen(request,timeout=180) as response:raw=response.read(10_000_001)
  if not raw or len(raw)>10_000_000:raise ValueError('selected voice gateway returned no bounded audio response')
  receipt=json.loads(raw)
  if receipt.get('status')!=200:
   failure={'attempt':attempt,'voice':voice,'characters':len(spoken),'text_sha256':digest,'upstream_status':receipt.get('status'),'error_status':receipt.get('error_status'),'error_reason':receipt.get('error_reason'),'gateway_execution_id':receipt.get('gateway_execution_id'),'quota_key':key}
   with connect() as c:c.execute("UPDATE voice_attempts SET state='stopped',receipt=? WHERE job_id=? AND attempt=?",(json.dumps(failure),jid,attempt))
   reason=receipt.get('error_reason') or receipt.get('error_status') or 'UNKNOWN_PROVIDER_RESULT'
   raise ValueError('selected Google voice unavailable: '+str(reason)+'; no fallback or resend')
  audio=base64.b64decode(receipt['body']['audioContent'],validate=True)
  folder=ROOT/'tmp'/jid;folder.mkdir(parents=True,exist_ok=True);path=folder/('voice-attempt-'+str(attempt)+'.mp3')
  with path.open('xb') as stream:stream.write(audio)
  duration_ms=round(float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)],text=True,timeout=10))*1000)
  audit={'attempt':attempt,'voice':voice,'characters':len(spoken),'text_sha256':digest,'audio_sha256':hashlib.sha256(audio).hexdigest(),'duration_ms':duration_ms,'quota_key':key}
  with connect() as c:c.execute("UPDATE voice_attempts SET state='measured',receipt=? WHERE job_id=? AND attempt=?",(json.dumps(audit),jid,attempt))
  try:
   cache.parent.mkdir(exist_ok=True);draft=folder/'cached-voice.json';draft.write_text(json.dumps({'audit':{**audit,'provider_send':True},'audio_base64':base64.b64encode(audio).decode()}));draft.replace(cache)
  except OSError:pass
  return path,audit
 except Exception:
  with connect() as c:c.execute("UPDATE voice_attempts SET state='stopped' WHERE job_id=? AND attempt=? AND state!='measured'",(jid,attempt))
  raise

def natural_voice_window(duration):
 from renderer import natural_audio_window
 return natural_audio_window(duration*1000)

def out_of_window_narrations(topic,lang,duration):
 voice=SELECTED_VOICES[lang][1];low,high=natural_voice_window(duration)
 with connect() as db:
  rows=db.execute("SELECT v.text_sha256 FROM voice_attempts v JOIN jobs j ON j.id=v.job_id WHERE j.topic=? AND j.language=? AND j.duration_s=? AND v.voice=? AND v.state='measured' GROUP BY v.text_sha256 ORDER BY MAX(v.rowid) DESC LIMIT 12",(topic,lang,duration,voice)).fetchall()
 excluded=set()
 for row in rows:
  digest=row['text_sha256'];cached=cached_native_voice(voice,digest)
  if not cached:continue
  milliseconds=cached[1].get('duration_ms')
  if isinstance(milliseconds,int) and not low<=milliseconds<=high:excluded.add(digest)
 return excluded

def initial_natural_budget(sources,topic,lang,duration):
 if source_overview_mode(sources):return duration
 from statistics import median
 with connect() as c:
  rows=c.execute("SELECT receipt FROM voice_attempts WHERE voice=? AND state='measured' AND receipt IS NOT NULL ORDER BY rowid DESC LIMIT 12",(SELECTED_VOICES[lang][1],)).fetchall()
 measures=[json.loads(row['receipt']) for row in rows]
 if not measures:return duration
 rate=median(item['duration_ms']/item['characters'] for item in measures if item.get('characters'))
 low,high=natural_voice_window(duration);target=high-500;budget=duration;seen=set();options=[]
 for _ in range(4):
  if budget in seen:break
  seen.add(budget);slots=plan_script(sources,topic,lang,budget,max_beats=duration//5)
  if not slots:break
  text=selected_voice_request(lang,' '.join(slot['text'] for slot in slots))['input']['text']
  predicted=len(text)*rate;options.append((abs(predicted-target),budget,predicted))
  if low<=predicted<=high:return budget
  budget=max(10,min(90,round(budget*target/max(predicted,1))))
 return min(options)[1] if options else duration

def source_verified_native_plan(evidence,receipt,sources,topic,lang,duration):
 low,high=natural_voice_window(duration);voice=SELECTED_VOICES[lang][1]
 if receipt.get('voice')!=voice or evidence.get('voice')!=voice or not low<=receipt.get('duration_ms',0)<=high:return None
 slots=[]
 for beat in evidence.get('beats',[]):
  old_index=beat.get('source_index',-1)
  if not 0<=old_index<len(evidence.get('sources',[])):return None
  url=evidence['sources'][old_index]['url'];index=next((i for i,source in enumerate(sources) if source['url']==url),None)
  span=beat.get('source_sentence','');start=beat.get('source_position',-1)
  if index is None or start<0 or not span or sources[index]['text'][start:start+len(span)]!=span:return None
  if truncated_dependent_clause(beat['text'],span,lang) or context_dependent_sentence(beat['text']) or incidental_place_event(beat['text'],topic,sources[0].get('entity_profile',{})):return None
  slots.append({'text':beat['text'],'language':lang,'source_index':index,'source_sentence':span,'source_position':start,'process_intent':bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))})
 if not slots or len(slots)>duration//5 or not script_covers_identifier_scope(sources,topic,lang,slots):return None
 spoken=selected_voice_request(lang,' '.join(slot['text'] for slot in slots))['input']['text']
 if spoken!=evidence.get('spoken_text') or hashlib.sha256(spoken.encode()).hexdigest()!=receipt.get('text_sha256'):return None
 return slots

def completed_narration_plan(sources,topic,lang,duration):
 if any(source.get('translation_model') for source in sources):return None
 entity=sources[0].get('entity_profile',{}).get('id') if sources else None
 if not entity:return None
 try:
  with connect() as db:rows=db.execute("SELECT manifest,review_status,review_note FROM jobs WHERE topic=? AND language=? AND duration_s=? AND status='ready' AND manifest IS NOT NULL ORDER BY created_at DESC LIMIT 12",(topic,lang,duration)).fetchall()
 except sqlite3.OperationalError:return None
 low,high=natural_voice_window(duration)
 for row in rows:
  if row['review_status']=='changes_requested' and not (row['review_note'] or '').casefold().startswith('assistant frame'):continue
  previous=json.loads(row['manifest']);voice=previous.get('narration',{})
  if previous.get('resolved_entity_id')!=entity or voice.get('voice')!=SELECTED_VOICES[lang][1] or not low<=voice.get('audio_duration_ms',0)<=high or voice.get('audio_tempo_factor')!=1.0:continue
  slots=[];valid=True
  for beat in previous.get('beats',[]):
   index=next((i for i,source in enumerate(sources) if source['url']==beat['source_url']),None)
   span=beat.get('source_span','');start=beat.get('source_start',-1)
   if index is None or start<0 or not span or sources[index]['text'][start:start+len(span)]!=span:valid=False;break
   if truncated_dependent_clause(beat['caption'],span,lang) or context_dependent_sentence(beat['caption']) or incidental_place_event(beat['caption'],topic,sources[0].get('entity_profile',{})):valid=False;break
   slots.append({'text':beat['caption'],'language':lang,'source_index':index,'source_sentence':span,'source_position':start,'process_intent':bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))})
  if not valid or not slots or len(slots)>duration//5 or not script_covers_identifier_scope(sources,topic,lang,slots):continue
  # A previously measured, source-verified script remains useful after its
  # audio cache expires. The normal worker still rechecks images before
  # synthesizing and validates the new recording against the natural window.
  spoken=selected_voice_request(lang,' '.join(slot['text'] for slot in slots))['input']['text']
  digest=hashlib.sha256(spoken.encode()).hexdigest()
  if any(item.get('text_sha256')==digest and item.get('audio_sha256')==voice.get('sha256') for item in voice.get('attempts',[])):
   return slots
 # A later alignment/render failure does not invalidate a completed native recording.
 # Reuse it only in a fresh job, with exact source spans and all downstream gates rerun.
 with connect() as db:rows=db.execute("SELECT v.job_id,v.receipt FROM voice_attempts v JOIN jobs j ON j.id=v.job_id WHERE j.topic=? AND j.language=? AND j.duration_s=? AND j.status='failed' AND COALESCE(j.review_status,'pending')!='changes_requested' AND v.voice=? AND v.state='measured' ORDER BY j.created_at DESC,v.attempt DESC LIMIT 12",(topic,lang,duration,SELECTED_VOICES[lang][1])).fetchall()
 for row in rows:
  try:
   receipt=json.loads(row['receipt']);digest=receipt.get('text_sha256','')
   if not safe_id(row['job_id']) or not re.fullmatch('[a-f0-9]{64}',digest):continue
   evidence=json.loads((RENDER/row['job_id']/('verified-input-'+digest[:16]+'.json')).read_text())
   slots=source_verified_native_plan(evidence,receipt,sources,topic,lang,duration)
   if slots and cached_native_voice(SELECTED_VOICES[lang][1],digest):return slots
  except (OSError,ValueError,KeyError,TypeError):continue
 return None

def narration_digest(lang,slots):
 spoken=selected_voice_request(lang,' '.join(slot['text'] for slot in slots))['input']['text']
 return hashlib.sha256(spoken.encode()).hexdigest()

def distinct_narration_plan(sources,topic,lang,duration,planning_seconds,seen,direction):
 if source_overview_mode(sources):
  target=duration*950
  best=None;probed=set();digests=set()
  for offset in (0,.5,-.5,1.5,-1.5,3,-3,5,-5):
   budget=max(5,min(90,planning_seconds+direction*offset))
   if budget in probed:continue
   probed.add(budget)
   candidate=plan_script(sources,topic,lang,budget,max_beats=duration//5,excluded_narrations=seen)
   if not candidate:continue
   digest=narration_digest(lang,candidate)
   if digest in seen or digest in digests:continue
   digests.add(digest)
   predicted=natural_duration_ms(' '.join(slot['text'] for slot in candidate),lang)
   error=abs(predicted-target)
   if error<=duration*15:return candidate,budget
   if best is None or error<best[0]:best=(error,candidate,budget)
  if best is not None:return best[1],best[2]
 for step in [*range(17),*range(-1,-17,-1)]:
  budget=max(5,min(90,planning_seconds+direction*step*.25))
  candidate=plan_script(sources,topic,lang,budget,max_beats=duration//5,excluded_narrations=seen)
  if candidate and narration_digest(lang,candidate) not in seen:return candidate,budget
 return [],planning_seconds

def prepare_illustrated_slots(sources,topic,lang,duration,planning_seconds,slots,before_send,seen=(),direction=1):
 from storyboard import SceneUnavailable,phrase_in
 for planning_attempt in range(20):
  if not slots:raise ValueError('No complete source narration with enough scene-matched media')
  try:
   before_send(slots)
   return slots
  except ImageServiceError as error:
   global IMAGE_SERVICE_RETRIES
   if error.status!=503 or IMAGE_SERVICE_RETRIES>=2:raise
   IMAGE_SERVICE_RETRIES+=1
   jid=getattr(before_send,'job_id',None)
   if jid:update(jid,stage='visuals',message='Image service temporarily unavailable; delayed retry '+str(IMAGE_SERVICE_RETRIES)+' of 2')
   time.sleep(5*IMAGE_SERVICE_RETRIES)
  except SceneUnavailable as error:
   source=sources[error.source_index]
   excluded=source.setdefault('excluded_visual_sentences',[])
   source.setdefault('visual_planning_rejections',[]).append({'source_sentence':error.source_sentence,'reason':str(error),'visual_target':error.visual_target})
   jid=getattr(before_send,'job_id',None)
   if jid:
    folder=RENDER/jid;folder.mkdir(parents=True,exist_ok=True)
    draft=folder/'planning-rejections.tmp';draft.write_text(json.dumps({'implementation_hashes':implementation_hashes(),'rejections':[row for item in sources for row in item.get('visual_planning_rejections',[])]},ensure_ascii=False));draft.replace(folder/'planning-rejections.json')
   if error.source_sentence in excluded:raise
   excluded.append(error.source_sentence)
   # If a linked subject has no suitable media, do not repeatedly choose
   # equivalent facts about the same unavailable subject.
   if error.visual_target and error.visual_target.get('intent',{}).get('name')!='person event':
    target=error.visual_target
    names=[target.get(key,'') for key in ('name','native_name','anchor')]
    for paragraph in source['text'].splitlines():
     for sentence in sentences(paragraph):
      if any(len(name)>=3 and phrase_in(name,sentence) for name in names) and sentence not in excluded:excluded.append(sentence)
   if seen:
    slots,planning_seconds=distinct_narration_plan(sources,topic,lang,duration,planning_seconds,seen,direction)
   else:
    slots=plan_script(sources,topic,lang,planning_seconds,max_beats=duration//5)
 raise ValueError('Scene planning exhausted its bounded source alternatives before synthesis')

def prepare_selected_narration(sources,topic,lang,jid,duration,before_send=None):
 # Change complete source sentences after a measured miss, never the voice or playback rate.
 planning_seconds=initial_natural_budget(sources,topic,lang,duration);seen=out_of_window_narrations(topic,lang,duration);attempts=[];slots=[];completed_plan=completed_narration_plan(sources,topic,lang,duration)
 for attempt in (1,2,3):
  direction=-1 if attempts and attempts[-1]['duration_ms']>duration*1000 else 1
  if attempt==1 and completed_plan:
   slots=completed_plan
  elif seen and source_overview_mode(sources):
   slots,planning_seconds=distinct_narration_plan(sources,topic,lang,duration,planning_seconds,seen,direction)
   if not slots:raise ValueError('no different complete text fits the correction range; no duplicate synthesis')
  else:
   slots=plan_script(sources,topic,lang,planning_seconds,max_beats=duration//5)
   if slots and narration_digest(lang,slots) in seen:
    slots,planning_seconds=distinct_narration_plan(sources,topic,lang,duration,planning_seconds,seen,direction)
    if not slots:raise ValueError('no different complete text fits the correction range; no duplicate synthesis')
  if not slots or len(slots)>duration//5:raise ValueError('no complete source narration fits the natural speaking budget')
  if before_send is not None:
   slots=prepare_illustrated_slots(sources,topic,lang,duration,planning_seconds,slots,before_send,seen,direction)
  script=' '.join(slot['text'] for slot in slots);spoken=selected_voice_request(lang,script)['input']['text'];identity=hashlib.sha256(spoken.encode()).hexdigest()
  if identity in seen:raise ValueError('Duplicate narration prevented before synthesis')
  seen.add(identity)
  update(jid,stage='voice',progress=50,message='Creating narration with your selected '+lang.upper()+' voice; attempt '+str(attempt))
  path,measured=google_voice_once(lang,script,jid,attempt);measured={**measured,'internal_duration_estimate_ms':measured_sentence_ms(spoken,lang)};attempts.append(measured);actual=measured['duration_ms']
  low,high=natural_voice_window(duration)
  if low<=actual<=high:break
  if source_overview_mode(sources):
   from statistics import median
   # Recalibrate the estimator using this job's completed native recordings.
   NATURAL_RATE_CACHE[lang]=median(item['duration_ms']/item['characters'] for item in attempts if item.get('characters'))
   NATURAL_INTERNAL_RATE_CACHE[lang]=median(item['duration_ms']/item['internal_duration_estimate_ms'] for item in attempts if item.get('internal_duration_estimate_ms'))
   # Visual replanning can leave only much shorter or longer scripts. Move the
   # search budget after calibration, while still ranking against the original
   # delivery window in distinct_narration_plan.
   predicted=natural_duration_ms(spoken,lang)
   shift=0 if low<=predicted<=high else max(-8,min(8,(duration*950-predicted)/1000))
   planning_seconds=max(5,min(90,duration+shift))
  else:planning_seconds=max(10,min(90,round(planning_seconds*(duration*1000-500)/max(actual,1))))
 else:raise ValueError('three distinct natural narration texts did not fit; no speed change or voice substitution')
 # Align the exact, unmodified natural audio through the existing media worker.
 final=VOICE/jid/'final.mp3';final.parent.mkdir(parents=True,exist_ok=True)
 with final.open('xb') as output:output.write(path.read_bytes())
 scene_inputs=[{'scene_uuid':str(uuid.uuid5(uuid.UUID(jid),'spoken:'+str(i))),'scene_key':str(i),'narration':slot['text']} for i,slot in enumerate(slots)]
 payload={'language_code':lang,'narration':script,'audio_sha256':measured['audio_sha256'],'audio_duration_ms':actual,'scenes':scene_inputs}
 update(jid,stage='alignment',progress=55,message='Aligning captions to the exact selected voice recording')
 request=urllib.request.Request(WORKER+'/alignments/'+jid,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(request,timeout=240) as response:alignment=json.loads(response.read(2_000_000))
 except urllib.error.HTTPError as error:
  try:failure=json.loads(error.read(4000))
  except (ValueError,AttributeError):failure={}
  message=failure.get('message','')
  raw_alignment=DATA/'alignments'/jid/'whisper.json'
  if error.code!=422 or 'lexical tokens do not reconstruct' not in message or not raw_alignment.is_file():raise ValueError('Narration alignment failed: '+(message or 'HTTP '+str(error.code))) from error
  from alignment_core import _build_scene_timings
  recovered=_build_scene_timings(script,scene_inputs,json.loads(raw_alignment.read_text()),actual)
  alignment={'status':'ready','audio_sha256':measured['audio_sha256'],**recovered,'tokenizer_recovery':'project apostrophe-normalized lexical tokens; no provider resend'}
  (raw_alignment.parent/'factory-recovered.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2))
 timings=alignment.get('scene_timings',[])
 if alignment.get('status')!='ready' or alignment.get('audio_sha256')!=measured['audio_sha256'] or alignment.get('global_coverage',0)<.95 or len(timings)!=len(slots):raise ValueError('selected voice alignment did not cover the complete narration')
 targets=[];speech=[];start=0
 for i,(slot,timing) in enumerate(zip(slots,timings)):
  if timing['scene_uuid']!=scene_inputs[i]['scene_uuid'] or timing['scene_key']!=str(i):raise ValueError('narration alignment identity changed')
  end=duration*1000 if i==len(slots)-1 else round((timing['end_ms']+timings[i+1]['start_ms'])/200)*100
  slot['speech_start_ms']=timing['start_ms'];slot['speech_end_ms']=timing['end_ms']
  targets.append(end-start);speech.append(timing['end_ms']-timing['start_ms']);start=end
 audit={'engine':'Google Cloud Text-to-Speech','voice':SELECTED_VOICES[lang][1],'audio_duration_ms':actual,'speech_duration_ms':speech,'beat_duration_ms':targets,'sha256':measured['audio_sha256'],'audio_tempo_factor':1.0,'attempts':attempts,'alignment_coverage':alignment['global_coverage']}
 return slots,final,actual,speech,targets,audit

def post_render(jid,payload):
 from renderer import render
 return render(jid,payload,DATA)
def scrub_error(e):
 if hasattr(e,'code'):return 'provider returned HTTP '+str(e.code)
 s=str(e)
 for group in PROVIDERS.values():
  if isinstance(group,dict):
   for v in group.values():
    if isinstance(v,str) and len(v)>6:s=s.replace(v,'[redacted]')
 return s[:500]
JOB_TIMEOUT_SECONDS=900
def execute_job(jid):
 process=None
 try:
  process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run-job',jid],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,start_new_session=True)
  try:_,error=process.communicate(timeout=JOB_TIMEOUT_SECONDS)
  except subprocess.TimeoutExpired:
   os.killpg(process.pid,signal.SIGKILL);process.communicate()
   raise TimeoutError('job exceeded the '+str(JOB_TIMEOUT_SECONDS)+' second runtime limit')
  job=get_job(jid) or {}
  if job.get('status') in {'queued','running'} or (process.returncode and job.get('status')!='ready'):
   raise RuntimeError((error or 'worker exited before producing a final job state')[-500:])
 except Exception as error:
  if process is not None and process.poll() is None:
   os.killpg(process.pid,signal.SIGKILL);process.communicate()
  for folder in (VISUAL/jid,VOICE/jid,ROOT/'tmp'/jid):shutil.rmtree(folder,ignore_errors=True)
  job=get_job(jid) or {}
  if job.get('status')!='ready':update(jid,status='failed',stage='failed',progress=100,message='Worker stopped',error=scrub_error(error))

def prepare_visuals(jid,sources,topic,lang,duration,slots):
 from storyboard import SceneUnavailable
 last_unavailable=None
 for _ in range(duration*2//5):
  try:return _prepare_visuals(jid,sources,topic,lang,duration,slots)
  except ShotCapacityError:
   if last_unavailable is not None:raise last_unavailable
   raise
  except SceneUnavailable as error:
   available=getattr(error,'verified_in_beat',0);beat=getattr(error,'beat_index',None)
   if available<2 or beat is None:raise
   old_cap=slots[beat].get('visual_shot_cap',duration*2//5)
   if available>=old_cap:raise
   slots[beat]['visual_shot_cap']=available;last_unavailable=error
   # Preserve the facts and total image count. Other beats may supply surplus
   # shots while this beat retains at least two independently verified photos.
   shutil.rmtree(VISUAL/jid,ignore_errors=True)
  except urllib.error.HTTPError as error:
   if error.code in {429,503}:raise ImageServiceError(error.code) from error
   raise
 if last_unavailable is not None:raise last_unavailable
 raise ValueError('Bounded scene layout did not complete')

def photo_selection_order(beat_for_shot,scene_slots,eligible_by_shot):
 ordinals=[];seen={}
 for beat in beat_for_shot:
  ordinals.append(seen.get(beat,0));seen[beat]=seen.get(beat,0)+1
 def priority(index):
  slot=scene_slots[index]
  specific=bool(slot.get('visual_target')) or (slot.get('process_intent') and scene_actions(slot['text'])!={'production'})
  return (ordinals[index]>=2,not specific,len(eligible_by_shot[index]),ordinals[index],index)
 return sorted(range(len(beat_for_shot)),key=priority)

def _prepare_visuals(jid,sources,topic,lang,duration,slots):
 visual_count=duration*2//5
 beat_count=len(slots)
 beat_for_shot=shot_beats(visual_count,beat_count);shots_per_beat=[beat_for_shot.count(index) for index in range(beat_count)];first_shot=[beat_for_shot.index(index) for index in range(beat_count)]
 for slot in slots:
  slot['language']=lang;slot['entity_profile']=sources[0].get('entity_profile',{});slot['source_driven']=source_overview_mode(sources);slot['requested_shots']=visual_count
  if named_place_subject(slot['entity_profile']):
   slot['place_features']=place_scene_features(slot['text'],lang)
   slot['place_detail_query']=place_detail_query(slot,slot['entity_profile'])
  if insect_subject(slot['entity_profile']):slot['insect_features']=insect_scene_features(slot['text'])
  if volcanic_subject(slot['entity_profile']):slot['volcanic_features']=volcanic_features(slot['text'])
  source=sources[slot['source_index']]
  if sources[0].get('english_search_topic'):slot['english_search_topic']=sources[0]['english_search_topic']
  slot['visual_title']=source.get('visual_title') or (source['title'] if lang=='en' else '')
  if not slot.get('process_intent'):
   primary_context=slot.get('source_driven') and slot['entity_profile'].get('kind')!='human'
   slot['visual_title']=(sources[0].get('visual_title') or sources[0]['title']) if primary_context else scoped_visual_title(slot,sources,lang) if slot.get('source_driven') else visual_context_title(slot,sources,lang)
 media_topic=media_search_topic(topic,lang,sources)
 update(jid,stage='visuals',progress=max(20,(get_job(jid) or {}).get('progress',0)),message='Searching a bounded photo pool; requiring unique relevant assets')
 aliases=[media_topic] if slots[0].get('process_intent') else media_aliases(media_topic)
 for slot in slots:slot['topic_aliases']=aliases
 from storyboard import build,shot_slots
 build(slots,sources,lang,sys.modules[__name__])
 beat_for_shot=storyboard_beats(visual_count,slots)
 shots_per_beat=[beat_for_shot.count(index) for index in range(beat_count)];first_shot=[beat_for_shot.index(index) for index in range(beat_count)]
 scene_slots=shot_slots(slots,beat_for_shot)
 if visual_count>=18 and slots[0]['source_driven'] and slots[0]['entity_profile'].get('kind')=='concept' and not slots[0].get('process_intent') and not sources[0].get('article_media_loaded'):
  try:
   for photo in article_photo_candidates(sources[0]):DISCOVERED_PHOTOS.setdefault((photo['provider'],photo['id']),photo)
  except urllib.error.HTTPError as error:
   if error.code in {429,503}:raise
  except (OSError,ValueError):pass
  sources[0]['article_media_loaded']=True
 candidates=discover_photos(media_topic,'en',slots)
 if sources[0].get('entity_profile',{}).get('kind')=='human':
  profile=sources[0]['entity_profile']
  portrait_queries={'haswbstatement:P180='+profile['id'],profile['name']+' incategory:"CC-BY-2.0" -intitle:Caricature -intitle:graph','intitle:"'+profile['name']+'" incategory:"CC-BY-4.0" -intitle:Caricature -intitle:graph'}
  from storyboard import query_plan
  event_queries=set(query_plan([{**slot,'visual_targets':[target for target in slot.get('visual_targets',[]) if target.get('intent',{}).get('name')=='person event']} for slot in slots]))
  bind_human_images([candidate for candidate in candidates if candidate.get('query') in portrait_queries|event_queries],profile)
 if named_place_subject(sources[0].get('entity_profile',{})) or slots[0].get('process_intent'):candidates=bind_place_images(candidates,sources[0]['entity_profile'])
 if len(candidates)<visual_count:raise ValueError('photo search found '+str(len(candidates))+' distinct candidates; '+str(visual_count)+' are required')
 competitors=[] if slots[0].get('process_intent') else visual_competitors(media_topic,candidates)
 for slot in slots:slot['visual_competitors']=competitors
 get_pixel_verifier()
 shot_options,edges=rank_storyboard_photos(candidates,scene_slots,beat_for_shot,media_topic)
 allocated=allocate_photos(candidates,slots,media_topic,visual_count,scene_slots=scene_slots,edges=edges)
 candidate_indexes={id(candidate):index for index,candidate in enumerate(candidates)}
 assigned_indexes=[candidate_indexes[id(candidate)] for candidate in allocated]
 eligible_by_shot=[set(edge) for edge in edges]
 selected=[];used_ids=set();hashes=[];rejected_contexts=set();used_origins=set()
 raw_cache=ROOT/'tmp'/jid/'scene-photo-cache';raw_cache.mkdir(parents=True,exist_ok=True)
 from photo_duplicates import fingerprint,duplicate
 fingerprints=[];selected_positions={}
 for i in photo_selection_order(beat_for_shot,scene_slots,eligible_by_shot):
  for slot,ranked_options in shot_options[i]:
   # Reserve scarce images only for a stricter future constraint. Equal
   # subject constraints share a pool; reserving their unverified assignments
   # can falsely exhaust today's scene despite usable images in that pool.
   current_eligible=set(ranked_options)
   reserved={index for future_index,index in enumerate(assigned_indexes[i+1:],i+1) if eligible_by_shot[future_index]<current_eligible}
   assigned=assigned_indexes[i]
   ranked=([assigned] if assigned in current_eligible else [])+[index for index in ranked_options if index!=assigned and index not in reserved]
   context_key=photo_audit_context(media_topic,slot)
   found=None;attempts=0;rejection_reasons=[]
   for index in ranked:
    p=candidates[index]
    key=(p['provider'],p['id'])
    context=(key,(slot.get('visual_target') or {}).get('id'),beat_for_shot[i])
    if key in used_ids or bool(photo_origins(p)&used_origins) or context in rejected_contexts:continue
    meta=set(tokens(p['alt']))
    if not meta:continue
    if attempts>=24:break
    attempts+=1
    shot=str(uuid.uuid4());folder=VISUAL/jid/shot;folder.mkdir(parents=True,exist_ok=False)
    cache_key=hashlib.sha256(json.dumps([p['provider'],p['id'],p['url']]).encode()).hexdigest()
    raw=raw_cache/(cache_key+'.source');final=folder/'selected.jpg'
    try:
     if not raw.exists():
      partial=raw.with_suffix('.part')
      try:download_photo(p,partial);partial.replace(raw)
      finally:partial.unlink(missing_ok=True)
     raw.touch()
     cache_files=sorted(raw_cache.glob('*.source'),key=lambda path:path.stat().st_mtime)
     cached_bytes=sum(path.stat().st_size for path in cache_files)
     for old_path in cache_files:
      if cached_bytes<=64*1024*1024:break
      if old_path!=raw:cached_bytes-=old_path.stat().st_size;old_path.unlink()
     with Image.open(raw) as im:ph=dhash(im.convert('RGB'))
     if any((ph^old).bit_count()<=4 for old in hashes):shutil.rmtree(folder);continue
     target=slot.get('visual_target') or {}
     audit_path=raw_cache/(cache_key+'-'+context_key+'.json');raw_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
     genre_path=raw_cache/(cache_key+'.photograph.json')
     genre_saved=json.loads(genre_path.read_text()) if genre_path.exists() else {}
     if genre_saved.get('raw_sha256')==raw_sha:photographic_audit=genre_saved['audit']
     else:
      photographic_audit=get_pixel_verifier().check_photograph(raw)
      genre_path.write_text(json.dumps({'raw_sha256':raw_sha,'audit':photographic_audit},ensure_ascii=False))
     if not photographic_audit['passed']:raise ValueError('Asset is not a verified photograph: score='+str(photographic_audit['positive_score'])+' margin='+str(photographic_audit['margin']))
     saved=json.loads(audit_path.read_text()) if audit_path.exists() else {}
     if saved.get('raw_sha256')==raw_sha:pixel_audit=saved['audit']
     else:
      pixel_audit=pixel_check(raw,media_topic,slot,p)
      audit_path.write_text(json.dumps({'raw_sha256':raw_sha,'audit':pixel_audit},ensure_ascii=False))
     if target:pixel_audit['scene_target']=target
     pixel_audit['photographic_screen']=photographic_audit
     if not pixel_audit['passed']:raise ValueError('pixel comparison rejected candidate: score='+str(pixel_audit['positive_score'])+' margin='+str(pixel_audit['margin']))
     source_fingerprint=fingerprint(raw)
     if any(duplicate(source_fingerprint,previous)['duplicate'] for previous in fingerprints):raise ValueError('Repeated source photograph after crop or resize')
     make_card(raw,slot['text'],final,p)
    except ImageServiceError:
     shutil.rmtree(folder,ignore_errors=True);raise
    except Exception as e:
     rejected_contexts.add(context);rejection_reasons.append(scrub_error(e));shutil.rmtree(folder,ignore_errors=True);continue
    row=dict(p);row.update({'visual_target':slot.get('visual_target'),'visual_role':slot.get('visual_role'),'pixel_verification':pixel_audit,'caption':slot['text'],'article_title':sources[slot['source_index']]['title'],'article_url':sources[slot['source_index']]['url'],'asset_sha256':hashlib.sha256(final.read_bytes()).hexdigest()})
    found={'provider':p,'shot':shot,'path':final,'hash':row['asset_sha256'],'phash':ph,'fingerprint':source_fingerprint,'row':row};break
   if found is not None:break
  if found is None:
   from storyboard import SceneUnavailable
   error=SceneUnavailable(slot,'no verified scene-matched image for shot '+str(i+1)+' after '+str(attempts)+' candidates; '+ '; '.join(rejection_reasons[-3:]))
   error.beat_index=beat_for_shot[i];error.verified_in_beat=sum(beat_for_shot[j]==error.beat_index for j in selected_positions)
   raise error
  used_origins.update(photo_origins(found['provider']));hashes.append(found['phash']);fingerprints.append(found['fingerprint']);used_ids.add((found['provider']['provider'],found['provider']['id']));selected.append(found);selected_positions[i]=found
  update(jid,progress=max(20+int(len(selected)*25/visual_count),(get_job(jid) or {}).get('progress',0)),message='Prepared '+str(len(selected))+' of '+str(visual_count)+' unique photos')
 selected=[selected_positions[index] for index in range(visual_count)]
 visual_rows=[item['row'] for item in selected]
 return {'selected':selected,'visual_rows':visual_rows,'media_topic':media_topic,'beat_count':beat_count,'beat_for_shot':beat_for_shot,'shots_per_beat':shots_per_beat,'first_shot':first_shot,'script':' '.join(slot['text'] for slot in slots)}

def beat_source(slot,source):
 span=slot['source_sentence'];start=slot['source_position']
 if not source.get('translation_model'):
  return {'source_span':span,'source_start':start}
 evidence=source['translated_spans'].get(str(start))
 if not evidence or evidence['translated_span']!=span:
  raise ValueError('Translated narration lost its original source sentence')
 return {**evidence,'source_language':source['source_language'],
         'source_revision_url':source['revision_url'],'translation_model':source['translation_model']}

def run_job(jid):
 j=get_job(jid);topic=j['topic'];lang=j['language'];duration=j['duration_s'];visual_count=duration*2//5;beat_count=duration//5
 try:
  connection=google_connection_status()
  if not connection['ready']:
   update(jid,status='needs_connection',stage='connection',progress=0,message=connection['message'],error=None);return
  update(jid,status='running',stage='research',progress=5,message='Finding cited facts in the selected language')
  sources=relevant_sources(load_sources(topic,lang,duration),topic,lang)
  if not sources:
   identifier=topic_identifier(topic)
   reference=identifier_article(identifier,lang) if identifier else {}
   if reference:
    language={'en':'English','pl':'Polish','ru':'Russian','uk':'Ukrainian'}[lang]
    message='Found '+reference['title']+', but no usable Wikipedia article for it in '+language+'.'
    partial={'sources':[reference],'resolved_topic':reference['title'],'input_reason':'source_language_unavailable'}
    update(jid,status='needs_input',stage='research',progress=0,message=message,error=None,manifest=json.dumps(partial,ensure_ascii=False));return
   partial={'input_reason':'source_not_found'}
   update(jid,status='needs_input',stage='research',progress=0,message='No usable Wikipedia source was found for this topic in the selected language.',error=None,manifest=json.dumps(partial,ensure_ascii=False));return
  if subject_rejected(topic,lang,sources[0].get('entity_profile',{}).get('id')):
   partial={'sources':[{'title':source['title'],'url':source['url']} for source in sources[:3]],'resolved_topic':sources[0]['title'],'resolved_entity_id':sources[0].get('entity_profile',{}).get('id'),'input_needed':'This source interpretation was rejected. Add context to specify the subject you mean.'}
   update(jid,status='needs_input',stage='research',progress=0,message=partial['input_needed'],error=None,manifest=json.dumps(partial,ensure_ascii=False));return
  slots=plan_script(sources,topic,lang,duration)
  if not slots and not sources[0].get('translation_model'):
   translated=translated_research_sources(topic,lang,duration)
   if translated and not subject_rejected(topic,lang,translated[0].get('entity_profile',{}).get('id')):
    translated_slots=plan_script(translated,topic,lang,duration)
    if translated_slots:sources,slots=translated,translated_slots
  if not slots:
   partial={'input_reason':'source_scope_unavailable'}
   update(jid,status='needs_input',stage='research',progress=0,message='The sources could not support a complete script covering the requested focus and duration.',error=None,manifest=json.dumps(partial,ensure_ascii=False));return
  visual_state={}
  def before_send(planned_slots):
   provenance=[beat_source(slot,sources[slot['source_index']]) for slot in planned_slots]
   shutil.rmtree(VISUAL/jid,ignore_errors=True)
   prepared=prepare_visuals(jid,sources,topic,lang,duration,planned_slots)
   visual_state.clear();visual_state.update(prepared)
   spoken=selected_voice_request(lang,' '.join(slot['text'] for slot in planned_slots))['input']['text'];text_hash=hashlib.sha256(spoken.encode()).hexdigest()
   evidence={'phase':'images verified before synthesis','job_id':jid,'voice':SELECTED_VOICES[lang][1],'spoken_text':spoken,'text_sha256':text_hash,'beats':[{**{key:slot.get(key) for key in ('text','source_index','source_sentence','source_position','visual_targets')},**source_proof} for slot,source_proof in zip(planned_slots,provenance,strict=True)],'visuals':prepared['visual_rows'],'sources':[{'title':source['title'],'url':source['url'],'revision_url':source.get('revision_url')} for source in sources],'implementation_hashes':implementation_hashes()}
   evidence_dir=RENDER/jid;evidence_dir.mkdir(parents=True,exist_ok=True)
   evidence_path=evidence_dir/('verified-input-'+text_hash[:16]+'.json')
   temporary=evidence_path.with_suffix('.tmp');temporary.write_text(json.dumps(evidence,ensure_ascii=False,indent=2));temporary.replace(evidence_path)
  before_send.job_id=jid
  slots,mp3,audio_ms,speech_ms,slot_targets,voice_audit=prepare_selected_narration(sources,topic,lang,jid,duration,before_send=before_send)
  if visual_state.get('script')!=' '.join(slot['text'] for slot in slots):raise ValueError('prepared storyboard does not match the final narration')
  selected=visual_state['selected'];visual_rows=visual_state['visual_rows'];media_topic=visual_state['media_topic']
  beat_count=visual_state['beat_count'];beat_for_shot=visual_state['beat_for_shot'];shots_per_beat=visual_state['shots_per_beat'];first_shot=visual_state['first_shot']
  audio_sha=hashlib.sha256(mp3.read_bytes()).hexdigest();target=duration*1000;beat_starts=[sum(slot_targets[:i]) for i in range(beat_count)];cursor=0;scenes=[]
  for i,item in enumerate(selected):
   beat=beat_for_shot[i];beat_start=beat_starts[beat];end=target if i==visual_count-1 else beat_start+slot_targets[beat]*(i-first_shot[beat]+1)//shots_per_beat[beat];end=round(end/100)*100;spoken_end=min(target,slots[beat]['speech_end_ms']);speech_start=max(cursor,slots[beat]['speech_start_ms']);speech_end=min(end,spoken_end,audio_ms)
   if speech_end<=speech_start:speech_start=cursor;speech_end=min(end,cursor+1)
   scenes.append({'scene_uuid':str(uuid.uuid4()),'shot_uuid':item['shot'],'visual_asset_id':str(uuid.uuid4()),'media_type':'photo','asset_sha256':item['hash'],'asset_path':str(item['path']),'asset_width':1080,'asset_height':1920,'scene_order':i+1,'segment_start_ms':cursor,'segment_end_ms':end,'speech_start_ms':speech_start,'speech_end_ms':speech_end})
   cursor=end
  update(jid,stage='render',progress=80,message='Rendering 1080×1920 MP4 and decoding the complete file')
  attribution=output_credits([sources[index] for index in sorted({slot['source_index'] for slot in slots})],visual_rows)
  rendered=post_render(jid,{'attribution':attribution,'input_audio_sha256':audio_sha,'audio_duration_ms':audio_ms,'target_duration_ms':target,'requested_duration_ms':duration*1000,'scenes':scenes})
  video=Path(rendered['storage_path'])
  full=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=150)
  if full.returncode:raise ValueError('full MP4 decode failed')
  if not rendered.get('qa_passed'):raise ValueError('media-worker render QA failed')
  manifest={'version':'universal-1','output_license':OUTPUT_LICENSE,'attribution':attribution,'implementation_hashes':implementation_hashes(),'job_id':jid,'topic':topic,'language':lang,'requested_duration_s':duration,'visual_search_topic':media_topic,'created_at':now(),'script':' '.join(x['text'] for x in slots),'resolved_topic':slots[0].get('resolved_topic',topic),'resolved_entity_id':sources[0].get('entity_profile',{}).get('id'),'script_mode':'source-grounded overview','llm_calls':0,'sources':[{'title':x['title'],'url':x['url'],'retrieval_note':x.get('retrieval_note'),'source_type':x.get('source_type','article'),'revision_id':x.get('revision_id'),'revision_url':x.get('revision_url'),'label':x.get('label'),'description':x.get('description')} for x in sources],'beats':[{'order':i+1,'caption':s['text'],**beat_source(s,sources[s['source_index']]),'source_title':sources[s['source_index']]['title'],'source_url':sources[s['source_index']]['url']} for i,s in enumerate(slots)],'visuals':[{'order':i+1,'provider':x['provider'],'provider_id':x['id'],'alt':x['alt'],'creator':x['creator'],'creator_url':x['creator_url'],'provider_page':x['source_url'],'license':x.get('license'),'license_url':x.get('license_url'),'changes':x.get('changes'),'search_query':x.get('query',topic),'caption':x['caption'],'source_article':x['article_url'],'source_title':x['article_title'],'asset_sha256':x['asset_sha256'],'pixel_verification':x['pixel_verification'],'visual_target':x.get('visual_target'),'visual_role':x.get('visual_role')} for i,x in enumerate(visual_rows)],'narration':voice_audit,'render':rendered,'audit':{'shots_required':visual_count,'narration_beats':beat_count,'unique_assets':len({x['asset_sha256'] for x in visual_rows}),'images_per_narration_beat':shots_per_beat,'minimum_two_images_per_beat':all(count>=2 for count in shots_per_beat),'average_shot_duration_ms':target/visual_count,'source_count':len(sources),'all_visuals_have_provenance':all(x['source_url'] and x['article_url'] for x in visual_rows),'images_verified_before_voice':True,'all_images_pixel_checked':all(x['pixel_verification']['passed'] for x in visual_rows),'all_images_photographically_screened':all(x['pixel_verification'].get('photographic_screen',{}).get('passed') for x in visual_rows),'scene_plan_version':'source-linked-v2','source_linked_shots':sum(bool(x.get('visual_target')) for x in visual_rows),'establishing_shots':sum(x.get('visual_role')=='establishing' for x in visual_rows),'full_decode':True,'renderer_gates':rendered.get('qa_gates',{})},'retention_days':30}
  (RENDER/jid/'universal-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
  shutil.rmtree(VISUAL/jid,ignore_errors=True);shutil.rmtree(VOICE/jid,ignore_errors=True);shutil.rmtree(ROOT/'tmp'/jid,ignore_errors=True)
  update(jid,status='ready',stage='review',progress=100,message='MP4 ready for review; listening approval pending',manifest=json.dumps(manifest,ensure_ascii=False),error=None)
 except Exception as e:
  for p in (VISUAL/jid,VOICE/jid,ROOT/'tmp'/jid):shutil.rmtree(p,ignore_errors=True)
  stage=(get_job(jid) or {}).get('stage','unknown')
  update(jid,status='failed',stage='failed',progress=100,message='Stopped at '+stage,error=scrub_error(e))
RENDER_MAX_BYTES=2*1024*1024*1024
CACHE_MAX_BYTES=512*1024*1024
DISK_RESERVE_BYTES=2*1024*1024*1024
def directory_bytes(path):
 total=0
 if not path.exists() or path.is_symlink():return 0
 for item in path.rglob('*'):
  try:
   if item.is_file() and not item.is_symlink():total+=item.stat().st_size
  except OSError:pass
 return total
def cleanup():
 cutoff=time.time()-30*86400;finished=[]
 with connect() as c:rows=c.execute("SELECT id,status,created_at,updated_at,review_status,manifest IS NOT NULL AS has_manifest FROM jobs WHERE status IN ('ready','failed','preflight_passed','expired')").fetchall()
 for row in rows:
  jid=safe_id(row['id'])
  if not jid or jid!=row['id']:continue
  try:created=datetime.fromisoformat(row['created_at']).timestamp();updated=datetime.fromisoformat(row['updated_at']).timestamp()
  except (TypeError,ValueError):continue
  path=RENDER/jid;alignment=DATA/'alignments'/jid
  if row['status']=='expired':
   if row['has_manifest']:update(jid,manifest=None)
   for target in (path,alignment):
    if target.exists() and not target.is_symlink():shutil.rmtree(target,ignore_errors=True)
   continue
  if row['status']=='failed':
   if updated<time.time()-86400:
    for target in (path,alignment,VISUAL/jid,VOICE/jid,ROOT/'tmp'/jid):
     if target.exists() and not target.is_symlink():shutil.rmtree(target,ignore_errors=True)
   continue
  if created<cutoff:
   try:
    for target in (path,alignment):
     if target.exists() and not target.is_symlink():shutil.rmtree(target)
    update(jid,status='expired',stage='expired',progress=100,message='MP4 expired after 30 days',manifest=None)
   except OSError:pass
   continue
  finished.append({'id':jid,'path':path,'created':created,'review':row['review_status'],'bytes':directory_bytes(path)+directory_bytes(alignment)})
 total=sum(item['bytes'] for item in finished)
 priority={'changes_requested':0,'pending':1,'approved':2}
 for item in sorted(finished,key=lambda x:(priority.get(x['review'],1),x['created'])):
  if total<=RENDER_MAX_BYTES:break
  try:
   for target in (item['path'],DATA/'alignments'/item['id']):
    if target.exists() and not target.is_symlink():shutil.rmtree(target)
   total-=item['bytes'];update(item['id'],status='expired',stage='expired',progress=100,message='MP4 removed under the 2 GB output retention limit',manifest=None)
  except OSError:pass
 cache=ROOT/'cache'
 if cache.exists():
  for path in cache.glob('*.json'):
   try:
    if not path.is_symlink() and time.time()-path.stat().st_mtime>86400:path.unlink()
   except OSError:pass
  files=[path for path in cache.glob('*.json') if not path.is_symlink()];total=sum(path.stat().st_size for path in files if path.exists())
  for path in sorted(files,key=lambda item:item.stat().st_mtime):
   if total<=CACHE_MAX_BYTES:break
   try:total-=path.stat().st_size;path.unlink()
   except OSError:pass
HTML=Path(__file__).with_name('index.html').read_text()
class Handler(BaseHTTPRequestHandler):
 def auth(self):
  return True
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
  if p=='/api/provider-status':
   force=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('refresh',['0'])[0]=='1'
   return self.json_out(200,google_connection_status(force=force))
  if p=='/api/jobs':
   view=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('view',['user'])[0]
   filters={'user':"origin='user' AND status!='expired'",'examples':"origin='test' AND status='ready' AND review_status!='changes_requested' AND json_extract(manifest,'$.narration.engine')='Google Cloud Text-to-Speech'",'tests':"origin='test'"}
   if view not in filters:return self.json_out(400,{'error':'unknown job view'})
   with connect() as c:rows=c.execute('SELECT id FROM jobs WHERE '+filters[view]+' ORDER BY created_at DESC LIMIT 50').fetchall()
   jobs=[public_job(get_job(row['id'])) for row in rows]
   for job in jobs:
    if job['manifest']:job['manifest']={key:job['manifest'][key] for key in ('script','sources','resolved_topic','resolved_entity_id','input_needed','input_reason') if key in job['manifest']}
   return self.json_out(200,{'jobs':jobs,'view':view})
  m=re.fullmatch(r'/api/jobs/([0-9a-fA-F-]{36})(?:/(video|manifest|credits))?',p)
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
   if m.group(2) in {'manifest','credits'}:
    f=RENDER/jid/('credits.txt' if m.group(2)=='credits' else 'universal-manifest.json')
    if not f.is_file():return self.json_out(404,{'error':'manifest_not_found'})
    b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8' if m.group(2)=='credits' else 'application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
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
   connection=google_connection_status()
   if not connection['ready']:return self.json_out(503,{'error':connection['message'],'code':connection['code']})
   cleanup()
   if shutil.disk_usage(DATA).free<DISK_RESERVE_BYTES:return self.json_out(507,{'error':'Less than 2 GB free disk space; no new job was created'})
   jid=str(uuid.uuid4());ts=now()
   with connect() as c:c.execute('INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message) VALUES(?,?,?,?,?,?,?,?,?,?)',(jid,ts,ts,topic,lang,duration,'queued','queued',0,'Waiting for the single worker'))
   if b.get('origin')=='test':update(jid,origin='test')
   POOL.submit(execute_job,jid);return self.json_out(202,{'id':jid,'status':'queued'})
  m=re.fullmatch(r'/api/jobs/([0-9a-fA-F-]{36})/subject',p)
  if m:
   jid=safe_id(m.group(1));j=get_job(jid) if jid else None
   if not j:return self.json_out(404,{'error':'job_not_found'})
   entity_id=(j.get('manifest') or {}).get('resolved_entity_id')
   try:reject_subject(j['topic'],j['language'],entity_id)
   except ValueError as error:return self.json_out(400,{'error':str(error)})
   update(jid,review_status='changes_requested',review_note='Wrong source subject')
   return self.json_out(200,{'ok':True})
  m=re.fullmatch(r'/api/jobs/([0-9a-fA-F-]{36})/review',p)
  if m:
   jid=safe_id(m.group(1));j=get_job(jid) if jid else None
   if not j:return self.json_out(404,{'error':'job_not_found'})
   state=str(b.get('status') or '')
   if state not in {'approved','changes_requested'}:return self.json_out(400,{'error':'review status must be approved or changes_requested'})
   update(jid,review_status=state,review_note=str(b.get('note') or '')[:500]);return self.json_out(200,{'ok':True})
  return self.json_out(404,{'error':'not_found'})
 def log_message(self,*args):return
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--run-job':
  jid=safe_id(sys.argv[2])
  if not jid:raise SystemExit('invalid job id')
  run_job(jid)
 else:
  init_db();cleanup()
  ThreadingHTTPServer(('0.0.0.0',3000),Handler).serve_forever()

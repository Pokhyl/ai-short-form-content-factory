#!/usr/bin/env python3
import base64, hashlib, hmac, json, os, re, shutil, sqlite3, subprocess, time, urllib.parse, urllib.request, uuid, wave, unicodedata, sys, signal, math
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

def now(): return datetime.now(timezone.utc).isoformat()
def connect():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row
 c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA busy_timeout=20000')
 return c
def init_db():
 with connect() as c:
  c.execute("""CREATE TABLE IF NOT EXISTS jobs(\n   id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,\n   topic TEXT NOT NULL, language TEXT NOT NULL, duration_s INTEGER NOT NULL,\n   status TEXT NOT NULL, stage TEXT NOT NULL, progress INTEGER NOT NULL,\n   message TEXT NOT NULL, error TEXT, manifest TEXT,\n   review_status TEXT NOT NULL DEFAULT 'pending', review_note TEXT)""")
  if 'origin' not in {row['name'] for row in c.execute('PRAGMA table_info(jobs)')}:c.execute("ALTER TABLE jobs ADD COLUMN origin TEXT NOT NULL DEFAULT 'user'")
  c.execute("CREATE TABLE IF NOT EXISTS voice_attempts(job_id TEXT NOT NULL,attempt INTEGER NOT NULL,text_sha256 TEXT NOT NULL,voice TEXT NOT NULL,state TEXT NOT NULL,receipt TEXT,PRIMARY KEY(job_id,attempt))")
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
  return len(re.findall(patterns.get(lang,patterns['en']),text or '',re.I|re.UNICODE))
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
 SKIP_TAGS={'script','style','table','figure','gallery','sup'}
 SKIP_CLASSES={'mw-editsection','reference','navbox','metadata','mw-references-wrap','toc','sidebar','hatnote','ambox','vertical-navbox','reflist'}
 SKIP_SECTIONS={
  'en':{'references','notes','see also','further reading','external links','bibliography','works cited','sources'},
  'pl':{'przypisy','bibliografia','zobacz też','zobacz takze','dalsza lektura','linki zewnętrzne','źródła'},
  'ru':{'примечания','источники','литература','см. также','ссылки','внешние ссылки'},
  'uk':{'примітки','джерела','література','див. також','посилання','зовнішні посилання'}
 }
 def __init__(self,lang='en',paragraphs_only=False):
  self.paragraphs_only=paragraphs_only;self.paragraph_depth=0
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
  if tag in self.SKIP_TAGS or classes&self.SKIP_CLASSES or (self.paragraphs_only and tag=='li'):
   if tag not in self.VOID:self.skip=1
   return
  if tag=='p':self.paragraph_depth+=1
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
  if tag=='p':self.paragraph_depth=max(0,self.paragraph_depth-1)
  if tag in {'p','h4','li'}:self.parts.append('\n')
  elif tag in {'a','b','strong','i','em','span'}:self.parts.append(' ')
 def handle_data(self,data):
  if self.heading:self.heading_text.append(data)
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
def fit_narration(rows,count,lang,process_intent=False,duration_ms=None):
 # Exact-count duration-constrained selection over source sentences, measured in the selected voice.
 budget=((duration_ms if duration_ms is not None else count*5000)-100)//25;states=[{} for _ in range(count+1)];states[0][0]=(0.0,())
 seen=set();candidates=[]
 for row in rows:
  norm=re.sub(r'\W+','',row[2].lower())
  if norm in seen:continue
  seen.add(norm);candidates.append(row)
  if len(candidates)>=60:break
 actions=[visual_actions(row[2])-{'production'} for row in candidates]
 terms=[set(topic_terms(row[2],lang)) for row in candidates]
 penalties=[]
 for i in range(len(candidates)):
  pair=[]
  for j in range(len(candidates)):
   overlap=len(terms[i]&terms[j])/max(1,len(terms[i]|terms[j]))
   pair.append((8*len(actions[i]&actions[j]) if process_intent else 0)+(10*overlap if overlap>.35 else 0))
  penalties.append(pair)
 for index,(score,source_index,sentence,words) in enumerate(candidates):
  cost=(measured_sentence_ms(sentence,lang)+24)//25
  if cost>budget:continue
  for selected in range(min(count,index+1),0,-1):
   for used,(total,chosen) in list(states[selected-1].items()):
    target=used+cost
    if target>budget:continue
    candidate=(total+score-sum(penalties[index][old] for old in chosen),chosen+(index,))
    if target not in states[selected] or candidate[0]>states[selected][target][0]:states[selected][target]=candidate
 if not states[count]:return []
 chosen=max(states[count].values(),key=lambda item:item[0])[1]
 return [{'text':candidates[index][2],'language':lang,'source_index':candidates[index][1],'source_sentence':candidates[index][2],'score':candidates[index][0]} for index in chosen]

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
   hits=[title for title in hits if core_set<=set(topic_terms(title,lang)) or bool((set(topic_terms(title,lang))-core_set)&method_terms) or (bool(set(topic_terms(title,lang))&core_set) and bool(re.search(r'manufactur|produc|fabricat|process|produk|wytwarz|proces|производ|изготов|процесс|виробниц|виготов|процес',title,re.I)))]
  hits=sorted(hits,key=lambda title:(-len(set(topic_terms(title,lang))&core_set),hits.index(title)))
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
    if actual and len(text)>220 and 'may refer to:' not in text[:600].lower():out.append({'title':actual,'url':'https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(actual.replace(' ','_')),'text':text,'visual_title':actual if lang=='en' else next((str(link.get('*') or link.get('title') or '') for link in parsed.get('langlinks',[]) if link.get('lang')=='en'),'')})
   except Exception as e:
    if getattr(e,'code',None)==429:raise
    continue
   if len(out)>=6:break
  return out
def sentences(paragraph):
 abbreviations=r'\b(?:e\.g|i\.e|U\.S|U\.K|Mr|Mrs|Dr|Prof|np|m\.in|itp|itd|tj|tzn|tzw|ok|godz|proc|por|rys|św|т\.е|т\.д|т\.п|гг|рис|ім|ст)\.'
 protected=re.sub(abbreviations,lambda match:match.group(0).replace('.',chr(0x2024)),paragraph,re.I)
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
def grounding_terms(text,lang):
 return {term[:4] if lang!='en' else term for term in topic_terms(text,lang)}
def source_slots(sources,topic,count,lang='en',duration_s=None):
  target_ms=(duration_s if duration_s is not None else count*5)*1000
  object_terms=grounding_terms(topic,lang)
  process_intent=bool(re.search(r'\b(make|made|manufactur\w*|produc\w*|fabricat\w*|build|create|zrobi\w*|produk\w*|wytwarz\w*|изготов\w*|производ\w*|виробля\w*|виготов\w*)\b',topic,re.I))
  bottle_words=grounding_terms('bottle bottles бутылка пляшка пляшки butelka butelki',lang)
  container_words=grounding_terms('container containers packaging jar pojemnik pojemniki opakowanie тара контейнер контейнери',lang)
  rows=[]
  for si,src in enumerate(sources):
   title_terms=grounding_terms(src['title'],lang)
   for paragraph_index,paragraph in enumerate(src['text'].splitlines()):
    for sentence in sentences(paragraph):
     sentence=re.sub(r'\[[^\]]{1,240}\]','',sentence).strip();sentence=re.sub(r'\s+([,.;:!?])',r'\1',sentence);words=sentence.split()
     if not sentence.endswith(('.', '!', '?')) or not (5 if process_intent else 8)<=len(words)<=(24 if process_intent else 36):continue
     if sentence.count('(')!=sentence.count(')') or re.search(r'\bIPA\s*:|U\+[0-9A-F]{4}|Unicode',sentence):continue
     if re.match(r'^(?:examples? include|another example|for example|such)\b',sentence,re.I):continue
     if lang=='uk' and re.search(r'\bяк\b',sentence,re.I) and not re.search(r'\b(?:є|має|може|можуть|було|були|була|був|\w+(?:ється|ються|ають|ують|ить|ає|ує|али|ала|ила|или))\b',sentence,re.I):continue
     if re.search(r'\b(?:этой|этого|этих|цього|цієї|tych|tej|tego|this|these|those|such|their)\b',sentence,re.I):continue
     if re.search(r'\b(?:it|they)\b',sentence,re.I) or re.match(r'^(?:he|she|он|она|оно|они|він|вона|воно|вони|one|ona|ono|oni|jej|jego|w ten sposób)\b',sentence,re.I):continue
     history_requested=bool(re.search(r'histor|ancient|истори|істор|dziej',topic,re.I))
     if process_intent and not history_requested and re.search(r'\b(?:invention|invented|ancient|century|centuries|were|was)\b|древн|стародав|wynalezion|starożytn',sentence,re.I):continue
     sentence_terms=grounding_terms(sentence,lang);combined=sentence_terms|title_terms
     topic_hits=len(combined&object_terms);needed=min(2,len(object_terms))
     if object_terms&bottle_words and combined&container_words:topic_hits=max(topic_hits,min(2,len(object_terms)))
     direct_topic=bool(sentence_terms&object_terms);process_overlap=process_signal(sentence,lang) if process_intent else 0
     if needed and topic_hits<needed:continue
     if not process_intent and object_terms and (not direct_topic or (lang=='en' and not grounding_terms(' '.join(words[:6]),lang)&object_terms)):continue
     if lang=='en' and not process_intent and unsupported_qualifier(sentence,topic,sources):continue
     if process_intent and (not process_overlap or not direct_topic or not visual_actions(sentence)):continue
     score=topic_hits*4+len(sentence_terms&object_terms)*3+process_overlap*2+min(len(words),15)/15-.25*max(0,len(words)-15)+(3 if paragraph_index<2 and not process_intent else 0)+(4 if si==0 and not process_intent else 0)+(8 if si==0 and paragraph_index==0 and not process_intent else 0)
     rows.append((score,si,sentence,words))
  rows.sort(key=lambda x:(-x[0],x[1],abs(len(x[3])-13)))
  all_rows=list(rows)
  chosen=[];seen=set();used=set();source_counts={};action_counts={}
  while rows and len(chosen)<count:
   best_i=max(range(len(rows)),key=lambda i:rows[i][0]+.3*len(set(topic_terms(rows[i][2],lang))-used)+2/(1+source_counts.get(rows[i][1],0))-(8 if process_intent else 0)*sum(action_counts.get(action,0) for action in visual_actions(rows[i][2]) if action!='production'))
   score,si,sentence,words=rows.pop(best_i);norm=re.sub(r'\W+','',sentence.lower())
   if norm in seen:continue
   seen.add(norm);chosen.append({'text':sentence,'language':lang,'process_intent':process_intent,'source_index':si,'source_sentence':sentence,'score':score})
   used.update(topic_terms(sentence,lang));source_counts[si]=source_counts.get(si,0)+1
   for action in visual_actions(sentence):action_counts[action]=action_counts.get(action,0)+1
  if len(chosen)!=count:return []
  if sum(measured_sentence_ms(slot['text'],lang) for slot in chosen)>target_ms-100:
   chosen=fit_narration(all_rows,count,lang,process_intent,target_ms)
   if len(chosen)!=count:return []
   for slot in chosen:slot['process_intent']=process_intent
  if process_intent and not re.search(r'histor|ancient|истори|істор|dziej',topic,re.I):
   stage_order={'heat':0,'shape':1,'cool':2,'inspect':3}
   return sorted(chosen,key=lambda x:(max((stage_order[action] for action in visual_actions(x['text']) if action in stage_order),default=0),x['source_index'],sources[x['source_index']]['text'].find(x['source_sentence'])))
  return sorted(chosen,key=lambda x:(x['source_index'],sources[x['source_index']]['text'].find(x['source_sentence'])))
def source_cache_key(topic,lang):return 'wikipedia-v8|'+lang+'|'+topic
def load_sources(topic,lang):
 current=ROOT/'cache'/(hashlib.sha256(source_cache_key(topic,lang).encode()).hexdigest()+'.json')
 previous=ROOT/'cache'/(hashlib.sha256(('wikipedia-v6|'+lang+'|'+topic).encode()).hexdigest()+'.json')
 if not current.exists() and previous.exists() and time.time()-previous.stat().st_mtime<86400:
  old=json.loads(previous.read_text())
  if isinstance(old,list) and any(grounding_terms(topic,lang)&grounding_terms(source.get('title',''),lang) for source in old if isinstance(source,dict)):shutil.copy2(previous,current)
 try:return cache_fetch(source_cache_key(topic,lang),lambda:wikipedia(topic,lang))
 except urllib.error.HTTPError as error:
  if error.code!=429:raise
  for version in (5,4,3):
   path=ROOT/'cache'/(hashlib.sha256(('wikipedia-v'+str(version)+'|'+lang+'|'+topic).encode()).hexdigest()+'.json')
   if not path.exists() or time.time()-path.stat().st_mtime>86400:continue
   sources=json.loads(path.read_text())
   if sources and all(source.get('text') and source.get('url') for source in sources):
    for source in sources:source['retrieval_note']='Previously retrieved source reused after Wikipedia HTTP 429'
    return sources
  raise ValueError('Wikipedia temporarily rate-limited (HTTP 429); no saved sources for this topic') from error

def relevant_sources(sources,topic,lang):
 terms=topic_terms(topic,lang)
 def stem(word):return word[:4] if not word.isascii() else word
 def title_rank(source):
  title=topic_terms(source['title'],lang)
  matched=sum(any(stem(a)==stem(b) for b in title) for a in terms)
  return (matched,-len(title))
 ranked=sorted(sources,key=title_rank,reverse=True)
 if not ranked:return []
 anchor=ranked[0]
 topic_words={stem(word) for word in terms}
 def vocabulary(source):return {stem(word) for word in topic_terms(source['text'][:1800],lang) if len(word)>3}-topic_words
 basis=vocabulary(anchor)
 def same_name_other_sense(source):
  base=lambda title:re.sub(r'\s*\([^)]*\)\s*','',title).strip().casefold()
  return base(source['title'])==base(anchor['title']) and source['title'].casefold()!=anchor['title'].casefold()
 return [anchor]+[source for source in ranked[1:] if not same_name_other_sense(source) and len(basis&vocabulary(source))>=3]
def plan_script(sources,topic,lang,duration,max_beats=None):
 process_intent=bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 for count in range(min(max_beats or 100,max(2,duration//(5 if process_intent else 7))),min(max_beats or 100,max(2,duration//10))-1,-1):
  slots=source_slots(sources,topic,count,lang,duration_s=duration)
  if len(slots)==count:return slots
 if sources and not process_intent:
  canonical=sources[0]['title']
  if canonical.casefold()!=topic.casefold():
   slots=plan_script(sources,canonical,lang,duration,max_beats=max_beats)
   for slot in slots:slot['resolved_topic']=canonical
   return slots
 return []

def shot_beats(shot_count,beat_count):
 if beat_count<1 or shot_count<2*beat_count:raise ValueError('storyboard requires at least two images per narration beat')
 return [index*beat_count//shot_count for index in range(shot_count)]

def photo_search(topic,lang):
 found=[];errors=[];pex=(PROVIDERS.get('Pexels API') or {}).get('value','').strip();pix=(PROVIDERS.get('Pixabay API') or {}).get('value','').strip()
 if pex:
  try:
   locale={'en':'en-US','pl':'pl-PL','ru':'ru-RU','uk':'uk-UA'}[lang];q=urllib.parse.urlencode({'query':topic,'per_page':80,'locale':locale})
   data=cache_fetch('pexels-all-v2|'+lang+'|'+topic,lambda:http_json('https://api.pexels.com/v1/search?'+q,{'Authorization':pex},25))
   for x in data.get('photos') or []:
    src=x.get('src') or {};url=src.get('portrait') or src.get('large') or src.get('original')
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
def commons_search(query):
 params=urllib.parse.urlencode({'action':'query','generator':'search','gsrsearch':query+' filetype:bitmap','gsrnamespace':6,'gsrlimit':20,'prop':'imageinfo','iiprop':'url|size|extmetadata','iiurlwidth':1600,'format':'json'})
 data=cache_fetch('commons-v1|'+query,lambda:http_json('https://commons.wikimedia.org/w/api.php?'+params,timeout=25))
 found=[]
 for page in sorted((data.get('query') or {}).get('pages',{}).values(),key=lambda x:x.get('index',999)):
  for im in page.get('imageinfo',[]):
   meta=im.get('extmetadata') or {}
   get=lambda key:plain_metadata((meta.get(key) or {}).get('value',''))
   license_name=get('LicenseShortName');license_url=get('LicenseUrl')
   if license_name not in {'Public domain','CC0','CC BY 2.0','CC BY 2.5','CC BY 3.0','CC BY 4.0'}:continue
   if license_name.startswith('CC BY') and (not license_url or not get('Artist')):continue
   url=im.get('thumburl') or im.get('url','');host=urllib.parse.urlparse(url).hostname
   if host not in {'upload.wikimedia.org','thumb.wikimedia.org'}:continue
   width=int(im.get('thumbwidth') or im.get('width') or 0);height=int(im.get('thumbheight') or im.get('height') or 0)
   if min(width,height)<640:continue
   source='https://commons.wikimedia.org/w/index.php?curid='+str(page['pageid'])
   found.append({'provider':'commons','id':str(page['pageid']),'alt':plain_metadata(page.get('title',''))+' '+get('ImageDescription'),'depiction':plain_metadata(page.get('title','')),'query':query,'url':url,'source_url':source,'creator':get('Artist') or get('Credit') or 'Wikimedia Commons','creator_url':im.get('descriptionurl') or source,'width':width,'height':height,'license':license_name,'license_url':license_url,'changes':'resized and composited with narration captions'})
 return found

def visual_context_title(slot,sources,lang):
 # Match the native-language fact to article introductions, then use their English titles.
 mapped=[source for source in sources if source.get('visual_title') and all(year in slot['text'] for year in re.findall(r'\b\d{4}\b',source['title']))]
 if not mapped:return slot.get('visual_title','')
 corpus=[set(topic_terms(source['title']+' '+source['text'][:1800],lang)) for source in mapped]
 weights={term:math.log(1+len(corpus)/(1+sum(term in doc for doc in corpus))) for doc in corpus for term in doc}
 query=set(topic_terms(slot['text'],lang))
 scores=[sum(weights.get(term,0)**2 for term in query&doc)/max(1,sum(weights[term]**2 for term in doc))**.5 for doc in corpus]
 return mapped[max(range(len(mapped)),key=lambda index:scores[index])]['visual_title']
def media_search_topic(topic,lang,sources):
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
def discover_photos(topic,lang,slots):
 pool={};errors=[]
 aliases=list(dict.fromkeys(alias for slot in slots for alias in slot.get('topic_aliases',[])))
 for query in list(dict.fromkeys(visual_queries(topic,lang,slots)+aliases))[:7]:
  try:
   for candidate in photo_search(query,lang):pool.setdefault((candidate['provider'],candidate['id']),candidate)
  except Exception as e:errors.append(str(e))
 # Commons supplements source-backed technical images, with a separate three-query bound.
 core_terms=list(dict.fromkeys(topic_terms(topic,lang)))
 core=' '.join(core_terms[:1])
 actions=set().union(*(visual_actions(slot['text']) if slot.get('process_intent',True) else set() for slot in slots))
 labels={'heat':'furnace','shape':'forming','cool':'annealing','inspect':'inspection','production':'manufacturing'}
 queries=[((' '.join(core_terms) if action=='inspect' else core)+' '+labels[action]).strip() for action in ('cool','inspect','heat','shape','production') if action in actions][:3]
 if not queries:queries=list(dict.fromkeys([slot.get('visual_title') for slot in slots if slot.get('visual_title')]+[topic]+aliases))[:3]
 for query in queries:
  try:
   for candidate in commons_search(query):pool.setdefault((candidate['provider'],candidate['id']),candidate)
  except Exception as e:errors.append('Commons: '+str(e))
 if not pool:raise ValueError('; '.join(errors) or 'no photo candidates')
 return list(pool.values())

def dhash(im):
 im=ImageOps.grayscale(im).resize((9,8));p=list(im.getdata());n=0
 for y in range(8):
  for x in range(8):n=(n<<1)|(1 if p[y*9+x]>p[y*9+x+1] else 0)
 return n
def visual_actions(text):
 patterns={
  'heat':r'\b(?:melt\w*|molten|furnace\w*|heat(?:ed|ing)|kiln\w*|topi\w*|piec\w*|плав\w*|печ\w*|нагр\w*)',
  'shape':r'\b(?:blow(?:n|ing|pipe)?|blows|glassblow\w*|form(?:ed|ing)|mold\w*|mould\w*|shap(?:ed|ing)|wydmuch\w*|formow\w*|wyduw\w*|выдув\w*|формов\w*|видув\w*|формув\w*)',
  'cool':r'\b(?:cool(?:ed|ing)|anneal\w*|lehr|leer|chłodz\w*|wyżarz\w*|охлажд\w*|отжиг\w*|охолодж\w*|відпал\w*)',
  'inspect':r'\b(?:inspect\w*|quality control|quality check\w*|test(?:ed|ing)|kontrol\w*|sprawdz\w*|провер\w*|контрол\w*|перевір\w*)',
  'production':r'\b(?:factor(?:y|ies)|manufactur\w*|production|assembly|automat\w*|machine\w*|fabryk\w*|produkc\w*|zakład\w*|завод\w*|производств\w*|виробниц\w*)'
 }
 return {key for key,pattern in patterns.items() if re.search(pattern,text or '',re.I)}
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
def photo_score(p,slot,topic):
 depiction=p.get('depiction') or p['alt']
 terms=set(tokens(topic+' '+slot['text']+' '+slot.get('visual_title','')));meta=set(tokens(depiction))
 process_topic=bool(re.search(r'made|making|manufactur|produc|изготов|производ|виготов|виробля|wytwarz|produk|powst',topic,re.I))
 anchors=set(topic_terms(topic,'en'))-{'energy','power','system','process','technology','science','history','type','method','production','manufacturing'}
 if process_topic and anchors and not anchors&meta:return -1
 if not process_topic and anchors:
  names=[topic]+slot.get('topic_aliases',[])
  groups=[set(topic_terms(name,'en'))-{'energy','power','system','process','technology','science','history','type','method','production','manufacturing'} for name in names]
  if not any(group and group<=meta for group in groups):return -1
 if not process_topic and p.get('provider')=='pixabay' and len(anchors)>1 and not any(group and group<=set(tokens(tag)) for group in groups for tag in depiction.split(',')):return -1
 if p.get('provider') in {'pixabay','pexels'} and re.search(r'\b(?:fantasy|sci[ -]?fi|digital art|3d render|ai[ -]generated)\b',depiction,re.I):return -1
 work_context=r'\b(?:factor(?:y|ies)|manufactur\w*|production|assembly|machine\w*|workshop|artisan\w*|craftsman|glassblow\w*|furnace\w*|kiln\w*|industrial|anneal\w*|lehr|leer|oven|inspection box|final inspection|glass works|laborator\w*|bakery|kitchen|brewery|fabryk\w*|warsztat\w*|завод\w*|цех\w*|мастерск\w*|майстер\w*|виробниц\w*)'
 if process_topic and not re.search(work_context,depiction,re.I):return -1
 if not process_topic:
  qualifiers={term for term in tokens(slot.get('visual_title','')) if term not in tokens(topic) and term.isalpha() and len(term)>=3}-{'energy','power','system','plant','factory','production','manufacturing','process','industry','technology','list','century'}
  if qualifiers and not qualifiers&meta:return -1
 required=visual_actions(slot['text']) if process_topic else set();depicted=visual_actions(depiction)
 specific=required-{'production'}
 if specific and not specific&depicted:return -1
 if required and not required&depicted:return -1
 return 2*len(terms&meta)+.8*len(set(tokens(topic))&meta)+8*len(required&depicted)+(6 if slot.get('visual_title') and slot['visual_title'].casefold()==p.get('query','').casefold() else 0)+(.5 if p['height']>=p['width'] else 0)
PIXEL_VERIFIER=None
def get_pixel_verifier():
 global PIXEL_VERIFIER
 if PIXEL_VERIFIER is None:PIXEL_VERIFIER=VisualVerifier()
 return PIXEL_VERIFIER
def pixel_check(raw,topic,slot):
 visual_subject=(slot.get('visual_title') or topic) if not slot.get('process_intent',True) else topic
 subject=' '.join(dict.fromkeys(topic_terms(visual_subject,'en')))
 return get_pixel_verifier().check(raw,subject or topic,visual_actions(slot['text']) if slot.get('process_intent',True) else set(),slot['text'] if slot.get('language','en')=='en' else '',slot.get('visual_competitors',[]),topic)

def allocate_photos(candidates,slots,topic,shot_count=None):
 # Assign the entire storyboard before downloads, preserving scarce assets for scenes that need them.
 subject=set(tokens(topic));edges=[]
 for beat in shot_beats(shot_count if shot_count is not None else len(slots)*2,len(slots)):
  slot=slots[beat]
  eligible=[index for index,p in enumerate(candidates) if photo_score(p,slot,topic)>=0]
  eligible.sort(key=lambda index:photo_score(candidates[index],slot,topic),reverse=True)
  edges.append(eligible)
 owner={}
 def assign(scene,seen):
  for candidate in edges[scene]:
   if candidate in seen:continue
   seen.add(candidate)
   if candidate not in owner or assign(owner[candidate],seen):owner[candidate]=scene;return True
  return False
 for scene in sorted(range(len(edges)),key=lambda index:len(edges[index])):
  if not assign(scene,set()):raise ValueError('not enough distinct action-matched images for the complete storyboard; scene '+str(scene+1))
 allocated=[None]*len(edges)
 for candidate,scene in owner.items():allocated[scene]=candidates[candidate]
 return allocated

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
  fg=ImageOps.contain(im,(1040,1420),method=Image.Resampling.LANCZOS)
  bg.paste(fg,((1080-fg.width)//2,95+(1420-fg.height)//2))
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
  Image.alpha_composite(bg.convert('RGBA'),layer).convert('RGB').save(dest,'JPEG',quality=88,optimize=True)
def download_photo(c,dest):
 host=(urllib.parse.urlparse(c['url']).hostname or '').lower()
 if urllib.parse.urlparse(c['url']).scheme!='https' or not(host in {'images.pexels.com','pixabay.com'} or host.endswith('.pixabay.com') or host in {'upload.wikimedia.org','thumb.wikimedia.org'}):raise ValueError('photo host not allowed')
 with urllib.request.urlopen(urllib.request.Request(c['url'],headers={'User-Agent':'UniversalShortFactory/1.0 (https://studio.hodor.com.pl/; educational video research)'}),timeout=25) as r:
  data=r.read(20_000_001);ct=r.headers.get('Content-Type','').split(';')[0].lower()
 if len(data)>20_000_000 or ct not in {'image/jpeg','image/png','image/webp'}:raise ValueError('photo payload invalid')
 Path(dest).write_bytes(data)
 with Image.open(dest) as im:im.verify()

SELECTED_VOICES={'en':('en-US','en-US-Chirp3-HD-Algenib'),'pl':('pl-PL','pl-PL-Chirp3-HD-Enceladus'),'ru':('ru-RU','ru-RU-Wavenet-D'),'uk':('uk-UA','uk-UA-Chirp3-HD-Enceladus')}
def selected_voice_request(lang,text):
 locale,voice=SELECTED_VOICES[lang]
 text=unicodedata.normalize('NFC',text).replace(chr(0x301),'')
 return {'input':{'text':text},'voice':{'languageCode':locale,'name':voice},'audioConfig':{'audioEncoding':'MP3'}}
def google_voice_once(lang,text,jid,attempt):
 import psycopg
 body=selected_voice_request(lang,text);spoken=body['input']['text'];voice=body['voice']['name']
 if not spoken.strip() or len(spoken.encode())>4800:raise ValueError('narration exceeds the selected voice request size')
 key='universal:'+jid+':voice:'+str(attempt);digest=hashlib.sha256(spoken.encode()).hexdigest()
 # A durable claim precedes quota accounting and the uncertain send; an interrupted attempt cannot replay.
 with connect() as c:
  c.execute('INSERT INTO voice_attempts(job_id,attempt,text_sha256,voice,state) VALUES(?,?,?,?,?)',(jid,attempt,digest,voice,'claimed'))
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
  if receipt.get('status')!=200:raise ValueError('selected Google voice returned HTTP '+str(receipt.get('status'))+'; no fallback or resend')
  audio=base64.b64decode(receipt['body']['audioContent'],validate=True)
  folder=ROOT/'tmp'/jid;folder.mkdir(parents=True,exist_ok=True);path=folder/('voice-attempt-'+str(attempt)+'.mp3')
  with path.open('xb') as stream:stream.write(audio)
  duration_ms=round(float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(path)],text=True,timeout=10))*1000)
  audit={'attempt':attempt,'voice':voice,'characters':len(spoken),'text_sha256':digest,'audio_sha256':hashlib.sha256(audio).hexdigest(),'duration_ms':duration_ms,'quota_key':key}
  with connect() as c:c.execute("UPDATE voice_attempts SET state='measured',receipt=? WHERE job_id=? AND attempt=?",(json.dumps(audit),jid,attempt))
  return path,audit
 except Exception:
  with connect() as c:c.execute("UPDATE voice_attempts SET state='stopped' WHERE job_id=? AND attempt=? AND state!='measured'",(jid,attempt))
  raise
def prepare_selected_narration(sources,topic,lang,jid,duration):
 # Change complete source sentences after a measured miss, never the voice or playback rate.
 planning_seconds=duration;seen=set();attempts=[];slots=[]
 for attempt in (1,2,3):
  slots=plan_script(sources,topic,lang,planning_seconds,max_beats=duration//5)
  if not slots or len(slots)>duration//5:raise ValueError('no complete source narration fits the natural speaking budget')
  script=' '.join(slot['text'] for slot in slots);spoken=selected_voice_request(lang,script)['input']['text'];identity=hashlib.sha256(spoken.encode()).hexdigest()
  if identity in seen:raise ValueError('natural-duration correction produced the same text; no duplicate synthesis')
  seen.add(identity)
  update(jid,stage='voice',progress=12,message='Creating narration with your selected '+lang.upper()+' voice; attempt '+str(attempt))
  path,measured=google_voice_once(lang,script,jid,attempt);attempts.append(measured);actual=measured['duration_ms']
  if duration*1000-1000<=actual<=duration*1000:break
  planning_seconds=max(10,min(90,round(planning_seconds*(duration*1000-500)/max(actual,1))))
 else:raise ValueError('three distinct natural narration texts did not fit; no speed change or voice substitution')
 # Align the exact, unmodified natural audio through the existing media worker.
 final=VOICE/jid/'final.mp3';final.parent.mkdir(parents=True,exist_ok=True)
 with final.open('xb') as output:output.write(path.read_bytes())
 scene_inputs=[{'scene_uuid':str(uuid.uuid5(uuid.UUID(jid),'spoken:'+str(i))),'scene_key':str(i),'narration':slot['text']} for i,slot in enumerate(slots)]
 payload={'language_code':lang,'narration':script,'audio_sha256':measured['audio_sha256'],'audio_duration_ms':actual,'scenes':scene_inputs}
 update(jid,stage='alignment',progress=16,message='Aligning captions to the exact selected voice recording')
 request=urllib.request.Request(WORKER+'/alignments/'+jid,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(request,timeout=240) as response:alignment=json.loads(response.read(2_000_000))
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
 req=urllib.request.Request(WORKER+'/renders/'+jid,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=240) as r:return json.loads(r.read().decode())
 except urllib.error.HTTPError as error:
  try:detail=json.loads(error.read(2000)).get('message') or 'HTTP '+str(error.code)
  except (ValueError,AttributeError):detail='HTTP '+str(error.code)
  raise ValueError('Renderer rejected the job: '+str(detail)[:400]) from error
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

def run_job(jid):
 j=get_job(jid);topic=j['topic'];lang=j['language'];duration=j['duration_s'];visual_count=duration*2//5;beat_count=duration//5
 try:
  update(jid,status='running',stage='research',progress=5,message='Finding cited facts in the selected language')
  sources=relevant_sources(load_sources(topic,lang),topic,lang)
  if not sources:raise ValueError('no usable source article; try a more specific topic or another language')
  slots=plan_script(sources,topic,lang,duration)
  if not slots:raise ValueError('not enough complete, topic-grounded source sentences fitting the requested duration')
  slots,mp3,audio_ms,speech_ms,slot_targets,voice_audit=prepare_selected_narration(sources,topic,lang,jid,duration)
  beat_count=len(slots)
  beat_for_shot=shot_beats(visual_count,beat_count);shots_per_beat=[beat_for_shot.count(index) for index in range(beat_count)];first_shot=[beat_for_shot.index(index) for index in range(beat_count)]
  for slot in slots:
   slot['language']=lang
   source=sources[slot['source_index']]
   slot['visual_title']=source.get('visual_title') or (source['title'] if lang=='en' else '')
   if not slot.get('process_intent'):slot['visual_title']=visual_context_title(slot,sources,lang)
  media_topic=media_search_topic(topic,lang,sources)
  update(jid,stage='visuals',progress=20,message='Searching a bounded photo pool; requiring unique relevant assets')
  aliases=[media_topic] if slots[0].get('process_intent') else media_aliases(media_topic)
  for slot in slots:slot['topic_aliases']=aliases
  candidates=discover_photos(media_topic,'en',slots)
  if len(candidates)<visual_count:raise ValueError('photo search found '+str(len(candidates))+' distinct candidates; '+str(visual_count)+' are required')
  competitors=[] if slots[0].get('process_intent') else visual_competitors(media_topic,candidates)
  for slot in slots:slot['visual_competitors']=competitors
  get_pixel_verifier()
  allocated=allocate_photos(candidates,slots,media_topic,visual_count)
  topic_terms=set(tokens(media_topic));selected=[];used_ids=set();hashes=[];visual_rows=[]
  for i in range(visual_count):
   slot=slots[beat_for_shot[i]]
   reserved={(p['provider'],p['id']) for p in allocated[i+1:]}
   ranked=[allocated[i]]+sorted([p for p in candidates if (p['provider'],p['id']) not in reserved and p is not allocated[i]],key=lambda p:photo_score(p,slot,media_topic),reverse=True)
   found=None;attempts=0;rejection_reasons=[]
   for p in ranked:
    key=(p['provider'],p['id'])
    if key in used_ids or photo_score(p,slot,media_topic)<0:continue
    meta=set(tokens(p['alt']))
    if not meta:continue
    if attempts>=24:break
    attempts+=1
    shot=str(uuid.uuid4());folder=VISUAL/jid/shot;folder.mkdir(parents=True,exist_ok=False)
    raw=folder/'source.download';final=folder/'selected.jpg'
    try:
     download_photo(p,raw)
     with Image.open(raw) as im:ph=dhash(im.convert('RGB'))
     if any((ph^old).bit_count()<=4 for old in hashes):raw.unlink(missing_ok=True);shutil.rmtree(folder);continue
     pixel_audit=pixel_check(raw,media_topic,slot)
     if not pixel_audit['passed']:raise ValueError('pixel comparison rejected candidate: score='+str(pixel_audit['positive_score'])+' margin='+str(pixel_audit['margin']))
     make_card(raw,slot['text'],final,p);raw.unlink(missing_ok=True)
    except Exception as e:
     rejection_reasons.append(scrub_error(e));shutil.rmtree(folder,ignore_errors=True);continue
    row=dict(p);row.update({'pixel_verification':pixel_audit,'caption':slot['text'],'article_title':sources[slot['source_index']]['title'],'article_url':sources[slot['source_index']]['url'],'asset_sha256':hashlib.sha256(final.read_bytes()).hexdigest()})
    found={'provider':p,'shot':shot,'path':final,'hash':row['asset_sha256'],'phash':ph,'row':row};break
   if found is None:raise ValueError('no verified distinct image for scene '+str(i+1)+' after '+str(attempts)+' candidates; '+ '; '.join(rejection_reasons[-3:]))
   hashes.append(found['phash']);used_ids.add((found['provider']['provider'],found['provider']['id']));selected.append(found);visual_rows.append(found['row'])
   update(jid,progress=20+int((i+1)*25/visual_count),message='Prepared '+str(i+1)+' of '+str(visual_count)+' unique photos')
  audio_sha=hashlib.sha256(mp3.read_bytes()).hexdigest();target=duration*1000;beat_starts=[sum(slot_targets[:i]) for i in range(beat_count)];cursor=0;scenes=[]
  for i,item in enumerate(selected):
   beat=beat_for_shot[i];beat_start=beat_starts[beat];end=target if i==visual_count-1 else beat_start+slot_targets[beat]*(i-first_shot[beat]+1)//shots_per_beat[beat];end=round(end/100)*100;spoken_end=min(target,slots[beat]['speech_end_ms']);speech_start=max(cursor,slots[beat]['speech_start_ms']);speech_end=min(end,spoken_end,audio_ms)
   if speech_end<=speech_start:speech_start=cursor;speech_end=min(end,cursor+1)
   scenes.append({'scene_uuid':str(uuid.uuid4()),'shot_uuid':item['shot'],'visual_asset_id':str(uuid.uuid4()),'media_type':'photo','asset_sha256':item['hash'],'asset_path':str(item['path']),'asset_width':1080,'asset_height':1920,'scene_order':i+1,'segment_start_ms':cursor,'segment_end_ms':end,'speech_start_ms':speech_start,'speech_end_ms':speech_end})
   cursor=end
  update(jid,stage='render',progress=80,message='Rendering 1080×1920 MP4 and decoding the complete file')
  rendered=post_render(jid,{'input_audio_sha256':audio_sha,'audio_duration_ms':audio_ms,'target_duration_ms':target,'requested_duration_ms':duration*1000,'scenes':scenes})
  video=Path(rendered['storage_path'])
  full=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True,timeout=150)
  if full.returncode:raise ValueError('full MP4 decode failed')
  if not rendered.get('qa_passed'):raise ValueError('media-worker render QA failed')
  manifest={'version':'universal-1','job_id':jid,'topic':topic,'language':lang,'requested_duration_s':duration,'visual_search_topic':media_topic,'created_at':now(),'script':' '.join(x['text'] for x in slots),'resolved_topic':slots[0].get('resolved_topic',topic),'script_mode':'source-grounded extractive','llm_calls':0,'sources':[{'title':x['title'],'url':x['url'],'retrieval_note':x.get('retrieval_note')} for x in sources],'beats':[{'order':i+1,'caption':s['text'],'source_span':s['source_sentence'],'source_title':sources[s['source_index']]['title'],'source_url':sources[s['source_index']]['url']} for i,s in enumerate(slots)],'visuals':[{'order':i+1,'provider':x['provider'],'provider_id':x['id'],'alt':x['alt'],'creator':x['creator'],'creator_url':x['creator_url'],'provider_page':x['source_url'],'license':x.get('license'),'license_url':x.get('license_url'),'changes':x.get('changes'),'search_query':x.get('query',topic),'caption':x['caption'],'source_article':x['article_url'],'source_title':x['article_title'],'asset_sha256':x['asset_sha256'],'pixel_verification':x['pixel_verification']} for i,x in enumerate(visual_rows)],'narration':voice_audit,'render':rendered,'audit':{'shots_required':visual_count,'narration_beats':beat_count,'unique_assets':len({x['asset_sha256'] for x in visual_rows}),'images_per_narration_beat':shots_per_beat,'minimum_two_images_per_beat':all(count>=2 for count in shots_per_beat),'average_shot_duration_ms':target/visual_count,'source_count':len(sources),'all_visuals_have_provenance':all(x['source_url'] and x['article_url'] for x in visual_rows),'all_images_pixel_checked':all(x['pixel_verification']['passed'] for x in visual_rows),'full_decode':True,'renderer_gates':rendered.get('qa_gates',{})},'retention_days':30}
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
 with connect() as c:rows=c.execute("SELECT id,status,created_at,updated_at,review_status FROM jobs WHERE status IN ('ready','failed')").fetchall()
 for row in rows:
  jid=safe_id(row['id'])
  if not jid or jid!=row['id']:continue
  try:created=datetime.fromisoformat(row['created_at']).timestamp();updated=datetime.fromisoformat(row['updated_at']).timestamp()
  except (TypeError,ValueError):continue
  path=RENDER/jid
  if row['status']=='failed':
   if updated<time.time()-86400:
    for target in (path,VISUAL/jid,VOICE/jid,ROOT/'tmp'/jid):
     if target.exists() and not target.is_symlink():shutil.rmtree(target,ignore_errors=True)
   continue
  if created<cutoff:
   try:
    if path.exists() and not path.is_symlink():shutil.rmtree(path)
    update(jid,status='expired',stage='expired',progress=100,message='MP4 expired after 30 days')
   except OSError:pass
   continue
  finished.append({'id':jid,'path':path,'created':created,'review':row['review_status'],'bytes':directory_bytes(path)})
 total=sum(item['bytes'] for item in finished)
 priority={'changes_requested':0,'pending':1,'approved':2}
 for item in sorted(finished,key=lambda x:(priority.get(x['review'],1),x['created'])):
  if total<=RENDER_MAX_BYTES:break
  try:
   if item['path'].exists() and not item['path'].is_symlink():shutil.rmtree(item['path'])
   total-=item['bytes'];update(item['id'],status='expired',stage='expired',progress=100,message='MP4 removed under the 2 GB output retention limit')
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
HTML='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Universal Video Factory</title><style>:root{color-scheme:dark;font:16px system-ui;background:#0b1020;color:#edf2ff}body{margin:0 auto;max-width:1100px;padding:32px 20px}h1{font-size:32px;margin:0}p{color:#aab6d3}form,.job{background:#141c31;border:1px solid #2b3858;border-radius:16px;padding:20px;margin:22px 0}form{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:end}label{display:grid;gap:6px;color:#bdc9e5}input,select,button{font:inherit;border-radius:9px;padding:12px;border:1px solid #3b4b70;background:#0b1020;color:#fff}button{cursor:pointer;background:#4b72ea;border:0;font-weight:700}button.secondary{background:#26344f}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.job h2{font-size:19px}.job video{width:100%;max-height:680px;background:#05070c}.bar{height:8px;background:#283653;border-radius:5px;overflow:hidden}.bar span{display:block;height:8px;background:#79a6ff}.sources a{color:#90b5ff}.error{color:#ff9e9e}.pill{display:inline-block;border-radius:99px;background:#283653;padding:4px 9px;font-size:12px}@media(max-width:760px){form,.grid{grid-template-columns:1fr}}</style><body><h1>Universal Video Factory</h1><p>Create a vertical video from a topic, with narration, unique images, captions and cited sources.</p><form id="new"><label>Topic<input name="topic" minlength="3" maxlength="180" required placeholder="Enter a topic"></label><label>Language<select name="language"><option value="en">English</option><option value="pl">Polski</option><option value="ru">Русский</option><option value="uk">Українська</option></select></label><label>Length<select name="duration_s"><option>15</option><option>30</option><option>45</option><option>60</option></select></label><button>Create MP4</button></form><div style="display:flex;gap:12px;align-items:end"><label>View<select id="historyView"><option value="user">My videos</option><option value="examples">Examples</option><option value="tests">Test history</option></select></label><button id="refresh" type="button" class="secondary">Refresh</button></div><div id="status" role="status"></div><div id="jobs" class="grid"></div><script>\n\nvar base=location.pathname.replace(/\\/$/,\'\');if(base===\'/\')base=\'\';\nvar requestNo=0,lastFetch=0,hasActiveJobs=false;\nvar list=document.getElementById(\'jobs\'),view=document.getElementById(\'historyView\'),statusBox=document.getElementById(\'status\');\nfunction esc(value){return String(value||\'\').replace(/[&<>"\']/g,function(c){return {\'&\':\'&amp;\',\'<\':\'&lt;\',\'>\':\'&gt;\',\'"\':\'&quot;\',"\'":\'&#39;\'}[c]})}\nasync function api(path,options){var response=await fetch(base+path,options||{});var data=await response.json();if(!response.ok)throw Error(data.error||response.status);return data}\nfunction cardHTML(j){\n var m=j.manifest||{},video=j.status===\'ready\'?\'<video controls playsinline preload="metadata" src="\'+base+\'/api/jobs/\'+j.id+\'/video"></video><p><a href="\'+base+\'/api/jobs/\'+j.id+\'/video" download>Download MP4</a> · <a href="\'+base+\'/api/jobs/\'+j.id+\'/manifest">Sources and media audit</a></p>\':\'\';\n var script=m.script?\'<details><summary>Script and cited sources</summary><p>\'+esc(m.script)+\'</p><div class="sources">\'+(m.sources||[]).map(function(source){return \'<p><a target="_blank" rel="noreferrer" href="\'+esc(source.url)+\'">\'+esc(source.title)+\'</a></p>\'}).join(\'\')+\'</div></details>\':\'\';\n var summary=j.message;\n if(j.status===\'failed\')summary=j.message.indexOf(\'research\')>=0?\'Could not prepare a complete script from the sources.\':j.message.indexOf(\'visual\')>=0?\'Could not find enough suitable images.\':\'Video creation failed.\';\n var error=j.error?\'<details><summary class="error">Error details</summary><p class="error">\'+esc(j.error)+\'</p></details>\':\'\';\n var review=j.status===\'ready\'?\'<p><span class="pill">Review: \'+esc(j.review_status)+\'</span> <button class="secondary" data-action="approved" data-id="\'+j.id+\'">Approve</button> <button class="secondary" data-action="changes_requested" data-id="\'+j.id+\'">Request changes</button></p>\':\'\';\n var resolved=m.resolved_topic&&m.resolved_topic!==j.topic?\'<p>Source topic: \'+esc(m.resolved_topic)+\'</p>\':\'\';\n return \'<article class="job" data-job-id="\'+j.id+\'" data-origin="\'+esc(j.origin)+\'" data-state="\'+esc(j.status)+\'"><h2>\'+esc(j.topic)+\' · \'+j.duration_s+\'s · \'+esc(j.language)+\'</h2><p>\'+esc(j.status)+\' — \'+esc(summary)+\'</p>\'+resolved+\'<div class="bar"><span style="width:\'+j.progress+\'%;\'+(j.status===\'failed\'?\'background:#d86969\':\'\')+\'"></span></div>\'+error+video+script+review+\'</article>\';\n}\nfunction patchCards(jobs){\n var ids=new Set(jobs.map(function(job){return job.id}));\n Array.from(list.children).forEach(function(node){if(!ids.has(node.dataset.jobId))node.remove()});\n jobs.forEach(function(job,index){\n  var signature=JSON.stringify(job),card=list.querySelector(\'[data-job-id="\'+job.id+\'"]\');\n  if(!card||card.dataset.signature!==signature){var template=document.createElement(\'template\');template.innerHTML=cardHTML(job);var next=template.content.firstElementChild;next.dataset.signature=signature;if(card)card.replaceWith(next);card=next;}\n  if(list.children[index]!==card)list.insertBefore(card,list.children[index]||null);\n });\n if(!jobs.length){list.innerHTML=\'<p>No videos in this view.</p>\';}\n}\nasync function draw(){\n var sequence=++requestNo,selected=view.value;\n try{var data=await api(\'/api/jobs?view=\'+encodeURIComponent(selected));if(sequence!==requestNo||selected!==view.value)return;var jobs=data.jobs||[];hasActiveJobs=jobs.some(function(job){return job.status===\'queued\'||job.status===\'running\'});patchCards(jobs);lastFetch=Date.now();statusBox.textContent=\'\';}\n catch(error){if(sequence===requestNo)statusBox.textContent=error.message;}\n}\nlist.addEventListener(\'click\',async function(event){var button=event.target.closest(\'button[data-action]\');if(!button)return;try{await api(\'/api/jobs/\'+button.dataset.id+\'/review\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({status:button.dataset.action})});await draw()}catch(error){statusBox.textContent=error.message}});\nview.addEventListener(\'change\',draw);document.getElementById(\'refresh\').addEventListener(\'click\',draw);\ndocument.getElementById(\'new\').addEventListener(\'submit\',async function(event){\n event.preventDefault();var form=event.target,button=form.querySelector(\'button\'),fields=new FormData(form);button.disabled=true;statusBox.textContent=\'Submitting…\';\n try{await api(\'/api/jobs\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({topic:fields.get(\'topic\'),language:fields.get(\'language\'),duration_s:Number(fields.get(\'duration_s\'))})});form.elements.topic.value=\'\';view.value=\'user\';await draw()}\n catch(error){statusBox.textContent=error.message}finally{button.disabled=false}\n});\ndraw();setInterval(function(){if(!document.hidden&&(hasActiveJobs||Date.now()-lastFetch>30000))draw()},4000);\n\n</script></body></html>'
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
   view=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('view',['user'])[0]
   filters={'user':"origin='user' AND status!='expired'",'examples':"origin='test' AND status='ready' AND json_extract(manifest,'$.narration.engine')='Google Cloud Text-to-Speech'",'tests':"origin='test'"}
   if view not in filters:return self.json_out(400,{'error':'unknown job view'})
   with connect() as c:rows=c.execute('SELECT id FROM jobs WHERE '+filters[view]+' ORDER BY created_at DESC LIMIT 50').fetchall()
   jobs=[public_job(get_job(row['id'])) for row in rows]
   for job in jobs:
    if job['manifest']:job['manifest']={key:job['manifest'][key] for key in ('script','sources','resolved_topic') if key in job['manifest']}
   return self.json_out(200,{'jobs':jobs,'view':view})
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
   cleanup()
   if shutil.disk_usage(DATA).free<DISK_RESERVE_BYTES:return self.json_out(507,{'error':'Less than 2 GB free disk space; no new job was created'})
   jid=str(uuid.uuid4());ts=now()
   with connect() as c:c.execute('INSERT INTO jobs(id,created_at,updated_at,topic,language,duration_s,status,stage,progress,message) VALUES(?,?,?,?,?,?,?,?,?,?)',(jid,ts,ts,topic,lang,duration,'queued','queued',0,'Waiting for the single worker'))
   if b.get('origin')=='test':update(jid,origin='test')
   POOL.submit(execute_job,jid);return self.json_out(202,{'id':jid,'status':'queued'})
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

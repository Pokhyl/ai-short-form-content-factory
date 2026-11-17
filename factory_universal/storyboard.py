"""Source-linked scene briefs. No topic-specific asset lists or paid model calls."""
import re
import hashlib
import urllib.parse
from html.parser import HTMLParser

class SceneUnavailable(ValueError):
 def __init__(self,slot,message):
  super().__init__(message)
  self.source_index=slot.get('source_index',0)
  self.source_sentence=slot.get('source_sentence') or slot['text']
  self.visual_target=slot.get('visual_target')

class ArticleLinks(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.paragraph=0;self.skip=0;self.anchor=None;self.links=[];self.paragraph_text=[];self.paragraph_links=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='p':
   self.paragraph+=1;self.paragraph_text=[];self.paragraph_links=[]
  if tag in {'table','figure','script','style','sup'}:self.skip+=1
  if tag=='a' and self.paragraph and not self.skip:
   href=attrs.get('href','')
   if href.startswith('/wiki/') and ':' not in href.removeprefix('/wiki/'):
    self.anchor={'title':urllib.parse.unquote(href[6:].split('#')[0]).replace('_',' '),'parts':[]}
 def handle_data(self,text):
  if self.paragraph and not self.skip:self.paragraph_text.append(text)
  if self.anchor:self.anchor['parts'].append(text)
 def handle_endtag(self,tag):
  if tag=='a' and self.anchor:
   label=re.sub(r'\s+',' ',''.join(self.anchor['parts'])).strip()
   if label:self.paragraph_links.append({'label':label,'title':self.anchor['title']})
   self.anchor=None
  if tag=='p':
   key=paragraph_key(''.join(self.paragraph_text))
   self.links.extend({**link,'paragraph_key':key} for link in self.paragraph_links)
   self.paragraph=max(0,self.paragraph-1)
  if tag in {'table','figure','script','style','sup'}:self.skip=max(0,self.skip-1)

def paragraph_key(text):
 return hashlib.sha256(re.sub(r'[\W_]+','',text.casefold()).encode()).hexdigest()

def phrase_in(phrase,text):
 return bool(phrase and re.search(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',text,re.I))

def extract_article(html,lang,api):
 class LinkedArticle(api.WikiHTML):
  def __init__(self):
   super().__init__(lang,paragraphs_only=True)
   self.visual_links=[];self.scene_anchor=None;self.scene_paragraph_start=0;self.scene_paragraph_links=[]
  def handle_starttag(self,tag,attrs):
   if tag=='p' and not self.skip and not self.skip_section:
    self.scene_paragraph_start=len(self.parts);self.scene_paragraph_links=[]
   if tag=='a' and self.paragraph_depth and not self.skip and not self.skip_section and not self.sup_level:
    href=dict(attrs).get('href','')
    if href.startswith('/wiki/') and ':' not in href[6:]:
     self.scene_anchor={'title':urllib.parse.unquote(href[6:].split('#')[0]).replace('_',' '),'start':len(self.parts)}
   super().handle_starttag(tag,attrs)
  def handle_endtag(self,tag):
   if tag=='a' and self.scene_anchor:
    row=self.scene_anchor
    row['label']=re.sub(r'\s+',' ',''.join(self.parts[row['start']:])).strip()
    if row['label']:self.scene_paragraph_links.append(row)
    self.scene_anchor=None
   super().handle_endtag(tag)
   if tag=='p' and self.scene_paragraph_links:
    paragraph=''.join(self.parts[self.scene_paragraph_start:])
    for row in self.scene_paragraph_links:
     offset=len(''.join(self.parts[self.scene_paragraph_start:row['start']]))
     begin=paragraph.rfind('\n',0,offset)+1;end=paragraph.find('\n',offset)
     if end<0:end=len(paragraph)
     self.visual_links.append({'label':row['label'],'title':row['title'],'paragraph_key':paragraph_key(paragraph[begin:end])})
    self.scene_paragraph_links=[]
 parser=LinkedArticle();parser.feed(html)
 return {'text':parser.text(),'visual_links':parser.visual_links}

def ensure_source(sources,lang,api):
 if not sources:return
 source=sources[0]
 def fetch():
  title=urllib.parse.unquote(urllib.parse.urlsplit(source['url']).path.split('/wiki/',1)[-1]).replace('_',' ')
  query=urllib.parse.urlencode({'action':'parse','page':title,'prop':'text|langlinks','format':'json'})
  parsed=api.http_json('https://'+lang+'.wikipedia.org/w/api.php?'+query,timeout=22).get('parse',{})
  article=extract_article(parsed.get('text',{}).get('*',''),lang,api)
  if len(article['text'])<220:raise ValueError('Source article text is unavailable')
  article['revision_id']=parsed.get('revid')
  article['revision_url']='https://'+lang+'.wikipedia.org/w/index.php?oldid='+str(parsed['revid']) if parsed.get('revid') else source['url']
  return article
 # Text and links must come from the same revision and the same paragraph parser.
 source.update(api.cache_fetch('scene-article-snapshot-v1|'+lang+'|'+source['url'],fetch))

def source_links(sources,lang,api):
 if 'visual_links' not in sources[0]:ensure_source(sources,lang,api)
 return sources[0].get('visual_links',[])

def resolve_links(links,lang,api):
 titles=sorted({link['title'] for link in links})[:40]
 if not titles:return {}
 def fetch():
  params={'action':'query','titles':'|'.join(titles),'prop':'langlinks|pageprops','lllang':'en','lllimit':'max','redirects':'1','format':'json','formatversion':'2'}
  data=api.http_json('https://'+lang+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params),timeout=22).get('query',{})
  pages={page['title']:page for page in data.get('pages',[])}
  aliases={row['from']:row['to'] for row in data.get('normalized',[])+data.get('redirects',[])}
  rows={}
  for title in titles:
   canonical=title;seen=set()
   while canonical in aliases and canonical not in seen:seen.add(canonical);canonical=aliases[canonical]
   page=pages.get(canonical,{})
   english=canonical if lang=='en' else next((row.get('title',row.get('*','')) for row in page.get('langlinks',[]) if row.get('lang')=='en'),'')
   qid=page.get('pageprops',{}).get('wikibase_item')
   if english and qid:rows[title]={'id':qid,'name':english,'native_name':canonical}
  ids=sorted({row['id'] for row in rows.values()})
  entities={}
  if ids:
   params={'action':'wbgetentities','ids':'|'.join(ids),'props':'labels|descriptions|aliases|claims','languages':'en|'+lang,'format':'json'}
   entities=api.http_json('https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(params),timeout=22).get('entities',{})
  for row in rows.values():
   entity=entities.get(row['id'],{});claims=entity.get('claims',{})
   values=lambda prop:[x.get('mainsnak',{}).get('datavalue',{}).get('value') for x in claims.get(prop,[])]
   types={v.get('id') for v in values('P31') if isinstance(v,dict)}
   row['kind']='human' if 'Q5' in types else 'entity'
   row['description']=entity.get('descriptions',{}).get('en',{}).get('value','')
   row['name']=entity.get('labels',{}).get('en',{}).get('value') or row['name']
   row['aliases']=list(dict.fromkeys(alias['value'] for language in dict.fromkeys(['en',lang]) for alias in entity.get('aliases',{}).get(language,[]) if 3<=len(alias.get('value',''))<=100))[:20]
   categories=[v for v in values('P373') if isinstance(v,str)]
   row['commons_category']=categories[0] if categories else ''
   row['source_url']='https://www.wikidata.org/wiki/'+row['id']
  return rows
 return api.cache_fetch('scene-linked-entities-v2|'+lang+'|'+'|'.join(titles),fetch)

def scene_intent(text,target):
 description=target.get('description','')
 intents=[
  ('medical treatment',r'treat\w*|therap\w*|lecze\w*|лікува\w*|лечен\w*',r'therap\w*|treat\w*|cancer|carcinoma|medical|clinic\w*|hospital|oncolog\w*|radiolog\w*|лечен\w*|лікува\w*|terapi\w*','medical treatment, radiotherapy equipment or clinical laboratory research'),
  ('landing',r'landing|landed|touchdown|посад\w*|спуск\w*|lądowa\w*',r'landing|landed|touchdown|drone ship|drone.ship|ASDS|посад\w*|lądowa\w*','a rocket landing on its landing pad or landing platform'),
  ('first conference',r'first.*conference|pierwsz\w*.*kongres|перш\w*.*конгрес|перв\w*.*конферен',r'\bfirst\b|\b1st\b|\bpremier\w*|перв\w*|перш\w*','the first conference'),
 ]
 for name,pattern,metadata,visual in intents:
  context=target.get('anchor','') if name=='first conference' else text
  if re.search(pattern,context,re.I):
   if name=='medical treatment' and not re.search(r'cancer|carcinoma|tumou?r|patient|medical|illness|disease|\brak\w*|\bрак\w*|nowotw\w*|хвор\w*|болез\w*',text+' '+description,re.I):continue
   result={'name':name,'metadata_pattern':metadata,'visual':visual,'query_suffix':name}
   if name=='landing':
    kind='rocket' if re.search(r'rocket|launch.?vehicle|spacecraft',description,re.I) else 'aircraft' if re.search(r'aircraft|airplane|airliner|helicopter',description,re.I) else target['name']
    result['visual']='a '+kind+' landing at its landing area or landing platform'
    result['forbidden_metadata']=r'engine test|landing leg test|ground test|simulation|rendering'
    result['negative_descriptions']=['A rocket or aircraft taking off and ascending.','An engine being tested on the ground or a vehicle inside a factory.']
   if name=='medical treatment':
    result['negative_descriptions']=['An atomic bomb test or a nuclear explosion.','A military weapon, nuclear missile or mushroom cloud.']
   return result
 if re.search(r'\b(?:award|prize|honou?r)\b|of the year',description+' '+target['name'],re.I):
  return {'name':'physical award','metadata_pattern':r'\b(?:medals?|troph(?:y|ies)|statuettes?|medaille\w*|medalla\w*|медал\w*)\b','visual':'the physical medal, trophy or award statuette','query_suffix':'medal trophy'}
 if re.search(r'company|corporation|manufacturer|business|social networking service',description,re.I) and any(c.isupper() for c in target['name']):
  subject='its products, production facility or headquarters building'
  if re.search(r'aerospace|spacecraft|rocket',description,re.I):subject='a rocket, spacecraft or space launch facility'
  elif re.search(r'vehicle|automotive|car manufacturer',description,re.I):subject='a vehicle, automotive factory or showroom'
  elif re.search(r'tunnel|infrastructure|construction',description,re.I):subject='tunnel construction machinery or an underground tunnel'
  elif re.search(r'neurotechnol|brain|implant',description,re.I):subject='a neural implant, brain interface device or laboratory equipment'
  elif re.search(r'social network|software|internet',description,re.I):subject='a photographed device displaying the service or its headquarters building'
  return {'name':'organization context','metadata_pattern':None,'visual':subject,'query_suffix':''}
 if re.search(r'chemical element.*atomic number|element with atomic number',description,re.I):
  return {'name':'physical sample','metadata_pattern':None,'visual':'a physical chemical sample, mineral specimen or laboratory vial containing '+target['name'],'query_suffix':''}
 return {'name':'linked subject','metadata_pattern':None,'visual':description[:180] or target['name'],'query_suffix':''}

def build(slots,sources,lang,api):
 profile=sources[0].get('entity_profile',{})
 links=source_links(sources,lang,api)
 alias_titles={}
 for link in links:alias_titles.setdefault(link['label'].casefold(),set()).add(link['title'])
 def alias_matches(link,text):
  if phrase_in(link['label'],text) or phrase_in(link['title'],text):return True
  if lang=='en' or not link['label'][:1].isupper():return False
  words=re.findall(r'[^\W\d_]+',link['label'].casefold());body=re.findall(r'[^\W\d_]+',text.casefold())
  if not words or len(words)>8:return False
  def same(left,right):
   if left==right:return True
   minimum=min(len(left),len(right))
   return minimum>=5 and abs(len(left)-len(right))<=3 and left[:max(4,minimum-2)]==right[:max(4,minimum-2)]
  return any(all(same(left,right) for left,right in zip(words,body[start:start+len(words)])) for start in range(len(body)-len(words)+1))
 def local_links(slot):
  source=sources[slot.get('source_index',0)]
  span=slot.get('source_sentence') or slot['text']
  paragraph=next((paragraph for paragraph in source['text'].splitlines() if span in paragraph),'')
  key=paragraph_key(paragraph);found={}
  for link in links:
   if re.fullmatch(r'[\d\W]+',link['label']):continue
   if not alias_matches(link,slot['text']):continue
   explicit=link.get('paragraph_key')==key
   unambiguous=len(alias_titles[link['label'].casefold()])==1
   if explicit or unambiguous:
    row={**link,'binding':'explicit paragraph link' if explicit else 'unambiguous article alias'}
    found.setdefault((link['label'],link['title']),row)
  return list(found.values())
 matched=list({(link['label'],link['title'],link.get('paragraph_key')):link for slot in slots for link in local_links(slot)}.values())
 resolved=resolve_links(matched,lang,api)
 for index,slot in enumerate(slots):
  targets={}
  if index==0:
   # The establishing scene may show the main subject. Subsequent factual
   # scenes must establish their own objects, places, institutions or events.
   slot['visual_targets']=[];slot['visual_role']='establishing';continue
  if slot.get('process_intent'):
   slot['visual_targets']=[];slot['visual_role']='process_evidence';continue
  for link in local_links(slot):
   entity=resolved.get(link['title'])
   if not entity or entity['id']==profile.get('id'):continue
   description=entity.get('description','')
   if entity.get('kind')=='human':continue
   if re.search(r'^(?:calendar year|year\b|date |month |day |century|decade|Wikimedia|disambiguation|given name|family name|occupation|profession|position|job title|role |term |concept|academic degree)',description,re.I):continue
   row={**entity,'anchor':link['label'],'article_url':sources[slot.get('source_index',0)]['url'],'source_sentence':slot.get('source_sentence',slot['text']),'binding':link.get('binding','explicit paragraph link')}
   # Specific objects/institutions outrank broad countries or disciplines.
   proper=any(character.isupper() for character in entity['name'])
   row['priority']=3 if proper else 1
   if re.search(r'^(?:country|sovereign state|continent|academic discipline|academic degree|field of|any |occupation|profession|official privileged social class|systematic study|relation of|mathematical)',description,re.I):row['priority']=0
   if re.search(r'chemical element.*atomic number|element with atomic number',description,re.I):row['priority']=3
   if re.search(r'conference|congress|summit|exhibition',description+' '+entity['name'],re.I):row['priority']=4
   if row['priority']==0:continue
   row['intent']=scene_intent(slot['text'],row)
   targets.setdefault(entity['id'],row)
  ranked=sorted(targets.values(),key=lambda row:(-row['priority'],-len(row['anchor']),row['name']))
  chosen=[row for row in ranked if row['priority']==ranked[0]['priority']][:2] if ranked else []
  chosen.sort(key=lambda row:slot['text'].casefold().find(row['anchor'].casefold()))
  slot['visual_targets']=chosen;slot['visual_role']='scene_evidence'
  if profile.get('kind')=='human' and not chosen:
   raise SceneUnavailable(slot,'No source-linked visual subject for a factual scene; a generic portrait is insufficient')
 return slots

def query_plan(slots):
 targets={}
 for slot in slots:
  for target in slot.get('visual_targets',[]):
   intent=target.get('intent',{})
   targets.setdefault((target['id'],intent.get('name','')),target)
 primary=[];second=[]
 for target in targets.values():
  name=target['name']
  if len(name)<3 and target.get('anchor','').isascii():name=target.get('anchor') or name
  suffix=target.get('intent',{}).get('query_suffix','')
  primary.extend([name+' medal',name+' trophy'] if target.get('intent',{}).get('name')=='physical award' else [name+(' '+suffix if suffix else '')])
  second.append(name+(' '+suffix if suffix else '')+' incategory:"CC-BY-2.0"')
 return list(dict.fromkeys(primary+second))

def shot_slots(slots,beat_for_shot):
 used={};out=[]
 for beat in beat_for_shot:
  ordinal=used.get(beat,0);used[beat]=ordinal+1
  row=dict(slots[beat]);targets=row.get('visual_targets',[])
  if targets:
   row['visual_target']=targets[ordinal%len(targets)]
   row['visual_target_optional']=ordinal>=len(targets)
  out.append(row)
 return out

def target_score(candidate,slot,api):
 target=slot['visual_target']
 if candidate.get('provider')!='commons':return -1
 categories=[category for category in candidate.get('categories',[]) if not re.search(r'\b(?:from|via|uploaded|taken with|photographs by|images by|files by)\b',category,re.I)]
 identity_fragments=[re.sub(r'^(?:File|Category):','',field,flags=re.I) for field in [candidate.get('depiction','')]+categories]
 identity_text=' '.join(identity_fragments)
 text=identity_text+' '+candidate.get('alt','')
 names={target['name'],target.get('native_name',''),target.get('commons_category',''),target.get('anchor','')}|set(target.get('aliases',[]))
 def identity_phrase(name):
  normalized_name=re.sub(r'[\W_]+',' ',name.casefold()).strip()
  for field in identity_fragments:
   normalized_text=re.sub(r'[\W_]+',' ',field.casefold()).strip()
   for match in re.finditer(r'(?<!\w)'+re.escape(normalized_name)+r'(?!\w)',normalized_text):
    if target.get('intent',{}).get('name')=='physical award' and match.start():
     prefix=normalized_text[:match.start()].split();last=prefix[-1] if prefix else ''
     if last not in {'of','the','a','an','in','for','by','at','to','s'} and not last.isdigit():continue
    return True
  return False
 if not any(identity_phrase(name) for name in names if len(name)>=3):return -1
 intent=target.get('intent',{})
 if intent.get('metadata_pattern') and not re.search(intent['metadata_pattern'],identity_text if intent.get('name')=='physical award' else text,re.I):return -1
 if intent.get('forbidden_metadata') and re.search(intent['forbidden_metadata'],text,re.I):return -1
 if intent.get('name')=='physical award' and re.search(r'portrait|headshot|laureates?|winners?|recipients?|ceremony|conference|banquet',candidate.get('depiction',''),re.I):return -1
 if intent.get('name')=='organization context':
  if any('screenshot' in category.lower() for category in candidate.get('categories',[])):return -1
  if re.search(r'\b(?:profiles?|accounts?|homepages?|screenshots?)\b',candidate.get('depiction',''),re.I):return -1
 if intent.get('name')=='organization context' and re.search(r'press.conference|portrait|headshot|interview|speaking at|speaking to',candidate.get('depiction','')+' '+candidate.get('alt',''),re.I):return -1
 return 30+len(set(api.tokens(target['name']))&set(api.tokens(text)))

"use strict";
const {DictionaryLemmas, fail, normalize, words, sourceLexicon, subjectCandidates, resolveSubject} = require('./VisualSubject');
const {focalSpans,timeBeats,validateBeats,rankMedia,quality,MAX_STATIC_MS,MIN_BEAT_MS}=require('./VisualBeats');
const USER_AGENT = 'ai-short-form-content-factory/1.0 (https://github.com/Pokhyl/ai-short-form-content-factory)';
const COMMONS = 'https://commons.wikimedia.org/w/api.php';
const encoded = value => encodeURIComponent(String(value));
const keyForFile = title => normalize(decodeURIComponent(String(title))).replace(/^file:/, '').trim();
const clean = value => String(value || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

function sourceSpec(terms) {
  const found = [];
  for (const term of terms || []) {
    const m = /^visualsource::(uk|ru|pl|en)::([^:]+)::(.+)$/i.exec(term);
    if (m) {
      try { found.push({lang: m[1].toLowerCase(), title: decodeURIComponent(m[2])}); }
      catch { fail('invalid_source', term); }
    }
  }
  if (found.length !== 1) fail('source_required', 'Exactly one localized visualsource is required');
  return found[0];
}
function pageFrom(payload) {
  if (payload.error) fail('wiki_api_error', payload.error.info || payload.error.code);
  const pages = Object.values(payload.query?.pages || {});
  if (pages.length !== 1) return null;
  const p = pages[0];
  return p.missing !== undefined || p.invalid !== undefined || p.pageprops?.disambiguation !== undefined ? null : p;
}
function mediaInfo(title, info, source) {
  if (!info) return null;
  let mime = String(info.mime || '');
  if (mime === 'image/svg+xml' && /\.png(?:\?|$)/i.test(info.thumburl || '')) mime = 'image/png';
  const kind = /^video\/(webm|mp4)$/.test(mime) ? 'video' : /^image\/(jpeg|png|webp|gif)$/.test(mime) ? 'image' : null;
  if (!kind) return null;
  const url = kind === 'video' ? info.url : info.thumburl || info.url;
  const width = Number(info.thumbwidth || info.width), height = Number(info.thumbheight || info.height);
  if (!/^https:\/\/(?:upload|thumb)\.wikimedia\.org\//i.test(url || '') || !width || !height || Math.max(width, height) < 700 || width / height > 3 || width / height < 1 / 3) return null;
  const mediaKey = keyForFile(title);
  return {id: `wikimedia:${mediaKey}`, mediaKey, title, url, width, height, kind, extension: mime.includes('png') ? '.png' : mime.includes('gif') ? '.gif' : mime.includes('webp') ? '.webp' : mime.includes('mp4') ? '.mp4' : mime.includes('webm') ? '.webm' : '.jpg', source};
}
// Filename is only a rejection signal. Positive proof requires exact pageimage
// provenance or a sole structured depicts (P180) statement for the chosen QID.
function safeCommonsTitle(title, englishTitle) {
  const name = keyForFile(title).replace(/\.(jpg|jpeg|png|webp|webm|mp4)$/i, '');
  const entity = normalize(englishTitle);
  if (name === entity) return true;
  if (!name.startsWith(entity + ' ') && !name.startsWith(entity + '-')) return false;
  const suffix = name.slice(entity.length).replace(/[-_()]/g, ' ').trim();
  return /^(?:(?:diagram|illustration|animation|simulation|schematic|image|photo|photograph|comparison|size|scale|en|uk|ru|pl|[0-9]+)\s*)+$/.test(suffix);
}

class PexelsAPI {
  constructor(_key, options = {}) {
    this.fetchJson = options.fetchJson;
    this.dictionary = options.dictionary || new DictionaryLemmas();
    this.sources = new Map();
    this.entities = new Map();
    this.mediaPools = new Map();
    this.plans = new WeakMap();
    this.wikidata = new Map();
  }
  async _fetchJson(url) {
    if (this.fetchJson) return this.fetchJson(url);
    for (let attempt = 0; attempt < 3; attempt++) {
      const response = await fetch(url, {headers: {'User-Agent': USER_AGENT}, signal: AbortSignal.timeout(15000)});
      if (response.ok) return response.json();
      if (![429, 502, 503, 504].includes(response.status) || attempt === 2) fail('wiki_unavailable', `HTTP ${response.status}`);
      await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)));
    }
  }
  async query(base, params) { return this._fetchJson(`${base}?${new URLSearchParams({...params, format: 'json'})}`); }
  async dataEntity(qid) {
    if (!this.wikidata.has(qid)) {
      const data = await this.query('https://www.wikidata.org/w/api.php', {action:'wbgetentities',ids:qid,props:'claims|labels|aliases|sitelinks',languages:'en',sitefilter:'enwiki'});
      const entity = data.entities?.[qid];
      if (!entity || entity.missing !== undefined) fail('wikidata_unavailable', qid);
      this.wikidata.set(qid, entity);
    }
    return this.wikidata.get(qid);
  }
  async belongsTo(qid, group, seen = new Set(), depth = 0) {
    if (qid === group) return true;
    if (depth >= 5 || seen.has(qid)) return false;
    seen.add(qid);
    const data = await this.dataEntity(qid);
    const parents = ['P31','P279'].flatMap(p => (data.claims?.[p] || []).filter(c => c.rank !== 'deprecated').map(c => c.mainsnak?.datavalue?.value?.id)).filter(Boolean);
    if (parents.includes(group)) return true;
    for (const parent of parents) if (await this.belongsTo(parent, group, seen, depth + 1)) return true;
    return false;
  }
  async lexicon(spec) {
    const key = `${spec.lang}:${spec.title}`;
    if (!this.sources.has(key)) {
      const data = await this.query(`https://${spec.lang}.wikipedia.org/w/api.php`, {action: 'parse', page: spec.title, prop: 'wikitext', redirects: '1'});
      const wikitext = data.parse?.wikitext?.['*'];
      if (!wikitext) fail('source_unavailable', key);
      this.sources.set(key, {entries: sourceLexicon(wikitext, spec.title), revision: data.parse.revid});
    }
    return this.sources.get(key);
  }
  async ground(lang, title) {
    const key = `${lang}:${title}`;
    if (this.entities.has(key)) return this.entities.get(key);
    const localData = await this.query(`https://${lang}.wikipedia.org/w/api.php`, {
      action: 'query', titles: title, redirects: '1', prop: 'langlinks|pageprops', lllang: 'en', lllimit: '1', ppprop: 'wikibase_item|disambiguation',
    });
    let local = pageFrom(localData);
    const fragment = localData.query?.redirects?.find(r => r.tofragment);
    if (fragment) {
      // The first lookup can redirect to a section too. Its destination QID
      // identifies the containing article, not the requested concept.
      const exact = await this.query('https://www.wikidata.org/w/api.php', {
        action:'wbgetentities',sites:`${lang}wiki`,titles:fragment.from,
        props:'claims|labels|aliases|sitelinks',languages:'en',sitefilter:`${lang}wiki|enwiki`,
      });
      const matches = Object.values(exact.entities || {}).filter(e =>
        /^Q\d+$/.test(e.id || '') && e.missing === undefined &&
        normalize(e.sitelinks?.[`${lang}wiki`]?.title) === normalize(fragment.from));
      if (matches.length !== 1) fail('exact_grounding_missing', key);
      const wd = matches[0];
      this.wikidata.set(wd.id, wd);
      local = {title:fragment.from,pageprops:{wikibase_item:wd.id},langlinks:[{lang:'en','*':wd.sitelinks?.enwiki?.title}]};
    }
    const qid = local?.pageprops?.wikibase_item;
    const englishTitle = lang === 'en' ? local?.title : local?.langlinks?.find(l => l.lang === 'en')?.['*'];
    if (!/^Q[0-9]+$/.test(qid || '') || !englishTitle) fail('exact_grounding_missing', key);
    const enData = await this.query('https://en.wikipedia.org/w/api.php', {
      action: 'query', titles: englishTitle, redirects: '1', prop: 'pageimages|pageprops', ppprop: 'wikibase_item|disambiguation', piprop: 'name|thumbnail', pithumbsize: '1080',
    });
    const en = pageFrom(enData);
    let entity;
    if (en && en.pageprops?.wikibase_item === qid) entity = {localTitle: local.title, englishTitle: en.title, qid, page: en};
    else if (enData.query?.redirects?.some(r => r.tofragment && normalize(r.from) === normalize(englishTitle))) {
      const wd = await this.dataEntity(qid);
      if (normalize(wd.sitelinks?.enwiki?.title) !== normalize(englishTitle)) fail('entity_identity_mismatch', key);
      // A section redirect identifies a concept, never the containing page's image.
      entity = {localTitle:local.title, englishTitle, qid, page:null, sectionRedirect:enData.query.redirects};
    } else fail('entity_identity_mismatch', key);
    this.entities.set(key, entity);
    return entity;
  }
  async pageImage(entity) {
    const {page} = entity;
    if (page?.pageimage && page.thumbnail) {
      const ext = /\.(jpe?g|png|webp|gif)(?:\?|$)/i.exec(new URL(page.thumbnail.source).pathname)?.[1].toLowerCase();
      const media = ext && mediaInfo(`File:${page.pageimage}`, {url: page.thumbnail.source, width: page.thumbnail.width, height: page.thumbnail.height, mime: `image/${ext === 'jpg' ? 'jpeg' : ext}`}, 'exact_english_wikipedia');
      if (media) return media;
    }
    // A missing/undersized page thumbnail does not invalidate exact P18 evidence.
    // Every alternative still passes the same MIME, dimensions and host gates.
    const wd = await this.dataEntity(entity.qid);
    const filenames = (wd.claims?.P18 || []).filter(c => c.rank !== 'deprecated').map(c => c.mainsnak?.datavalue?.value).filter(f => typeof f === 'string');
    for (const filename of filenames) {
      const data = await this.query(COMMONS, {action:'query',titles:`File:${filename}`,prop:'imageinfo',iiprop:'url|mime|size',iiurlwidth:'1080'});
      const p = Object.values(data.query?.pages || {})[0];
      const media = p && mediaInfo(p.title, p.imageinfo?.[0], 'exact_wikidata_p18');
      if (media) return media;
    }
    return null;
  }
  async commonsMedia(entity, preferVideo) {
    const result = await this.query(COMMONS, {action: 'query', generator: 'search', gsrsearch: `${words(entity.englishTitle).map(w => `intitle:${w.text}`).join(' ')}${preferVideo ? ' filetype:video' : ''}`, gsrnamespace: '6', gsrlimit: '24', prop: 'imageinfo', iiprop: 'url|mime|size|extmetadata', iiurlwidth: '1080'});
    const candidates = [];
    for (const p of Object.values(result.query?.pages || {})) if (await this.exactMediaTitle(p.title, entity)) candidates.push(p);
    if (!candidates.length) return [];
    const data = await this.query(COMMONS, {action: 'wbgetentities', ids: candidates.map(p => `M${p.pageid}`).join('|'), props: 'claims'});
    const media = [];
    for (const p of candidates) {
      const statements = data.entities?.[`M${p.pageid}`]?.statements || data.entities?.[`M${p.pageid}`]?.claims || {};
      const depicts = (statements.P180 || []).filter(c => c.rank !== 'deprecated').map(c => c.mainsnak?.datavalue?.value?.id);
      if (!depicts.length || depicts.some(q => !/^Q\d+$/.test(q || ''))) continue;
      if (depicts.length === 1 && depicts[0] !== entity.qid) continue;
      let relevant = true;
      for (const qid of depicts) if (!await this.belongsTo(qid, entity.qid)) {relevant = false; break;}
      if (!relevant) continue;
      const item = mediaInfo(p.title, p.imageinfo?.[0], 'exact_entity_commons');
      if (!item || (preferVideo && item.kind !== 'video')) continue;
      const metadata = p.imageinfo[0].extmetadata || {};
      item.description = clean(metadata.ImageDescription?.value);
      item.depicts = entity.qid;
      media.push(item);
    }
    return media.sort((a, b) => a.mediaKey.localeCompare(b.mediaKey, 'en'));
  }
  async exactMediaTitle(title, entity) {
    if (safeCommonsTitle(title, entity.englishTitle)) return true;
    const text = keyForFile(title).replace(/\.[a-z0-9]+$/i, '');
    const aliases = [entity.englishTitle];
    // Dictionary-normalized whole aliases plus a closed, topic-neutral vocabulary
    // of presentation descriptors. Extra substantive co-subjects are rejected.
    const wd = await this.dataEntity(entity.qid);
    aliases.push(...(wd.aliases?.en || []).map(a => a.value));
    aliases.push(...aliases.filter(a => /^[A-Z]{2,8}$/.test(a)).map(a => a + 's'));
    const matches = await subjectCandidates(text, 'en', [{title:entity.englishTitle,aliases}], this.dictionary);
    if (!matches.length) return false;
    const remainder = words(text).filter(w => !matches.some(m => w.start >= m.start && w.end <= m.end));
    return remainder.every(w => /^(?:\d+|largest|smallest|known|sizes?|of|the|diagram|illustration|animation|simulation|schematic|image|photo|photograph|comparison|scale|en|uk|ru|pl)$/.test(w.text));
  }
  async selectMedia(entity, used, preferVideo = false, excluded = []) {
    const primary = await this.pageImage(entity);
    const prior = primary && used.get(primary.mediaKey);
    if (primary && !prior && !excluded.includes(primary.id)) return {...primary, resolutionType: primary.source};
    const poolKey = `${entity.qid}:${preferVideo}`;
    if (!this.mediaPools.has(poolKey)) this.mediaPools.set(poolKey, await this.commonsMedia(entity, preferVideo));
    const pool = this.mediaPools.get(poolKey);
    const available = pool.find(m => !used.has(m.mediaKey) && !excluded.includes(m.id));
    if (available) return {...available, resolutionType: 'exact_entity_commons'};
    // Media already assigned to a different entity must never be reused.
    const reusable = [primary, ...pool].find(m => m && used.get(m.mediaKey)?.qid === entity.qid && !excluded.includes(m.id));
    if (reusable) return {...reusable, resolutionType: reusable.source, reuseReason: 'same_entity_no_alternative'};
    fail('exact_media_missing', entity.englishTitle);
  }
  async structuredGroupMedia(entity, used) {
    const wd = await this.dataEntity(entity.qid);
    const claims = (wd.claims?.P527 || []).filter(c => c.rank !== 'deprecated');
    if (claims.some(c => Object.keys(c.qualifiers || {}).length)) fail('exact_media_missing', entity.englishTitle);
    const ids = [...new Set(claims.map(c => c.mainsnak?.datavalue?.value?.id))];
    if (ids.length < 2 || ids.length > 8 || ids.some(id => !/^Q\d+$/.test(id || ''))) fail('exact_media_missing', entity.englishTitle);
    const components = [], memberUsed = new Map(used);
    for (const id of ids) {
      const data = await this.dataEntity(id);
      const title = data.sitelinks?.enwiki?.title;
      if (!title) fail('exact_grounding_missing', id);
      const member = await this.ground('en', title);
      if (member.qid !== id) fail('entity_identity_mismatch', title);
      const media = await this.selectMedia(member, memberUsed);
      memberUsed.set(media.mediaKey, {qid:id});
      components.push({...media,groundedEntity:member.englishTitle,groundedEntityId:id});
    }
    const mediaKey = `montage:${entity.qid}:${components.map(m=>m.mediaKey).join('|')}`;
    return {id:mediaKey,mediaKey,kind:'image',extension:'.jpg',width:1080,height:1920,title:`${entity.englishTitle}: ${components.map(m=>m.title).join(' + ')}`,source:'exact_wikidata_parts',resolutionType:'exact_wikidata_parts',components};
  }
  async entityMedia(entity, used) {
    try { return await this.selectMedia(entity, used); }
    catch (error) {
      if (error.code !== 'exact_media_missing') throw error;
      return this.structuredGroupMedia(entity, used);
    }
  }
  async explicitGroupMedia(subject, spec, lexicon, entity, used) {
    if (!subject.listText || !/[,]|(?:\s(?:and|та|і|и|oraz|i)\s)/iu.test(subject.listText)) return null;
    const candidates = await subjectCandidates(subject.listText, spec.lang, lexicon, this.dictionary);
    const unmatched = words(subject.listText).filter(w => !candidates.some(c => w.start >= c.start && w.end <= c.end));
    if (unmatched.some(w => !/^(?:and|та|і|и|oraz|i)$/.test(w.text))) fail('unresolved_group_member', subject.listText);
    const members = new Map();
    const memberUsed = new Map(used);
    const spanIdentities = new Map();
    const grounded = [];
    for (const candidate of candidates.sort((a,b) => a.start-b.start)) {
      const member = await this.ground(spec.lang, candidate.title);
      const span = `${candidate.start}:${candidate.end}`;
      if (spanIdentities.has(span) && spanIdentities.get(span) !== member.qid) fail('ambiguous_group_member', candidate.surface);
      spanIdentities.set(span, member.qid);
      grounded.push(member);
    }
    for (const member of grounded) {
      if (member.qid === entity.qid) continue;
      if (members.has(member.qid)) continue;
      const media = await this.selectMedia(member, memberUsed);
      memberUsed.set(media.mediaKey, {qid:member.qid});
      members.set(member.qid, {...media, groundedEntity:member.englishTitle, groundedEntityId:member.qid});
    }
    if (members.size < 2 || members.size > 8) fail('ambiguous_group_members', subject.listText);
    const components = [...members.values()];
    const mediaKey = `montage:${entity.qid}:${components.map(m => m.mediaKey).join('|')}`;
    return {id:mediaKey,mediaKey,kind:'image',extension:'.jpg',width:1080,height:1920,title:`${entity.englishTitle}: ${components.map(m => m.title).join(' + ')}`,source:'exact_listed_members',resolutionType:'exact_listed_members',components};
  }
  prepareScenes(scenes) {
    if (!Array.isArray(scenes) || !scenes.length) fail('empty_scenes', 'At least one scene is required');
    return scenes.flatMap((scene, inputSceneIndex) => {
      if (typeof scene?.text !== 'string' || !scene.text.trim()) fail('empty_scene', `Scene ${inputSceneIndex}`);
      const spec = sourceSpec(scene.searchTerms);
      const segments = [...new Intl.Segmenter(spec.lang, {granularity: 'sentence'}).segment(String(scene.text || ''))];
      return segments.map(s => ({...scene, text: s.segment.trim(), mediaContext: s.segment.trim(), mediaHistory: undefined, inputSceneIndex})).filter(s => s.text);
    });
  }
  async preflightScenes(scenes) {
    if (!Array.isArray(scenes) || !scenes.length) fail('empty_scenes', 'At least one scene is required');
    const media = [], used = new Map();
    let previous = null;
    for (const [sceneIndex, scene] of scenes.entries()) {
      const spec = sourceSpec(scene.searchTerms), source = await this.lexicon(spec);
      // User-supplied mediaContext/mediaHistory cannot inject subjects or history.
      const antecedent = previous && previous.lang === spec.lang && previous.sourceTitle === spec.title ? previous : null;
      const subject = await resolveSubject(scene.text, spec.lang, source.entries, this.dictionary, antecedent, async title => (await this.ground(spec.lang, title)).qid);
      const entity = subject.mode === 'current_enumeration'
        ? {qid: `list:${subject.listText}`, englishTitle: subject.listText, localTitle: subject.listText}
        : await this.ground(spec.lang, subject.title);
      const selected = await this.explicitGroupMedia(subject, spec, source.entries, entity, used) || await this.entityMedia(entity, used);
      const item = {...selected, sceneIndex, narration: scene.text, subject, groundedEntity: entity.englishTitle, groundedEntityId: entity.qid, visualQuery: entity.englishTitle, confidence: 'high', sourceRevision: source.revision};
      media.push(item);
      this.plans.set(item, {entity, used});
      used.set(item.mediaKey, {qid: entity.qid, sceneIndex});
      for (const component of item.components || []) used.set(component.mediaKey, {qid:component.groundedEntityId, sceneIndex});
      previous = subject.mode === 'current_enumeration' ? null : {...entity, lang: spec.lang, sourceTitle: spec.title, sceneIndex};
    }
    return media;
  }
  async exactBeatPool(entity, relational) {
    const primary = await this.pageImage(entity);
    const wd = await this.dataEntity(entity.qid);
    const images = primary ? [primary] : [];
    for (const claim of wd.claims?.P18 || []) {
      const filename = claim.mainsnak?.datavalue?.value;
      if (claim.rank === 'deprecated' || typeof filename !== 'string') continue;
      const data = await this.query(COMMONS,{action:'query',titles:`File:${filename}`,prop:'imageinfo',iiprop:'url|mime|size|extmetadata',iiurlwidth:'1600'});
      const page=Object.values(data.query?.pages||{})[0], info=page?.imageinfo?.[0];
      const media=page&&mediaInfo(page.title,info,'exact_wikidata_p18');
      if(media)images.push({...media,description:clean(info.extmetadata?.ImageDescription?.value)});
    }
    images.push(...await this.commonsMedia(entity,false));
    const unique=new Map();
    for(const image of images.filter(quality))if(!unique.has(image.mediaKey))unique.set(image.mediaKey,image);
    const ranked=rankMedia([...unique.values()],relational);
    if(!ranked.length)fail('exact_high_quality_media_missing',entity.englishTitle);
    return ranked;
  }
  async preflightVisualBeats(scenes) {
    const primary=await this.preflightScenes(scenes), bundles=[];
    let previousKey=null;
    for(const [i,scene] of scenes.entries()) {
      const spec=sourceSpec(scene.searchTerms), lexicon=await this.lexicon(spec);
      const spans=await focalSpans(scene.text,spec.lang,lexicon.entries,this.dictionary,primary[i].subject);
      const beats=[], spanIds=new Map();
      for(const span of spans) {
        const entity=span.title?await this.ground(spec.lang,span.title):this.plans.get(primary[i]).entity;
        // Existing explicit composite subjects retain every component as a group.
        if(String(entity.qid).startsWith('list:')) {
          const components=primary[i].components;
          if(!components?.length||components.some(c=>!quality(c)))fail('exact_high_quality_media_missing',entity.englishTitle);
          beats.push({...primary[i],span,concept:entity.englishTitle,resolutionMode:'explicit_group',alternatives:[]});continue;
        }
        const spanKey=`${span.startChar}:${span.endChar}`;
        if(spanIds.has(spanKey)){if(spanIds.get(spanKey)!==entity.qid)fail('ambiguous_beat_span',scene.text);continue;}
        spanIds.set(spanKey,entity.qid);
        const relational=spans.length===1&&/(?<!\p{L})(?:between|між|между|między|orbit|орбіт|орбит)/iu.test(scene.text);
        const pool=await this.exactBeatPool(entity,relational);
        const selected=pool.find(m=>m.mediaKey!==previousKey);
        if(!selected)fail('duplicate_visual_identity',entity.englishTitle);
        beats.push({...selected,span,concept:entity.englishTitle,groundedEntityId:entity.qid,resolutionMode:spans.length>1?'focal_list_item':'focal_claim',alternatives:pool.filter(m=>m.mediaKey!==selected.mediaKey)});
        previousKey=selected.mediaKey;
      }
      // More than six items remain visible as one deterministic all-member group.
      // Never discard the end of a list. Timing can choose the same strategy for a short list.
      bundles.push({primary:primary[i],beats,groupRequired:beats.length>6});
    }
    return bundles;
  }
  planVisualBeats(bundle, timeline, previousKey=null) {
    let beats=bundle.beats;
    const montage=()=>{
      const components=beats.map(({alternatives,...media})=>media);
      const mediaKey=`montage:${components.map(c=>c.mediaKey).join('|')}`;
      return [{kind:'image',extension:'.jpg',width:1080,height:1920,components,mediaKey,id:mediaKey,title:components.map(c=>c.title).join(' + '),source:'exact_focal_group',concept:components.map(c=>c.concept).join(' + '),resolutionMode:'all_members_group',spans:components.map(c=>c.span),startMs:timeline.sceneStartMs,endMs:timeline.sceneEndMs,alternatives:[]}];
    };
    if(bundle.groupRequired)beats=montage();
    else {
      beats=timeBeats(beats,timeline);
      if(beats.length>1&&beats.some(b=>b.endMs-b.startMs<MIN_BEAT_MS))beats=montage();
    }
    const dense=[];
    for(const beat of beats){
      const duration=beat.endMs-beat.startMs;
      const count=beat.kind==='video'?1:Math.ceil(duration/MAX_STATIC_MS);
      const pool=[beat,...(beat.alternatives||[])];
      if(count>1&&pool.length<2)fail('visual_density',beat.concept);
      for(let j=0;j<count;j++)dense.push({...beat,...pool[j%pool.length],span:beat.span,spans:beat.spans,concept:beat.concept,resolutionMode:beat.resolutionMode,startMs:beat.startMs+duration*j/count,endMs:beat.startMs+duration*(j+1)/count});
    }
    validateBeats(dense,timeline.sceneStartMs,timeline.sceneEndMs,previousKey);
    return dense;
  }
  async planShots(media, durationSeconds) {
    const context = this.plans.get(media);
    if (!context || !Number.isFinite(durationSeconds) || durationSeconds <= 0) fail('invalid_visual_plan', 'Use preflight media with a positive duration');
    if (durationSeconds <= 8) return [{startSeconds: 0, durationSeconds, media}];
    const {entity, used} = context;
    if (media.components) return [{startSeconds: 0, durationSeconds, media, holdReason: 'explicit_members_montage'}];
    const poolKey = `${entity.qid}:false`;
    if (!this.mediaPools.has(poolKey)) this.mediaPools.set(poolKey, await this.commonsMedia(entity, false));
    const alternatives = this.mediaPools.get(poolKey).filter(m => m.mediaKey !== media.mediaKey && (!used.has(m.mediaKey) || used.get(m.mediaKey).qid === entity.qid));
    if (!alternatives.length) return [{startSeconds: 0, durationSeconds, media, holdReason: 'same_entity_no_alternative'}];
    const pool = [media, ...alternatives];
    const count = Math.ceil(durationSeconds / 8);
    return Array.from({length: count}, (_, index) => {
      const candidate = pool[index % pool.length];
      used.set(candidate.mediaKey, {qid: entity.qid, sceneIndex: media.sceneIndex});
      return {startSeconds: durationSeconds * index / count, durationSeconds: durationSeconds / count, media: candidate};
    });
  }
  async findVideo(terms, _duration, excludeIds = []) {
    // Legacy callers can resolve a single explicit scene, but cannot supply arbitrary
    // direct URLs, generic queries, or unverified history to bypass preflight.
    const spec = sourceSpec(terms);
    const contexts = (terms || []).filter(t => t.startsWith('scenecontext::'));
    if (contexts.length !== 1) fail('scene_required', 'Exactly one narration is required');
    let text;
    try { text = decodeURIComponent(contexts[0].slice('scenecontext::'.length)); } catch { fail('invalid_scene', 'Malformed context'); }
    const source = await this.lexicon(spec);
    const subject = await resolveSubject(text, spec.lang, source.entries, this.dictionary, null, async title => (await this.ground(spec.lang, title)).qid);
    const entity = await this.ground(spec.lang, subject.title);
    const selected = await this.selectMedia(entity, new Map(), false, excludeIds);
    return {...selected, subject, groundedEntity: entity.englishTitle, groundedEntityId: entity.qid, visualQuery: entity.englishTitle, confidence: 'high'};
  }
}
module.exports = {PexelsAPI, sourceSpec, pageFrom, mediaInfo, safeCommonsTitle, keyForFile};

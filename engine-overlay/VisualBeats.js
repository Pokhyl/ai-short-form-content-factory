'use strict';
const {words,normalize,subjectCandidates,fail}=require('./VisualSubject');
const MAX_STATIC_MS=5000, MIN_BEAT_MS=350;
const LIST_COPULA=/(?<!\p{L})(?:є|являются|są|are)(?!\p{L})\s+/iu;
const LIST_HEAD=/^(?:найбільшими|найменшими|крупнейшими|наибольшими|największymi|najmniejszymi|(?:the\s+)?(?:largest|smallest|biggest))/iu;
const POSSESSION=/(?<!\p{L})(?:мають|має|имеют|имеет|мають|mają|ma|posiadają|posiada|have|has|possess|possesses)(?!\p{L})/iu;
const RELATIVE_CLAUSE=/,\s*(?:which|who|that|що|який|яка|яке|які|который|которая|которые|которое|który|która|które)(?!\p{L})/iu;
const META_PAGE_TITLE=/^(?:list\s+of|список(?:\s|$)|lista(?:\s|$))/iu;
function withSpan(candidate,text,offset=0){ const raw=words(text),startChar=candidate.start+offset,endChar=candidate.end+offset; return {...candidate,startChar,endChar,startWord:raw.findIndex(w=>w.start>=startChar),endWord:raw.filter(w=>w.start<endChar).length}; }
async function appendPossessionObject(base,text,lang,lexicon,dictionary){ const verb=POSSESSION.exec(text); if(!verb)return base; const relative=RELATIVE_CLAUSE.exec(text); if(relative&&relative.index<verb.index)return base; const tailStart=verb.index+verb[0].length,rawTail=text.slice(tailStart),boundary=rawTail.search(/[,;.!?]/u),clause=(boundary>=0?rawTail.slice(0,boundary):rawTail).trim(); if(!clause)return base; const clauseOffset=tailStart+rawTail.indexOf(clause),candidates=(await subjectCandidates(clause,lang,lexicon,dictionary)).filter(c=>!META_PAGE_TITLE.test(c.title)),titles=[...new Set(candidates.map(c=>normalize(c.title)))]; if(titles.length!==1)return base; const chosen=candidates.sort((a,b)=>b.size-a.size||a.start-b.start)[0],relation={...withSpan(chosen,text,clauseOffset),mode:'focal_relation_object'}; if(base.some(item=>normalize(item.title)===normalize(relation.title)&&item.startChar===relation.startChar&&item.endChar===relation.endChar))return base; return [...base,relation].sort((a,b)=>a.startChar-b.startChar||b.endChar-a.endChar); }
// In a typed list ("countries France and Germany"), the adjacent lower-case
// class labels qualify the named members; they are not additional focal objects.
function namedListMembers(candidates,text){return candidates.filter(c=>!(/^\p{Ll}/u.test(c.surface)&&candidates.some(next=>next.start>=c.end&&/^\p{Lu}/u.test(next.surface)&&/^\s+$/u.test(text.slice(c.end,next.start)))));}
async function focalSpans(text,lang,lexicon,dictionary,subject){ let list=subject.listText,offset=list?normalize(text).indexOf(normalize(list)):-1; if(!list&&(subject.mode==='previous_scene_anaphora'||LIST_HEAD.test(text))){const copula=LIST_COPULA.exec(text);if(copula){offset=copula.index+copula[0].length;list=text.slice(offset).replace(/[.!?]\s*$/u,'');}} if(list&&offset>=0){const candidates=await subjectCandidates(list,lang,lexicon,dictionary),unmatched=words(list).filter(w=>!candidates.some(c=>c.start<=w.start&&c.end>=w.end));if(unmatched.some(w=>!/^(?:and|та|і|и|oraz|i)$/iu.test(w.text)))fail('unresolved_focal_list',list);if(candidates.length>=2)return appendPossessionObject(namedListMembers(candidates,list).sort((a,b)=>a.start-b.start).map(c=>withSpan(c,text,offset)),text,lang,lexicon,dictionary);} if(list&&offset<0){const all=await subjectCandidates(text,lang,lexicon,dictionary),members=all.filter(c=>normalize(list).includes(normalize(c.surface)));if(members.length>=2)return appendPossessionObject(members.sort((a,b)=>a.start-b.start).map(c=>withSpan(c,text)),text,lang,lexicon,dictionary);} const match=Number.isFinite(subject.start)?subject:(await subjectCandidates(text,lang,lexicon,dictionary)).find(c=>c.title===subject.title); const base=[{title:subject.title,...(match?withSpan(match,text):{startChar:0,endChar:0,startWord:0,endWord:1}),mode:'focal_claim'}]; return appendPossessionObject(base,text,lang,lexicon,dictionary); }
function quality(media){return Math.max(media.width||0,media.height||0)>=1000&&Math.min(media.width||0,media.height||0)>=600;}
function rankMedia(media,relational=false){ const score=m=>{const text=`${m.title||''} ${m.description||''}`,diagram=/diagram|taxonomy|taxonomic|legend|logo|euler|classification|schematic/iu.test(text),direct=/photograph|photo|portrait|painting|engraving|spacecraft|telescope|render|observation/iu.test(text),memorial=/grave|gravestone|tombstone|memorial|plaque|monument|headstone|cemetery|kirkyard/iu.test(text),document=/book|title\s*page|manuscript|treatise|lessons?|leçons/iu.test(text),provenance=m.source==='exact_wikidata_p18'?80:m.source==='exact_english_wikipedia'?65:m.source==='exact_wikidata_p373'?50:m.source==='exact_wikipedia_article_media'?25:0; return provenance+(diagram?(relational?40:-40):0)+(direct?30:0)-(memorial?55:0)-(document?15:0)+Math.min(10,Math.max(m.width||0,m.height||0)/1000);}; return [...media].sort((a,b)=>score(b)-score(a)||a.mediaKey.localeCompare(b.mediaKey,'en')); }
function timeBeats(beats,{sceneStartMs,sceneEndMs,wordToCaption=[],captions=[]}){
  if(!beats.length)fail('empty_visual_beats','No focal visual');
  if(beats.length===1)return[{...beats[0],startMs:sceneStartMs,endMs:sceneEndMs,timingEvidence:{alignmentSource:'semantic_scene'}}];
  const mapping=[...wordToCaption],recovered=new Set();
  // Recover only a one-to-one gap bracketed by two existing monotonic anchors.
  // No timestamps are interpolated: every recovered entry is a real caption.
  for(let left=0;left<mapping.length;left++){
    if(!Number.isInteger(mapping[left]))continue;
    let right=left+1;while(right<mapping.length&&!Number.isInteger(mapping[right]))right++;
    const missing=right-left-1;
    if(missing&&right<mapping.length&&mapping[right]-mapping[left]-1===missing){
      for(let w=left+1;w<right;w++){mapping[w]=mapping[left]+w-left;recovered.add(w);}
    }
    left=right-1;
  }
  const timed=beats.map((beat,i)=>{
    const span=beat.span;
    if(!span||!Number.isInteger(span.startWord)||!Number.isInteger(span.endWord)||span.endWord<=span.startWord)fail('unaligned_beat',beat.title);
    if(i&&span.startWord<beats[i-1].span.endWord)fail('unaligned_beat','Overlapping or unordered source spans');
    const indices=[];let gap=false;
    for(let w=span.startWord;w<span.endWord;w++){
      const index=mapping[w];if(!Number.isInteger(index)||!Number.isFinite(captions[index]?.startMs))fail('unaligned_beat',beat.title);
      if(indices.length&&index<indices.at(-1))fail('unaligned_beat','Non-monotonic captions');
      indices.push(index);gap ||= recovered.has(w);
    }
    const first=indices[0],last=indices.at(-1),spokenStartMs=captions[first].startMs;
    if(i){const previous=beats[i-1].span;const previousLast=mapping[previous.endWord-1];if(first<=previousLast)fail('unaligned_beat','Distinct names share a caption interval');}
    const spokenEndMs=captions[last].endMs??captions[last+1]?.startMs??sceneEndMs;
    const anchor=!i&&span.startWord===0?sceneStartMs:spokenStartMs;
    return{...beat,startMs:anchor,timingEvidence:{alignmentSource:gap?'bounded_caption_gap':'direct_caption',captionStartIndex:first,captionEndIndex:last,spokenStartMs,spokenEndMs,startAdjustmentMs:0}};
  });
  // Keep exact onsets whenever possible. A short name can borrow only the
  // beginning of the following name's spoken interval to satisfy readability.
  for(let i=0;i<timed.length;i++){
    const beat=timed[i],anchor=beat.startMs;
    if(i)beat.startMs=Math.max(anchor,timed[i-1].startMs+MIN_BEAT_MS);
    beat.timingEvidence.startAdjustmentMs=beat.startMs-anchor;
    if(beat.startMs<sceneStartMs||beat.startMs>=beat.timingEvidence.spokenEndMs||beat.startMs+MIN_BEAT_MS>sceneEndMs)fail('visual_timing_capacity',beat.concept||beat.title);
  }
  return timed.map((beat,i)=>({...beat,endMs:timed[i+1]?.startMs??sceneEndMs}));
}
function validateBeats(beats,startMs,endMs,previousKey=null){let cursor=startMs,key=previousKey;for(const b of beats){if(!Number.isFinite(b.startMs)||!Number.isFinite(b.endMs)||Math.abs(b.startMs-cursor)>1||b.endMs<=b.startMs||b.endMs>endMs+1)fail('invalid_visual_timing',b.title);if(b.endMs-b.startMs>MAX_STATIC_MS+1&&b.kind!=='video')fail('visual_density',b.title);if(b.mediaKey===key)fail('duplicate_visual_identity',b.mediaKey);cursor=b.endMs;key=b.mediaKey;}if(!beats.length||Math.abs(cursor-endMs)>1)fail('invalid_visual_coverage','Scene coverage');return true;}
module.exports={focalSpans,timeBeats,validateBeats,rankMedia,quality,MAX_STATIC_MS,MIN_BEAT_MS};

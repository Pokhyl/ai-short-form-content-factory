'use strict';
const {words,normalize,subjectCandidates,fail}=require('./VisualSubject');
const MAX_STATIC_MS=5000, MIN_BEAT_MS=350;
const LIST_COPULA=/(?<!\p{L})(?:є|являются|są|are)(?!\p{L})\s+/iu;
const LIST_HEAD=/^(?:найбільшими|найменшими|крупнейшими|наибольшими|największymi|najmniejszymi|(?:the\s+)?(?:largest|smallest|biggest))/iu;
function withSpan(candidate,text,offset=0){
 const raw=words(text),startChar=candidate.start+offset,endChar=candidate.end+offset;
 return {...candidate,startChar,endChar,startWord:raw.findIndex(w=>w.start>=startChar),endWord:raw.filter(w=>w.start<endChar).length};
}
async function focalSpans(text,lang,lexicon,dictionary,subject){
 let list=subject.listText,offset=list?normalize(text).indexOf(normalize(list)):-1;
 if (!list && (subject.mode==='previous_scene_anaphora'||LIST_HEAD.test(text))) {
  const copula=LIST_COPULA.exec(text);
  if(copula){offset=copula.index+copula[0].length;list=text.slice(offset).replace(/[.!?]\s*$/u,'');}
 }
 if(list && offset>=0){
  const candidates=await subjectCandidates(list,lang,lexicon,dictionary);
  const unmatched=words(list).filter(w=>!candidates.some(c=>c.start<=w.start&&c.end>=w.end));
  if(unmatched.some(w=>!/^(?:and|та|і|и|oraz|i)$/iu.test(w.text)))fail('unresolved_focal_list',list);
  if(candidates.length>=2)return candidates.sort((a,b)=>a.start-b.start).map(c=>withSpan(c,text,offset));
 }
 if(list&&offset<0){
  const all=await subjectCandidates(text,lang,lexicon,dictionary);
  const members=all.filter(c=>normalize(list).includes(normalize(c.surface)));
  if(members.length>=2)return members.sort((a,b)=>a.start-b.start).map(c=>withSpan(c,text));
 }
 // Keep the already resolved claim. Incidental names never produce extra beats.
 const match=Number.isFinite(subject.start)?subject:(await subjectCandidates(text,lang,lexicon,dictionary)).find(c=>c.title===subject.title);
 return [{title:subject.title,...(match?withSpan(match,text):{startChar:0,endChar:0,startWord:0,endWord:1}),mode:'focal_claim'}];
}
function quality(media){return media.kind==='video'||(Math.max(media.width||0,media.height||0)>=1000&&Math.min(media.width||0,media.height||0)>=600);}
function rankMedia(media,relational=false){
 const score=m=>{
  const text=`${m.title||''} ${m.description||''}`;
  const diagram=/diagram|taxonomy|taxonomic|legend|logo|euler|classification|schematic/iu.test(text);
  const direct=/photograph|photo|spacecraft|telescope|render|observation/iu.test(text);
  return (diagram?(relational?40:-40):0)+(direct?20:0)+Math.min(10,Math.max(m.width||0,m.height||0)/1000);
 };
 return [...media].sort((a,b)=>score(b)-score(a)||a.mediaKey.localeCompare(b.mediaKey,'en'));
}
function timeBeats(beats,{sceneStartMs,sceneEndMs,wordToCaption,captions}){
 if(!beats.length)fail('empty_visual_beats','No focal visual');
 const starts=beats.map((beat,i)=>{
  if(!i)return sceneStartMs;
  const span=beat.span;
  if(!span)fail('unaligned_beat',beat.title);
  let index;
  for(let w=span.startWord;w<span.endWord;w++)if(Number.isInteger(wordToCaption[w])){index=wordToCaption[w];break;}
  if(index===undefined||!Number.isFinite(captions[index]?.startMs))fail('unaligned_beat',beat.title);
  return captions[index].startMs;
 });
 return beats.map((beat,i)=>({...beat,startMs:starts[i],endMs:starts[i+1]??sceneEndMs}));
}
function validateBeats(beats,startMs,endMs,previousKey=null){
 let cursor=startMs,key=previousKey;
 for(const b of beats){
  if(!Number.isFinite(b.startMs)||!Number.isFinite(b.endMs)||Math.abs(b.startMs-cursor)>1||b.endMs<=b.startMs||b.endMs>endMs+1)fail('invalid_visual_timing',b.title);
  if(b.endMs-b.startMs>MAX_STATIC_MS+1&&b.kind!=='video')fail('visual_density',b.title);
  if(b.mediaKey===key)fail('duplicate_visual_identity',b.mediaKey);
  cursor=b.endMs;key=b.mediaKey;
 }
 if(!beats.length||Math.abs(cursor-endMs)>1)fail('invalid_visual_coverage','Scene coverage');
 return true;
}
module.exports={focalSpans,timeBeats,validateBeats,rankMedia,quality,MAX_STATIC_MS,MIN_BEAT_MS};

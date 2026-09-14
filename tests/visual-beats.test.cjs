const {test}=require('node:test');const assert=require('node:assert/strict');
const {focalSpans,timeBeats,validateBeats,rankMedia}=require('../engine-overlay/VisualBeats');
const {sourceLexicon,DictionaryLemmas}=require('../engine-overlay/VisualSubject');
const dictionary=new DictionaryLemmas();
for(const [lang,text,names] of [
 ['uk','Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида.',['Плутон','Седна','Гаумеа','Макемаке','Ерида']],
 ['ru','Крупнейшими из них являются Плутон, Седна, Хаумеа, Макемаке и Эрида.',['Плутон','Седна','Хаумеа','Макемаке','Эрида']],
 ['pl','Największymi z nich są Pluton, Sedna, Haumea, Makemake i Eris.',['Pluton','Sedna','Haumea','Makemake','Eris']],
 ['en','The largest of them are Pluto, Sedna, Haumea, Makemake and Eris.',['Pluto','Sedna','Haumea','Makemake','Eris']],
])test(`five focal named spans retained without truncation: ${lang}`,async()=>{
 const result=await focalSpans(text,lang,sourceLexicon(names.map(n=>`[[${n}]]`).join(' '),'Source'),dictionary,{mode:'previous_scene_anaphora'});
 assert.equal(result.length,5);assert.deepEqual(result.map(r=>text.slice(r.startChar,r.endChar)),names);
 assert.ok(result.every((r,i)=>!i||r.startWord>result[i-1].startWord));
});
test('relation endpoints and comparison objects do not become portrait beats',async()=>{
 const text='The asteroid belt, which lies between Mars and Jupiter, is smaller than the Oort cloud.';
 const result=await focalSpans(text,'en',sourceLexicon('[[Asteroid belt|asteroid belt]] [[Mars]] [[Jupiter]] [[Oort cloud]]','Source'),dictionary,{title:'Asteroid belt',start:4,end:17,mode:'current_subject'});
 assert.equal(result.length,1);assert.equal(result[0].title,'Asteroid belt');
});
const media=id=>({mediaKey:id,title:id,source:'exact_english_wikipedia',width:1080,height:1080,groundedEntity:id});
test('real repeated word offsets map through actual captions, not unique tokens or equal slicing',()=>{
 const result=timeBeats([{...media('a'),span:{startWord:0,endWord:1}},{...media('b'),span:{startWord:4,endWord:5}}],{sceneStartMs:1000,sceneEndMs:5000,wordToCaption:[0,1,2,3,4],captions:[{startMs:1000},{startMs:1300},{startMs:1600},{startMs:2000},{startMs:3800}]});
 assert.deepEqual(result.map(b=>[b.startMs,b.endMs]),[[1000,3800],[3800,5000]]);
});
test('missing span alignment fails instead of equal-duration timing',()=>{
 assert.throws(()=>timeBeats([{...media('a'),span:{startWord:0,endWord:1}},{...media('b'),span:{startWord:4,endWord:5}}],{sceneStartMs:0,sceneEndMs:4000,wordToCaption:[0],captions:[{startMs:0}]}),/unaligned_beat/);
});
test('invalid bounds, long holds, and adjacent identity duplicates fail',()=>{
 for(const beats of [[{...media('a'),startMs:0,endMs:6000}],[{...media('a'),startMs:0,endMs:2000},{...media('a'),startMs:2000,endMs:4000}],[{...media('a'),startMs:2000,endMs:1000}]])assert.throws(()=>validateBeats(beats,0,beats.at(-1).endMs),/visual/);
});
test('direct exact photography outranks taxonomy unless claim is relational',()=>{
 const diagram={...media('diagram'),description:'taxonomy diagram',kind:'image'};const photo={...media('photo'),description:'scientific photograph',kind:'image'};
 assert.equal(rankMedia([diagram,photo],false)[0].mediaKey,'photo');
 assert.equal(rankMedia([diagram,photo],true)[0].mediaKey,'diagram');
});
const {PexelsAPI}=require('../engine-overlay/Pexels');
test('seven-member strategy keeps all seven identities',()=>{
 const resolver=new PexelsAPI('');const beats=Array.from({length:7},(_,i)=>({...media('object'+i),span:{startWord:i,endWord:i+1}}));
 const result=resolver.planVisualBeats({beats,groupRequired:true},{sceneStartMs:0,sceneEndMs:4000},null);
 assert.equal(result.length,1);assert.equal(result[0].components.length,7);
});
test('short five-name lists become a complete group instead of truncation',()=>{
 const resolver=new PexelsAPI('');const beats=Array.from({length:5},(_,i)=>({...media('object'+i),span:{startWord:i,endWord:i+1}}));
 const result=resolver.planVisualBeats({beats},{sceneStartMs:0,sceneEndMs:1000,wordToCaption:[0,1,2,3,4],captions:[0,100,200,300,400].map(startMs=>({startMs}))});
 assert.equal(result[0].components.length,5);
});
test('low-resolution exact page image continues to full-resolution same-QID P18',async()=>{
 const resolver=new PexelsAPI('');resolver.pageImage=async()=>({...media('small'),kind:'image',width:314,height:316});
 resolver.dataEntity=async()=>({claims:{P18:[{mainsnak:{datavalue:{value:'Exact object photograph.jpg'}}}]}});
 resolver.query=async()=>({query:{pages:{1:{title:'File:Exact object photograph.jpg',imageinfo:[{mime:'image/jpeg',width:1600,height:1200,url:'https://upload.wikimedia.org/exact.jpg'}]}}}});
 resolver.commonsMedia=async()=>[];
 const pool=await resolver.exactBeatPool({qid:'Q123'},false);
 assert.equal(pool.length,1);assert.equal(pool[0].source,'exact_wikidata_p18');assert.equal(pool[0].width,1600);
});
test('density uses distinct exact alternatives within the same claim',()=>{
 const resolver=new PexelsAPI('');const result=resolver.planVisualBeats({beats:[{...media('a'),kind:'image',span:{startWord:0,endWord:1},alternatives:[{...media('b'),kind:'image'}]}]},{sceneStartMs:0,sceneEndMs:12000});
 assert.deepEqual(result.map(r=>r.mediaKey),['a','b','a']);assert.ok(result.every(r=>r.endMs-r.startMs<=5000));
});
test('non-astronomy five-name lists use the identical extraction path',async()=>{
 const text='The largest of them are Alice, Boris, Clara, David and Elena.';
 const spans=await focalSpans(text,'en',sourceLexicon('[[Alice]] [[Boris]] [[Clara]] [[David]] [[Elena]]','Reference'),dictionary,{mode:'previous_scene_anaphora'});
 assert.equal(spans.length,5);assert.equal(text.slice(spans[4].startChar,spans[4].endChar),'Elena');
});
test('list lead-in does not move the first named object before its spoken source span',()=>{
 const beats=[{...media('a'),span:{startWord:2,endWord:3}},{...media('b'),span:{startWord:3,endWord:4}}];
 const result=timeBeats(beats,{sceneStartMs:0,sceneEndMs:4000,wordToCaption:[0,1,2,3],captions:[0,400,1200,2600].map(startMs=>({startMs}))});
 assert.deepEqual(result.map(b=>[b.startMs,b.endMs]),[[1200,2600],[2600,4000]]);
});
test('source-quality threshold applies to exact video as well as still images',()=>{
 const {quality}=require('../engine-overlay/VisualBeats');
 assert.equal(quality({kind:'video',width:320,height:240}),false);
 assert.equal(quality({kind:'video',width:1920,height:1080}),true);
});

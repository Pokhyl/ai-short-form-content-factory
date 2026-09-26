const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const n=Object.fromEntries(w.nodes.map(n=>[n.name,n]));
const response=r=>({statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify(r)}]}}]}});
const source={storyboard:{narration:'Wrong lexical form.'},accepted_voiceover_candidate:{audio_base64:'exact-existing-audio',audio_sha256:'existing-hash'}};
const ctx={source,language_code:'uk',narration:source.storyboard.narration,review_quotes:[source.storyboard.narration]};
const run=(name,data)=>new Function('$','$json',n[name].parameters.jsCode)(()=>({first:()=>({json:ctx})}),data).json;
for(const suffix of ['',' Retry',' Final']) {
 test('language review'+suffix+' fails closed on provider/malformed/unanchored findings',()=>{
  const name='Validate Narration Language Review'+suffix;
  assert.throws(()=>run(name,{error:{description:'provider unavailable'}}),/provider failed/);
  for(const result of [{language:'en',issues:[]},{language:'uk',issues:[{quote:'invented',category:'grammar',explanation:'not input'}]},{language:'uk',issues:null}])assert.throws(()=>run(name,response(result)),/contract invalid|not anchored/);
 });
 test('language review'+suffix+' preserves exact narration/audio on PASS',()=>{
  const out=run('Validate Narration Language Review'+suffix,response({language:'uk',issues:[]}));
  assert.deepEqual(out.storyboard,source.storyboard);assert.deepEqual(out.accepted_voiceover_candidate,source.accepted_voiceover_candidate);assert.equal(out.language_review.passed,true);
 });
}
test('language repair bounded to one pass; final and retry rejects cannot reach audio commit',()=>{
 const issues=[{quote:source.storyboard.narration,category:'wrong_language',explanation:'wrong language'}];
 assert.equal(run('Validate Narration Language Review',response({language:'uk',issues})).language_review.passed,false);
 for(const suffix of [' Retry',' Final']) {
  const name='Validate Narration Language Review'+suffix;
  assert.throws(()=>run(name,response({language:'uk',issues})),/M5_LANGUAGE_QA_FAILED/);
  assert.equal(w.connections[name].main[1][0].node,'Prepare Script Failure');
 }
 assert.equal(w.connections['Route Narration Language PASS'].main[1][0].node,'Build Narration Language Repair');
 assert.equal(w.connections['Validate Narration Language Repair'].main[0][0].node,'Build Narration Language Review Retry');
 for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2'])assert.equal(w.connections[name].main[0][0].node,'Build Narration Language Review');
 assert.equal(w.connections['Canonicalize Final Storyboard'].main[0][0].node,'Build Narration Language Review Final');
});
test('new requests retain model, credentials and bounded provider retries',()=>{
 for(const name of ['Review Narration Language','Review Narration Language Retry','Review Narration Language Final','Repair Narration Language']){
  assert.equal(n[name].parameters.url,n['Generate Storyboard'].parameters.url);
  assert.deepEqual(n[name].credentials,n['Generate Storyboard'].credentials);
  assert.equal(n[name].maxTries,5);assert.equal(n[name].onError,'continueRegularOutput');
 }
});
test('live exact 10042 language replay rejects defective draft and accepts four language controls',()=>{
 const fixtures=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-review.json'));
 for(const f of fixtures){
  const context={...f,source:{storyboard:{narration:f.narration}}};
  const result=new Function('$','$json',n['Validate Narration Language Review'].parameters.jsCode)(()=>({first:()=>({json:context})}),{statusCode:f.http_status,body:f.response}).json;
  assert.equal(result.language_review.passed,f.expected_pass);
 }
});
test('targeted language repair preserves untouched scenes without forcing exact word slots',()=>{
 const c=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-repair-context.json'));
 const narrations=Object.fromEntries(c.base_storyboard.scenes.filter(s=>c.repair_scene_ids.includes(s.scene_id)).map(s=>[s.scene_id,s.narration]));
 const $=name=>({first:()=>({json:name==='Build Narration Language Repair'?c:c})});
 const validate=values=>new Function('$','$json',n['Validate Narration Language Repair'].parameters.jsCode)($,response({narrations:values})).json;
 const out=validate(narrations);
 assert.deepEqual(out.storyboard.scenes.map(s=>s.narration),c.base_storyboard.scenes.map(s=>s.narration));
 assert.deepEqual(Object.keys(out.language_repair_reference).sort(),c.repair_scene_ids.slice().sort());
 assert.throws(()=>validate({...narrations,S99:'extra scene'}),/REPAIR_CONTRACT/);
 const missing=structuredClone(narrations);delete missing.S8;assert.throws(()=>validate(missing),/REPAIR_CONTRACT/);
 const short={...narrations,S8:'Одне.'};assert.throws(()=>validate(short),/invalid repaired narration/);
 const long={...narrations,S8:Array.from({length:15},(_,i)=>'слово'+i).join(' ')+'.'};assert.throws(()=>validate(long),/invalid repaired narration/);
});

test('retry language review can reject semantic drift after repair',()=>{
 const repaired={...source,language_repair_reference:{S8:'Кожна комірка має транзистор та конденсатор.'},storyboard:{narration:'Кожна комірка має лише транзистор.',scenes:[{scene_id:'S8',narration:'Кожна комірка має лише транзистор.'}]}};
 const build=new Function('$','$json',n['Build Narration Language Review Retry'].parameters.jsCode)(()=>({first:()=>({json:{language_code:'uk'}})}),repaired).json;
 assert.equal(build.reference_pairs.length,1);
 assert.equal(build.reference_pairs[0].original,'Кожна комірка має транзистор та конденсатор.');
 const validate=new Function('$','$json',n['Validate Narration Language Review Retry'].parameters.jsCode);
 const $=()=>({first:()=>({json:build})});
 assert.throws(()=>validate($,response({language:'uk',issues:[{quote:'Кожна комірка має лише транзистор.',category:'meaning_change',explanation:'The capacitor concept was dropped.'}]})),/M5_LANGUAGE_QA_FAILED/);
});

test('live 10042 natural repair replay preserves meaning and passes second review',()=>{
 const c=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-repair-context.json'));
 const initial=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-review.json')).find(x=>x.expected_pass===false);
 const issues=JSON.parse(initial.response.candidates[0].content.parts[0].text).issues;
 const live=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-natural-language-repair.json'));
 const buildRepair=new Function('$','$json',n['Build Narration Language Repair'].parameters.jsCode)(
  ()=>({first:()=>({json:c})}),
  {storyboard:c.base_storyboard,language_review:{passed:false,language:'uk',narration:c.base_storyboard.narration,issues}}
 ).json;
 const provider={statusCode:live.repair_provider.http_status,body:{candidates:[{content:{parts:[{text:JSON.stringify(live.repair_provider.response)}]}}]}};
 const repaired=new Function('$','$json',n['Validate Narration Language Repair'].parameters.jsCode)(
  name=>({first:()=>({json:name==='Build Narration Language Repair'?buildRepair:c})}),
  provider
 ).json;
 assert.equal(repaired.storyboard.narration,live.repaired_narration);
 assert.match(repaired.storyboard.scenes.find(s=>s.scene_id==='S8').narration,/комірка.*транзистор.*конденсатор/u);
 const reviewBuild=new Function('$','$json',n['Build Narration Language Review Retry'].parameters.jsCode)(
  ()=>({first:()=>({json:c})}),repaired
 ).json;
 const reviewProvider={statusCode:live.second_review_provider.http_status,body:{candidates:[{content:{parts:[{text:JSON.stringify(live.second_review_provider.response)}]}}]}};
 const final=new Function('$','$json',n['Validate Narration Language Review Retry'].parameters.jsCode)(
  ()=>({first:()=>({json:reviewBuild})}),reviewProvider
 ).json;
 assert.equal(final.language_review.passed,true);
 assert.deepEqual(final.language_review.issues,[]);
});




test('retry spoken-language QA treats punctuation-only grammar and filler as advisory',()=>{
 const retryCtx={
  source,
  language_code:'uk',
  narration:'Барометр це прилад для вимірювання атмосферного тиску.',
  review_quotes:['Барометр це прилад для вимірювання атмосферного тиску.'],
 };
 const runRetry=(issues)=>new Function('$','$json',n['Validate Narration Language Review Retry'].parameters.jsCode)(
  ()=>({first:()=>({json:retryCtx})}),
  response({language:'uk',issues})
 ).json;
 const out=runRetry([
  {quote:retryCtx.review_quotes[0],category:'grammar',explanation:'Пропущено кома перед підйменником або зворотом, оскільки відсутня необхідна розділова вказівка.'},
  {quote:retryCtx.review_quotes[0],category:'grammar',explanation:"Дієприслівниковий зворот не виділено комою."},
  {quote:retryCtx.review_quotes[0],category:'filler',explanation:'Стилістичне зауваження без зміни вимови.'},
 ]);
 assert.equal(out.language_review.passed,true);
 assert.equal(out.language_review.blocking_issues.length,0);
 assert.equal(out.language_review.advisory_issues.length,3);
});

test('retry spoken-language QA still blocks audible grammar, wrong language and meaning change',()=>{
 const retryCtx={
  source,
  language_code:'uk',
  narration:'Поточний текст.',
  review_quotes:['Поточний текст.'],
 };
 const validate=(issue)=>new Function('$','$json',n['Validate Narration Language Review Retry'].parameters.jsCode)(
  ()=>({first:()=>({json:retryCtx})}),
  response({language:'uk',issues:[issue]})
 );
 for(const issue of [
  {quote:'Поточний текст.',category:'wrong_language',explanation:'Foreign lexical form.'},
  {quote:'Поточний текст.',category:'meaning_change',explanation:'Meaning was changed.'},
  {quote:'Поточний текст.',category:'grammar',explanation:'Incorrect verb agreement changes the spoken sentence.'},
 ]) assert.throws(()=>validate(issue),/M5_LANGUAGE_QA_FAILED/);
});

test('final spoken-language QA treats punctuation-only grammar and filler as advisory',()=>{
 const finalCtx={
  source,
  language_code:'uk',
  narration:'Райдуга це дивовижне атмосферне оптичне явище.',
  review_quotes:['Райдуга це дивовижне атмосферне оптичне явище.'],
 };
 const runFinal=(issues)=>new Function('$','$json',n['Validate Narration Language Review Final'].parameters.jsCode)(
  ()=>({first:()=>({json:finalCtx})}),
  response({language:'uk',issues})
 ).json;
 const out=runFinal([
  {quote:finalCtx.review_quotes[0],category:'grammar',explanation:'Відсутня кома або тире між частинами речення.'},
  {quote:finalCtx.review_quotes[0],category:'filler',explanation:'Можливе стилістичне нагромадження означень.'},
 ]);
 assert.equal(out.language_review.passed,true);
 assert.equal(out.language_review.blocking_issues.length,0);
 assert.equal(out.language_review.advisory_issues.length,2);
});

test('final spoken-language QA still blocks audible grammar, wrong language and meaning change',()=>{
 const finalCtx={
  source,
  language_code:'uk',
  narration:'Поточний текст.',
  review_quotes:['Поточний текст.'],
 };
 const validate=(issue)=>new Function('$','$json',n['Validate Narration Language Review Final'].parameters.jsCode)(
  ()=>({first:()=>({json:finalCtx})}),
  response({language:'uk',issues:[issue]})
 );
 for(const issue of [
  {quote:'Поточний текст.',category:'wrong_language',explanation:'Foreign lexical form.'},
  {quote:'Поточний текст.',category:'meaning_change',explanation:'Meaning was changed.'},
  {quote:'Поточний текст.',category:'grammar',explanation:'Incorrect verb agreement changes the spoken sentence.'},
 ]) assert.throws(()=>validate(issue),/M5_LANGUAGE_QA_FAILED/);
});

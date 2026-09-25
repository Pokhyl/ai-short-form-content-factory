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
test('targeted language repair preserves untouched scenes and rejects packed words or extra scenes',()=>{
 const c=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-repair-context.json'));
 const slots=Object.fromEntries(c.base_storyboard.scenes.filter(s=>c.repair_scene_ids.includes(s.scene_id)).map(s=>[s.scene_id,s.narration.split(/\s+/)]));
 const validate=words=>new Function('$','$json',n['Validate Narration Language Repair'].parameters.jsCode)(()=>({first:()=>({json:c})}),response({narration_words:words})).json;
 const out=validate(slots);
 assert.deepEqual(out.storyboard.scenes.map(s=>s.narration),c.base_storyboard.scenes.map(s=>s.narration));
 const packed=structuredClone(slots);packed.S8[4]='two words';assert.throws(()=>validate(packed),/one lexical word/);
 assert.throws(()=>validate({...slots,S99:['extra']}),/SLOT_CONTRACT/);
 const missing=structuredClone(slots);delete missing.S8;assert.throws(()=>validate(missing),/SLOT_CONTRACT/);
 const short=structuredClone(slots);short.S8.pop();assert.throws(()=>validate(short),/count mismatch/);
});

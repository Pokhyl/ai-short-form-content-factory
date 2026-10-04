const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-12075-clause-review.json'));
const names=w.nodes.filter(n=>n.name.startsWith('Build Narration Language Review')).map(n=>n.name);
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const run=(input,name=names[0])=>new Function('$','$json',code(name))(()=>({first:()=>({json:f.ctx})}),input).json;
const draft=texts=>({...f.initial_source,storyboard:{...f.initial_source.storyboard,narration:texts.join(' '),scenes:texts.map((narration,i)=>({...f.initial_source.storyboard.scenes[i],scene_id:'S'+(i+1),narration}))}});
test('saved missing-clause punctuation appears in a complete sentence spanning multiple visual cuts',()=>{
 for(const name of names){
  const out=run(f.retry_source,name);
  const sentence=out.sentence_contexts.find(c=>c.narration.startsWith('Sprężyna'));
  assert.equal(sentence.narration,'Sprężyna nieustannie podaje kolejne elementy w kierunku przodu gdy kartki papieru trafiają pomiędzy ramiona urządzenia.');
  assert.deepEqual(sentence.affected_quotes,f.retry_source.storyboard.scenes.slice(3,6).map(s=>s.narration));
  const second=out.sentence_contexts.find(c=>c.narration.startsWith('Nacisk'));
  assert.equal(second.narration,'Nacisk na obudowę sprawia że pionowa blaszka wypycha zszywkę.');
  assert.deepEqual(second.affected_quotes,f.retry_source.storyboard.scenes.slice(5,7).map(s=>s.narration));
 }
});
test('a visual scene crossing a sentence boundary is included in both sentence contexts',()=>{
 const input=draft(['The device holds paper. Pressing','the cover moves the driver.']);
 assert.deepEqual(run(input).sentence_contexts,[{narration:'The device holds paper.',affected_quotes:[input.storyboard.scenes[0].narration]},{narration:'Pressing the cover moves the driver.',affected_quotes:input.storyboard.scenes.map(s=>s.narration)}]);
});
test('unpunctuated run-on remains one complete review context without invented boundaries',()=>{
 const input=draft(['A force is applied','then the machine responds']);
 assert.deepEqual(run(input).sentence_contexts,[{narration:input.storyboard.narration,affected_quotes:input.storyboard.scenes.map(s=>s.narration)}]);
});
test('ellipsis, questions and Cyrillic text retain exact source spelling and punctuation',()=>{
 const input=draft(['Що відбувається? Натиск…','рухає деталь!']);
 const out=run(input);assert.deepEqual(out.sentence_contexts.map(c=>c.narration),['Що відбувається?','Натиск…','рухає деталь!']);
 assert.equal(out.narration,input.storyboard.narration);
});
test('source, quote enums, semantic references and visual records remain unchanged',()=>{
 for(const name of names){
  const input=JSON.parse(JSON.stringify(f.retry_source)),before=JSON.stringify(input),out=run(input,name);
  const old=new Function('$','$json',f.baseline_builders[name])(()=>({first:()=>({json:f.ctx})}),input).json;
  assert.equal(JSON.stringify(input),before);assert.deepEqual(out.response_json_schema,old.response_json_schema);
  assert.deepEqual(out.reference_pairs,old.reference_pairs);assert.deepEqual(out.visual_records,old.visual_records);
  assert.deepEqual(out.review_quotes,old.review_quotes);assert.equal(out.narration,old.narration);
 }
});
test('mismatched source scene fails instead of providing fabricated sentence evidence',()=>{
 const input=draft(['The machine is running.']);input.storyboard.scenes[0].narration='An absent sentence.';
 assert.throws(()=>run(input),/not in continuous narration/);
});
test('unchanged final gate still rejects the actual saved missed-comma findings',()=>{
 assert.throws(()=>new Function('$','$json',code('Validate Narration Language Review Final'))(()=>({first:()=>({json:f.final_ctx})}),f.final_response),/M5_LANGUAGE_QA_FAILED/);
});

test('saved exact provider review and repair close every observed defect through unchanged strict validators',()=>{
 const state={'Build Script Prompt':f.ctx};
 const execute=(name,input)=>{
  const result=new Function('$','$json',code(name))(n=>({first:()=>({json:state[n]})}),input).json;
  state[name]=result;return result;
 };
 execute('Build Narration Language Review',f.initial_source);
 const reviewed=execute('Validate Narration Language Review',f.provider_replay['initial-review-response']);
 assert.equal(reviewed.language_review.passed,false);
 const repair=execute('Build Narration Language Repair',reviewed);
 assert.deepEqual(repair.repair_scene_ids,['S5','S6','S7','S9']);
 const repaired=execute('Validate Narration Language Repair',f.provider_replay['repair-response']);
 assert.equal(repaired.storyboard.narration,f.provider_replay.accepted.storyboard.narration);
 assert.ok(repaired.storyboard.narration.includes('przodu, gdy'));
 assert.ok(repaired.storyboard.narration.includes('sprawia, że'));
 assert.ok(!repaired.storyboard.narration.includes('codziennie'));
 execute('Build Narration Language Review Retry',repaired);
 const checked=execute('Validate Narration Language Review Retry',f.provider_replay['retry-review-response']);
 assert.equal(checked.language_review.passed,true);assert.deepEqual(checked.language_review.issues,[]);
 execute('Build Narration Language Review Final',checked);
 const accepted=execute('Validate Narration Language Review Final',f.provider_replay['final-review-response']);
 assert.equal(accepted.language_review.passed,true);assert.deepEqual(accepted.language_review.issues,[]);
 assert.deepEqual(accepted.language_review.visual_repairs,[]);
});

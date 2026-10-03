const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m8-11994-invented-pressing-hand.json','utf8'));
for(const node of workflow.nodes.filter(n=>n.parameters?.jsCode?.includes('function canonicalizeTransientPhotoActionIntent'))){
 const src=node.parameters.jsCode;
 const start=src.indexOf('function canonicalizeTransientPhotoActionIntent');
 const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
 const normalize=new Function(src.slice(start,end)+';return canonicalizeTransientPhotoActionIntent;')();
 test(node.name+': exact 11994 impersonal mechanism preserves device without invented actor',()=>{
  assert.equal(normalize(fixture.shot.must_show,fixture.shot.visual_intent,{
   sceneNarration:fixture.scene_narration,narration:fixture.scene_narration
  }),'A clear photo of office stapler.');
 });
 for(const [scene,device] of [
  ['Pressing the button activates the latch.','door latch'],
  ['Naciśnięcie przycisku uruchamia mechanizm.','hole punch'],
  ['Нажатие кнопки запускает механизм.','push button'],
  ['Натискання кнопки запускає механізм.','stapler'],
 ]){
  test(node.name+': generic nominal pressure '+scene,()=>{
   assert.equal(normalize([device],'Hand pressing the '+device+'.',{sceneNarration:scene,narration:scene}),'A clear photo of '+device+'.');
  });
 }
 for(const narration of ['Your hand presses the cover.','She presses the cover.','Kobieta naciska pokrywę.','Вона натискає кнопку.','Użytkownik naciska pokrywę.','Ręka naciska pokrywę.','Рука нажимает крышку.','Людина натискає кришку.']){
  test(node.name+': preserves narrated actor '+narration,()=>{
   const intent=fixture.shot.visual_intent;
   assert.equal(normalize(['office stapler'],intent,{sceneNarration:fixture.scene_narration,narration}),intent);
  });
 }
 test(node.name+': preserves explicit human anchors, imperative and ungrounded context',()=>{
  const intent=fixture.shot.visual_intent;
  assert.equal(normalize(['hand','office stapler'],intent,{sceneNarration:fixture.scene_narration,narration:fixture.scene_narration}),intent);
  assert.equal(normalize(['office stapler'],intent,{sceneNarration:'Naciśnij pokrywę zszywacza.',narration:'Naciśnij pokrywę zszywacza.'}),intent);
  assert.equal(normalize(['office stapler'],intent),intent);
  const holding='Hands holding an office stapler.';
  assert.equal(normalize(['office stapler'],holding,{sceneNarration:fixture.scene_narration,narration:fixture.scene_narration}),holding);
 });
 test(node.name+': call supplies narration grounding',()=>assert.match(src,/canonicalizeTransientPhotoActionIntent\(mustShow, visualIntent, \{sceneNarration/));
}
test('generation prompt avoids invented actors while preserving narrated human action',()=>{
 const prompt=workflow.nodes.find(n=>n.name==='Build Script Prompt').parameters.jsCode;
 assert.match(prompt,/Do not invent a visible person or hand/);
 assert.match(prompt,/Preserve a human action when narration explicitly/);
});

test('baseline reproduces invented hand contract',()=>{
 const baseline=new Function('function canonicalizeTransientPhotoActionIntent'+fixture.baseline_helper+';return canonicalizeTransientPhotoActionIntent;')();
 assert.equal(baseline(fixture.shot.must_show,fixture.shot.visual_intent),fixture.shot.visual_intent);
});

test('exact final-node replay persists canonical contract and unchanged narration',()=>{
 const node=workflow.nodes.find(n=>n.name==='Canonicalize Final Storyboard');
 const ctx={language_code:'pl',target_duration_seconds:30,word_min:45,word_max:70};
 const source={storyboard:fixture.storyboard};
 const lookup=(name)=>({first:()=>({json:name==='Build Script Prompt'?ctx:source})});
 const execute=new Function('$json','$',node.parameters.jsCode);
 const output=execute(source,lookup).json.storyboard;
 const shot=output.scenes.flatMap(s=>s.shots).find(s=>s.shot_id==='S5-A');
 assert.equal(shot.visual_intent,'A clear photo of office stapler.');
 assert.deepEqual(shot.must_show,['office stapler']);
 assert.deepEqual(shot.must_not_show,['stapler interior']);
 assert.equal(shot.queries_en.length,3);
 assert.equal(output.narration,source.storyboard.narration);
 assert.equal(source.storyboard.scenes.flatMap(s=>s.shots).find(s=>s.shot_id==='S5-A').visual_intent,fixture.shot.visual_intent);
});

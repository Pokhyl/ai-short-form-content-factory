const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-12064-mislocalized-language.json'));
const names=['Build Narration Language Repair','Build Narration Language Repair Second Pass'];
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const run=(input,name=names[0],src=code(name))=>new Function('$','$json',src)(()=>({first:()=>({json:f.ctx})}),input).json;
const draft=(texts,quote,explanation)=>({...f.first,storyboard:{...f.first.storyboard,narration:texts.join(' '),scenes:texts.map((narration,i)=>({...f.first.storyboard.scenes[i],scene_id:'S'+(i+1),narration}))},language_review:{passed:false,issues:[{quote,category:'grammar',explanation}]}});
test('exact failed first/retry routes select S5/S2 before correction and S9 afterward',()=>{
 for(const [index,input] of [[0,f.first],[1,f.retry]]){
  const name=names[index];assert.deepEqual(run(input,name,f.baseline_builders[name]).repair_scene_ids,[index?'S2':'S5']);
  const out=run(input,name);assert.deepEqual(out.repair_scene_ids,['S9']);
  assert.deepEqual(out.response_json_schema.properties.narrations.required,['S9']);
  const scenes=JSON.parse(out.user_message).scenes_to_correct;assert.deepEqual(scenes.map(s=>s.scene_id),['S9']);
  assert.equal(scenes[0].incorrect_draft,input.storyboard.scenes[8].narration);
  assert.ok(scenes[0].errors_to_fix.every(issue=>issue.quote===input.storyboard.scenes[8].narration));
 }
});
test('source storyboard and original review verdict are never mutated',()=>{
 for(const name of names){const input=JSON.parse(JSON.stringify(f.first)),before=JSON.stringify(input);run(input,name);assert.equal(JSON.stringify(input),before);assert.equal(input.language_review.passed,false);}
});
test('two quoted adjacent source words localize an unrelated quote in any language',()=>{
 const input=draft(['The machine is running.','It makes strong stable joints.'],'The machine is running.',"Missing separator between 'strong' and 'stable'.");
 for(const name of names)assert.deepEqual(run(input,name).repair_scene_ids,['S2']);
});
test('longer literal source phrase outranks incidental spelling references',()=>{
 const input=draft(['Quick assembly is useful.','The plates form strong stable joints.'],'Quick assembly is useful.',"The spelling 'Quick' is actually correct; the defect is 'strong stable joints' later in the narration.");
 assert.deepEqual(run(input).repair_scene_ids,['S2']);
});
test('literal problem crossing a visual cut selects both source fragments',()=>{
 const input=draft(['The machine is running.','It makes strong','stable joints.'],'The machine is running.',"Missing a separator in 'strong stable'.");
 assert.deepEqual(run(input).repair_scene_ids,['S2','S3']);
});
test('ambiguous repeated references keep original quoted scope',()=>{
 const input=draft(['The machine is running.','It makes strong stable joints.','Another frame shows strong stable panels.'],'The machine is running.',"The phrase 'strong stable' needs a separator.");
 assert.deepEqual(run(input).repair_scene_ids,['S1']);
});
test('proposed replacement absent from source cannot relocate a finding',()=>{
 const input=draft(['It makes strong stable joints.','Another frame shows a panel.'],'It makes strong stable joints.',"Use 'swift sturdy' for a smoother phrase.");
 assert.deepEqual(run(input).repair_scene_ids,['S1']);
});
test('already grounded findings retain the exact original issue object',()=>{
 const quote=f.first.storyboard.scenes[8].narration;const input={...f.first,language_review:{passed:false,issues:[{...f.first.language_review.issues[0],quote}]}};
 const out=run(input);assert.deepEqual(out.repair_scene_ids,['S9']);assert.deepEqual(JSON.parse(out.user_message).scenes_to_correct[0].errors_to_fix,input.language_review.issues);
});
test('non-source quote remains invalid rather than becoming an invented repair target',()=>{
 const input=draft(['The machine is running.','It makes strong stable joints.'],'An invented scene.',"Missing separator in 'strong stable'.");
 assert.throws(()=>run(input),/quote is not an original scene/);
});
test('unchanged strict final language gate rejects the actual saved failed review',()=>{
 const source=code('Validate Narration Language Review Second Pass');
 assert.throws(()=>new Function('$','$json',source)(name=>({first:()=>({json:name==='Build Script Prompt'?f.ctx:f.final_review_ctx})}),f.final_review_response),/trwałe|stabilne/);
});

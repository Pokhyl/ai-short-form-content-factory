const fs=require('node:fs');
const assert=require('node:assert/strict');
const {test}=require('node:test');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const code=workflow.nodes.find(n=>n.name==='Validate Final Measured Word Count Retry').parameters.jsCode;
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m5-9221-final-retry.json'));
function run(f){return new Function('$','$json',code)(name=>{if(!f[name])throw Error("Node hasn't been executed");return {first:()=>({json:f[name]})};},f.response).json;}
test('9221 exact replay: measured shorter scenes complete the strict 21-word target',()=>{
 const out=run(structuredClone(fixture));
 assert.equal(out.narration_word_count,21);
 assert.equal(out.word_count_exact,true);
 assert.equal(out.deterministic_word_hybrid_used,true);
 assert.equal(out.storyboard.scenes.length,5);
 const originals=fixture['Normalize Timing Probe'].storyboard.scenes;
 out.storyboard.scenes.forEach((s,i)=>assert.equal(s.scene_id,originals[i].scene_id));
});
test('skipped earlier probes may use the bounded nearest semantic hybrid before Probe 5',()=>{
 const f=structuredClone(fixture);delete f['Normalize Timing Probe 2'];delete f['Normalize Timing Probe 3'];
 const out=run(f);
 assert.equal(out.narration_word_count,22);
 assert.equal(out.target_word_count,21);
 assert.equal(out.word_count_exact,false);
 assert.equal(out.deterministic_word_hybrid_used,true);
});
test('semantically invalid earlier drafts cannot rescue the exact target or enter the bounded nearest hybrid',()=>{
 const f=structuredClone(fixture);
 for(const name of ['Normalize Timing Probe 2','Normalize Timing Probe 3'])for(const scene of f[name].storyboard.scenes)scene.narration='Ogromne samochody jadą drogą.';
 const out=run(f);
 assert.equal(out.narration_word_count,22);
 assert.equal(out.word_count_exact,false);
 assert.ok(out.storyboard.scenes.every(scene=>scene.narration!=='Ogromne samochody jadą drogą.'));
});
test('earlier drafts from a different scene identity cannot enter the bounded nearest hybrid',()=>{
 const f=structuredClone(fixture);
 for(const name of ['Normalize Timing Probe 2','Normalize Timing Probe 3'])for(const scene of f[name].storyboard.scenes)scene.scene_id='unrelated';
 const out=run(f);
 assert.equal(out.narration_word_count,22);
 assert.equal(out.word_count_exact,false);
 const originals=fixture['Normalize Timing Probe'].storyboard.scenes;
 out.storyboard.scenes.forEach((scene,i)=>assert.equal(scene.scene_id,originals[i].scene_id));
});


test('9516 regression: semantic-invalid base option cannot re-enter final measured hybrid',()=>{
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-9516-final-measured.json'));
 const out=run(f);
 assert.equal(out.narration_word_count,24);
 assert.equal(out.target_word_count,24);
 assert.equal(out.word_count_exact,true);
 assert.equal(out.deterministic_word_hybrid_used,true);
 assert.equal(
   out.storyboard.scenes[2].narration,
   f['Normalize Timing Probe'].storyboard.scenes[2].narration
 );
 assert.notEqual(
   out.storyboard.scenes[2].narration,
   f['Build Final Measured Word Count Retry'].base_storyboard.scenes[2].narration
 );
});

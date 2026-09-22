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
test('skipped earlier probes retain fail-closed exact-total behavior',()=>{
 const f=structuredClone(fixture);delete f['Normalize Timing Probe 2'];delete f['Normalize Timing Probe 3'];
 assert.throws(()=>run(f),/got 22, target 21/);
});
test('semantically invalid earlier drafts cannot rescue exact word target',()=>{
 const f=structuredClone(fixture);
 for(const name of ['Normalize Timing Probe 2','Normalize Timing Probe 3'])for(const s of f[name].storyboard.scenes)s.narration='Ogromne samochody jadą drogą.';
 assert.throws(()=>run(f),/got 22, target 21/);
});
test('earlier drafts cannot supply narration from a different scene identity',()=>{
 const f=structuredClone(fixture);
 for(const name of ['Normalize Timing Probe 2','Normalize Timing Probe 3'])for(const s of f[name].storyboard.scenes)s.scene_id='unrelated';
 assert.throws(()=>run(f),/got 22, target 21/);
});

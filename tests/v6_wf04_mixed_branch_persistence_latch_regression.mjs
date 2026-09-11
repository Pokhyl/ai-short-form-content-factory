import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
const expand=by.get('Expand Reserved Story Assets').parameters.jsCode;
const persist=by.get('Persist Reserved Visual').parameters;
const collect=by.get('Collect Persisted Reserved Visuals').parameters.jsCode;
const verify=by.get('Verify Reserved Visual Completion').parameters.query;
assert.match(expand,/expected_shot_count=shotNumber/);
assert.match(persist.query,/persisted_count AS/);
assert.match(persist.query,/\$27::int AS expected_shot_count/);
assert.match(persist.query,/AS all_persisted/);
assert.match(persist.options.queryReplacement,/\$json\.expected_shot_count/);
assert.doesNotMatch(collect,/Reserved visual persistence cardinality/);
assert.match(collect,/if\(!ready\.length\)return \[\]/);
assert.match(verify,/q\.planned_shot_count=q\.shot_count/);
assert.match(verify,/q\.shot_count>=q\.expected_count/);
const expanded=[1,2,3,4].map((shot_number,i)=>({json:{shot_number,story_unit_count:4}}));
const $=name=>{assert.equal(name,'Expand Reserved Story Assets');return{all:()=>expanded}};
const run=rows=>new Function('$input','$',collect)({all:()=>rows.map(json=>({json}))},$);
assert.deepEqual(run([{job_id:'j',shot_number:3,persisted:true,expected_shot_count:4,all_persisted:false}]),[]);
assert.deepEqual(run([
 {job_id:'j',shot_number:1,persisted:true,expected_shot_count:4,all_persisted:false},
 {job_id:'j',shot_number:2,persisted:true,expected_shot_count:4,all_persisted:false},
 {job_id:'j',shot_number:4,persisted:true,expected_shot_count:4,all_persisted:true}
]),[{json:{job_id:'j',story_unit_count:4,expected_shot_count:4}}]);
assert.throws(()=>run([{job_id:'j',shot_number:4,persisted:true,expected_shot_count:3,all_persisted:true}]),/expected-shot drift/);
assert.throws(()=>run([{job_id:'j',shot_number:4,persisted:false,expected_shot_count:4,all_persisted:true}]),/was not persisted/);
console.log('V6_WF04_MIXED_BRANCH_PERSISTENCE_LATCH_REGRESSION_PASS');

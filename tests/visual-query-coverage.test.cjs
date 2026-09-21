const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const begin={visual_run_id:'run',shots_json:[
 {shot_uuid:'one',shot_key:'S1-A',scene_order:1,must_show:['penstock pipe'],queries_en:['water flowing through penstock pipe','hydroelectric penstock pipe','penstock pipe'],preferred_media_type:'photo'},
 {shot_uuid:'two',shot_key:'S2-A',scene_order:2,must_show:['turbine'],queries_en:['water turbine','hydroelectric turbine'],preferred_media_type:'photo'}]};
for (const provider of ['Pixabay','Pexels','Wikimedia']) test(provider+' covers every query including shorter fallback with stable provenance',()=>{
 const code=workflow.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
 const out=new Function('$',code)(()=>({first:()=>({json:begin})})).map(x=>x.json);
 assert.equal(out.length,5);
 for(const shot of begin.shots_json) {
  const rows=out.filter(x=>x.shot_uuid===shot.shot_uuid);
  assert.deepEqual(rows.map(x=>x.query),shot.queries_en);
  assert.deepEqual(rows.map(x=>x.query_index),shot.queries_en.map((_,i)=>i+1));
  assert.ok(rows.every(x=>x.provider===provider.toLowerCase()&&x.visual_run_id==='run'));
 }
});
test('expanded Commons coverage retains sequential pacing and timeout',()=>{
 const n=workflow.nodes.find(n=>n.name==='Wikimedia Search');
 assert.deepEqual(n.parameters.options.batching.batch,{batchSize:1,batchInterval:8000});
 assert.equal(n.parameters.options.timeout,60000);
});

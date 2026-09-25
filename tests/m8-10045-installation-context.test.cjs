const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const exact=JSON.parse(fs.readFileSync('acceptance/2026-09-25-m8-10045-s5.json'));
const c=exact.contract;
const shot={
 shot_uuid:'diag-s5',
 shot_key:c.shot_key,
 scene_order:5,
 shot_order:1,
 narration:'Накопичувач дає повільний доступ.',
 visual_intent:c.visual_intent,
 must_show:c.must_show,
 must_not_show:c.must_not_show,
 queries_en:['solid state drive storage','SSD storage drive','internal SSD drive'],
 preferred_media_type:'photo',
 duration_ms:3000,
};
for(const provider of ['Pexels','Pixabay','Wikimedia']){
 test(provider+' preserves corrected installation-context query for failed 10045 S5',()=>{
  const code=w.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
  const out=new Function('$',code)(()=>({first:()=>({json:{visual_run_id:'diag',shots_json:[shot]}})})).map(i=>i.json);
  assert.equal(out.length,3);
  assert.deepEqual(out.map(x=>x.query),shot.queries_en);
  assert.equal(out[2].provider_query,'internal SSD drive');
  assert.match(out[2].provider_query,/internal/i);
 });
}

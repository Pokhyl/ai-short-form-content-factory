const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json','utf8'));

const shot={
 shot_uuid:'11111111-1111-4111-8111-111111111111',
 shot_key:'S6-A',
 scene_order:6,
 preferred_media_type:'photo',
 visual_intent:'A mercury column inside a graduated glass tube showing the measured height.',
 must_show:['mercury column'],
 must_not_show:['empty tube'],
 queries_en:[
  'mercury column inside graduated glass tube',
  'barometric mercury column height measurement',
  'mercury column',
 ],
};

for(const provider of ['Pixabay','Pexels','Wikimedia']){
 test(provider+' keeps the final contained-object fallback broad',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
  const out=new Function('$',code)(()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})).map(x=>x.json);
  const final=out.find(x=>x.query_index===3);
  assert.equal(final.query,'mercury column');
  assert.equal(final.provider_query,'mercury column');
  assert.ok(!final.domain_context_terms.includes('graduated'));
 });
}

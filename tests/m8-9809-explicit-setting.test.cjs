const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const shots=[
 {shot_key:'S2-A',scene_order:2,preferred_media_type:'photo',must_show:['lamp bulb'],must_not_show:[],visual_intent:'A bright lamp glowing inside a lighthouse lantern room',queries_en:['lighthouse lamp illumination','bright warning light equipment lamp bulb','lamp bulb']},
 {shot_key:'S3-A',scene_order:3,preferred_media_type:'photo',must_show:['lamp fixture'],must_not_show:[],visual_intent:'Interior machinery room of a lighthouse with lamps and optics',queries_en:['lighthouse interior lamp system','lighthouse equipment room lamp fixture','lamp fixture']},
];
for(const provider of ['Pixabay','Pexels','Wikimedia']){
 const code=w.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
 const run=rows=>new Function('$',code)(()=>({first:()=>({json:{visual_run_id:'test',shots_json:rows}})})).map(x=>x.json);
 test(provider+' 9809 carries explicit lighthouse setting for non-machinery subjects',()=>{
  const rows=run(shots);
  assert.equal(rows.length,6);
  assert.ok(rows.every(r=>r.domain_context_terms.includes('lighthouse')));
  assert.ok(rows.every(r=>/lighthouse/i.test(r.provider_query)));
  assert.equal(rows.find(r=>r.shot_key==='S2-A'&&r.query_index===3).query,'lamp bulb');
 });
 test(provider+' derives setting from input without lighthouse-specific mapping',()=>{
  const rows=run([{...shots[0],must_show:['microscope'],visual_intent:'A microscope inside a hospital laboratory',queries_en:['hospital microscope','medical microscope','microscope']}]);
  assert.ok(rows.every(r=>r.domain_context_terms.includes('hospital')));
  const unsupported=run([{...shots[0],visual_intent:'A bright lamp inside a decorative room',queries_en:['lamp bulb','glowing lamp bulb','lamp bulb']}]);
  assert.ok(unsupported.every(r=>!r.domain_context_terms.includes('decorative')));
 });
}
test('9809 replay marks exact wrong-context Pexels lamps rejected for metadata ranking',()=>{
 const records=JSON.parse(fs.readFileSync('tests/fixtures/m8-9809-pexels-context.json'));
 const build=w.nodes.find(n=>n.name==='Build Pexels Requests').parameters.jsCode;
 const normalize=w.nodes.find(n=>n.name==='Normalize Pexels').parameters.jsCode;
 const requests=new Function('$',build)(()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})).map(x=>x.json);
 const wrong=new Set(['3324439','18109261','15664927']);
 const seen=new Set();
 for(const record of records){
  const updated=requests.find(r=>r.shot_key===record.request.shot_key&&r.query_index===record.request.query_index);
  const ctx={...record.request,domain_context_terms:updated.domain_context_terms};
  const $=name=>{assert.equal(name,'Build Pexels Requests');return {item:{json:ctx}}};
  const out=new Function('$','$json',normalize)($,record.response).json;
  for(const c of out.candidates){
   if(wrong.has(c.provider_asset_id)){
    seen.add(c.provider_asset_id);
    assert.equal(c.rejected,true,c.provider_asset_id+' remained eligible');
   }
  }
 }
 assert.deepEqual([...seen].sort(),[...wrong].sort());
});

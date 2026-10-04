const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12040-fastened-result.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(provider='Pexels',shot=f.grounded_shot,src=code('Build '+provider+' Requests'))=>new Function('$',src)(()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})).map(x=>x.json);
const normalize=(ctx,body=f.pexels_result_response,src=code('Normalize Pexels'))=>new Function('$','$json',src)(()=>({item:{json:ctx}}),{statusCode:200,body}).json.candidates;
test('all providers compact only final explicit fastened-result query and preserve all requirements',()=>{
 for(const provider of ['Pexels','Pixabay','Wikimedia']){
  const after=requests(provider),before=requests(provider,f.grounded_shot,f.baseline_builders['Build '+provider+' Requests']);
  assert.equal(after.length,3);assert.deepEqual(after.slice(0,2),before.slice(0,2));
  assert.equal(after[2].provider_query,'stapled documents');
  assert.equal(after[2].fastened_result_context.connector,'staple');
  for(const key of ['query','visual_intent','must_show','must_not_show'])assert.deepEqual(after[2][key],before[2][key]);
 }
});
test('actual photographed fastening reaches semantic review with bounded caption-pair evidence while retaining rejection',()=>{
 const ctx=requests()[2];const before=normalize(ctx,f.pexels_result_response,f.baseline_normalizer).find(c=>c.provider_asset_id==='6991328');const after=normalize(ctx).find(c=>c.provider_asset_id==='6991328');
 assert.ok(after.relevance_score>=before.relevance_score);assert.ok(after.relevance_score<=100);assert.ok(after.relevance_score>=55,JSON.stringify(after));
 assert.equal(after.metadata.paired_subject_review,true);assert.equal(after.rejected,true);
 assert.equal(after.rejection_reason,before.rejection_reason);assert.match(after.rejection_reason,/missing_primary_subject_anchor:office documents/);
});
test('generic bolted metal plates retain mandatory material, connector and exclusion',()=>{
 const shot={...f.grounded_shot,must_show:['metal plates','bolt'],visual_intent:'A stack of bolted metal plates',queries_en:['bolted metal plates joint','metal plates bolt head','plates bolt']};
 const ctx=requests('Pexels',shot)[2];assert.equal(ctx.provider_query,'bolted plates');assert.deepEqual(ctx.must_show,shot.must_show);assert.deepEqual(ctx.must_not_show,shot.must_not_show);
});
test('ordinary paper and binder-clip alternatives are not promoted as a stapled result',()=>{
 const cs=normalize(requests()[2]);
 for(const id of ['7054391','6077886','6077587'])assert.ok(!cs.find(c=>c.provider_asset_id===id).metadata.paired_subject_review,id);
});
test('filename alone and vector descriptions cannot nominate',()=>{
 for(const alt of ['Sheets of paper on a desk','Vector illustration of a stapler fastening paper']){
  const body=JSON.parse(JSON.stringify(f.pexels_result_response));const p=body.photos.find(p=>p.id===6991328);p.alt=alt;
  assert.ok(!normalize(requests()[2],body).find(c=>c.provider_asset_id==='6991328').metadata.paired_subject_review);
 }
});
test('non-fastened scenes, missing connector anchors and detailed final queries retain baseline',()=>{
 for(const shot of [
  f.shot,
  {...f.grounded_shot,visual_intent:'A stack of office documents beside staples'},
  {...f.grounded_shot,must_show:['office documents','paper clips']},
  {...f.grounded_shot,queries_en:[...f.grounded_shot.queries_en.slice(0,2),'document staple corner closeup']},
 ])assert.deepEqual(requests('Pexels',shot),requests('Pexels',shot,f.baseline_builders['Build Pexels Requests']));
});

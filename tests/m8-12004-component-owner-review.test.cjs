const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m8-12004-component-owner-pool.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(shot=fixture.shot,src=code('Build Wikimedia Requests'))=>new Function('$',src)(
 ()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})
).map(x=>x.json);
const normalize=(ctx,body=fixture.commons_owner_response,src=code('Normalize Wikimedia'))=>new Function('$','$json',src)(
 ()=>({item:{json:ctx}}),{statusCode:200,body}
).json.candidates;
test('exact baseline misses the owner query and excludes actual exposed-spring photo',()=>{
 const ctx=requests(fixture.shot,fixture.baseline_builder).find(x=>x.query_index===3);
 assert.equal(ctx.provider_query,'Stapler magazine');
 const c=normalize(ctx,fixture.commons_owner_response,fixture.baseline_normalizer).find(c=>c.provider_asset_id==='7824198');
 assert.equal(c.relevance_score,49);
 assert.equal(c.rejected,true);
 assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
 assert.ok(!fixture.candidate_pool.some(c=>c.provider_asset_id==='7824198'));
});
test('compound internal fallback retrieves the owner with all shot requirements unchanged',()=>{
 const req=requests();
 assert.equal(req.length,3);
 assert.deepEqual(req.slice(0,2).map(x=>x.provider_query),['stapler magazine spring','stapler spring feed']);
 const ctx=req[2];
 assert.equal(ctx.query,'spring mechanism');
 assert.equal(ctx.provider_query,'stapler');
 assert.equal(ctx.component_owner_query,'stapler');
 assert.equal(ctx.visual_intent,fixture.shot.visual_intent);
 assert.deepEqual(ctx.must_show,['Stapler magazine','spring mechanism']);
 assert.deepEqual(ctx.must_not_show,['closed housing']);
});
test('pixel-confirmed Delfin open magazine reaches semantic review, never metadata approval',()=>{
 const ctx=requests()[2];
 const c=normalize(ctx).find(c=>c.provider_asset_id==='7824198');
 assert.ok(c.relevance_score>=55,JSON.stringify(c));
 assert.equal(c.rejected,true);
 assert.match(c.rejection_reason,/missing_primary_subject_anchor/);
 assert.doesNotMatch(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
 assert.equal(c.metadata.component_owner_review,true);
});
test('ordinary closed stapler metadata is unchanged and receives no exposed-owner promotion',()=>{
 const ctx=requests()[2];
 const c=normalize(ctx).find(c=>c.provider_asset_id==='7537726');
 const baselineCtx=requests(fixture.shot,fixture.baseline_builder)[2];
 const before=normalize(baselineCtx,fixture.commons_owner_response,fixture.baseline_normalizer).find(c=>c.provider_asset_id==='7537726');
 assert.equal(c.relevance_score,before.relevance_score);
 assert.equal(c.rejected,true);
 assert.equal(c.metadata.component_owner_review,false);
 assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});
test('generic internal camera housing owner works without topic mappings',()=>{
 const shot={...fixture.shot,visual_intent:'Open camera housing exposing the shutter mechanism.',must_show:['camera housing','shutter mechanism'],queries_en:['camera housing shutter','camera shutter interior','shutter mechanism']};
 const ctx=requests(shot)[2];
 assert.equal(ctx.provider_query,'camera');
 assert.equal(ctx.component_owner_query,'camera');
 assert.deepEqual(ctx.must_show,shot.must_show);
});
test('material labels and exterior component scenes retain baseline provider query',()=>{
 for(const shot of [
  {...fixture.shot,must_show:['metal housing','spring mechanism']},
  {...fixture.shot,visual_intent:'Camera housing photographed beside a shutter mechanism.',must_show:['camera housing','shutter mechanism'],queries_en:['camera housing shutter','camera shutter casing','shutter mechanism']},
  {...fixture.shot,visual_intent:'A camera beside a tripod.',must_show:['camera','tripod'],queries_en:['camera tripod equipment','camera on tripod','tripod']},
 ]){
  const after=requests(shot)[2],before=requests(shot,fixture.baseline_builder)[2];
  assert.equal(after.provider_query,before.provider_query);
  assert.equal(after.component_owner_query,'');
  assert.deepEqual(after.must_show,shot.must_show);
 }
});
test('unrelated open-owner captions cannot prove requested owner',()=>{
 const ctx=requests()[2];
 const body=JSON.parse(JSON.stringify(fixture.commons_owner_response));
 const page=body.query.pages['7824198'];
 page.title='File:Open camera housing.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Open camera housing'};
 page.imageinfo[0].extmetadata.ImageDescription={value:'An opened camera'};
 page.imageinfo[0].extmetadata.Categories={value:'Cameras'};
 const c=normalize(ctx,body).find(c=>c.provider_asset_id==='7824198');
 assert.equal(c.metadata.component_owner_review,false);
 assert.match(c.rejection_reason,/wikimedia_primary_only_contextual_metadata/);
});
test('budget remains three previews and search count stays unchanged',()=>{
 assert.match(code('Build Gemini Vision Request'),/candidates\.length\s*>\s*3/);
 const limit=w.nodes.find(n=>n.name==='Wikimedia Search').parameters.queryParameters.parameters.find(x=>x.name==='gsrlimit');
 assert.equal(limit.value,'20');
 assert.equal(requests().length,3);
});

test('exact normalized pool snapshot matches executable normalizer',()=>{
 assert.deepEqual(normalize(requests()[2]),fixture.normalized_owner_candidates);
});

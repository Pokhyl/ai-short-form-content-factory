const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12040-surface-owner.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(shot=f.shot,src=code('Build Wikimedia Requests'))=>new Function('$',src)(()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})).map(x=>x.json);
const normalize=(ctx,body=f.commons_surface_response,src=code('Normalize Wikimedia'))=>new Function('$','$json',src)(()=>({item:{json:ctx}}),{statusCode:200,body}).json.candidates;
test('exact S8 retrieves the surface and subfeature owner without changing the contract',()=>{
 const after=requests(),before=requests(f.shot,f.baseline_builder);
 assert.deepEqual(after.slice(0,2),before.slice(0,2));
 assert.equal(after.length,3);assert.equal(after[2].provider_query,'staple paper');
 assert.deepEqual(after[2].paired_compact_anchors,['paper','staple']);
 assert.equal(after[2].surface_owner_pair,true);
 for(const key of ['query','visual_intent','must_show','must_not_show'])assert.deepEqual(after[2][key],before[2][key]);
});
test('actual photographed staple ends reach semantic review without metadata approval',()=>{
 const ctx=requests()[2],before=normalize(ctx,f.commons_surface_response,f.baseline_normalizer).find(c=>c.provider_asset_id==='12612756'),after=normalize(ctx).find(c=>c.provider_asset_id==='12612756');
 assert.ok(!before.metadata.paired_subject_review);
 assert.equal(after.metadata.paired_subject_review,true);assert.equal(after.rejected,true);
 assert.ok(after.relevance_score>=55,JSON.stringify(after));
 assert.match(after.rejection_reason,/missing_primary_subject_anchor:paper sheets/);
});
test('subfeature extraction generalizes to a cloth with curved wire tips',()=>{
 const shot={...f.shot,must_show:['cloth'],visual_intent:'Cloth showing curved wire tips on its back',queries_en:['curved wire tips cloth','wire fastener cloth back','cloth']};
 const ctx=requests(shot)[2];assert.equal(ctx.provider_query,'wire cloth');assert.deepEqual(ctx.must_show,['cloth']);
});
test('one category must name both objects; unrelated category mosaic cannot nominate',()=>{
 const body=JSON.parse(JSON.stringify(f.commons_surface_response));body.query.pages['12612756'].imageinfo[0].extmetadata.Categories.value='Paper|Staples';
 const c=normalize(requests()[2],body).find(c=>c.provider_asset_id==='12612756');assert.ok(!c.metadata.paired_subject_review);
});
test('diagram rejection is never cleared by category nomination',()=>{
 const body=JSON.parse(JSON.stringify(f.commons_surface_response));const p=body.query.pages['12612756'];p.title='File:Paper staples diagram.jpg';
 const c=normalize(requests()[2],body).find(c=>c.provider_asset_id==='12612756');assert.ok(!c.metadata.paired_subject_review);assert.match(c.rejection_reason,/wikimedia_non_photographic_asset/);
});
test('ordinary exterior surface, unsupported owner and explicit co-subjects retain baseline',()=>{
 for(const shot of [
  {...f.shot,visual_intent:'Paper sheets on a table'},
  {...f.shot,visual_intent:'Paper sheets showing bent nail ends on back'},
  {...f.shot,must_show:['paper sheets','desk']},
  {...f.shot,queries_en:['bent staple ends paper','paper staple back','paper sheets stack']},
 ])assert.deepEqual(requests(shot),requests(shot,f.baseline_builder));
});
test('paper-staple boxes and loose objects without a state caption receive no subfeature priority',()=>{
 const ctx=requests(f.grounded_shot)[2];
 const cs=normalize(ctx);
 assert.equal(cs.find(c=>c.provider_asset_id==='12612756').metadata.paired_subject_review,true);
 for(const id of ['91457820','77734699'])assert.ok(!cs.find(c=>c.provider_asset_id===id).metadata.paired_subject_review,id);
});

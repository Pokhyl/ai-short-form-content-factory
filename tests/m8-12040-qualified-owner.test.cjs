const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12040-qualified-owner.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(shot=f.shot,src=code('Build Wikimedia Requests'))=>new Function('$',src)(()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})).map(x=>x.json);
const normalize=ctx=>new Function('$','$json',code('Normalize Wikimedia'))(()=>({item:{json:ctx}}),{statusCode:200,body:f.commons_owner_response}).json.candidates;
test('exact failed S3 broadens only final qualified internal owner retrieval',()=>{
 const before=requests(f.shot,f.baseline_builder),after=requests();
 assert.equal(before[2].provider_query,'desktop stapler');
 assert.deepEqual(after.slice(0,2),before.slice(0,2));
 assert.equal(after.length,3);
 assert.equal(after[2].provider_query,'stapler');
 assert.equal(after[2].component_owner_query,'stapler');
 for(const key of ['query','visual_intent','must_show','must_not_show'])assert.deepEqual(after[2][key],before[2][key]);
});
test('real pixel-confirmed open owner reaches rejected semantic review',()=>{
 const before=normalize(requests(f.shot,f.baseline_builder)[2]).find(c=>c.provider_asset_id==='7824198');
 const after=normalize(requests()[2]).find(c=>c.provider_asset_id==='7824198');
 assert.equal(before.metadata.component_owner_review,false);
 assert.equal(after.metadata.component_owner_review,true);
 assert.ok(after.relevance_score>=55,JSON.stringify(after));
 assert.equal(after.rejected,true);
 assert.match(after.rejection_reason,/missing_primary_subject_anchor:desktop stapler/);
});
test('closed owner never receives open-view promotion',()=>{
 const c=normalize(requests()[2]).find(c=>c.provider_asset_id==='7537726');
 assert.equal(c.metadata.component_owner_review,false);
 assert.equal(c.rejected,true);
});
test('qualified unrelated owner generalizes to portable camera without replacing the contract',()=>{
 const shot={...f.shot,must_show:['portable camera'],visual_intent:'An open portable camera exposing internal parts',queries_en:['open portable camera shutter','camera inner housing','portable camera']};
 const c=requests(shot)[2];
 assert.equal(c.provider_query,'camera');
 assert.equal(c.component_owner_query,'camera');
 assert.deepEqual(c.must_show,shot.must_show);
 assert.equal(c.visual_intent,shot.visual_intent);
});
test('exterior, independent co-subject, technical subtype and detailed final queries are unchanged',()=>{
 for(const shot of [
  {...f.shot,visual_intent:'A desktop stapler on a table'},
  {...f.shot,must_show:['desktop stapler','paper sheets']},
  {...f.shot,must_show:['surgical stapler'],queries_en:['open surgical stapler mechanism','surgical stapler internal parts','surgical stapler']},
  {...f.shot,queries_en:['open desktop stapler mechanism','stapler arm','desktop stapler spring']},
 ])assert.deepEqual(requests(shot),requests(shot,f.baseline_builder));
});
test('preview and request budgets stay fixed',()=>{
 assert.match(code('Build Gemini Vision Request'),/candidates\.length\s*>\s*3/);
 assert.equal(requests().length,3);
});

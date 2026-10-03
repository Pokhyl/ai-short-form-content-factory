const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12015-paired-objects.json'));
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const request=(shot=f.shot,src=code('Build Wikimedia Requests'))=>new Function('$',src)(()=>({first:()=>({json:{visual_run_id:'run',shots_json:[shot]}})})).map(x=>x.json);
const normalize=(ctx,body=f.commons_response)=>new Function('$','$json',code('Normalize Wikimedia'))(()=>({item:{json:ctx}}),{statusCode:200,body}).json.candidates;
test('12015 compact fallback retains both objects, original contract and three-search budget',()=>{
 const before=request(f.shot,f.baseline_builder),after=request();
 assert.equal(before[2].provider_query,'metal staples paper sheets');
 assert.equal(after[2].provider_query,'staple paper');
 assert.equal(after.length,3);
 assert.deepEqual(after.slice(0,2).map(x=>x.provider_query),before.slice(0,2).map(x=>x.provider_query));
 for(const key of ['visual_intent','must_show','must_not_show','query']) assert.deepEqual(after[2][key],before[2][key]);
});
test('actual photograph of staples and documents reaches vision without metadata approval',()=>{
 const c=normalize(request()[2]).find(c=>c.provider_asset_id==='77734699');
 assert.ok(c.relevance_score>=55,JSON.stringify(c));
 assert.equal(c.rejected,true);
 assert.equal(c.metadata.paired_subject_review,true);
 assert.doesNotMatch(c.rejection_reason,/wikimedia_primary_only_contextual_metadata|wikimedia_non_photographic_asset/);
 assert.match(c.rejection_reason,/missing_primary_subject_anchor/);
});
test('single-subject staple boxes receive no paired-object priority',()=>{
 const cs=normalize(request()[2]);
 for(const id of ['91457820','1744612','7824197']) {
  const c=cs.find(c=>c.provider_asset_id===id);
  assert.ok(c);
  assert.notEqual(c.metadata.paired_subject_review,true);
  assert.equal(c.rejected,true);
 }
});
test('an actual diagram retains non-photographic rejection',()=>{
 const c=normalize(request()[2]).find(c=>c.provider_asset_id==='86705692');
 assert.match(c.rejection_reason,/wikimedia_non_photographic_asset/);
 assert.notEqual(c.metadata.paired_subject_review,true);
});
test('independent qualified objects generalize beyond observed topic',()=>{
 const shot={...f.shot,must_show:['copper coins','paper sheets'],queries_en:['copper coins paper sheets','coins on paper sheets','paper sheets'],visual_intent:'Copper coins beside paper sheets'};
 const ctx=request(shot)[2];
 assert.equal(ctx.provider_query,'coin paper');
 assert.deepEqual(ctx.must_show,shot.must_show);
});
test('unmodified anchors and operating-domain fallbacks retain baseline queries',()=>{
 for(const shot of [
  {...f.shot,must_show:['camera','tripod'],queries_en:['camera tripod','camera beside tripod','tripod']},
  {...f.shot,must_show:['hydroelectric generator','metal shaft'],queries_en:['hydroelectric generator shaft','generator shaft','metal shaft']},
 ]) assert.equal(request(shot)[2].provider_query,request(shot,f.baseline_builder)[2].provider_query);
});

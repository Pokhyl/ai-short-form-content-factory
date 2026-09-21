const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const shot={shot_uuid:'s3',shot_key:'S3-A',scene_order:3,preferred_media_type:'photo',visual_intent:'Large electric generator inside a hydroelectric power station',must_show:['electric generator','power station'],must_not_show:[],queries_en:['electric generator in hydroelectric station','power generator equipment inside plant','electric generator']};
for(const provider of ['Pixabay','Pexels','Wikimedia']) {
 test(provider+': exact S3 bare fallback adds equipment without rewriting provenance',()=>{
  const rows=new Function('$',code('Build '+provider+' Requests'))(()=>({first:()=>({json:{visual_run_id:'test',shots_json:[shot]}})})).map(r=>r.json);
  assert.deepEqual(rows.map(r=>r.query),shot.queries_en);
  assert.equal(rows[2].provider_query,'hydroelectric electric generator equipment');
  assert.equal(rows[0].provider_query,shot.queries_en[0]);
  assert.equal(rows[1].provider_query,'hydroelectric '+shot.queries_en[1]);
 });
 const src=code('Normalize '+provider);
 const helpers=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {semanticSet,scoreCandidate};')();
 test(provider+': powerhouse semantic expansion is directional',()=>{
  const specific=helpers.semanticSet('powerhouse');
  assert.ok(['power','station','powerstation'].every(t=>specific.has(t)));
  assert.equal(helpers.semanticSet('railway station').has('power'),false);
  assert.equal(helpers.semanticSet('power station').has('powerhouse'),false);
 });
 test(provider+': compound secondary context cannot pass via station alone',()=>{
  const ctx={...shot,query:'electric generator',domain_context_terms:['hydroelectric']};
  const score=text=>helpers.scoreCandidate(ctx,text,'photo',2000,2000,1,'',text);
  const positive=score('Electric generator equipment inside a hydroelectric powerhouse');
  const negative=score('Electric generator equipment at a hydroelectric railway station');
  assert.equal(positive.rejected,false,JSON.stringify(positive));
  assert.equal(negative.rejected,true,JSON.stringify(negative));
  assert.match(negative.rejection_reason,/missing_secondary_subject_context/);
 });
}

test('exact Commons Cedar Falls powerhouse candidate supports S3 compound context',()=>{
 const fixture=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v51-s3-powerhouse.json'));
 const result=new Function('$','$json',code('Normalize Wikimedia'))(()=>({item:{json:fixture.ctx}}),{statusCode:200,body:fixture.body}).json.candidates;
 assert.equal(result.length,1);
 assert.equal(result[0].provider_asset_id,'78928898');
 assert.equal(result[0].rejected,false,result[0].rejection_reason);
 assert.ok(result[0].relevance_score>=55);
});

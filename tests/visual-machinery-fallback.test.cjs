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

for(const provider of ['Pixabay','Pexels','Wikimedia']) test(provider+': generic unit/room are not machinery domains',()=>{
 const shots=[{...shot,shot_uuid:'s3',must_show:['generator'],visual_intent:'Electric generator in hydroelectric plant',queries_en:['electric generator power station','hydroelectric generator machine','generator']},{...shot,shot_uuid:'s4',visual_intent:'Industrial electric generator unit inside a power plant',must_show:['generator'],queries_en:['electric generator unit power plant','industrial electric generator room','generator']}];
 shots.push({...shot,shot_uuid:'s2',must_show:['turbine'],visual_intent:'Hydroelectric turbine',queries_en:['hydroelectric turbine','water turbine','turbine']});
 const rows=new Function('$',code('Build '+provider+' Requests'))(()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})).map(r=>r.json);
 const fallback=rows.find(r=>r.shot_uuid==='s4'&&r.query_index===3);
 assert.deepEqual(fallback.domain_context_terms,['hydroelectric']);
 assert.equal(fallback.query,'generator');
 assert.equal(fallback.provider_query,'hydroelectric generator equipment');
});

test('exact generator nameplate is rejected as a surface, but requested nameplate remains allowed',()=>{
 const f=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v52-nameplate.json'));
 const normalize=ctx=>new Function('$','$json',code('Normalize Wikimedia'))(()=>({item:{json:ctx}}),{statusCode:200,body:f.body}).json.candidates[0];
 const c=normalize(f.ctx);
 assert.equal(c.rejected,true);
 assert.match(c.rejection_reason,/depicts_surface/);
 const allowed=normalize({...f.ctx,query:'generator nameplate',visual_intent:'Generator nameplate',must_show:['nameplate'],must_not_show:[],domain_context_terms:[]});
 assert.equal(allowed.rejected,false,allowed.rejection_reason);
});

const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

const shots=[{
  shot_uuid:'s2',
  shot_key:'S2-A',
  scene_order:2,
  preferred_media_type:'photo',
  visual_intent:'Water falling down through a penstock in a hydroelectric plant',
  must_show:['penstock'],
  must_not_show:['steam turbine','wind turbine'],
  queries_en:[
    'flowing water falling through penstock',
    'water dropping inside hydroelectric plant penstock',
    'penstock'
  ],
}];

function requests(provider){
  return new Function('$',code('Build '+provider+' Requests'))(
    ()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})
  ).map(x=>x.json);
}

for(const provider of ['Pixabay','Pexels','Wikimedia']){
  test(provider+': closed infrastructure keeps explicit operating domain on broad fallback',()=>{
    const rows=requests(provider);
    assert.equal(rows.length,3);
    assert.ok(rows.every(r=>r.domain_context_terms.includes('hydroelectric')));
    const q3=rows.find(r=>r.query_index===3);
    assert.equal(q3.query,'penstock');
    assert.equal(q3.provider_query,'hydroelectric penstock');
    assert.ok(!q3.provider_query.includes('equipment'));
  });

  test(provider+': hidden-process action words do not become infrastructure domains',()=>{
    const rows=requests(provider);
    const domains=new Set(rows.flatMap(r=>r.domain_context_terms));
    for(const wrong of ['flow','flowing','fall','falling','drop','dropping','down','through']){
      assert.ok(!domains.has(wrong),wrong+' leaked as domain');
    }
  });
}

test('Wikimedia hydroelectric-penstock live response yields compliant candidates with current scorer',()=>{
  const body=JSON.parse(fs.readFileSync('tests/fixtures/wikimedia-hydroelectric-penstock.json'));
  const ctx=requests('Wikimedia').find(r=>r.query_index===3);
  const lookup=name=>{
    if(name==='Build Wikimedia Requests') return {item:{json:ctx}};
    throw new Error(name);
  };
  const out=new Function('$','$json',code('Normalize Wikimedia'))(
    lookup,{statusCode:200,body}
  ).json;
  const eligible=out.candidates.filter(c=>!c.rejected);
  assert.ok(eligible.length>=1,JSON.stringify(out.candidates.map(c=>({
    id:c.provider_asset_id,
    reason:c.rejection_reason,
    score:c.relevance_score
  }))));
  assert.ok(eligible.some(c=>/penstock/i.test(String(c.metadata?.title||c.metadata_text||''))));
});

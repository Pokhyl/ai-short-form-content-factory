const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m8-9229-saved-provider-responses.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function requests(provider){
  return new Function('$',code('Build '+provider+' Requests'))(
    ()=>({first:()=>({json:fixture.begin})})
  ).map(x=>x.json);
}

function wikimediaSavedCandidate(assetId){
  for(const row of fixture.responses){
    if(row.provider!=='Wikimedia') continue;
    const pages=row.response?.body?.query?.pages||{};
    for(const page of Object.values(pages)){
      if(String(page.pageid)!==String(assetId)) continue;
      const ctx=requests('Wikimedia').find(
        r=>r.shot_uuid===row.ctx.shot_uuid && r.query_index===row.ctx.query_index
      );
      const $=name=>{
        if(name==='Build Wikimedia Requests') return {item:{json:ctx}};
        throw new Error(name);
      };
      const out=new Function('$','$json',code('Normalize Wikimedia'))(
        $,
        row.response
      ).json;
      return out.candidates.find(c=>String(c.provider_asset_id)===String(assetId));
    }
  }
  throw new Error('saved asset not found '+assetId);
}

for(const provider of ['Pixabay','Pexels','Wikimedia']){
  test(provider+': 9229 S2 closed pipeline inherits the adjacent hydroelectric operating domain',()=>{
    const rows=requests(provider).filter(r=>r.shot_key==='S2-A');
    assert.equal(rows.length,3);
    assert.ok(rows.every(r=>r.domain_context_terms.includes('hydroelectric')));
    assert.equal(rows[0].provider_query,'hydroelectric water pipeline penstock');
    assert.equal(rows[2].provider_query,'hydroelectric water pipeline');
  });

  test(provider+': 9229 S5 effective retrieval query is de-duplicated and still contains both visible objects',()=>{
    const rows=requests(provider).filter(r=>r.shot_key==='S5-A');
    const q2=rows.find(r=>r.query_index===2);
    const q3=rows.find(r=>r.query_index===3);
    assert.equal(
      q2.provider_query,
      'substation electrical transformer power lines grid'
    );
    assert.equal(
      q3.provider_query,
      'substation electrical transformer power lines'
    );
  });
}

test('9229 old broad penstock candidate is rejected when saved metadata cannot prove inherited hydroelectric domain',()=>{
  const c=wikimediaSavedCandidate('42498812');
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_storyboard_domain_context:hydroelectric/);
});

test('9229 refreshed hydro penstock query yields an eligible domain-grounded candidate',()=>{
  const overlay=JSON.parse(
    fs.readFileSync('tests/fixtures/m8-9229-live-overlay-provider-responses.json')
  );
  const row=overlay.responses.find(r=>
    r.provider==='wikimedia' &&
    r.ctx.shot_key==='S2-A' &&
    r.ctx.query_index===1 &&
    r.ctx.provider_query==='hydroelectric water pipeline penstock'
  );
  assert.ok(row,'missing refreshed Wikimedia S2 q1 overlay response');

  const ctx=requests('Wikimedia').find(
    r=>r.shot_key==='S2-A' && r.query_index===1
  );
  const $=name=>{
    if(name==='Build Wikimedia Requests') return {item:{json:ctx}};
    throw new Error(name);
  };
  const out=new Function('$','$json',code('Normalize Wikimedia'))(
    $,row.response
  ).json;
  const c=out.candidates.find(
    c=>String(c.provider_asset_id)==='39943534'
  );
  assert.ok(c,'expected refreshed response to contain 39943534');
  assert.equal(c.rejected,false,c.rejection_reason);
  assert.equal(c.relevance_score,100);
});

test('9229 Wikimedia old coal-plant intake pipeline is rejected for the inherited hydroelectric domain',()=>{
  const c=wikimediaSavedCandidate('139296455');
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_storyboard_domain_context:hydroelectric/);
});

test('penstock semantic expansion is directional: a generic pipeline does not imply a penstock',()=>{
  const src=code('Normalize Wikimedia');
  const before=src.slice(0,src.indexOf('const ctx ='));
  const {semanticSet}=new Function(before+';return {semanticSet};')();
  assert.ok(semanticSet('penstock').has('pipeline'));
  assert.ok(!semanticSet('pipeline').has('penstock'));
});

test('9229 S5 fresh paired Commons query admits a transformer plus overhead-lines photograph',()=>{
  const body=JSON.parse(fs.readFileSync('tests/fixtures/m8-9229-s5-paired-current.json'));
  const ctx={
    visual_run_id:'test',
    shot_uuid:'8771d26b-f252-4652-bfc1-1ef730624098',
    shot_key:'S5-A',
    scene_order:5,
    query_index:3,
    query:'electrical transformer',
    provider_query:'substation electrical transformer power lines',
    provider:'wikimedia',
    endpoint_kind:'photo',
    preferred_media_type:'photo',
    visual_intent:'electrical substation transformer and power lines',
    must_show:['electrical transformer','power lines'],
    must_not_show:['underground cable','wind turbine'],
    primary_repeated:false,
    domain_context_terms:['substation'],
  };
  const $=name=>{
    if(name==='Build Wikimedia Requests') return {item:{json:ctx}};
    throw new Error(name);
  };
  const candidates=new Function('$','$json',code('Normalize Wikimedia'))(
    $,{statusCode:200,body}
  ).json.candidates;
  const candidate=candidates.find(c=>String(c.provider_asset_id)==='27207173');
  assert.ok(candidate,'expected current Commons response to contain 27207173');
  assert.equal(candidate.rejected,false,candidate.rejection_reason);
  assert.equal(candidate.relevance_score,100);
});


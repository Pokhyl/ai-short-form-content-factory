const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const fixtures=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v94-selected-commons.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function normalize(ctx,body){
  return new Function('$','$json',code('Normalize Wikimedia'))(
    ()=>({item:{json:ctx}}),
    {statusCode:200,body}
  ).json.candidates[0];
}

function candidate(description){
  const base=structuredClone(fixtures.find(f=>f.scene==='S4'));
  const page=Object.values(base.body.query.pages)[0];

  page.pageid=135264822;
  page.title='File:Kraftwerk Wienerbruck Generator 2 2023-06-17.jpg';
  page.imageinfo[0].extmetadata.ObjectName={
    value:'Kraftwerk Wienerbruck Generator 2 2023-06-17'
  };
  page.imageinfo[0].extmetadata.ImageDescription={value:description};
  page.imageinfo[0].extmetadata.Categories={
    value:'Hydroelectric generators|Kraftwerk Wienerbruck'
  };

  const ctx={
    ...base.ctx,
    query:'power generator equipment',
    provider_query:'hydro hydroelectric power generator equipment',
    visual_intent:'electric power generation equipment in hydro plant',
    must_show:['electric generator'],
    must_not_show:['coal pile'],
    domain_context_terms:['hydro','hydroelectric'],
    visual_detail_terms:[],
  };
  return normalize(ctx,base.body);
}

test('9683 regression: concise direct caption can prove operational hydro-plant setting without proving primary subject',()=>{
  const c=candidate(
    'Wienerbruck hydro power plant, Generator 2 of the original equipment to provide electricity for the Mariazellerbahn in working condition'
  );
  assert.equal(c.rejected,false,c.rejection_reason);
  assert.doesNotMatch(String(c.rejection_reason||''),/missing_operational_setting_context/);
});

test('9683 negative: disused generator remains rejected as non-operational lifecycle context',()=>{
  const c=candidate(
    'Wienerbruck hydro power plant, Generator 3 of the original equipment to provide electricity for the Mariazellerbahn, disused'
  );
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/conflicting_non_operational_context:disus/);
});

test('operational context evidence does not change primary depiction proof source',()=>{
  const base=structuredClone(fixtures.find(f=>f.scene==='S4'));
  const page=Object.values(base.body.query.pages)[0];

  page.pageid=999001;
  page.title='File:Power plant exterior.jpg';
  page.imageinfo[0].extmetadata.ObjectName={value:'Power plant exterior'};
  page.imageinfo[0].extmetadata.ImageDescription={
    value:'Hydro power plant in working condition with an electric generator mentioned in the caption but not identified as the photographed subject'
  };
  page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric power plants'};

  const c=normalize({
    ...base.ctx,
    query:'electric generator',
    provider_query:'hydro hydroelectric electric generator equipment',
    visual_intent:'electric power generation equipment in hydro plant',
    must_show:['electric generator'],
    must_not_show:[],
    domain_context_terms:['hydro','hydroelectric'],
    visual_detail_terms:[],
  },base.body);

  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_primary_subject_anchor|wikimedia_primary_only_contextual_metadata/);
});

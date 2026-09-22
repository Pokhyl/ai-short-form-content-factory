const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json')
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

const shots=[
  {
    shot_uuid:'22222222-2222-4222-8222-222222222222',
    shot_key:'S2-A',
    scene_order:2,
    preferred_media_type:'photo',
    visual_intent:'Concrete photo of a powerful water stream falling down through penstock pipes',
    must_show:['water stream'],
    must_not_show:['dry riverbed'],
    queries_en:[
      'powerful water stream flowing down penstock pipe',
      'water stream falling through hydroelectric penstock',
      'water stream',
    ],
  },
  {
    shot_uuid:'33333333-3333-4333-8333-333333333333',
    shot_key:'S3-A',
    scene_order:3,
    preferred_media_type:'photo',
    visual_intent:'Detailed photo of industrial water turbine runner blades inside a power plant',
    must_show:['water turbine'],
    must_not_show:['wind turbine'],
    queries_en:[
      'water turbine runner blades mechanism',
      'industrial water turbine inside hydro power plant',
      'water turbine',
    ],
  },
  {
    shot_uuid:'44444444-4444-4444-8444-444444444444',
    shot_key:'S4-A',
    scene_order:4,
    preferred_media_type:'photo',
    visual_intent:'Close-up photo of rotating water turbine shaft in operation',
    must_show:['water turbine'],
    must_not_show:['wind turbine'],
    queries_en:[
      'rotating water turbine shaft mechanical motion',
      'moving water turbine mechanism inside powerhouse',
      'water turbine',
    ],
  },
];

function planner(nodeName){
  const $=name=>{
    if(name!=='Begin Visuals') throw new Error('unexpected node '+name);
    return {
      first:()=>({
        json:{
          visual_run_id:'11111111-1111-4111-8111-111111111111',
          shots_json:shots,
        },
      }),
    };
  };
  return new Function('$',byName[nodeName].parameters.jsCode)($)
    .map(item=>item.json);
}

function scoreHelper(nodeName){
  const src=byName[nodeName].parameters.jsCode;
  return new Function(
    src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};'
  )().scoreCandidate;
}

function firstCtx(rows,shotKey){
  return rows.find(row=>row.shot_key===shotKey && row.query_index===1);
}

test('9601 planner preserves shot-specific visual detail anchors in every provider query',()=>{
  for(const nodeName of [
    'Build Pixabay Requests',
    'Build Pexels Requests',
    'Build Wikimedia Requests',
  ]){
    const rows=planner(nodeName);

    const s2=rows.filter(x=>x.shot_key==='S2-A');
    assert.deepEqual(s2[0].visual_detail_terms,['penstock','pipe'],nodeName);
    for(const row of s2){
      assert.match(row.provider_query,/\bpenstock\b/,nodeName);
      assert.match(row.provider_query,/\bpipe\b/,nodeName);
    }

    const s3=rows.filter(x=>x.shot_key==='S3-A');
    assert.deepEqual(s3[0].visual_detail_terms,['blade','runner'],nodeName);
    for(const row of s3){
      assert.match(row.provider_query,/\bblades?\b/,nodeName);
      assert.match(row.provider_query,/\brunner\b/,nodeName);
    }

    const s4=rows.filter(x=>x.shot_key==='S4-A');
    assert.deepEqual(s4[0].visual_detail_terms,['shaft'],nodeName);
    for(const row of s4){
      assert.match(row.provider_query,/\bshaft\b/,nodeName);
    }
  }
});

test('9601 selected S2 brook is rejected while real penstock-flow evidence passes',()=>{
  const rows=planner('Build Pexels Requests');
  const ctx=firstCtx(rows,'S2-A');

  for(const nodeName of [
    'Normalize Pixabay',
    'Normalize Pexels',
    'Normalize Wikimedia',
  ]){
    const score=scoreHelper(nodeName);
    const bad='A natural stream flowing over rocks with a blue tube guiding water flow in a serene outdoor setting.';
    const rejected=score(ctx,bad,'photo',940,650,3,'',bad,bad);
    assert.equal(rejected.rejected,true,nodeName);
    assert.match(
      rejected.rejection_reason,
      /missing_visual_detail_anchor:penstock,pipe/,
      nodeName
    );

    const good='Powerful water stream falling through a hydroelectric penstock pipe.';
    const accepted=score(ctx,good,'photo',1600,1200,1,'',good,good);
    assert.equal(accepted.rejected,false,nodeName+' '+accepted.rejection_reason);
  }
});

test('9601 selected S3 turbine hall is rejected without runner blades',()=>{
  const rows=planner('Build Pexels Requests');
  const ctx=firstCtx(rows,'S3-A');

  for(const nodeName of [
    'Normalize Pixabay',
    'Normalize Pexels',
    'Normalize Wikimedia',
  ]){
    const score=scoreHelper(nodeName);
    const bad='Expansive view of industrial turbines inside a hydroelectric power station.';
    const rejected=score(ctx,bad,'photo',940,650,1,'',bad,bad);
    assert.equal(rejected.rejected,true,nodeName);
    assert.match(
      rejected.rejection_reason,
      /missing_visual_detail_anchor:blade,runner/,
      nodeName
    );

    const good='Detailed water turbine runner blades inside a hydroelectric power plant.';
    const accepted=score(ctx,good,'photo',1600,1200,1,'',good,good);
    assert.equal(accepted.rejected,false,nodeName+' '+accepted.rejection_reason);
  }
});

test('9601 selected S4 museum turbine is rejected as non-operational and shaft-less',()=>{
  const rows=planner('Build Wikimedia Requests');
  const ctx=firstCtx(rows,'S4-A');

  for(const nodeName of [
    'Normalize Pixabay',
    'Normalize Pexels',
    'Normalize Wikimedia',
  ]){
    const score=scoreHelper(nodeName);
    const bad='Turbine-dtmuseum2 Henschel Jonval water turbine from 1840 Engines in the Deutsches Museum.';
    const rejected=score(ctx,bad,'photo',1200,1600,1,'',bad,bad);
    assert.equal(rejected.rejected,true,nodeName);
    assert.match(
      rejected.rejection_reason,
      /conflicting_non_operational_context:museum/,
      nodeName
    );
    assert.match(
      rejected.rejection_reason,
      /missing_visual_detail_anchor:shaft/,
      nodeName
    );

    const good='Operating water turbine shaft inside hydroelectric powerhouse.';
    const accepted=score(ctx,good,'photo',1200,1600,1,'',good,good);
    assert.equal(accepted.rejected,false,nodeName+' '+accepted.rejection_reason);
  }
});

test('visual detail anchor rule stays inactive when no shared specific detail exists',()=>{
  const genericShot={
    shot_uuid:'55555555-5555-4555-8555-555555555555',
    shot_key:'S5-A',
    scene_order:5,
    preferred_media_type:'photo',
    visual_intent:'Industrial photo of a large electrical generator in a hydroelectric power station',
    must_show:['electrical generator'],
    must_not_show:['solar panel'],
    queries_en:[
      'large electrical generator hydroelectric power station',
      'industrial electric generator inside power plant',
      'electrical generator',
    ],
  };
  const $=name=>{
    if(name!=='Begin Visuals') throw new Error(name);
    return {
      first:()=>({
        json:{
          visual_run_id:'11111111-1111-4111-8111-111111111111',
          shots_json:[genericShot],
        },
      }),
    };
  };
  const rows=new Function(
    '$',
    byName['Build Pexels Requests'].parameters.jsCode
  )($).map(x=>x.json);
  assert.deepEqual(rows[0].visual_detail_terms,[]);
});

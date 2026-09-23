const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json')
);
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

const shots=[
  {
    shot_uuid:'11111111-1111-4111-8111-111111111111',
    shot_key:'S1-A',
    scene_order:1,
    preferred_media_type:'photo',
    visual_intent:'Hydroelectric dam reservoir storing water behind a large barrier structure',
    must_show:['water reservoir','dam wall'],
    must_not_show:[],
    queries_en:[
      'hydroelectric dam water reservoir aerial photo',
      'large water reservoir behind dam wall',
      'dam wall',
    ],
  },
  {
    shot_uuid:'22222222-2222-4222-8222-222222222222',
    shot_key:'S2-A',
    scene_order:2,
    preferred_media_type:'photo',
    visual_intent:'Water turbine runner mechanism inside a hydroelectric power plant',
    must_show:['water turbine'],
    must_not_show:[],
    queries_en:[
      'hydroelectric water turbine runner blades photo',
      'water turbine inside power plant',
      'water turbine',
    ],
  },
  {
    shot_uuid:'33333333-3333-4333-8333-333333333333',
    shot_key:'S3-A',
    scene_order:3,
    preferred_media_type:'photo',
    visual_intent:'Large electrical generator connected to a turbine in a power station',
    must_show:['electric generator','turbine machine'],
    must_not_show:[],
    queries_en:[
      'hydroelectric power plant generator machine photo',
      'generator connected to turbine',
      'generator turbine',
    ],
  },
  {
    shot_uuid:'44444444-4444-4444-8444-444444444444',
    shot_key:'S4-A',
    scene_order:4,
    preferred_media_type:'photo',
    visual_intent:'Industrial electrical equipment generating electricity inside a plant',
    must_show:['electrical generator'],
    must_not_show:[],
    queries_en:[
      'power plant electrical generator equipment photo',
      'electricity generator machine photo',
      'electrical generator',
    ],
  },
  {
    shot_uuid:'55555555-5555-4555-8555-555555555555',
    shot_key:'S5-A',
    scene_order:5,
    preferred_media_type:'photo',
    visual_intent:'High voltage electrical transmission towers and power lines network',
    must_show:['transmission tower','power lines'],
    must_not_show:[],
    queries_en:[
      'high voltage electrical power grid tower photo',
      'electricity transmission lines network photo',
      'power lines',
    ],
  },
];

function requests(provider){
  const $=name=>{
    if(name!=='Begin Visuals') throw new Error('unexpected node '+name);
    return {
      first:()=>({
        json:{
          visual_run_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          shots_json:shots,
        },
      }),
    };
  };
  return new Function('$',code('Build '+provider+' Requests'))($).map(x=>x.json);
}

for(const provider of ['Pixabay','Pexels','Wikimedia']){
  test(provider+': 9640 process/output words do not become repeated generator hard domains',()=>{
    const rows=requests(provider).filter(r=>['S3-A','S4-A'].includes(r.shot_key));
    assert.equal(rows.length,6);
    for(const row of rows){
      assert.deepEqual(row.domain_context_terms,['hydroelectric']);
      for(const wrong of ['electricity','energy','current','voltage','output']){
        assert.ok(!row.domain_context_terms.includes(wrong),wrong+' leaked into hard domain');
      }
    }
  });

  test(provider+': 9640 paired generator+turbine shot gets structural unit retrieval only',()=>{
    const rows=requests(provider).filter(r=>r.shot_key==='S3-A');
    assert.equal(rows.length,3);
    for(const row of rows){
      const q=row.provider_query.toLowerCase();
      assert.match(q,/\bgenerator\b/);
      assert.match(q,/\bturbine\b/);
      assert.match(q,/\bunit\b/);
      assert.ok(!row.domain_context_terms.includes('unit'));
      assert.ok(row.retrieval_structure_terms.includes('generator'));
      assert.ok(row.retrieval_structure_terms.includes('turbine'));
      assert.ok(row.retrieval_structure_terms.includes('unit'));
    }
    assert.equal(
      rows[2].provider_query,
      'hydroelectric generator turbine unit'
    );
  });

  test(provider+': 9640 inside-plant generator gets plant interior retrieval without a hard interior domain',()=>{
    const rows=requests(provider).filter(r=>r.shot_key==='S4-A');
    assert.equal(rows.length,3);
    for(const row of rows){
      const q=row.provider_query.toLowerCase();
      assert.match(q,/\bplant\b/);
      assert.match(q,/\binterior\b/);
      assert.ok(!row.domain_context_terms.includes('plant'));
      assert.ok(!row.domain_context_terms.includes('interior'));
      assert.ok(row.retrieval_structure_terms.includes('plant'));
      assert.ok(row.retrieval_structure_terms.includes('interior'));
    }
    assert.equal(
      rows[2].provider_query,
      'hydroelectric plant interior electrical generator'
    );
  });
}

test('9640 retrieval enrichment does not rewrite storyboard query provenance',()=>{
  const rows=requests('Wikimedia');
  for(const shot of shots){
    const shotRows=rows.filter(r=>r.shot_key===shot.shot_key);
    assert.equal(shotRows.length,shot.queries_en.length);
    shotRows.forEach((row,index)=>{
      assert.equal(row.query,shot.queries_en[index]);
    });
  }
});

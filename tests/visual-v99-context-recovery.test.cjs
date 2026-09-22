const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(provider,shots)=>new Function('$',code('Build '+provider+' Requests'))(
  ()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})
).map(x=>x.json);

for(const provider of ['Pixabay','Pexels','Wikimedia']) {
  test(provider+': secondary object head remains required and hydroelectric supplies the water modifier',()=>{
    const src=code('Normalize '+provider);
    const {scoreCandidate}=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};')();
    const damCtx={
      query:'hydroelectric dam reservoir',
      visual_intent:'hydroelectric dam reservoir holding water',
      must_show:['hydroelectric dam','water reservoir'],
      must_not_show:[],
      domain_context_terms:[],
      preferred_media_type:'photo',
    };
    const positive=scoreCandidate(
      damCtx,
      'Tri An Hydroelectric Dam And Its Reservoir',
      'photo',1600,1067,1,'',
      'Tri An Hydroelectric Dam And Its Reservoir'
    );
    assert.equal(positive.rejected,false,JSON.stringify(positive));

    const nectarCtx={
      query:'honey bee nectar droplets',
      visual_intent:'honey bee with nectar droplets',
      must_show:['honey bee','nectar droplets'],
      must_not_show:[],
      domain_context_terms:[],
      preferred_media_type:'photo',
    };
    const negative=scoreCandidate(
      nectarCtx,
      'Honey bee with dew droplets',
      'photo',1600,1067,1,'',
      'Honey bee with dew droplets'
    );
    assert.equal(negative.rejected,true,JSON.stringify(negative));
    assert.match(negative.rejection_reason,/missing_secondary_subject_context/);
  });
}

test('Wikimedia map matching dam and reservoir words remains non-photographic',()=>{
  const f=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v99-dam-reservoir.json'));
  const body=structuredClone(f.body);
  const page=Object.values(body.query.pages)[0];
  const info=page.imageinfo[0];
  page.title='File:Pacific Northwest hydroelectric dam reservoir storage capacity map.png';
  info.mime='image/png';
  info.extmetadata.ObjectName={value:'Pacific Northwest hydroelectric dam reservoir storage capacity map'};
  info.extmetadata.Categories={value:'Maps of dams in the United States|Hydroelectric power|Reservoir storage maps'};
  const $=name=>name==='Build Wikimedia Requests'?{item:{json:f.ctx}}:(()=>{throw new Error(name)})();
  const candidate=new Function('$','$json',code('Normalize Wikimedia'))($,{statusCode:200,body}).json.candidates[0];
  assert.equal(candidate.rejected,true);
  assert.match(candidate.rejection_reason,/wikimedia_non_photographic_asset/);
});

const s5=[{
  shot_uuid:'s5',shot_key:'S5-A',scene_order:5,preferred_media_type:'photo',
  visual_intent:'electrical substation transformer and power lines',
  must_show:['electrical transformer','power lines'],
  must_not_show:['underground cable','wind turbine'],
  queries_en:['electrical transformer substation','power lines electrical grid','electrical transformer'],
}];

for(const provider of ['Pixabay','Pexels','Wikimedia']) {
  test(provider+': bare machinery fallback retrieves every mandatory visible object',()=>{
    const rows=requests(provider,s5);
    const q3=rows.find(r=>r.query_index===3);
    assert.equal(q3.query,'electrical transformer');
    assert.deepEqual(q3.domain_context_terms,['substation']);
    assert.equal(q3.provider_query,'substation electrical transformer power lines equipment');
  });
}

const hydroChain=[
  {
    shot_uuid:'s3',shot_key:'S3-A',scene_order:3,preferred_media_type:'photo',
    visual_intent:'water turbine runner inside hydroelectric power plant',
    must_show:['water turbine'],must_not_show:['wind turbine','steam turbine'],
    queries_en:['water turbine runner','turbine blades hydro plant','water turbine'],
  },
  {
    shot_uuid:'s4',shot_key:'S4-A',scene_order:4,preferred_media_type:'photo',
    visual_intent:'electric generator machine inside power station',
    must_show:['electric generator'],must_not_show:['solar panel','battery pack'],
    queries_en:['electric generator machine','hydroelectric generator rotor','electric generator'],
  },
];

for(const provider of ['Pixabay','Pexels','Wikimedia']) {
  test(provider+': adjacent machinery keeps the previous operating domain when the next shot is generic',()=>{
    const rows=requests(provider,hydroChain);
    const s3rows=rows.filter(r=>r.shot_key==='S3-A');
    const s4rows=rows.filter(r=>r.shot_key==='S4-A');
    assert.ok(s3rows.every(r=>r.domain_context_terms.includes('hydroelectric')));
    assert.ok(s4rows.every(r=>r.domain_context_terms.includes('hydroelectric')));
    assert.equal(s4rows[2].provider_query,'hydroelectric electric generator equipment');
  });
}

test('explicit new machinery domain overrides inherited previous domain',()=>{
  const switched=[
    hydroChain[0],
    {
      shot_uuid:'s4',shot_key:'S4-A',scene_order:4,preferred_media_type:'photo',
      visual_intent:'gas generator inside gas power plant',
      must_show:['electric generator'],must_not_show:[],
      queries_en:['gas electric generator','gas generator equipment','electric generator'],
    },
  ];
  const rows=requests('Wikimedia',switched).filter(r=>r.shot_key==='S4-A');
  assert.ok(rows.every(r=>r.domain_context_terms.includes('gas')));
  assert.ok(rows.every(r=>!r.domain_context_terms.includes('hydroelectric')));
  assert.equal(rows[2].provider_query,'gas electric generator equipment');
});


test('Wikimedia contextual primary category cannot by itself prove a visible reservoir',()=>{
  const f=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v99-dam-reservoir.json'));
  const body=structuredClone(f.body);
  const page=Object.values(body.query.pages)[0];
  page.pageid=110885891;
  page.title='File:Peechi Dam 4.jpg';
  const ext=page.imageinfo[0].extmetadata;
  ext.ObjectName={value:'Peechi Dam 4'};
  ext.Categories={value:'Hydroelectricity|Dams|Hydroelectric power plants|Peechi Dam|Peechi Dam reservoir'};
  ext.ImageDescription={value:'Peechi Dam (dam situated outside Thrissur City in Kerala, India)'};
  const $=name=>name==='Build Wikimedia Requests'?{item:{json:f.ctx}}:(()=>{throw new Error(name)})();
  const c=new Function('$','$json',code('Normalize Wikimedia'))($,{statusCode:200,body}).json.candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_secondary_subject_context/);
});

test('Wikimedia direct reservoir evidence remains eligible',()=>{
  const f=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v99-dam-reservoir.json'));
  const $=name=>name==='Build Wikimedia Requests'?{item:{json:f.ctx}}:(()=>{throw new Error(name)})();
  const c=new Function('$','$json',code('Normalize Wikimedia'))($,{statusCode:200,body:f.body}).json.candidates[0];
  assert.equal(c.rejected,false,c.rejection_reason);
});

test('Wikimedia independent power-line category can support transformer plus lines scene',()=>{
  const f=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v99-dam-reservoir.json'));
  const body=structuredClone(f.body);
  const page=Object.values(body.query.pages)[0];
  page.pageid=27207173;
  page.title='File:Chantecoq-FR-45-B-08.JPG';
  const ext=page.imageinfo[0].extmetadata;
  ext.ObjectName={value:'Chantecoq-FR-45-B-08'};
  ext.Categories={value:'Utility poles in France|Overhead power lines in France|Transformer towers in France|Electrical substations in Loiret'};
  ext.ImageDescription={value:'Electrical transformer at Chantecoq'};
  const ctx={
    ...f.ctx,
    query:'electrical transformer',
    provider_query:'substation electrical transformer power lines equipment',
    visual_intent:'electrical substation transformer and power lines',
    must_show:['electrical transformer','power lines'],
    must_not_show:['underground cable','wind turbine'],
    domain_context_terms:['substation'],
  };
  const $=name=>name==='Build Wikimedia Requests'?{item:{json:ctx}}:(()=>{throw new Error(name)})();
  const c=new Function('$','$json',code('Normalize Wikimedia'))($,{statusCode:200,body}).json.candidates[0];
  assert.equal(c.rejected,false,c.rejection_reason);
});

for(const provider of ['Pixabay','Pexels','Wikimedia']) {
  test(provider+': manufacturing context conflicts with an operational power-station shot',()=>{
    const src=code('Normalize '+provider);
    const {scoreCandidate}=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};')();
    const ctx={
      query:'electric generator machine',
      visual_intent:'electric generator machine inside hydroelectric power station',
      must_show:['electric generator'],
      must_not_show:[],
      domain_context_terms:['hydroelectric'],
      preferred_media_type:'photo',
    };
    const c=scoreCandidate(
      ctx,
      'hydroelectric generator manufacturing for dam',
      'photo',1600,2000,1,'',
      'hydroelectric generator manufacturing for dam'
    );
    assert.equal(c.rejected,true,JSON.stringify(c));
    assert.match(c.rejection_reason,/conflicting_non_operational_context/);
  });
}


for(const provider of ['Pixabay','Pexels','Wikimedia']) {
  test(provider+': explicit power-plant setting rejects an aviation generator even when generator and turbine both match',()=>{
    const src=code('Normalize '+provider);
    const {scoreCandidate}=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};')();
    const ctx={
      query:'generator driven by turbine',
      visual_intent:'Industrial electric generator connected to a turbine inside power plant',
      must_show:['electric generator','turbine'],
      must_not_show:[],
      domain_context_terms:[],
      preferred_media_type:'photo',
    };
    const bad='Airplanes parts wind driven electric generator Crocker Wheeler ram air turbines aviation';
    const c=scoreCandidate(ctx,bad,'photo',1600,1200,1,'',bad,bad);
    assert.equal(c.rejected,true,JSON.stringify(c));
    assert.match(c.rejection_reason,/missing_operational_setting_context/);
  });

  test(provider+': power station metadata satisfies an explicit power-plant setting synonym',()=>{
    const src=code('Normalize '+provider);
    const {scoreCandidate}=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};')();
    const ctx={
      query:'generator driven by turbine',
      visual_intent:'Industrial electric generator connected to a turbine inside power plant',
      must_show:['electric generator','turbine'],
      must_not_show:[],
      domain_context_terms:[],
      preferred_media_type:'photo',
    };
    const good='Industrial electric generator connected to turbine inside power station';
    const c=scoreCandidate(ctx,good,'photo',1600,1200,1,'',good,good);
    assert.equal(c.rejected,false,JSON.stringify(c));
  });

  test(provider+': a generic plant word without power context cannot satisfy power-plant setting',()=>{
    const src=code('Normalize '+provider);
    const {scoreCandidate}=new Function(src.slice(0,src.indexOf('const ctx ='))+';return {scoreCandidate};')();
    const ctx={
      query:'generator driven by turbine',
      visual_intent:'Industrial electric generator connected to a turbine inside power plant',
      must_show:['electric generator','turbine'],
      must_not_show:[],
      domain_context_terms:[],
      preferred_media_type:'photo',
    };
    const bad='Electric generator and turbine beside a green plant';
    const c=scoreCandidate(ctx,bad,'photo',1600,1200,1,'',bad,bad);
    assert.equal(c.rejected,true,JSON.stringify(c));
    assert.match(c.rejection_reason,/missing_operational_setting_context/);
  });
}

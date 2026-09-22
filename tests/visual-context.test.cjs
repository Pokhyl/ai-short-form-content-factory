const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const evidence=JSON.parse(fs.readFileSync('docs/acceptance/2026-09-21-pl15-v94-review.json'));
const fixtures=JSON.parse(fs.readFileSync('tests/fixtures/pl15-v94-selected-commons.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;
function requests(provider,shots){return new Function('$',code('Build '+provider+' Requests'))(()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})).map(x=>x.json);}
function normalize(ctx,body){return new Function('$','$json',code('Normalize Wikimedia'))(()=>({item:{json:ctx}}),{statusCode:200,body}).json.candidates[0];}
const shots=evidence.selected.map(s=>({...s,shot_uuid:s.scene_key,shot_key:s.scene_key+'-A',preferred_media_type:'photo'}));
for(const provider of ['Pixabay','Pexels','Wikimedia'])test(provider+': broad fallback retains shared context for repeated subject',()=>{
 const out=requests(provider,shots);
 for(const shot of ['S3-A','S4-A'])assert.ok(out.filter(r=>r.shot_key===shot).every(r=>r.domain_context_terms.includes('hydroelectric')));
 assert.ok(out.filter(r=>r.shot_key==='S2-A').every(r=>r.domain_context_terms.includes('hydro')));
 assert.equal(out.length,15); // search cardinality/provenance contract unchanged

 const byShot=Object.fromEntries(shots.map(s=>[s.shot_key,s]));
 for(const row of out){
   const original=byShot[row.shot_key].queries_en[row.query_index-1];
   assert.equal(row.query,original,'original storyboard query must remain unchanged');
   assert.ok(row.provider_query,'effective provider query is required');
 }

 for(const shot of ['S3-A','S4-A']){
   const rows=out.filter(r=>r.shot_key===shot);
   assert.ok(rows.every(r=>r.provider_query.toLowerCase().includes('hydroelectric')));
 }
 const s3=out.filter(r=>r.shot_key==='S3-A');
 assert.equal(s3[0].provider_query,s3[0].query); // already qualified; no duplicate prefix
 assert.equal(s3[1].provider_query,'hydroelectric '+s3[1].query);
 assert.equal(s3[2].provider_query,'hydroelectric '+s3[2].query+' equipment');
 const s2=out.filter(r=>r.shot_key==='S2-A');
 assert.equal(s2[0].provider_query,s2[0].query);
 assert.equal(s2[1].provider_query,'hydro '+s2[1].query);
 assert.equal(s2[2].provider_query,'hydro '+s2[2].query+' equipment');
});

for(const provider of ['Pixabay','Pexels','Wikimedia'])test(provider+': form-modified repeated primary subjects share the same context key',()=>{
 const sample=[
  {
   shot_uuid:'s3',shot_key:'S3-A',scene_order:3,preferred_media_type:'photo',
   must_show:['generator'],must_not_show:['solar panels'],
   visual_intent:'Generator unit driven by a turbine in a power station',
   queries_en:['generator unit driven by turbine','hydroelectric generator machinery','generator'],
  },
  {
   shot_uuid:'s4',shot_key:'S4-A',scene_order:4,preferred_media_type:'photo',
   must_show:['electrical generator'],must_not_show:['water pump'],
   visual_intent:'Electrical generator equipment generating electric power',
   queries_en:['electrical generator equipment generating power','hydroelectric power generator device','electrical generator'],
  },
 ];
 const rows=requests(provider,sample);
 for(const shot of ['S3-A','S4-A']) {
   const shotRows=rows.filter(r=>r.shot_key===shot);
   assert.equal(shotRows.length,3);
   assert.ok(shotRows.every(r=>r.domain_context_terms.includes('hydroelectric')),shot);
 }
 const s4q1=rows.find(r=>r.shot_key==='S4-A'&&r.query_index===1);
 assert.equal(s4q1.query,'electrical generator equipment generating power');
 assert.equal(s4q1.provider_query,'hydroelectric electrical generator equipment generating power');
 const s4q2=rows.find(r=>r.shot_key==='S4-A'&&r.query_index===2);
 assert.equal(s4q2.provider_query,s4q2.query); // do not duplicate existing context
});


for(const provider of ['Pixabay','Pexels','Wikimedia'])test(provider+': singleton machinery retains explicit local operating domain',()=>{
 const sample=[{
   shot_uuid:'t1',shot_key:'S2-A',scene_order:2,preferred_media_type:'photo',
   must_show:['water turbine'],must_not_show:[],
   visual_intent:'Water turbine spinning inside a hydroelectric power station',
   queries_en:['water turbine inside hydroelectric plant','turbine spinning in water power station','water turbine'],
 }];
 const rows=requests(provider,sample);
 assert.equal(rows.length,3);
 assert.ok(rows.every(r=>r.domain_context_terms.includes('hydroelectric')));
 assert.equal(rows[0].provider_query,rows[0].query);
 assert.equal(rows[1].provider_query,'hydroelectric '+rows[1].query);
 assert.equal(rows[2].provider_query,'hydroelectric water turbine equipment');
});

test('non-machinery subject is not overconstrained by local operating-domain inference',()=>{
 const sample=[{
   shot_uuid:'r1',shot_key:'S1-A',scene_order:1,preferred_media_type:'photo',
   must_show:['water reservoir'],must_not_show:[],
   visual_intent:'Large water reservoir behind a concrete dam in a hydroelectric plant',
   queries_en:['water reservoir behind concrete dam','hydroelectric plant water reservoir','water reservoir'],
 }];
 const rows=requests('Wikimedia',sample);
 assert.ok(rows.every(r=>r.domain_context_terms.length===0));
 assert.equal(rows[2].provider_query,'water reservoir');
});

test('fresh PL15 theme-park water turbine is rejected while actual hydro turbine remains eligible',()=>{
 const base=structuredClone(fixtures.find(f=>f.scene==='S2'));
 const ctx={
   ...base.ctx,
   query:'water turbine',
   visual_intent:'Water turbine spinning inside a hydroelectric power station',
   must_show:['water turbine'],
   must_not_show:[],
   domain_context_terms:['hydroelectric'],
 };
 const page=Object.values(base.body.query.pages)[0];

 page.title='File:Disney California Adventure Grizzly Rapids water turbine.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Disney California Adventure Grizzly Rapids water turbine'};
 page.imageinfo[0].extmetadata.ImageDescription={value:'Old house with a water wheel at Disney California Adventure Grizzly River Run'};
 page.imageinfo[0].extmetadata.Categories={value:'Water turbines|Theme park attractions|Disney California Adventure'};
 let c=normalize(ctx,base.body);
 assert.equal(c.rejected,true);
 assert.match(c.rejection_reason,/missing_storyboard_domain_context:hydroelectric/);

 page.title='File:Hydroelectric power station turbines.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Hydroelectric power station turbines'};
 page.imageinfo[0].extmetadata.ImageDescription={value:'Industrial turbines inside a hydroelectric power station'};
 page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric power stations|Water turbines'};
 c=normalize(ctx,base.body);
 assert.equal(c.rejected,false,c.rejection_reason);
});

test('context derives from arbitrary storyboard vocabulary, not hydro topic rules',()=>{
 const sample=[{shot_uuid:'a',must_show:['research vessel'],queries_en:['marine research vessel','marine expedition ship']},{shot_uuid:'b',must_show:['engine'],queries_en:['marine engine','engine equipment']},{shot_uuid:'c',must_show:['engine'],queries_en:['industrial engine','engine']}];
 const rows=requests('Wikimedia',sample);
 const repeated=rows.filter(r=>['b','c'].includes(r.shot_uuid));
 assert.ok(repeated.every(r=>r.domain_context_terms.includes('marine')));
 assert.equal(rows.find(r=>r.shot_uuid==='b'&&r.query_index===1).provider_query,'marine engine');
 assert.equal(rows.find(r=>r.shot_uuid==='b'&&r.query_index===2).provider_query,'marine engine equipment');
 assert.equal(rows.find(r=>r.shot_uuid==='c'&&r.query_index===1).provider_query,'marine industrial engine');
 assert.equal(rows.find(r=>r.shot_uuid==='c'&&r.query_index===2).provider_query,'marine engine equipment');
 assert.ok(!code('Build Wikimedia Requests').includes('hydroelectric'));
});
test('exact rejected final-frame assets fail, including museum machinery for an operational shot',()=>{
 const rows=requests('Wikimedia',shots);
 for(const f of fixtures){
  const ctx={...f.ctx,domain_context_terms:rows.find(r=>r.shot_key===f.ctx.shot_key).domain_context_terms};
  const c=normalize(ctx,f.body);
  assert.equal(c.rejected,true,f.scene);
  if(f.scene==='S2')assert.match(c.rejection_reason,/conflicting_non_operational_context/);
  if(['S3','S4'].includes(f.scene))assert.match(c.rejection_reason,/missing_storyboard_domain_context/);
  if(f.scene==='S5')assert.match(c.rejection_reason,/depicts_surface/);
 }
});

test('hydroelectric generator metadata satisfies electric-generator subject without weakening domain gate',()=>{
 const f=structuredClone(fixtures.find(f=>f.scene==='S4'));
 const page=Object.values(f.body.query.pages)[0];
 page.title='File:Fankel Generator 01.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Fankel Generator 01'};
 page.imageinfo[0].extmetadata.ImageDescription={value:'Turbine-generator set from a hydroelectric power plant'};
 page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric generators|Francis turbines|Power station equipment'};
 const c=normalize({...f.ctx,domain_context_terms:['hydroelectric']},f.body);
 assert.equal(c.rejected,false,c.rejection_reason);
});

test('museum context conflicts with an explicitly operational power-plant shot',()=>{
 const f=structuredClone(fixtures.find(f=>f.scene==='S4'));
 const page=Object.values(f.body.query.pages)[0];
 page.title='File:Hydroelectric electric generator.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Hydroelectric electric generator'};
 page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric generators|Museum exhibits'};
 const c=normalize({...f.ctx,domain_context_terms:['hydroelectric']},f.body);
 assert.equal(c.rejected,true);
 assert.match(c.rejection_reason,/conflicting_non_operational_context/);
});

test('museum context remains allowed when the storyboard actually requests a museum display',()=>{
 const f=structuredClone(fixtures.find(f=>f.scene==='S4'));
 const page=Object.values(f.body.query.pages)[0];
 page.title='File:Hydroelectric electric generator.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Hydroelectric electric generator'};
 page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric generators|Museum exhibits'};
 const c=normalize({
   ...f.ctx,
   query:'hydroelectric electric generator',
   visual_intent:'Hydroelectric electric generator museum exhibit',
   must_show:['electric generator'],
   must_not_show:[],
   domain_context_terms:['hydroelectric'],
 },f.body);
 assert.equal(c.rejected,false,c.rejection_reason);
});
test('sign photographs remain allowed when signage is the requested visible subject',()=>{
 const f=fixtures.find(f=>f.scene==='S5');
 const c=normalize({...f.ctx,query:'electrical warning signs',visual_intent:'Electrical warning signs on door',must_show:['warning signs'],must_not_show:[]},f.body);
 assert.equal(c.rejected,false);
});


for(const provider of ['Pixabay','Pexels','Wikimedia'])test(provider+': spatial presentation words do not become machinery operating-domain gates',()=>{
 const sample=[{
   shot_uuid:'x4',shot_key:'S4-A',scene_order:4,preferred_media_type:'photo',
   must_show:['electrical transformer','power station'],must_not_show:['wind mill'],
   visual_intent:'Large electrical transformer outdoors near a power station',
   queries_en:['electrical transformer outdoors station','power transformer equipment','electrical transformer'],
 }];
 const rows=requests(provider,sample);
 assert.equal(rows.length,3);
 assert.ok(rows.every(r=>!r.domain_context_terms.includes('outdoors')));
 assert.ok(rows.every(r=>!r.domain_context_terms.includes('outdoor')));
 assert.deepEqual(rows.map(r=>r.query),sample[0].queries_en);
 assert.deepEqual(rows.map(r=>r.provider_query),[...sample[0].queries_en.slice(0,2),'electrical transformer equipment']);
});

test('PL15 S4 regression: described transformer at a power station is not rejected for missing literal outdoors metadata',()=>{
 const request=requests('Pexels',[{
   shot_uuid:'x4',shot_key:'S4-A',scene_order:4,preferred_media_type:'photo',
   must_show:['electrical transformer','power station'],must_not_show:['wind mill'],
   visual_intent:'Large electrical transformer outdoors near a power station',
   queries_en:['electrical transformer outdoors station','power transformer equipment','electrical transformer'],
 }])[0];
 const normalizePexels=code('Normalize Pexels');
 const $=name=>{
   if(name==='Build Pexels Requests') return {item:{json:request}};
   throw new Error('unexpected node '+name);
 };
 const body={photos:[{
   id:28912007,
   width:1365,
   height:2048,
   url:'https://www.pexels.com/photo/high-voltage-transformers-at-a-power-station-28912007/',
   alt:'Close-up of high voltage transformers at a power station in Austria during daylight.',
   photographer:'Michael Pointner',
   photographer_url:'https://www.pexels.com/@michael-pointner/',
   src:{
     large2x:'https://images.pexels.com/photos/28912007/pexels-photo-28912007.jpeg',
     medium:'https://images.pexels.com/photos/28912007/pexels-photo-28912007.jpeg',
   },
 }]};
 const out=new Function('$','$json',normalizePexels)($,{statusCode:200,body}).json.candidates[0];
 assert.equal(request.domain_context_terms.length,0);
 assert.equal(out.rejected,false,out.rejection_reason);
 assert.doesNotMatch(String(out.rejection_reason||''),/missing_storyboard_domain_context:outdoors/);
});

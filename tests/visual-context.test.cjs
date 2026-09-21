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
 assert.ok(out.filter(r=>r.shot_key==='S2-A').every(r=>r.domain_context_terms.length===0));
 assert.equal(out.length,15); // search/provenance contract unchanged
});
test('context derives from arbitrary storyboard vocabulary, not hydro topic rules',()=>{
 const sample=[{shot_uuid:'a',must_show:['research vessel'],queries_en:['marine research vessel','marine expedition ship']},{shot_uuid:'b',must_show:['engine'],queries_en:['marine engine','engine equipment']},{shot_uuid:'c',must_show:['engine'],queries_en:['industrial engine','engine']}];
 const rows=requests('Wikimedia',sample);
 assert.ok(rows.filter(r=>['b','c'].includes(r.shot_uuid)).every(r=>r.domain_context_terms.includes('marine')));
 assert.ok(!code('Build Wikimedia Requests').includes('hydroelectric'));
});
test('exact rejected final-frame assets fail while museum water runner remains eligible',()=>{
 const rows=requests('Wikimedia',shots);
 for(const f of fixtures){
  const ctx={...f.ctx,domain_context_terms:rows.find(r=>r.shot_key===f.ctx.shot_key).domain_context_terms};
  const c=normalize(ctx,f.body);
  assert.equal(c.rejected,f.scene!=='S2',f.scene);
  if(['S3','S4'].includes(f.scene))assert.match(c.rejection_reason,/missing_storyboard_domain_context/);
  if(f.scene==='S5')assert.match(c.rejection_reason,/depicts_surface/);
 }
});
test('actual domain evidence accepts a museum generator without museum blacklist',()=>{
 const f=structuredClone(fixtures.find(f=>f.scene==='S4'));
 const page=Object.values(f.body.query.pages)[0];
 page.title='File:Hydroelectric electric generator.jpg';
 page.imageinfo[0].extmetadata.ObjectName={value:'Hydroelectric electric generator'};
 page.imageinfo[0].extmetadata.Categories={value:'Hydroelectric generators|Museum exhibits'};
 const c=normalize({...f.ctx,domain_context_terms:['hydroelectric']},f.body);
 assert.equal(c.rejected,false);
});
test('sign photographs remain allowed when signage is the requested visible subject',()=>{
 const f=fixtures.find(f=>f.scene==='S5');
 const c=normalize({...f.ctx,query:'electrical warning signs',visual_intent:'Electrical warning signs on door',must_show:['warning signs'],must_not_show:[]},f.body);
 assert.equal(c.rejected,false);
});

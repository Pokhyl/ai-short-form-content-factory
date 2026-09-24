const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const records=JSON.parse(fs.readFileSync('tests/fixtures/m8-9948-request-contracts.json'));
const groups=new Map();for(const r of records){if(!groups.has(r.shot_key))groups.set(r.shot_key,{...r,queries_en:[]});groups.get(r.shot_key).queries_en.push(r.query);}
const shots=[...groups.values()];
for(const provider of ['Pexels','Pixabay','Wikimedia']){
 const code=w.nodes.find(n=>n.name==='Build '+provider+' Requests').parameters.jsCode;
 const run=shots=>new Function('$',code)(()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})).map(i=>i.json);
 test(provider+' 9948 preserves missing ship and lighthouse from explicit intent',()=>{
  const out=run(shots);
  for(const [shot,term] of [['S4-A','ship'],['S5-A','lighthouse']]){
   const rows=out.filter(r=>r.shot_key===shot);assert.equal(rows.length,3);
   assert(rows.every(r=>r.domain_context_terms.includes(term)));
   assert(rows.every(r=>r.provider_query.split(' ').includes(term)));
   assert.deepEqual(rows.map(r=>r.query),records.filter(r=>r.shot_key===shot).map(r=>r.query));
  }
 });
 test(provider+' explicit-subject preservation is generic and does not infer topic context',()=>{
  const base={...shots[0],must_show:['railway platform'],visual_intent:'A train approaching a railway platform',queries_en:['railway platform','station platform railway','railway platform station']};
  assert(run([base]).every(r=>r.domain_context_terms.includes('train')));
  const already={...base,must_show:['train'],visual_intent:'A bright red train approaching a railway platform'};
  assert(run([already]).every(r=>!r.domain_context_terms.includes('bright')&&!r.domain_context_terms.includes('red')));
  const unspoken={...base,visual_intent:'Railway platform used for travel'};
  assert(run([unspoken]).every(r=>!r.domain_context_terms.includes('train')));
 });
}

test('9948 saved Pexels rock-only photos no longer pass the lighthouse-intent metadata gate',()=>{
 const responses=JSON.parse(fs.readFileSync('tests/fixtures/m8-9948-pexels-responses.json'));
 assert.equal(responses.length,records.length);
 const build=w.nodes.find(n=>n.name==='Build Pexels Requests').parameters.jsCode;
 const normalize=w.nodes.find(n=>n.name==='Normalize Pexels').parameters.jsCode;
 const requests=new Function('$',build)(()=>({first:()=>({json:{visual_run_id:'test',shots_json:shots}})})).map(i=>i.json);
 let seen=false;
 for(let i=0;i<records.length;i++){
  if(records[i].shot_key!=='S5-A')continue;
  const ctx={...records[i],domain_context_terms:requests[i].domain_context_terms};
  const out=new Function('$','$json',normalize)(()=>({item:{json:ctx}}),responses[i]).json;
  for(const c of out.candidates){if(c.provider_asset_id==='37438538'){
   seen=true;assert.equal(c.rejected,true);assert.match(c.rejection_reason,/missing_storyboard_domain_context:lighthouse/);
  }}
 }
 assert.equal(seen,true,'exact wrongly admitted photo not found in replay');
});

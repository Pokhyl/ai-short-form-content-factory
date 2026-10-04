const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12093-paired-preview.json'));
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const requests=(begin=f.begin,src=code('Build Wikimedia Requests'))=>new Function('$',src)(()=>({first:()=>({json:begin})})).map(v=>v.json);
const normalize=(ctx,response,src=code('Normalize Wikimedia'))=>new Function('$','$json',src)(()=>({item:{json:ctx}}),response).json.candidates;
const context=key=>requests().find(c=>c.shot_key===key && c.query_index===3);
const original=key=>f.providers.wikimedia.find(b=>b.ctx.shot_key===key && b.ctx.query_index===3);
test('saved corpus broadens S6 noun variation and S9 physical result only in final fallbacks',()=>{
 const before=requests(f.begin,f.baseline_nodes['Build Wikimedia Requests'].jsCode),after=requests();
 assert.equal(after.length,27);
 const changed=after.filter((c,i)=>JSON.stringify(c)!==JSON.stringify(before[i]));
 assert.deepEqual(changed.map(c=>[c.shot_key,c.query_index]),[['S6-A',3],['S9-A',3]]);
 assert.equal(changed[0].provider_query,'stapler staples');
 assert.ok(changed[1].fastened_result_context);assert.match(changed[1].provider_query,/^(?:stapled|staple) /);
 for(const c of changed){const old=before.find(r=>r.shot_key===c.shot_key&&r.query_index===c.query_index);for(const key of ['query','visual_intent','must_show','must_not_show','domain_context_terms'])assert.deepEqual(c[key],old[key]);}
 const old=before.find(c=>c.shot_key==='S6-A'&&c.query_index===3);
 for(const k of ['query','visual_intent','must_show','must_not_show','domain_context_terms'])assert.deepEqual(changed[0][k],old[k]);
});
test('pixel-confirmed open owner and consumable are nominated but never metadata-approved',()=>{
 const c=normalize(context('S6-A'),f.plural_pair_response).find(c=>c.provider_asset_id==='8141312');
 assert.equal(c.metadata.paired_subject_review,true);assert.equal(c.rejected,true);
 assert.ok(c.relevance_score>=55,JSON.stringify(c));assert.ok(c.rejection_reason);
});
test('purpose-only loose consumables cannot nominate the absent owner',()=>{
 const cs=normalize(context('S6-A'),original('S6-A').response);
 for(const id of ['11334157','26029614'])assert.ok(!cs.find(c=>c.provider_asset_id===id).metadata.paired_subject_review,id);
});
test('a compound object type cannot nominate its adjective as an independent surface',()=>{
 const cs=normalize(context('S7-A'),original('S7-A').response);
 assert.ok(!cs.find(c=>c.provider_asset_id==='130306651').metadata.paired_subject_review);
});
test('one paired category and direct state caption nominate the photographed surface pair',()=>{
 const c=normalize(context('S7-A'),original('S7-A').response).find(c=>c.provider_asset_id==='12612756');
 assert.equal(c.metadata.paired_subject_review,true);assert.equal(c.rejected,true);assert.ok(c.relevance_score>=55);
});
test('exact failed preview URLs become query-free and unscaled dimensions reflect original bytes',()=>{
 for(const key of ['S6-A','S7-A']){
  const bundle=original(key),cs=normalize(context(key),bundle.response);
  for(const page of Object.values(bundle.response.body.query.pages)){
   const c=cs.find(c=>c.provider_asset_id===String(page.pageid));if(!c)continue;
   assert.ok(!/[?#]/u.test(c.preview_url||''));assert.ok(!/[?#]/u.test(c.download_url));
   const info=page.imageinfo[0];
   if(info.thumburl.split('?')[0]===info.url.split('?')[0]){
    assert.equal(c.width,info.width);assert.equal(c.height,info.height);
   }
  }
 }
 const c=normalize(context('S7-A'),original('S7-A').response).find(c=>c.provider_asset_id==='75797646');
 assert.equal(c.width,584);assert.equal(c.height,555);
});
test('category mosaics and diagram labels never gain state-pair nomination',()=>{
 const response=JSON.parse(JSON.stringify(original('S7-A').response));
 let page=response.body.query.pages['12612756'];page.imageinfo[0].extmetadata.Categories.value='Paper|Staples';
 let c=normalize(context('S7-A'),response).find(c=>c.provider_asset_id==='12612756');assert.ok(!c.metadata.paired_subject_review);
 page.imageinfo[0].extmetadata.Categories.value='Paper staples';page.title='File:Paper staples diagram.jpg';
 c=normalize(context('S7-A'),response).find(c=>c.provider_asset_id==='12612756');assert.ok(!c.metadata.paired_subject_review);assert.match(c.rejection_reason,/non_photographic/);
});
test('unrequested open packaging cannot gain pair nomination from a category',()=>{
 const response=JSON.parse(JSON.stringify(original('S7-A').response));const page=response.body.query.pages['12612756'];
 page.title='File:Open carton.jpg';page.imageinfo[0].extmetadata.ObjectName.value='Open carton';page.imageinfo[0].extmetadata.ImageDescription.value='An open carton.';
 const c=normalize(context('S7-A'),response).find(c=>c.provider_asset_id==='12612756');assert.ok(!c.metadata.paired_subject_review);
});
test('preview transport evidence is real HTTP200 for all three original failures',()=>{
 assert.deepEqual(f.query_free_probe.map(p=>[p.asset_id,p.status]),[['11334157',200],['26029614',200],['75797646',200]]);
 assert.ok(f.query_free_probe.every(p=>p.bytes>0&&p.sha256.length===64));
});

test('authored plural retrieval generalizes to another physical owner and consumable pair',()=>{
 const begin=JSON.parse(JSON.stringify(f.begin));
 const pair=begin.shots_json.find(s=>s.shot_key==='S6-A');
 Object.assign(pair,{must_show:['office binder','metal ring'],must_not_show:[],visual_intent:'A close-up photo of office binder with metal ring.',queries_en:['office binder ring mechanism','binder ring opening','metal ring']});
 const plural=begin.shots_json.find(s=>s.shot_key==='S3-A');plural.must_show=['office binder','metal rings'];
 const c=requests(begin).find(c=>c.shot_key==='S6-A'&&c.query_index===3);
 assert.equal(c.provider_query,'binder rings');assert.deepEqual(c.must_show,['office binder','metal ring']);
 plural.must_show=['office binder','metal ring'];
 const unchanged=requests(begin).find(c=>c.shot_key==='S6-A'&&c.query_index===3);
 assert.notEqual(unchanged.provider_query,'binder rings');
});
test('actual Gemini responses replay through the unchanged strict per-concept parser',()=>{
 for(const row of f.gemini_replay){
  const parsed=new Function('$','$json',code('Parse Gemini Vision Result'))(()=>({item:{json:row.request}}),row.response).json;
  assert.deepEqual(parsed,row.parsed);
  const id=row.request.shot_key==='S6-A'?'8141312':'12612756';
  const c=parsed.candidates.find(c=>c.provider_asset_id===id);
  const e=parsed.evaluations.find(e=>e.candidate_index===c.candidate_index);
  assert.equal(e.vision_pass,true);assert.ok(e.must_show_checks.every(check=>check.visible));
  assert.equal(c.metadata_rejected,true);
 }
 const row=f.gemini_replay.find(r=>r.request.shot_key==='S7-A');
 assert.equal(row.parsed.evaluations[0].must_show_visible,true);
 assert.equal(row.parsed.evaluations[0].intent_match,false);
 assert.equal(row.parsed.evaluations[0].vision_pass,false);
});
test('all nine actual scene reviews produce a complete unique strict assignment after paired replay',()=>{
 const collect=rows=>new Function('$input','$',code('Collect Gemini Selections'))({all:()=>rows.map(json=>({json}))},()=>({first:()=>({json:f.begin})}))[0].json;
 assert.throws(()=>collect(f.parsed_reviews),/no Gemini-approved unique visual candidate for shot S6-A/);
 const rows=f.parsed_reviews.map(r=>f.gemini_replay.find(v=>v.parsed.shot_key===r.shot_key)?.parsed||r);
 const result=collect(rows);assert.equal(result.selections.length,9);
 const selected=result.selections.map(s=>{
  const row=rows.find(r=>r.shot_uuid===s.shot_uuid),c=row.candidates.find(c=>c.candidate_id===s.candidate_id);
  assert.ok(s.validation_evidence.vision_pass&&s.validation_evidence.intent_match&&s.validation_evidence.must_show_visible&&s.validation_evidence.must_not_show_clear);
  assert.ok(c.relevance_score>=55);
  return c.provider+':'+c.provider_asset_id;
 });
 assert.equal(new Set(selected).size,9);assert.ok(selected.includes('wikimedia:8141312'));assert.ok(selected.includes('wikimedia:12612756'));
 assert.ok(!selected.includes('wikimedia:75797646'));
});

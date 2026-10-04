// Replay persisted provider responses through current native code; no API or DB calls.
const fs=require('node:fs'),assert=require('node:assert/strict'),crypto=require('node:crypto');
function replay(path='tests/fixtures/release-m8-12108-integrated.json'){
 const f=JSON.parse(fs.readFileSync(path)),w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
 const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
 const ranking=JSON.parse(fs.readFileSync('tests/fixtures/m8-12108-fastening-contract.json'));
 const {samePreviewSources}=require('./visual_preview_identity.cjs');
 const parsed=f.bundles.map(b=>{
  const expected=ranking.ranking_replay.candidate_sets.find(s=>s.shot_key===b.shot);assert(samePreviewSources(b.ctx.candidates,expected.candidates),b.shot+' stale sources');
  const original=f.begin.shots_json.find(s=>s.shot_key===b.shot);for(const key of ['must_show','must_not_show','visual_intent'])assert.deepEqual(b.ctx[key],original[key],b.shot+' changed original contract');
  const p=new Function('$','$json',code('Parse Gemini Vision Result'))(()=>({item:{json:b.ctx}}),b.response).json;
  assert.deepEqual(p,b.expected_parsed,b.shot+' saved native parsing changed');return p;
 });
 const collection=new Function('$input','$',code('Collect Gemini Selections'))({all:()=>parsed.map(json=>({json}))},()=>({first:()=>({json:f.begin})}))[0].json;
 const selected=collection.selections.map(s=>{const p=parsed.find(r=>r.shot_uuid===s.shot_uuid),c=p.candidates.find(c=>c.candidate_id===s.candidate_id),e=p.evaluations.find(e=>e.candidate_index===c.candidate_index);assert.equal(e.vision_pass,true);assert.equal(e.intent_match,true);assert.equal(e.must_not_show_clear,true);assert.equal(e.must_show_checks.length,f.bundles.find(b=>b.shot===p.shot_key).ctx.must_show.length);assert(e.must_show_checks.every(x=>x.visible));return {shot:p.shot_key,provider:c.provider,asset:c.provider_asset_id,score:e.match_score};});
 assert.equal(selected.length,f.begin.shots_json.length);assert.equal(new Set(selected.map(s=>s.provider+':'+s.asset)).size,selected.length);
 const input=f.s4_preview_input,ctx=new Function('$','$json',code('Build Gemini Vision Request'))(()=>({item:{json:input.ctx}}),input.worker_response).json;
 assert.deepEqual(ctx.candidates,f.bundles.find(b=>b.shot==='S4-A').ctx.candidates);
 const s4=parsed.find(p=>p.shot_key==='S4-A');assert.deepEqual(s4.evaluations.map(e=>e.vision_pass),[false,false,true]);
 return {provider_calls:0,production_mutations:0,provenance:f.provenance,selected,s4_request_sha256:crypto.createHash('sha256').update(JSON.stringify(ctx.gemini_body)).digest('hex')};
}
module.exports={replay};
if(require.main===module){const r=replay(process.argv[2]);if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(r,null,2)+'\n');console.log(JSON.stringify(r));}

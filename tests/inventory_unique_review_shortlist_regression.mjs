import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const raw=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json',import.meta.url)));
const wf=Array.isArray(raw)?raw[0]:raw;
const run=new Function('$input','$',wf.nodes.find(n=>n.name==='Prepare Inventory Review Batches').parameters.jsCode);
const asset=(id,hash)=>({asset_identity:'test:'+id,provider:'test',provider_asset_id:id,target_anchor_pass:true,visual_hash:hash??createHash('sha256').update(id).digest('hex'),preview_url:'https://example.org/'+id+'.jpg'});
const row=(n,items)=>({claim_number:n,claim_id:'C'+n,claim:'hypothesis',evidence_ids:['S1'],fingerprinted_candidates:items});
const prepare=(rows,target=15)=>run({all:()=>rows.map(json=>({json}))},()=>({first:()=>({json:{target_duration_seconds:target,canonical_subject:'subject',user_intent:'explain',research_rows:[{id:'S1',snippet:'fact one'},{id:'S2',snippet:'fact two'}]}})}));
const exposed=out=>out.flatMap(x=>x.json.claims.flatMap(c=>c.review_candidates));
for(const subject of ['clock','telescope']){
 const shared=[asset(subject+'a'),asset(subject+'b'),asset(subject+'c')];
 const rows=Array.from({length:5},(_,i)=>row(i+1,[...shared,...Array.from({length:5},(_,j)=>asset(subject+i+'-'+j))]));
 const out=prepare(rows),xs=exposed(out);
 assert.equal(xs.length,20);assert.equal(new Set(xs.map(x=>x.asset_identity)).size,20);
 assert(xs.some(x=>x.provider_asset_id===subject+'0-3'),'deeper candidates must fill duplicate slots');
 assert(out.every(x=>x.json.visual_review_request.input.filter(i=>i.type==='image').length<=24));
 assert(out.every(x=>x.json.visual_review_request.input.length<=80));
}
const only=[row(1,Array.from({length:8},(_,i)=>asset('only'+i))),row(2,[]),row(3,[])];
assert.equal(exposed(prepare(only)).length,8,'one productive bucket can support multiple observations');
const sameHash=asset('original').visual_hash;
assert.throws(()=>prepare([row(1,[asset('original'),asset('copy',sameHash),asset('second')])]),/unique fingerprinted assets/);
const bad=asset('bad');bad.target_anchor_pass=false;
assert.throws(()=>prepare([row(1,[asset('one'),asset('two'),bad])]),/unique fingerprinted assets/);
const many=prepare(Array.from({length:10},(_,i)=>row(i+1,Array.from({length:8},(_,j)=>asset('many'+i+'-'+j)))),60);
assert.equal(exposed(many).length,40);assert.equal(many.length,2);
console.log('GLOBAL_UNIQUE_REVIEW_SHORTLIST_PASS');

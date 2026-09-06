import assert from 'node:assert/strict';
import fs from 'node:fs';
import {discoverVisualCandidates} from '../services/media-worker/src/visual-discovery.mjs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'))[0];
const code=w.nodes.find(n=>n.name==='Validate Candidate Claims').parameters.jsCode;
const claims=Array.from({length:4},(_,i)=>({claim_id:`C${i+1}`,claim:`Supported fact ${i+1}.`,evidence_ids:[i%2?'S2':'S1'],visual_target:`A detailed image of subject ${i+1}, showing its distinct mechanism and every relevant component.`,search_query_en:`subject mechanism ${i+1}`}));
const base={research_rows:[{id:'S1'},{id:'S2'}],candidate_claim_range:[4,6],canonical_subject:'Subject'};
const run=rows=>new Function('$input','$',code)({first:()=>({json:{text:JSON.stringify({claims:rows})}})},()=>({first:()=>({json:base})}))[0].json;
const valid=run(claims);
assert.throws(()=>run(claims.map(c=>({...c,search_query_en:''}))),/compact search_query_en/);
const requests=[];
const out=await discoverVisualCandidates({canonicalSource:{language:'en',title:'Subject'},inventoryClaims:valid.candidate_claims,fetchImpl:async url=>{requests.push(String(url));return new Response(JSON.stringify({query:{pages:[]}}),{status:200});}});
for(let i=0;i<claims.length;i++){
 assert.equal(out.inventory_claims[i].provider_queries[0],claims[i].search_query_en);
 assert.equal(out.inventory_claims[i].visual_target,claims[i].visual_target,'retrieval must not weaken acceptance target');
 assert(requests.some(u=>new URL(u).searchParams.get('gsrsearch')===claims[i].search_query_en));
}
console.log('INVENTORY_RETRIEVAL_QUERY_CONTRACT_PASS');

import assert from 'node:assert/strict';
import fs from 'node:fs';
import {discoverVisualCandidates} from '../services/media-worker/src/visual-discovery.mjs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'))[0];
const code=w.nodes.find(n=>n.name==='Validate Candidate Claims').parameters.jsCode;
const roles=['hook','mechanism','detail','result'];const claims=Array.from({length:4},(_,i)=>({claim_id:`C${i+1}`,claim:`Supported fact ${i+1}.`,evidence_ids:[i%2?'S2':'S1'],editorial_role:roles[i],visual_form:i===1?'diagram':'photo',visual_target:`Subject component ${i+1}`,search_query_en:`subject mechanism ${i+1}`,inventory_asset_ids:[`V${i+1}`]}));
const base={research_rows:[{id:'S1'},{id:'S2'}],candidate_claim_range:[4,6],canonical_subject:'Subject',available_visual_assets:Array.from({length:6},(_,i)=>({inventory_id:`V${i+1}`,preclaim_visual_form:i===1?'diagram':'photo',preclaim_visible_description:`Subject component ${i+1}${i===1?' diagram':''}`,title:`Subject component ${i+1}`,description:`Subject mechanism component ${i+1}`,categories:'Subject'}))};
const run=rows=>new Function('$input','$',code)({first:()=>({json:{text:JSON.stringify({claims:rows})}})},()=>({first:()=>({json:base})}))[0].json;
const valid=run(claims);
assert.throws(()=>run(claims.map(c=>({...c,search_query_en:''}))),/compact search_query_en/);
// Provider contract is a character budget, not an arbitrary word-count ceiling.
for (const query of ['mechanical clock gear train cross section technical drawing photo', 'one two six ten red blue gear ring dial face hand stem']) {
 const rows=claims.map(c=>({...c,search_query_en:query}));
 assert.equal(run(rows).candidate_claims[0].search_query_en,query);
}
for (const query of ['singleword','word '.repeat(20).trim()]) {
 assert.throws(()=>run(claims.map(c=>({...c,search_query_en:query}))),/compact search_query_en/);
}
const requestCode=w.nodes.find(n=>n.name==='Build Draft Candidate Claims Request').parameters.jsCode;
const request=new Function('$json',requestCode)({claim_prompt:'test'}).json.model_request;
assert.equal(request.response_schema.properties.claims.items.properties.search_query_en.maxLength,90);
const requests=[];
const out=await discoverVisualCandidates({canonicalSource:{language:'en',title:'Subject'},inventoryClaims:valid.candidate_claims,fetchImpl:async url=>{requests.push(String(url));return new Response(JSON.stringify({query:{pages:[]}}),{status:200});}});
for(let i=0;i<claims.length;i++){
 assert.equal(out.inventory_claims[i].provider_queries[0],claims[i].search_query_en);
 assert.equal(out.inventory_claims[i].visual_target,claims[i].visual_target,'retrieval must not weaken acceptance target');
 assert(requests.some(u=>new URL(u).searchParams.get('gsrsearch')===claims[i].search_query_en));
}
console.log('INVENTORY_RETRIEVAL_QUERY_CONTRACT_PASS');

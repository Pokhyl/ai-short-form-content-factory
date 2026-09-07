import assert from 'node:assert/strict';
import fs from 'node:fs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json'))[0];
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const hashes=['0'.repeat(64),'f'.repeat(64),'a'.repeat(64)];
const claims=hashes.map((hash,i)=>({claim_number:i+1,claim_id:`C${i+1}`,claim:'Proposed fact with an unobserved extra detail.',visual_target:'A prescribed composition with an extra background object.',evidence_ids:[`S${i+1}`],research_rows:[{id:`S${i+1}`,snippet:`Research supports component ${i+1}.`}],fingerprinted_candidates:[{candidate_id:`asset-${i}`,provider:'wikimedia',provider_asset_id:`asset-${i}`,preview_urls:[`https://example.com/${i}.jpg`],target_anchor_pass:true,visual_hash:hash,title:`Specific visible component ${i+1}`,description:`Specific visible component ${i+1}`,license:'CC BY'}]}));
const base={target_duration_seconds:15,research_rows:claims.flatMap(c=>c.research_rows)};
const batches=new Function('$input','$',code('Prepare Inventory Review Batches'))({all:()=>claims.map(json=>({json}))},()=>({first:()=>({json:base})})).map(x=>x.json);
assert(batches[0].visual_review_request.input.some(x=>x.text?.includes('S1: Research supports component 1.')),'reviewer receives actual cited research, not just a claim');
const decisions=claims.map((c,i)=>({claim_number:i+1,verdicts:[{review_id:`C${i+1}-I1`,relevant:true,visible_description:`Specific visible component ${i+1}`,supported_claim:`Research-supported fact about component ${i+1}.`,supported_evidence_ids:[`S${i+1}`]}]}));
const run=ds=>new Function('$input','$',code('Select Verified Claim Inventory'))({all:()=>[{json:{text:JSON.stringify({claims:ds})}}]},name=>name==='Prepare Inventory Review Batches'?{all:()=>batches.map(json=>({json}))}:{first:()=>({json:base})})[0].json;
const out=run(decisions);
assert.equal(out.verified_claim_count,3);
assert.equal(out.verified_claims[0].claim,decisions[0].verdicts[0].supported_claim);
assert.equal(out.verified_claims[0].visual_target,'Specific visible component 1');
assert.equal(out.verified_claims[0].proposed_visual_target,claims[0].visual_target);
assert.deepEqual(out.verified_claims[0].evidence_ids,['S1']);
for(const change of [{supported_evidence_ids:['S999']},{supported_claim:''},{supported_evidence_ids:[]},{relevant:false}]){
 const bad=structuredClone(decisions);Object.assign(bad[0].verdicts[0],change);
 assert.throws(()=>run(bad),/verified visual inventory 2\/3/,'invalid grounding cannot reserve an asset');
}
const request=new Function('$json',code('Build Review Inventory Candidate Images Request'))({input:[]}).json.model_request;
assert(request.response_schema.properties.claims.items.properties.verdicts.items.required.includes('supported_evidence_ids'));
console.log('INVENTORY_OBSERVED_CLAIM_CONTRACT_PASS');

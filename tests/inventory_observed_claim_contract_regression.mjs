import assert from 'node:assert/strict';
import fs from 'node:fs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json'))[0];
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const mk=(n,hash,title)=>({candidate_id:`asset-${n}`,provider:'wikimedia',provider_asset_id:`asset-${n}`,asset_identity:`wikimedia:asset-${n}`,preview_urls:[`https://example.com/${n}.jpg`],download_url:`https://example.com/${n}-full.jpg`,target_anchor_pass:true,visual_hash:hash,title,description:title,license:'CC BY'});
const research=[{id:'S1',snippet:'Research supports visible component alpha.'},{id:'S2',snippet:'Research supports visible component beta.'},{id:'S3',snippet:'Research supports visible component gamma.'}];
const candidateClaims=[
 {claim_number:1,claim_id:'C1',claim:'Fact about visible component alpha.',visual_target:'Visible component alpha.',evidence_ids:['S1'],editorial_role:'hook',visual_form:'photo'},
 {claim_number:2,claim_id:'C2',claim:'Fact about visible component beta.',visual_target:'Visible component beta.',evidence_ids:['S2'],editorial_role:'mechanism',visual_form:'photo'},
 {claim_number:3,claim_id:'C3',claim:'Fact about visible component gamma.',visual_target:'Visible component gamma.',evidence_ids:['S3'],editorial_role:'result',visual_form:'photo'},
];
const claims=[
 {claim_number:1,claim_id:'C1',claim:'Origin hypothesis one.',visual_target:'Origin target one.',evidence_ids:['S1'],research_rows:research,fingerprinted_candidates:[mk(1,'0'.repeat(64),'Visible component beta'),mk(2,'3'.repeat(64),'Visible component gamma')]},
 {claim_number:2,claim_id:'C2',claim:'Origin hypothesis two.',visual_target:'Origin target two.',evidence_ids:['S2'],research_rows:research,fingerprinted_candidates:[mk(3,'f'.repeat(64),'Visible component alpha'),mk(4,'a'.repeat(64),'Visible component beta')]},
 {claim_number:3,claim_id:'C3',claim:'Origin hypothesis three.',visual_target:'Origin target three.',evidence_ids:['S3'],research_rows:research,fingerprinted_candidates:[mk(5,'5'.repeat(64),'Visible component alpha'),mk(6,'c'.repeat(64),'Visible component gamma')]}
];
const base={target_duration_seconds:15,canonical_subject:'Example subject',user_intent:'Explain the subject',research_rows:research,candidate_claims:candidateClaims};
const baseLookup=name=>name==='Validate Candidate Claims'?{first:()=>({json:base})}:null;
const batches=new Function('$input','$',code('Prepare Inventory Review Batches'))({all:()=>claims.map(json=>({json}))},baseLookup).map(x=>x.json);
const inputText=batches[0].visual_review_request.input.filter(x=>x.type==='text').map(x=>x.text).join('\n');
assert.match(inputText,/retrieval hypothesis.*must not force acceptance/);
assert.match(inputText,/CLAIM INVENTORY/);
assert.match(inputText,/C1 \| FACT: Fact about visible component alpha/);
assert.match(inputText,/FULL RESEARCH CORPUS/);
assert.match(inputText,/S2: Research supports visible component beta/,'every discovery bucket must expose the global research corpus');
const verdicts=[
 {review_id:'C1-I1',relevant:true,visible_description:'Visible component beta',supported_claim_id:'C2'},
 {review_id:'C1-I2',relevant:true,visible_description:'Visible component gamma',supported_claim_id:'C3'},
 {review_id:'C2-I1',relevant:true,visible_description:'Visible component alpha',supported_claim_id:'C1'},
 {review_id:'C2-I2',relevant:true,visible_description:'Visible component beta',supported_claim_id:'C2'},
 {review_id:'C3-I1',relevant:true,visible_description:'Visible component alpha',supported_claim_id:'C1'},
 {review_id:'C3-I2',relevant:true,visible_description:'Visible component gamma',supported_claim_id:'C3'},
];
const lookup=name=>name==='Prepare Inventory Review Batches'?{all:()=>batches.map(json=>({json}))}:name==='Validate Candidate Claims'?{first:()=>({json:base})}:null;
const run=entries=>new Function('$input','$',code('Select Verified Claim Inventory'))({all:()=>[{json:{text:JSON.stringify({verdicts:entries})}}]},lookup)[0].json;
const out=run(verdicts);
assert.equal(out.verified_claim_count,3,'all grounded claims remain available after visual review');
assert.deepEqual(out.verified_claims.map(x=>x.claim_id),['C1','C2','C3']);
assert.deepEqual(out.verified_claims.map(x=>x.source_claim_id),['C1','C2','C3']);
assert.equal(out.verified_visual_asset_count,6,'global reviewed pool must retain six unique assets');
assert.equal(out.verified_visual_claim_count,3,'global reviewed pool must cover three grounded visual groups');
assert(out.verified_claims.every(x=>x.direct_assets.length===2),'fixture should expose two directly reviewed assets per grounded claim while keeping binding global');
assert.equal(new Set(out.verified_visual_assets.map(a=>`${a.provider}:${a.provider_asset_id}`)).size,6);
assert.deepEqual(out.verified_claims[0].evidence_ids,['S1']);
const beta=out.verified_claims.find(x=>x.source_claim_id==='C2');
assert(beta.direct_assets.some(a=>a.metadata.origin_claim_id==='C1'),'an image retrieved for another hypothesis may support an existing grounded claim');
assert(beta.direct_assets.some(a=>a.metadata.origin_claim_id==='C2'));
for(const change of [{supported_claim_id:'C999'},{supported_claim_id:''},{relevant:false}]){
 const bad=structuredClone(verdicts);Object.assign(bad[0],change);
 assert.throws(()=>run(bad),/global reviewed visual inventory/,'invalid global grounding cannot pad the reviewer-approved global visual pool');
}
const request=new Function('$json',code('Build Review Inventory Candidate Images Request'))({input:[]}).json.model_request;
assert(request.response_schema.properties.verdicts.items.required.includes('supported_claim_id'));
assert(!request.response_schema.properties.verdicts.items.required.includes('supported_claim'),'reviewer must bind to an existing claim id rather than inventing a freeform fact');
console.log('INVENTORY_OBSERVED_CLAIM_CONTRACT_PASS');

assert.equal(run([...verdicts].reverse()).verified_visual_claim_count,3,'flat IDs must preserve grounded visual bindings regardless of retrieval group or response order');
for(const [entries,error] of [
 [verdicts.slice(1),/incomplete verdicts/],
 [[...verdicts,verdicts[0]],/duplicate review_id/],
 [[...verdicts,{review_id:'unknown'}],/unknown review_id/]
])assert.throws(()=>run(entries),error);

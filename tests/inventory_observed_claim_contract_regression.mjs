import assert from 'node:assert/strict';
import fs from 'node:fs';
const w=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json'))[0];
const code=name=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const mk=(n,hash,title)=>({candidate_id:`asset-${n}`,provider:'wikimedia',provider_asset_id:`asset-${n}`,asset_identity:`wikimedia:asset-${n}`,preview_urls:[`https://example.com/${n}.jpg`],download_url:`https://example.com/${n}-full.jpg`,target_anchor_pass:true,visual_hash:hash,title,description:title,license:'CC BY'});
const research=[{id:'S1',snippet:'Research supports visible component alpha.'},{id:'S2',snippet:'Research supports visible component beta.'},{id:'S3',snippet:'Research supports visible component gamma.'}];
const claims=[
 {claim_number:1,claim_id:'C1',claim:'Origin hypothesis one.',visual_target:'Origin target one.',evidence_ids:['S1'],research_rows:research,fingerprinted_candidates:[mk(1,'0'.repeat(64),'Visible component beta'),mk(2,'3'.repeat(64),'Visible component gamma')]},
 {claim_number:2,claim_id:'C2',claim:'Origin hypothesis two.',visual_target:'Origin target two.',evidence_ids:['S2'],research_rows:research,fingerprinted_candidates:[mk(3,'f'.repeat(64),'Unusable component')]},
 {claim_number:3,claim_id:'C3',claim:'Origin hypothesis three.',visual_target:'Origin target three.',evidence_ids:['S3'],research_rows:research,fingerprinted_candidates:[mk(4,'a'.repeat(64),'Visible component alpha')]}
];
const base={target_duration_seconds:15,canonical_subject:'Example subject',user_intent:'Explain the subject',research_rows:research};
const baseLookup=name=>name==='Validate Candidate Claims'?{first:()=>({json:base})}:null;
const batches=new Function('$input','$',code('Prepare Inventory Review Batches'))({all:()=>claims.map(json=>({json}))},baseLookup).map(x=>x.json);
const inputText=batches[0].visual_review_request.input.filter(x=>x.type==='text').map(x=>x.text).join('\n');
assert.match(inputText,/retrieval hypotheses only/);
assert.match(inputText,/FULL RESEARCH CORPUS/);
assert.match(inputText,/S1: Research supports visible component alpha/);
assert.match(inputText,/S2: Research supports visible component beta/,'every discovery bucket must expose the global research corpus');
const decisions=[
 {claim_number:1,verdicts:[
  {review_id:'C1-I1',relevant:true,visible_description:'Visible component beta',supported_claim:'Research-supported fact about beta.',supported_evidence_ids:['S2']},
  {review_id:'C1-I2',relevant:true,visible_description:'Visible component gamma',supported_claim:'Research-supported fact about gamma.',supported_evidence_ids:['S3']}
 ]},
 {claim_number:2,verdicts:[{review_id:'C2-I1',relevant:false,visible_description:'Unusable component',supported_claim:'',supported_evidence_ids:[]}]},
 {claim_number:3,verdicts:[{review_id:'C3-I1',relevant:true,visible_description:'Visible component alpha',supported_claim:'Research-supported fact about alpha.',supported_evidence_ids:['S1']}]}
];
const lookup=name=>name==='Prepare Inventory Review Batches'?{all:()=>batches.map(json=>({json}))}:name==='Validate Candidate Claims'?{first:()=>({json:base})}:null;
const run=ds=>new Function('$input','$',code('Select Verified Claim Inventory'))({all:()=>[{json:{text:JSON.stringify({claims:ds})}}]},lookup)[0].json;
const out=run(decisions);
assert.equal(out.verified_claim_count,3,'global observed pool can reserve multiple valid observations from one discovery hypothesis');
assert.deepEqual(out.verified_claims.map(x=>x.claim_id),['C1','C2','C3'],'observed facts receive fresh stable story identities');
assert.equal(out.verified_claims[0].origin_claim_id,'C1');
assert.deepEqual(out.verified_claims[0].evidence_ids,['S2'],'an image may bind to globally supported evidence outside its discovery hypothesis');
assert.equal(out.verified_claims.filter(x=>x.origin_claim_id==='C1').length,2,'one discovery bucket is not limited to one final observed fact');
assert(out.verified_claims.some(x=>x.origin_claim_id==='C3'));
for(const change of [{supported_evidence_ids:['S999']},{supported_claim:''},{supported_evidence_ids:[]},{relevant:false}]){
 const bad=structuredClone(decisions);Object.assign(bad[0].verdicts[0],change);
 assert.throws(()=>run(bad),/verified visual inventory 2\/3/,'invalid global grounding cannot reserve an asset');
}
const request=new Function('$json',code('Build Review Inventory Candidate Images Request'))({input:[]}).json.model_request;
assert(request.response_schema.properties.claims.items.properties.verdicts.items.required.includes('supported_evidence_ids'));
console.log('INVENTORY_OBSERVED_CLAIM_CONTRACT_PASS');

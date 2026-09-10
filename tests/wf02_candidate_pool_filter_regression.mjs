import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));const w=Array.isArray(raw)?raw[0]:raw;const validate=w.nodes.find(n=>n.name==='Validate Candidate Claims').parameters.jsCode;
const assets=[
 {inventory_id:'V1',preclaim_visual_form:'photo',preclaim_visible_description:'View of a ship inside concrete walls of a Panama Canal lock chamber.',title:'Panama Canal lock ship',description:'ship lock chamber',categories:'Panama Canal'},
 {inventory_id:'V2',preclaim_visual_form:'photo',preclaim_visible_description:'View of concrete walls and a narrow water channel in the Panama Canal lock system.',title:'Panama Canal water channel',description:'concrete walls water channel',categories:'Panama Canal'},
 {inventory_id:'V3',preclaim_visual_form:'illustration',preclaim_visible_description:'Historical illustration of large miter lock gates in a wall.',title:'Panama Canal miter gates',description:'miter gates lock wall',categories:'Panama Canal'},
 {inventory_id:'V4',preclaim_visual_form:'photo',preclaim_visible_description:'Electric mule locomotive on tracks beside a Panama Canal lock wall.',title:'Panama Canal mule locomotive',description:'electric locomotive tracks',categories:'Panama Canal'},
 {inventory_id:'V5',preclaim_visual_form:'photo',preclaim_visible_description:'Bulk carrier inside a large concrete Panama Canal lock chamber.',title:'Panama Canal bulk carrier',description:'bulk carrier lock chamber',categories:'Panama Canal'},
 {inventory_id:'V6',preclaim_visual_form:'photo',preclaim_visible_description:'Two large ships inside partitioned Panama Canal lock chambers.',title:'Panama Canal ships',description:'two ships lock chambers',categories:'Panama Canal'},
];
const base={target_duration_seconds:15,user_intent:'Explain how the Panama Canal lock system works',canonical_subject:'Panama Canal lock system operation',research_rows:Array.from({length:6},(_,i)=>({id:`S${i+1}`})),candidate_claim_range:[6,6],available_visual_assets:assets};
const claims=[
 {claim_id:'C1',claim:'The Panama Canal uses lock chambers to lift ships above sea level.',evidence_ids:['S1'],editorial_role:'establish',visual_form:'photo',visual_target:'ship inside concrete lock chamber',search_query_en:'Panama Canal ship lock chamber',inventory_asset_ids:['V1']},
 {claim_id:'C2',claim:'Freshwater from surrounding lakes fills or drains the lock chambers using gravity.',evidence_ids:['S2'],editorial_role:'mechanism',visual_form:'photo',visual_target:'water channel between concrete walls',search_query_en:'Panama Canal gravity lock water',inventory_asset_ids:['V2']},
 {claim_id:'C3',claim:'Massive miter gates close to seal the lock chambers.',evidence_ids:['S3'],editorial_role:'detail',visual_form:'illustration',visual_target:'large miter gates in wall',search_query_en:'Panama Canal miter gates wall',inventory_asset_ids:['V3']},
 {claim_id:'C4',claim:'Electric mule locomotives guide ships through the locks.',evidence_ids:['S4'],editorial_role:'mechanism',visual_form:'photo',visual_target:'electric mule locomotive on tracks',search_query_en:'Panama Canal mule locomotive tracks',inventory_asset_ids:['V4']},
 {claim_id:'C5',claim:'The chambers use communicating vessels and valves to manage water flow.',evidence_ids:['S5'],editorial_role:'mechanism',visual_form:'photo',visual_target:'bulk carrier inside lock chamber',search_query_en:'Panama Canal communicating vessels',inventory_asset_ids:['V5']},
 {claim_id:'C6',claim:'The lock system allows ships to transit between ocean sides.',evidence_ids:['S6'],editorial_role:'result',visual_form:'photo',visual_target:'two large ships in lock chambers',search_query_en:'Panama Canal ships lock chambers',inventory_asset_ids:['V6']},
];
const run=rows=>new Function('$input','$',validate)({first:()=>({json:{text:JSON.stringify({claims:rows})}})},name=>{assert.equal(name,'Prepare Candidate Claims');return {first:()=>({json:base})}})[0].json;
const out=run(claims);
assert.deepEqual(out.candidate_claims.map(c=>c.claim_id),['C1','C3','C4','C6']);
assert.deepEqual(out.candidate_claims.map(c=>c.claim_number),[1,2,3,4]);
assert.deepEqual(out.candidate_claims.map(c=>c.source_claim_number),[1,3,4,6]);
assert.deepEqual(out.candidate_rejections.map(x=>x.source_claim_id),['C2','C5']);
assert(out.candidate_rejections.every(x=>/mechanism visual target is not claim-aligned/.test(x.reason)));
assert.equal(out.candidate_pool_contract.raw_count,6);assert.equal(out.candidate_pool_contract.accepted_count,4);assert.equal(out.candidate_pool_contract.minimum_accepted,4);
assert(!out.inventory_request.inventory_claims.some(c=>['C2','C5'].includes(c.claim_id)),'rejected hidden-mechanism hypotheses must not reach visual discovery');
const insufficient=structuredClone(claims);insufficient[5]={...insufficient[5],editorial_role:'mechanism',visual_target:'generic exterior facility view',inventory_asset_ids:['V6']};
assert.throws(()=>run(insufficient),/candidate claim pool only 3\/4 after deterministic rejection/,'candidate pool must still fail closed below downstream story capacity');
console.log('WF02_CANDIDATE_POOL_FILTER_REGRESSION_PASS');

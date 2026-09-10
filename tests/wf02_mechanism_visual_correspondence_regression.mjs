import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const w=Array.isArray(raw)?raw[0]:raw;const nodes=new Map(w.nodes.map(n=>[n.name,n]));
const validate=nodes.get('Validate Candidate Claims').parameters.jsCode;
const assets=[
 {inventory_id:'V1',preclaim_visual_form:'photo',preclaim_visible_description:'Hydroelectric dam exterior and reservoir',title:'dam reservoir',description:'dam exterior',categories:'hydroelectric'},
 {inventory_id:'V2',preclaim_visual_form:'diagram',preclaim_visible_description:'Cutaway diagram of turbine runner blades connected to a shaft',title:'turbine runner diagram',description:'runner blades shaft',categories:'hydroelectric turbine'},
 {inventory_id:'V3',preclaim_visual_form:'photo',preclaim_visible_description:'Governor linkage beside turbine machinery',title:'governor linkage',description:'governor linkage',categories:'hydroelectric'},
 {inventory_id:'V4',preclaim_visual_form:'photo',preclaim_visible_description:'Generator hall exterior machinery',title:'generator hall',description:'generator hall',categories:'hydroelectric'},
 {inventory_id:'V5',preclaim_visual_form:'photo',preclaim_visible_description:'Transmission lines leaving a power station',title:'transmission lines',description:'power lines',categories:'hydroelectric'},
 {inventory_id:'V6',preclaim_visual_form:'photo',preclaim_visible_description:'Reservoir water behind a concrete dam',title:'reservoir dam',description:'reservoir water',categories:'hydroelectric'},
];
const base={target_duration_seconds:15,user_intent:'Explain how the hydroelectric system works',canonical_subject:'Hydroelectric plant',research_rows:[{id:'S1'},{id:'S2'}],candidate_claim_range:[6,6],available_visual_assets:assets};
const roles=['hook','mechanism','detail','result','context','establish'];
const good=[
 {claim_id:'C1',claim:'The plant stores water behind the dam.',evidence_ids:['S1'],editorial_role:'hook',visual_form:'photo',visual_target:'concrete dam reservoir',search_query_en:'hydroelectric plant dam reservoir',inventory_asset_ids:['V1']},
 {claim_id:'C2',claim:'Water turns turbine runner blades connected to a shaft.',evidence_ids:['S1'],editorial_role:'mechanism',visual_form:'diagram',visual_target:'turbine runner blades diagram',search_query_en:'hydroelectric plant turbine runner diagram',inventory_asset_ids:['V2']},
 {claim_id:'C3',claim:'The governor linkage adjusts the turbine response.',evidence_ids:['S2'],editorial_role:'detail',visual_form:'photo',visual_target:'governor linkage machinery',search_query_en:'hydroelectric plant governor linkage',inventory_asset_ids:['V3']},
 {claim_id:'C4',claim:'The generator hall contains the conversion equipment.',evidence_ids:['S2'],editorial_role:'result',visual_form:'photo',visual_target:'generator hall machinery',search_query_en:'hydroelectric plant generator hall',inventory_asset_ids:['V4']},
 {claim_id:'C5',claim:'Power leaves the station through transmission lines.',evidence_ids:['S1'],editorial_role:'context',visual_form:'photo',visual_target:'power station transmission lines',search_query_en:'hydroelectric plant transmission lines',inventory_asset_ids:['V5']},
 {claim_id:'C6',claim:'The reservoir supplies stored water.',evidence_ids:['S2'],editorial_role:'establish',visual_form:'photo',visual_target:'reservoir concrete dam',search_query_en:'hydroelectric plant reservoir dam',inventory_asset_ids:['V6']},
];
const run=claims=>new Function('$input','$',validate)({first:()=>({json:{text:JSON.stringify({claims})}})},name=>{assert.equal(name,'Prepare Candidate Claims');return {first:()=>({json:base})}});
assert.equal(run(good)[0].json.candidate_claims.length,6);
const contextOnly=structuredClone(good);contextOnly[1]={...contextOnly[1],claim:'Water turns hidden turbine machinery and raises electrical output.',visual_form:'photo',visual_target:'dam exterior reservoir',search_query_en:'hydroelectric plant dam exterior',inventory_asset_ids:['V1']};
const contextFiltered=run(contextOnly)[0].json;assert(!contextFiltered.candidate_claims.some(c=>c.claim_id==='C2'),'generic context must not visually stand in for a hidden mechanism');assert.match(contextFiltered.candidate_rejections.find(x=>x.source_claim_id==='C2').reason,/mechanism visual target is not claim-aligned/);
const unreviewedAnchor=structuredClone(good);unreviewedAnchor[1]={...unreviewedAnchor[1],visual_target:'turbine wicket gate assembly',search_query_en:'hydroelectric plant wicket gate assembly',inventory_asset_ids:['V2']};
const unreviewedFiltered=run(unreviewedAnchor)[0].json;assert(!unreviewedFiltered.candidate_claims.some(c=>c.claim_id==='C2'));assert.match(unreviewedFiltered.candidate_rejections.find(x=>x.source_claim_id==='C2').reason,/mechanism visual target is not claim-aligned|not represented in cited real inventory|not present in pixel-reviewed inventory/);

const finalCode=nodes.get('Build Final Inventory Story').parameters.jsCode;
const mkAsset=(id,supported,desc)=>({asset_id:id,supported_claim_id:supported,supported_editorial_role:'mechanism',supported_visual_form:'photo',visible_description:desc,visual_hash:(id.charCodeAt(1)%16).toString(16).repeat(64),provider:'fixture',provider_asset_id:id});
const finalBase={user_intent:'Explain how the system works',story_unit_bounds:[3,3],target_duration_seconds:15,target_word_min:30,target_word_max:42,language_code:'en',job_id:'00000000-0000-0000-0000-000000000001',topic:'Example',canonical_subject:'Example system',topic_resolution:{},required_claim_ids:['C2'],research_rows:[{id:'S1',title:'one',url:'https://example.invalid/1',snippet:'one'},{id:'S2',title:'two',url:'https://example.invalid/2',snippet:'two'}],verified_claims:[
 {claim_id:'C1',claim:'A chamber receives the input.',evidence_ids:['S1'],editorial_role:'hook',visual_form:'photo',visual_target:'input chamber'},
 {claim_id:'C2',claim:'A turbine runner transfers force to the shaft.',evidence_ids:['S1','S2'],editorial_role:'mechanism',visual_form:'photo',visual_target:'turbine runner shaft'},
 {claim_id:'C3',claim:'The output leaves the machine.',evidence_ids:['S2'],editorial_role:'result',visual_form:'photo',visual_target:'output machine'},
],verified_visual_assets:[mkAsset('A1','C1','input chamber'),mkAsset('A2','C3','general machine context'),mkAsset('A3','C3','shaft housing context'),mkAsset('A4','C1','facility overview'),mkAsset('A5','C3','output machine'),mkAsset('A6','C3','output line')]};
const model={units:[
 {claim_id:'C1',narration:'The chamber receives the input before the process begins.',shot_plan:[{asset_id:'A1',shot_intent:'notice the input chamber'},{asset_id:'A2',shot_intent:'notice the surrounding machine'}]},
 {claim_id:'C2',narration:'The turbine runner transfers force directly into the rotating shaft.',shot_plan:[{asset_id:'A3',shot_intent:'notice the shaft housing'},{asset_id:'A4',shot_intent:'notice the facility context'}]},
 {claim_id:'C3',narration:'The converted output then leaves the machine through its line.',shot_plan:[{asset_id:'A5',shot_intent:'notice the output machine'},{asset_id:'A6',shot_intent:'notice the output line'}]},
]};
const runFinal=base=>new Function('$input','$',finalCode)({first:()=>({json:{text:JSON.stringify(model),model:'fixture'}})},name=>{assert.equal(name,'Prepare Inventory Grounded Story');return {first:()=>({json:base})}});
assert.throws(()=>runFinal(finalBase),/lacks a direct reviewer-bound mechanism visual/);
const direct=structuredClone(finalBase);direct.verified_visual_assets.find(a=>a.asset_id==='A3').supported_claim_id='C2';assert.equal(runFinal(direct)[0].json.story_package.units.length,3);
assert.match(nodes.get('Prepare Candidate Claims').parameters.jsCode,/SCREEN EXPLAINABILITY IS BINDING/);
assert.match(nodes.get('Prepare Inventory Grounded Story').parameters.jsCode,/never substitute a generic subject\/context image/);
assert.doesNotMatch(nodes.get('Prepare Inventory Grounded Story').parameters.jsCode,/do not omit that essential grounded mechanism because no literal diagram exists/);
console.log('WF02_MECHANISM_VISUAL_CORRESPONDENCE_REGRESSION_PASS');

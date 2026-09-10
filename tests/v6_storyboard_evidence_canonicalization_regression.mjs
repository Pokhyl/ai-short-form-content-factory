import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map(n=>[n.name,n]));
const build=by.get('Build Storyboard Director Request').parameters.jsCode;
assert.match(build,/storyboard_response_schema/);
assert.match(build,/model_request:\{prompt:x\.storyboard_prompt,response_format:'json'\}/);
assert.doesNotMatch(build,/model_request:\{prompt:x\.storyboard_prompt,response_format:'json',response_schema/);
const code=by.get('Validate Storyboard').parameters.jsCode;
assert.match(code,/rawFacts/);
assert.match(code,/const facts=rawFacts\.slice\(0,3\)/);
assert.match(code,/rawDf/);
assert.match(code,/df=rawDf\.slice\(0,3\)/);
const base={scene_bounds:[3,5],research_rows:[1,2,3,4].map(i=>({id:`S${i}`})),user_intent:'Explain why the sky is blue',topic:'Why is the sky blue?',job_id:'00000000-0000-4000-8000-000000000001'};
const diagram=(id,facts)=>({shot_id:id,representation:'diagram',must_show:['sunlight','air molecules'],must_not_show:[],search_query_en:'',communication_goal:'Explain scattering clearly',crop_policy:'not_applicable',diagram_spec:{shot_id:id,grounded_fact_ids:facts,archetype:'flow',entities:[{id:'a',label:'Sunlight',role:'input',phase:0},{id:'b',label:'Scattered blue light',role:'result',phase:1}],relations:[{from:'a',to:'b',kind:'transforms',phase:1}]}});
const external=(id)=>({shot_id:id,representation:'context_media',must_show:['blue daytime sky'],must_not_show:[],search_query_en:'blue daytime sky vertical',communication_goal:'Establish the visible blue sky',crop_policy:'portrait_required',diagram_spec:null});
const payload={scenes:[
 {scene_id:'S1',purpose:'hook',grounded_fact_ids:['S1'],narration_intent:'Show the familiar blue daytime sky',shots:[external('S1A')]},
 {scene_id:'S2',purpose:'explain',grounded_fact_ids:['S1','S2','S3','S4'],narration_intent:'Explain that shorter blue wavelengths scatter more',shots:[diagram('S2A',['S1','S2','S3','S4'])]},
 {scene_id:'S3',purpose:'close',grounded_fact_ids:['S2'],narration_intent:'Connect stronger blue scattering to what viewers see',shots:[diagram('S3A',['S2'])]}
]};
const $input={first:()=>({json:{provider_exhausted:false,text:JSON.stringify(payload),model:'poolside/laguna-s-2.1:free',provider:'kilo-storyboard'}})};
const $=(name)=>{if(name!=='Prepare Storyboard Director')throw new Error(`unexpected node ${name}`);return {first:()=>({json:base})};};
const out=new Function('$input','$',code)($input,$)[0].json;
assert.deepEqual(out.storyboard_scenes[1].grounded_fact_ids,['S1','S2','S3']);
assert.deepEqual(out.storyboard_scenes[1].shots[0].diagram_spec.grounded_fact_ids,['S1','S2','S3']);
assert.equal(out.external_shots.length,1);
console.log('V6_STORYBOARD_EVIDENCE_CANONICALIZATION_REGRESSION_PASS');

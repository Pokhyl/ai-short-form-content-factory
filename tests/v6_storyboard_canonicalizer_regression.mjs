import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;
const code=wf.nodes.find(n=>n.name==='Validate Storyboard').parameters.jsCode;
const base={topic:'why sky blue',user_intent:'why process',scene_bounds:[3,5],research_rows:[{id:'S1'},{id:'S2'}]};
const response={provider_exhausted:false,model:'cohere/north-mini-code:free',provider:'kilo-storyboard',text:JSON.stringify({scenes:[
 {scene_id:'S1',purpose:'hook',grounded_fact_ids:['S1'],narration_intent:'Show the real sky first',shots:[{shot_id:'S1A',representation:'context_media',must_show:'blue sky',must_not_show:'night sky',search_query_en:'clear blue sky',communication_goal:'Viewer sees a blue sky',crop_policy:'portrait_required',diagram_spec:null}]},
 {scene_id:'S2',purpose:'explain',grounded_fact_ids:['S1','S2'],narration_intent:'Explain the scattering process',shots:[{shot_id:'S2A',representation:'diagram',must_show:'light scatters',must_not_show:'wrong mechanism',search_query_en:'',communication_goal:'Viewer understands the mechanism',crop_policy:'not_applicable',diagram_spec:{shot_id:'S2A',grounded_fact_ids:['S1','S2'],archetype:'flow',short_title:'Scattering',entities:[{id:'sun',label:'Sun',role:'source',shape:'circle'},{id:'air',label:'Air',role:'process',shape:'box'},{id:'blue',label:'Blue',role:'output',shape:'arrow'}],relations:[{from:'sun',to:'air',kind:'enters'},{from:'air',to:'blue',kind:'scatters'},{from:'blue',to:'viewer',kind:'reaches'}]}}]},
 {scene_id:'S3',purpose:'close',grounded_fact_ids:['S2'],narration_intent:'Return to the real sky',shots:[{shot_id:'S3A',representation:'context_media',must_show:['blue daytime sky'],must_not_show:[],search_query_en:'blue daytime sky',communication_goal:'Viewer connects explanation to reality',crop_policy:'portrait_required',diagram_spec:null}]}
]})};
const fn=new Function('$input','$',code);
const out=fn({first:()=>({json:response})},()=>({first:()=>({json:base})}));
const data=out[0].json;
assert.deepEqual(data.storyboard_scenes[0].shots[0].must_show,['blue sky']);
assert.deepEqual(data.storyboard_scenes[0].shots[0].must_not_show,['night sky']);
const d=data.storyboard_scenes[1].shots[0].diagram_spec;
assert.equal(d.entities.find(e=>e.id==='sun').role,'input');
assert.equal(d.entities.find(e=>e.id==='blue').shape,'pill');
assert.equal(d.relations.length,2);
assert.equal(d.relations[0].kind,'flow');
assert.equal(d.relations[1].kind,'emits');
assert.equal(d.title,'Scattering');
console.log('V6_STORYBOARD_CANONICALIZER_REGRESSION_PASS');

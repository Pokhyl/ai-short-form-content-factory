import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateDiagramSpec,compileDiagramSpec} from '../services/media-worker/src/diagram-compiler.mjs';
const spec={shot_id:'S2A',grounded_fact_ids:['S7','S8'],archetype:'split',title:'Rayleigh',entities:[
{id:'e1',label:'Sunlight',role:'input',shape:'circle',lane:'top',order:1,phase:0},
{id:'e2',label:'Blue light',role:'input',shape:'pill',lane:'left',order:2,phase:1},
{id:'e3',label:'Red light',role:'input',shape:'pill',lane:'left',order:3,phase:1},
{id:'e4',label:'Atmosphere',role:'process',shape:'box',lane:'center',order:4,phase:2},
{id:'e5',label:'Scattered blue',role:'output',shape:'circle',lane:'right',order:5,phase:3},
{id:'e6',label:'Direct red',role:'output',shape:'circle',lane:'right',order:6,phase:3},
{id:'e7',label:'Eye',role:'subject',shape:'circle',lane:'right',order:7,phase:4}],relations:[
{from:'e1',to:'e2',kind:'splits',phase:1},{from:'e1',to:'e3',kind:'splits',phase:1},{from:'e2',to:'e4',kind:'flow',phase:2},{from:'e3',to:'e4',kind:'flow',phase:2},{from:'e4',to:'e5',kind:'emits',phase:3},{from:'e4',to:'e6',kind:'flow',phase:3},{from:'e5',to:'e7',kind:'flow',phase:4},{from:'e6',to:'e7',kind:'flow',phase:4}]};
const v=validateDiagramSpec(spec,{expectedShotId:'S2A',allowedFactIds:['S7','S8']});
assert.equal(v.entities.filter(e=>e.role==='input').length,1);
assert.equal(v.entities.find(e=>e.id==='e2').role,'process');
assert.equal(v.entities.find(e=>e.id==='e3').role,'process');
assert.equal(v.entities.find(e=>e.id==='e7').role,'result');
assert.equal(v.entities.find(e=>e.id==='e1').lane,'center');
assert.doesNotThrow(()=>compileDiagramSpec(spec,4,{expectedShotId:'S2A',allowedFactIds:['S7','S8']}));
const wfSpec=structuredClone(spec);wfSpec.relations.find(r=>r.from==='e2'&&r.to==='e4').kind='flows';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const code=wf.nodes.find(n=>n.name==='Validate Storyboard').parameters.jsCode;
const base={scene_bounds:[3,5],research_rows:[{id:'S7'},{id:'S8'},{id:'S9'}],user_intent:'Explain why',topic:'Why sky blue'};
const payload={scenes:[
{scene_id:'S1',purpose:'establish',grounded_fact_ids:['S9'],narration_intent:'Show the visible blue sky',shots:[{shot_id:'S1A',representation:'context_media',must_show:['blue sky'],must_not_show:[],search_query_en:'blue sky daytime vertical',communication_goal:'Viewer sees the real blue sky',crop_policy:'portrait_required',diagram_spec:null}]},
{scene_id:'S2',purpose:'explain',grounded_fact_ids:['S7','S8'],narration_intent:'Explain wavelength dependent scattering',shots:[{shot_id:'S2A',representation:'diagram',must_show:['sunlight','blue waves','red waves','atmosphere','scattered blue','direct red'],must_not_show:['dust','ocean reflection','night','fake'],search_query_en:'',communication_goal:'Viewer sees why blue scatters more',crop_policy:'not_applicable',diagram_spec:wfSpec}]},
{scene_id:'S3',purpose:'close',grounded_fact_ids:['S9'],narration_intent:'Reconnect explanation to the sky',shots:[{shot_id:'S3A',representation:'context_media',must_show:['person looking up','blue sky'],must_not_show:[],search_query_en:'person looking up blue sky vertical',communication_goal:'Viewer reconnects the mechanism to reality',crop_policy:'portrait_required',diagram_spec:null}]}
]};
const out=new Function('$input','$',code)({first:()=>({json:{provider_exhausted:false,text:JSON.stringify(payload),model:'x',provider:'x'}})},()=>({first:()=>({json:base})}))[0].json;
const shot=out.storyboard_scenes[1].shots[0];
assert.equal(shot.must_show.length,5);
assert.equal(shot.must_not_show.length,4);
assert.equal(shot.diagram_spec.entities.filter(e=>e.role==='input').length,1);
assert.equal(shot.diagram_spec.entities.find(e=>e.id==='e2').role,'process');
assert.equal(shot.diagram_spec.entities.find(e=>e.id==='e7').role,'result');
assert.equal(shot.diagram_spec.relations.find(r=>r.from==='e2'&&r.to==='e4').kind,'flow');
console.log('V6_STORYBOARD_BOUNDARY_CANONICALIZATION_PASS');

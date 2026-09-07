import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map(n=>[n.name,n]));
assert(by.has('Build Exact Story Unit Timings'));
for(const oldName of ['Prepare Beat Timings','Final Narration Needs Visual Rebind','Prepare Final Visual Rebind','Rebind Visual Queries To Final Beats','Apply Final Visual Rebind']) assert(!by.has(oldName),`${oldName} must be retired`);
const code=by.get('Build Exact Story Unit Timings').parameters.jsCode;
assert(!/BEATS_BY_DURATION|15:6|30:10|45:14|60:18/u.test(code),'exact timing must not use fixed beat counts');
const story={version:'inventory-first-story-v1',units:[
 {unit_id:'U1',claim_id:'C1',narration:'Alpha beta.',evidence_ids:['S1'],asset_id:'A1'},
 {unit_id:'U2',claim_id:'C2',narration:'Gamma 26 meters delta.',evidence_ids:['S2'],asset_id:'A2'},
 {unit_id:'U3',claim_id:'C3',narration:'Zeta eta.',evidence_ids:['S3'],asset_id:'A3'},
],assets:[{asset_id:'A1'},{asset_id:'A2'},{asset_id:'A3'}]};
const job={job_id:'11111111-1111-4111-8111-111111111111',topic:'x',fact_primary_title:'X',language_code:'en',target_duration_seconds:15,story_package:story,script_text:story.units.map(u=>u.narration).join(' '),script_fit_passes:0};
const words=[
 ['Alpha',0.2,0.5],['beta.',0.55,1.0],['Gamma',1.4,1.7],['26 meters',1.75,2.2],['delta.',2.25,2.6],['Zeta',3.0,3.3],['eta.',3.35,3.9],
].map(([text,start_seconds,end_seconds])=>({text,start_seconds,end_seconds}));
const stored={...job,voiceover_path:'jobs/x.wav',duration_seconds:4.5,provider:'microsoft_edge_readaloud',model:'edge_neural',voice:'en-US-AndrewNeural',word_timing_path:'jobs/x.words.json',word_timing:{version:'provider-word-timing-v1',duration_seconds:4.5,words}};
const $=name=>{assert.equal(name,'Require Eligible Voiceover Job');return {first:()=>({json:job})}};
const out=new Function('$input','$',code)({first:()=>({json:stored})},$)[0].json;
assert.equal(out.unit_timings.length,3);
assert.deepEqual(out.unit_timings.map(x=>x.story_unit_id),['U1','U2','U3']);
assert.deepEqual(out.unit_timings.map(x=>x.asset_id),['A1','A2','A3']);
assert.equal(out.unit_timings[0].beat_start_seconds,0);
assert.equal(out.unit_timings[0].beat_end_seconds,1.2);
assert.equal(out.unit_timings[1].beat_end_seconds,2.8);
assert.equal(out.unit_timings[2].beat_end_seconds,4.5);
assert.deepEqual(out.unit_timings[1].narration_support_evidence_ids,['S2']);
const persist=by.get('Persist Voiceover Result').parameters.query;
assert.match(persist,/story_unit_id/);
assert.match(persist,/claim_id/);
assert.match(persist,/asset_id/);
assert.match(persist,/jsonb_array_length\(i\.story_package->'units'\)/);
console.log('WF03_STORY_UNIT_TIMING_REGRESSION_PASS');

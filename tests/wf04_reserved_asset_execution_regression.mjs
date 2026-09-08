import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map(n=>[n.name,n]));
for(const name of ['Expand Reserved Story Assets','Download Reserved Visual','Store Reserved Visual','Validate Stored Reserved Visual','Fingerprint Stored Reserved Visual','Verify Reserved Visual Identity','Persist Reserved Visual','Collect Persisted Reserved Visuals','Verify Reserved Visual Completion','Require Reserved Visual Completion']) assert(by.has(name),`missing ${name}`);
for(const old of ['Fetch Canonical Media','Build Deterministic Visual Plans','Rank Eligible Visuals','Prepare Multimodal Visual Review','Review Actual Candidate Images','Detect Global No-Repeat Conflict','Fetch Conflict Recovery Candidates','Choose Visual Assignment']) assert(!by.has(old),`${old} must not remain in post-freeze critical path`);
const a=(asset_id,provider,provider_asset_id,hash,letter)=>({asset_id,provider,provider_asset_id,candidate_id:`${provider}:${provider_asset_id}`,download_url:`https://example.invalid/${letter}.jpg`,source_url:`https://example.invalid/${letter}`,media_kind:'photo',visual_hash:hash,visual_cluster_key:`preview:${letter}`,visible_description:`${letter} visible`,metadata:{}});
const a1=a('A1','wikimedia','p1','0'.repeat(64),'a'),a2=a('A2','pexels','p2','3'.repeat(64),'b'),a3=a('A3','wikimedia','p3','f'.repeat(64),'c'),a4=a('A4','pexels','p4','c'.repeat(64),'d');
const story={version:'inventory-first-story-v1',editorial_contract_version:'shot-intent-v1',units:[
 {unit_id:'U1',claim_id:'C1',narration:'One fact.',evidence_ids:['S1'],editorial_role:'hook',visual_form:'photo',asset_id:'A1',asset_ids:['A1','A2'],visual_target:'first target',visible_description:'first visible',shot_plan:[{asset_id:'A1',shot_intent:'Notice the first verified subject'},{asset_id:'A2',shot_intent:'Notice the second verified subject'}]},
 {unit_id:'U2',claim_id:'C2',narration:'Second fact.',evidence_ids:['S2'],editorial_role:'mechanism',visual_form:'diagram',asset_id:'A3',asset_ids:['A3','A4'],visual_target:'second target',visible_description:'second visible',shot_plan:[{asset_id:'A3',shot_intent:'Notice the mechanism overview'},{asset_id:'A4',shot_intent:'Notice the mechanism detail'}]},
],assets:[
 {...a1,claim_id:'C1',visual_target:'first target',shot_assets:[a1,a2]},
 {...a3,claim_id:'C2',visual_target:'second target',shot_assets:[a3,a4]},
]};
const job={job_id:'11111111-1111-4111-8111-111111111111',topic:'x',fact_primary_title:'X',story_package:story,scenes:[
 {scene_id:'s1',scene_number:1,narration:'One fact.',narration_support_evidence_ids:['S1'],beat_start_seconds:0,beat_end_seconds:2,duration_seconds:2},
 {scene_id:'s2',scene_number:2,narration:'Second fact.',narration_support_evidence_ids:['S2'],beat_start_seconds:2,beat_end_seconds:4,duration_seconds:2},
]};
const expand=by.get('Expand Reserved Story Assets').parameters.jsCode;
const $=name=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:job})}};
const rows=new Function('$input','$',expand)({first:()=>({json:{ready_to_run:true}})},$);
assert.equal(rows.length,2);
assert.deepEqual(rows.map(x=>x.json.provider_asset_id),['p1','p3']);
assert.deepEqual(rows.map(x=>x.json.planned_shot_count),[1,1]);
assert.deepEqual(rows.map(x=>x.json.visual_target),['first target','second target']);assert.deepEqual(rows.map(x=>x.json.shot_intent),['Notice the first verified subject','Notice the mechanism overview']);assert.deepEqual(rows.map(x=>x.json.editorial_role),['hook','mechanism']);
const verify=by.get('Verify Reserved Visual Identity').parameters.jsCode;
const reserved={...rows[0].json,visual_path:'jobs/11111111-1111-4111-8111-111111111111/visuals/shot-01.jpg',stored_media_type:'image'};
const dollar=name=>{assert.equal(name,'Validate Stored Reserved Visual');return {item:{json:reserved}}};
const ok=new Function('$json','$',verify)({visual_hash:'0'.repeat(64)},dollar).json;
assert.equal(ok.preview_to_stored_hamming,0);
assert.throws(()=>new Function('$json','$',verify)({visual_hash:'f'.repeat(64)},dollar),/identity diverged/);
assert.equal(by.get('Fingerprint Stored Reserved Visual').parameters.url,'http://media-worker:3001/visual/fingerprint-stored');
const persist=by.get('Persist Reserved Visual').parameters.query;
assert.match(persist,/INSERT INTO public\.visual_segments/);
assert.match(persist,/INSERT INTO public\.visual_shots/);
assert.match(persist,/1\.0/);
const complete=by.get('Verify Reserved Visual Completion').parameters.query;
assert.match(complete,/post_freeze_search_used','false|post_freeze_search_used/);
console.log('WF04_RESERVED_ASSET_EXECUTION_REGRESSION_PASS');

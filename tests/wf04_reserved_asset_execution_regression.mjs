import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map(n=>[n.name,n]));
for(const name of ['Expand Reserved Story Assets','Download Reserved Visual','Store Reserved Visual','Validate Stored Reserved Visual','Fingerprint Stored Reserved Visual','Verify Reserved Visual Identity','Persist Reserved Visual','Collect Persisted Reserved Visuals','Verify Reserved Visual Completion','Require Reserved Visual Completion']) assert(by.has(name),`missing ${name}`);
for(const old of ['Fetch Canonical Media','Build Deterministic Visual Plans','Rank Eligible Visuals','Prepare Multimodal Visual Review','Review Actual Candidate Images','Detect Global No-Repeat Conflict','Fetch Conflict Recovery Candidates','Choose Visual Assignment']) assert(!by.has(old),`${old} must not remain in post-freeze critical path`);
const story={version:'inventory-first-story-v1',units:[
 {unit_id:'U1',claim_id:'C1',narration:'One fact.',evidence_ids:['S1'],asset_id:'A1',visual_target:'first target',visible_description:'first visible'},
 {unit_id:'U2',claim_id:'C2',narration:'Second fact.',evidence_ids:['S2'],asset_id:'A2',visual_target:'second target',visible_description:'second visible'},
],assets:[
 {asset_id:'A1',provider:'wikimedia',provider_asset_id:'p1',candidate_id:'wikimedia:p1',download_url:'https://example.invalid/a.jpg',source_url:'https://example.invalid/a',media_kind:'photo',visual_hash:'0'.repeat(64),visual_cluster_key:'preview:a',metadata:{}},
 {asset_id:'A2',provider:'pexels',provider_asset_id:'p2',candidate_id:'pexels:p2',download_url:'https://example.invalid/b.jpg',source_url:'https://example.invalid/b',media_kind:'photo',visual_hash:'f'.repeat(64),visual_cluster_key:'preview:b',metadata:{}},
]};
const job={job_id:'11111111-1111-4111-8111-111111111111',topic:'x',fact_primary_title:'X',story_package:story,scenes:[
 {scene_id:'s1',scene_number:1,narration:'One fact.',narration_support_evidence_ids:['S1'],beat_start_seconds:0,beat_end_seconds:2,duration_seconds:2},
 {scene_id:'s2',scene_number:2,narration:'Second fact.',narration_support_evidence_ids:['S2'],beat_start_seconds:2,beat_end_seconds:4,duration_seconds:2},
]};
const expand=by.get('Expand Reserved Story Assets').parameters.jsCode;
const $=name=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:job})}};
const rows=new Function('$input','$',expand)({first:()=>({json:{ready_to_run:true}})},$);
assert.equal(rows.length,2);
assert.deepEqual(rows.map(x=>x.json.provider_asset_id),['p1','p2']);
assert.deepEqual(rows.map(x=>x.json.visual_target),['first target','second target']);
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

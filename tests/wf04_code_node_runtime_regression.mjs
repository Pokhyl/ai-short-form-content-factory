import fs from 'node:fs';
import assert from 'node:assert/strict';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const prep=wf.nodes.find(n=>n.name==='Prepare Canonical Media Request');
const planner=wf.nodes.find(n=>n.name==='Build Deterministic Visual Plans');
assert(prep?.parameters?.jsCode&&planner?.parameters?.jsCode);
const context={job_id:'11111111-1111-4111-8111-111111111111',fact_source_language:'en',fact_primary_title:'Refrigerator',voiceover_duration_seconds:4,
evidence:[{evidence_id:'E1',evidence_text:'A refrigerator keeps an insulated compartment cold.'},{evidence_id:'E2',evidence_text:'A refrigeration system transfers heat to the room.'}],
script_support:[{evidence_id:'E1',text:'A refrigerator keeps an insulated compartment cold.'},{evidence_id:'E2',text:'A refrigeration system transfers heat to the room.'}],
scenes:[{scene_number:1,narration:'A refrigerator keeps an insulated compartment cold.',narration_support_evidence_ids:['E1'],beat_start_seconds:0,beat_end_seconds:2,duration_seconds:2},{scene_number:2,narration:'A refrigeration system transfers heat to the room.',narration_support_evidence_ids:['E2'],beat_start_seconds:2,beat_end_seconds:4,duration_seconds:2}]};
const lookup=(name)=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:context})};};
const prepared=new Function('$input','$',prep.parameters.jsCode)({first:()=>({json:{ready_to_run:true}})},lookup)[0].json;
assert.equal(prepared.discovery_request.canonical_source.title,'Refrigerator');
assert.equal(prepared.discovery_request.timed_beats.length,2);
const candidates=[
{candidate_id:'wikimedia:fridge',provider:'wikimedia',provider_asset_id:'fridge',title:'File:Refrigerator interior.jpg',description:'Refrigerator cold compartment shelves',categories:'Refrigerators',media_kind:'photo',preview_url:'https://example.invalid/w.jpg',download_url:'https://example.invalid/w.jpg',metadata:{retrieval_source:'commons_search'}},
{candidate_id:'pixabay:fridge',provider:'pixabay',provider_asset_id:'fridge-stock',title:'refrigerator kitchen appliance',description:'open refrigerator cold food compartment',categories:'',media_kind:'photo',preview_url:'https://example.invalid/p.jpg',download_url:'https://example.invalid/p.jpg',metadata:{retrieval_source:'pixabay_search'}},
{candidate_id:'pexels:fridge',provider:'pexels',provider_asset_id:'fridge-video',title:'refrigerator cooling appliance',description:'video of an open refrigerator',categories:'',media_kind:'video',preview_url:'https://example.invalid/v.jpg',download_url:'https://example.invalid/v.mp4',metadata:{retrieval_source:'pexels_search'}},
{candidate_id:'pixabay:beach',provider:'pixabay',provider_asset_id:'beach',title:'sunny beach',description:'ocean sand palm trees',categories:'',media_kind:'photo',preview_url:'https://example.invalid/b.jpg',download_url:'https://example.invalid/b.jpg',metadata:{retrieval_source:'pixabay_search'}}];
const discovery={canonical_source:{language:'en',title:'Refrigerator',english_title:'Refrigerator'},provider_errors:[],segmentation_version:'visual-segmentation-v1',visual_segments:[
{segment_number:1,first_scene_number:1,last_scene_number:1,start_seconds:0,end_seconds:2,duration_seconds:2,narration:context.scenes[0].narration,support_evidence_ids:['E1'],search_terms:['refrigerator compartment'],planned_shot_count:1,candidates},
{segment_number:2,first_scene_number:2,last_scene_number:2,start_seconds:2,end_seconds:4,duration_seconds:2,narration:context.scenes[1].narration,support_evidence_ids:['E2'],search_terms:['refrigeration heat'],planned_shot_count:1,candidates}]};
const $=(name)=>{if(name==='Require Eligible Visual Job')return {first:()=>({json:context})};throw new Error(`Unexpected ${name}`)};
const out=new Function('$input','$',planner.parameters.jsCode)({first:()=>({json:discovery})},$)[0].json;
assert.equal(out.plans.length,2);assert.equal(out.visual_segment_count,2);assert.equal(out.planned_shot_count,2);
for(const p of out.plans){assert.equal(p.visual_lane,'reference');assert(p.segment_number>0);assert(Array.isArray(p.support_evidence_ids)&&p.support_evidence_ids.length);assert(p.candidate_pool.some(c=>c.provider==='wikimedia'));assert(p.candidate_pool.some(c=>c.provider==='pixabay'));assert(p.candidate_pool.some(c=>c.provider==='pexels'));assert(!p.candidate_pool.some(c=>c.candidate_id==='pixabay:beach'));}
console.log('WF04_CODE_NODE_RUNTIME_V3_PASS',out.plans.map(p=>p.segment_number));

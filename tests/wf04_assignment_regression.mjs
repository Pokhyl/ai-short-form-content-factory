import fs from 'node:fs';import assert from 'node:assert/strict';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const node=wf.nodes.find(n=>n.name==='Choose Visual Assignment');assert(node?.parameters?.jsCode);const run=new Function('$input',node.parameters.jsCode);
const H={A:'0'.repeat(64),B:'f'.repeat(64),C:'a'.repeat(64),D:'5'.repeat(64),E:'3'.repeat(64)};const c=(id,u)=>({candidate_id:id,media_kind:'photo',visual_hash:H[id],selection_utility:u,local_rank_score:u,local_siglip_rank:1});
const rows=[
 {segment_number:1,start_seconds:0,end_seconds:4,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('A',.99)]},
 {segment_number:2,start_seconds:4,end_seconds:8,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('B',.99)]},
 {segment_number:3,start_seconds:8,end_seconds:12,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('A',.99),c('C',.5)]},
 {segment_number:4,start_seconds:12,end_seconds:16,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('C',.99)]},
 {segment_number:5,start_seconds:16,end_seconds:20,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('D',.99)]},
 {segment_number:6,start_seconds:20,end_seconds:24,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('E',.99)]},
];
const out=run({all:()=>rows.map(json=>({json}))}).map(x=>x.json);assert.equal(out.length,6);assert.deepEqual(out.map(x=>x.shot_number),[1,2,3,4,5,6]);assert(out.every(x=>x.segment_shot_number===1));assert.equal(out[0].candidate_id,'A');assert.equal(out[2].candidate_id,'A','non-adjacent truthful asset reuse should remain available when video-level perceptual limits allow it');assert.equal(new Set(out.map(x=>x.candidate_id)).size,5);assert.equal(out[0].visual_quality_pre_render.all_assets_unique,false);assert.equal(out[0].visual_quality_pre_render.asset_reuse_count,1);assert(out.every(x=>x.selection_method==='semantic_segment_siglip_shot_beam_v3'));assert(out.every(x=>x.visual_quality_pre_render?.pass===true));
const impossible=[
 {segment_number:1,start_seconds:0,end_seconds:4,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('A',.9)]},
 {segment_number:2,start_seconds:4,end_seconds:8,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('A',.9)]},
 {segment_number:3,start_seconds:8,end_seconds:12,duration_seconds:4,planned_shot_count:1,ranked_candidates:[c('B',.9)]},
];assert.throws(()=>run({all:()=>impossible.map(json=>({json}))}),/No valid semantic visual shot assignment/);
console.log('WF04_ASSIGNMENT_V3_PASS',out.map(x=>`${x.shot_number}:${x.candidate_id}:${x.visual_cluster_key}`));

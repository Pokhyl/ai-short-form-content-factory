import fs from 'node:fs';import assert from 'node:assert/strict';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const node=wf.nodes.find(n=>n.name==='Choose Visual Assignment');const run=new Function('$input',node.parameters.jsCode);
const H={a:'0'.repeat(64),b:'f'.repeat(64),c:'a'.repeat(64),a2:'1'+'0'.repeat(63),b2:'e'+'f'.repeat(63),c2:'b'+'a'.repeat(63),d:'5'.repeat(64)};const cand=(id,h,u=.8)=>({candidate_id:id,visual_hash:h,local_rank_score:u,selection_utility:u,media_kind:'photo'});
const rows=[
{segment_number:1,start_seconds:0,end_seconds:4,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('a1',H.a),cand('b1',H.b,.7)]},
{segment_number:2,start_seconds:4,end_seconds:8,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('b2',H.b2),cand('c1',H.c,.7)]},
{segment_number:3,start_seconds:8,end_seconds:12,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('a2',H.a2),cand('c2',H.c2,.7)]},
{segment_number:4,start_seconds:12,end_seconds:16,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('c3',H.c),cand('b3',H.b,.7),cand('d1',H.d,.6)]},
];
const out=run({all:()=>rows.map(json=>({json}))}).map(x=>x.json);const clusters=out.map(x=>x.visual_cluster_key);assert.equal(out.length,4);assert(new Set(clusters).size>=2);for(let i=1;i<clusters.length;i++)assert.notEqual(clusters[i],clusters[i-1]);assert(out[0].visual_quality_pre_render.max_visual_cluster_occurrence_count<=2);assert.equal(out[0].visual_quality_pre_render.version,'visual-segments-v3');
const fail=[{segment_number:1,start_seconds:0,end_seconds:4,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('a1',H.a)]},{segment_number:2,start_seconds:4,end_seconds:8,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('a2',H.a2)]},{segment_number:3,start_seconds:8,end_seconds:12,duration_seconds:4,planned_shot_count:1,ranked_candidates:[cand('d1',H.d)]}];assert.throws(()=>run({all:()=>fail.map(json=>({json}))}),/No valid semantic visual shot assignment/);
console.log('WF04_PERCEPTUAL_ASSIGNMENT_V3_PASS',clusters);

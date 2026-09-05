import fs from 'node:fs';
import assert from 'node:assert/strict';

const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const node=(name)=>wf.nodes.find(n=>n.name===name);
const detector=node('Detect Global No-Repeat Conflict');
const prepare=node('Prepare Conflict Recovery Search');
const merge=node('Merge Conflict Recovery Approval');
const choose=node('Choose Visual Assignment');
assert.ok(detector?.parameters?.jsCode);
assert.ok(prepare?.parameters?.jsCode);
assert.ok(merge?.parameters?.jsCode);
assert.ok(choose?.parameters?.jsCode);

const H={A:'0'.repeat(64),B:'f'.repeat(64),C:'a'.repeat(64),D:'5'.repeat(64),E:'3'.repeat(64)};
const c=(id,u=0.9)=>({
  candidate_id:id,provider:'fixture',provider_asset_id:id,media_kind:'photo',
  visual_hash:H[id],selection_utility:u,download_url:`https://example.test/${id}.jpg`,
  preview_urls:[`https://example.test/${id}.jpg`],
});
const base=(segment_number,start,end,ids)=>({
  job_id:'fixture-job',segment_id:`segment-${segment_number}`,segment_number,
  start_seconds:start,end_seconds:end,duration_seconds:end-start,planned_shot_count:2,
  canonical_subject:'fixture subject',visual_target:`exact target ${segment_number}`,
  narration:`narration ${segment_number}`,support_evidence_ids:['S1'],
  visual_reviewed_candidate_ids:ids.map(id=>`reviewed:${id}`),
  ranked_candidates:ids.map(id=>c(id)),
});
const runDetector=new Function('$input',detector.parameters.jsCode);

const conflict=[
  base(1,0,4,['A','B']),
  base(2,4,8,['B','C']),
];
const detected=runDetector({all:()=>conflict.map(json=>({json}))}).map(x=>x.json);
assert.equal(detected.length,2);
assert.ok(detected.every(x=>x.global_assignment_recovery_required===true));
assert.deepEqual(detected[0].global_conflict_segment_numbers,[1,2]);
assert.equal(detected[0].global_assignment_matching_count,3);
assert.equal(detected[0].global_assignment_slot_count,4);

const feasible=[
  base(1,0,4,['A','B']),
  base(2,4,8,['C','D']),
];
const feasibleOut=runDetector({all:()=>feasible.map(json=>({json}))}).map(x=>x.json);
assert.ok(feasibleOut.every(x=>x.global_assignment_recovery_required===false));
assert.deepEqual(feasibleOut[0].global_conflict_segment_numbers,[]);
assert.equal(feasibleOut[0].global_assignment_matching_count,4);

const runPrepare=new Function('$input',prepare.parameters.jsCode);
const recoveryRequests=runPrepare({all:()=>detected.map(json=>({json}))}).map(x=>x.json);
assert.equal(recoveryRequests.length,2);
for(const row of recoveryRequests){
  assert.equal(row.conflict_recovery_request.visual_target,row.visual_target);
  const excluded=new Set(row.conflict_recovery_request.exclude_candidate_ids);
  for(const id of row.visual_reviewed_candidate_ids)assert.ok(excluded.has(id));
  for(const id of row.ranked_candidates.map(c=>c.candidate_id))assert.ok(excluded.has(id));
  assert.equal(row.global_conflict_recovery_round,1);
}

const prepared=[{
  job_id:'fixture-job',batch_number:1,batch_count:1,
  recovery_segments:[
    {...detected[0],recovery_review_candidates:[c('E')]},
    {...detected[1],recovery_review_candidates:[c('D')]},
  ],
}];
const responses=[{
  text:JSON.stringify({segments:[
    {segment_number:1,selected_candidate_ids:[],reasons:{}},
    {segment_number:2,selected_candidate_ids:['D'],reasons:{D:'exact visible match'}},
  ]}),
  model:'fixture-vision',
}];
const runMerge=new Function('$input','$',merge.parameters.jsCode);
const $merge=(name)=>{
  if(name==='Prepare Conflict Recovery Review')return {all:()=>prepared.map(json=>({json}))};
  if(name==='Detect Global No-Repeat Conflict')return {all:()=>detected.map(json=>({json}))};
  throw new Error(`unexpected node ${name}`);
};
const merged=runMerge({all:()=>responses.map(json=>({json}))},$merge).map(x=>x.json);
assert.equal(merged[1].global_conflict_recovery_added_count,1);
assert.ok(merged[1].ranked_candidates.some(x=>x.candidate_id==='D'));
assert.ok(!merged[0].ranked_candidates.some(x=>x.candidate_id==='E'),'unapproved recovery image must never enter the assignment pool');

const runChoose=new Function('$input','$',choose.parameters.jsCode);
const $choose=(name)=>{
  if(name==='Require Visual Plans')return {first:()=>({json:{visual_segment_count:2}})};
  throw new Error(`unexpected node ${name}`);
};
const assigned=runChoose({all:()=>merged.map(json=>({json}))},$choose).map(x=>x.json);
assert.equal(assigned.length,4);
assert.equal(new Set(assigned.map(x=>x.candidate_id)).size,4,'recovery must restore a globally unique assignment');
assert.ok(assigned.every(x=>x.visual_quality_pre_render?.all_assets_unique===true));
assert.ok(assigned.every(x=>x.selection_method==='multimodal_exact_beat_shot_beam_v4'));

const conn=wf.connections;
const dests=(name,branch=0)=>(conn[name]?.main?.[branch]??[]).map(x=>x.node);
assert.ok(dests('Require Multimodal Visual Selection').includes('Detect Global No-Repeat Conflict'));
assert.ok(dests('Global No-Repeat Recovery Required?',0).includes('Prepare Conflict Recovery Search'));
assert.ok(dests('Global No-Repeat Recovery Required?',1).includes('Choose Visual Assignment'));
assert.ok(dests('Merge Conflict Recovery Approval').includes('Choose Visual Assignment'));
assert.equal(node('Fetch Conflict Recovery Candidates')?.parameters?.url,'http://media-worker:3001/visual/recover-conflict');
assert.match(prepare.parameters.jsCode,/exclude_candidate_ids/);
assert.match(merge.parameters.jsCode,/filter\(id=>own\.has\(id\)\)/);
assert.equal(node('Global No-Repeat Recovery Required?')?.parameters?.conditions?.conditions?.[0]?.leftValue,'={{ $json.global_assignment_recovery_required }}');
for(const name of ['Fetch Conflict Recovery Candidates','Fingerprint Conflict Recovery','Inline Conflict Recovery Images','Review Conflict Recovery Images']){
  assert.match(String(node(name)?.parameters?.jsonBody??''),/^=\{\{/);
}
console.log('WF04_GLOBAL_NO_REPEAT_RECOVERY_REGRESSION_PASS');

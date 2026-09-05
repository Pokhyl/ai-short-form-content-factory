import assert from 'node:assert/strict';
import fs from 'node:fs';

const wf02 = JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json', import.meta.url), 'utf8'))[0];
const wf04 = JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF04-visual-sourcing.json', import.meta.url), 'utf8'))[0];
const n2 = new Map(wf02.nodes.map(node => [node.name, node]));
const n4 = new Map(wf04.nodes.map(node => [node.name, node]));

assert.match(n2.get('Persist Grounded AI Narration').parameters.query, /visual_search_queries_en/);
assert.match(n4.get('Load Visual Context').parameters.query, /visual_search_queries_en/);
assert.match(n4.get('Require Eligible Visual Job').parameters.jsCode, /Grounded English visual query inventory is missing/);
assert.match(n4.get('Prepare Canonical Media Request').parameters.jsCode, /visual_queries_en:j\.visual_search_queries_en/);

const expandCode = n4.get('Expand Rank Items').parameters.jsCode;
assert.match(expandCode, /plan\.visual_target\|\|plan\.canonical_subject/);
assert.doesNotMatch(expandCode, /plan\.visual_description/);

const attachCode = n4.get('Attach Rank Results').parameters.jsCode;
assert.doesNotMatch(attachCode, /MIN_VISUAL_RELEVANCE|metadata_overlap.*0\.018/);
assert.match(attachCode, /Local visual fingerprinting/);
assert(n4.has('Prepare Multimodal Visual Review'));
assert(n4.has('Inline Candidate Images'));
assert(n4.has('Review Actual Candidate Images'));
assert(n4.has('Require Multimodal Visual Selection'));
const prepareCode=n4.get('Prepare Multimodal Visual Review').parameters.jsCode;
const reviewCode=n4.get('Require Multimodal Visual Selection').parameters.jsCode;
assert.match(prepareCode, /Judge only visible content/);
assert.match(prepareCode, /Reject lexical coincidences/);
assert.match(prepareCode, /batchSize=6/);
assert.match(prepareCode, /input\.length>80/);
assert.match(prepareCode, /up to four IDs/);
assert.match(reviewCode, /selected_candidate_ids/);
assert.match(reviewCode, /Multimodal review batch set is incomplete/);
assert.match(reviewCode, /unreviewed fallback is forbidden/);
assert.doesNotMatch(reviewCode,/localFallback|segment-local ranked recovery candidate/);
assert.equal(n4.get('Prepare Multimodal Visual Review').parameters.mode,'runOnceForAllItems');
assert.equal(n4.get('Require Multimodal Visual Selection').parameters.mode,'runOnceForAllItems');
assert.equal(n4.get('Inline Candidate Images').parameters.url,'http://media-worker:3001/visual/inline-review-images');
assert.match(n4.get('Review Actual Candidate Images').parameters.jsonBody,/input: \$json\.input/);
assert.equal(wf04.connections['Inline Candidate Images'].main[1][0].node,'Prepare Visual Failure');
assert.equal(wf04.connections['Review Actual Candidate Images'].main[1][0].node,'Prepare Visual Failure');

const prepareReview=new Function('$input',prepareCode);
const longSegments=Array.from({length:18},(_,segmentIndex)=>({json:{
  job_id:'00000000-0000-4000-8000-000000000001',
  segment_number:segmentIndex+1,
  planned_shot_count:2,
  canonical_subject:'Wind turbine',
  visual_target:`target ${segmentIndex+1}`,
  narration:`narration ${segmentIndex+1}`,
  ranked_candidates:Array.from({length:10},(_,candidateIndex)=>({
    candidate_id:`photo:${segmentIndex+1}:${candidateIndex+1}`,
    media_kind:'photo',
    preview_url:`https://example.test/${segmentIndex+1}/${candidateIndex+1}.jpg`,
  })),
}}));
const preparedBatches=prepareReview({all:()=>longSegments});
assert.equal(preparedBatches.length,3,'18 final beats must be split into three bounded visual-review batches');
assert(preparedBatches.every(item=>item.json.visual_review_request.input.length<=80));
assert.deepEqual(preparedBatches.map(item=>item.json.batch_number),[1,2,3]);
assert(preparedBatches.every(item=>item.json.batch_count===3));
const preparedSegments=preparedBatches.flatMap(item=>item.json.segments);
assert.equal(preparedSegments.length,18);
assert.deepEqual(preparedSegments.map(s=>s.segment_number),Array.from({length:18},(_,i)=>i+1));
assert(preparedSegments.every(s=>s.visual_review_candidates.length===6),'six-segment batches must expose six reviewed alternatives per exact beat');

const attach = new Function('$json', '$', attachCode);
const context = {
  segment_number: 1,
  candidate_pool: [
    { candidate_id: 'photo:good', media_kind: 'photo', metadata_overlap: 2, target_metadata_overlap: 1, representation_preference_rank: 0 },
    { candidate_id: 'photo:garbage', media_kind: 'photo', metadata_overlap: 5, target_metadata_overlap: 0, representation_preference_rank: 0 },
    { candidate_id: 'video:weak', media_kind: 'video', metadata_overlap: 5, target_metadata_overlap: 1, representation_preference_rank: 3 },
  ],
};
const $attach = () => ({ item: { json: context } });
const hash = character => character.repeat(64);
const accepted = attach({ model: 'fixture', dtype: 'q4', ranked: [
  { candidate_id: 'photo:good', score: 0.4, visual_hash: hash('a') },
  { candidate_id: 'photo:garbage', score: 0.000000001, visual_hash: hash('b') },
  { candidate_id: 'video:weak', score: 0.2, visual_hash: hash('c') },
] }, $attach).json.ranked_candidates;
assert.deepEqual(accepted.map(item => item.candidate_id), ['photo:good', 'photo:garbage', 'video:weak']);

const review=new Function('$input','$',reviewCode);
const reviewContext={job_id:'00000000-0000-4000-8000-000000000001',batch_number:1,batch_count:1,segments:[{...context,planned_shot_count:1,visual_review_candidates:accepted}]};
const review$=name=>{assert.equal(name,'Prepare Multimodal Visual Review');return {all:()=>[{json:reviewContext}]}};
const selected=review({all:()=>[{json:{text:JSON.stringify({segments:[{segment_number:1,selected_candidate_ids:['photo:good'],reasons:{'photo:good':'visible exact subject'}}]}),model:'fixture'}}]},review$)[0].json.ranked_candidates;
assert.deepEqual(selected.map(item=>item.candidate_id),['photo:good']);
assert.equal(selected[0].multimodal_reason,'visible exact subject');
assert.throws(()=>review({all:()=>[{json:{text:JSON.stringify({segments:[{segment_number:1,selected_candidate_ids:[]}]})}}]},review$),/approved 0\/1 relevant images/);

const twoShotContext={job_id:'00000000-0000-4000-8000-000000000001',batch_number:1,batch_count:1,segments:[{...context,planned_shot_count:2,visual_review_candidates:accepted}]};
const twoShot$=()=>({all:()=>[{json:twoShotContext}]});
const approvedTwo=review({all:()=>[{json:{text:JSON.stringify({segments:[{segment_number:1,selected_candidate_ids:['photo:good','photo:garbage'],reasons:{'photo:good':'visible exact subject','photo:garbage':'second visibly relevant fixture'}}]})}}]},twoShot$)[0].json.ranked_candidates;
assert.deepEqual(approvedTwo.map(item=>item.candidate_id),['photo:good','photo:garbage']);
assert.equal(new Set(approvedTwo.map(item=>item.candidate_id)).size,2);

const multiPrepared=[
  {json:{job_id:'j',batch_number:1,batch_count:2,segments:[{...context,segment_number:1,planned_shot_count:1,visual_review_candidates:accepted}]}},
  {json:{job_id:'j',batch_number:2,batch_count:2,segments:[{...context,segment_number:2,planned_shot_count:1,visual_review_candidates:accepted.map(c=>({...c,candidate_id:c.candidate_id+':2'}))}]}},
];
const multiResponses=[
  {json:{model:'fixture-a',text:JSON.stringify({segments:[{segment_number:1,selected_candidate_ids:['photo:good'],reasons:{'photo:good':'one'}}]})}},
  {json:{model:'fixture-b',text:JSON.stringify({segments:[{segment_number:2,selected_candidate_ids:['photo:good:2'],reasons:{'photo:good:2':'two'}}]})}},
];
const multi$=()=>({all:()=>multiPrepared});
const multiOut=review({all:()=>multiResponses},multi$).map(x=>x.json);
assert.deepEqual(multiOut.map(x=>x.segment_number),[1,2]);
assert.deepEqual(multiOut.map(x=>x.visual_review_batch),[1,2]);
assert.deepEqual(multiOut.map(x=>x.ranked_candidates[0].candidate_id),['photo:good','photo:good:2']);

assert.match(n4.get('Choose Visual Assignment').parameters.jsCode, /assetCount>1\)continue/);
assert.throws(()=>review({all:()=>[{json:{text:'not-json'}}]},review$),/approved 0\/1 relevant images/);

for (const node of [...wf02.nodes, ...wf04.nodes].filter(node => node.type === 'n8n-nodes-base.code')) {
  new Function('$input', '$', node.parameters.jsCode);
}

console.log('WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS');

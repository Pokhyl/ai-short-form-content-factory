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
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /Judge only visible content/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /Reject lexical coincidences/);
assert.match(n4.get('Require Multimodal Visual Selection').parameters.jsCode, /selected_candidate_ids/);
assert.match(n4.get('Require Multimodal Visual Selection').parameters.jsCode, /topic_anchor_candidate_ids/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /topic anchors/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /Select 6-12 topic anchors/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /slice\(0,10\)/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /final timeline requires/);
assert.match(n4.get('Prepare Multimodal Visual Review').parameters.jsCode, /never repeat an ID/);
assert.equal(n4.get('Prepare Multimodal Visual Review').parameters.mode,'runOnceForAllItems');
assert.equal(n4.get('Require Multimodal Visual Selection').parameters.mode,'runOnceForAllItems');
assert.equal(n4.get('Inline Candidate Images').parameters.url,'http://media-worker:3001/visual/inline-review-images');
assert.match(n4.get('Review Actual Candidate Images').parameters.jsonBody,/input: \$json\.input/);

const attach = new Function('$json', '$', attachCode);
const context = {
  segment_number: 1,
  candidate_pool: [
    { candidate_id: 'photo:good', media_kind: 'photo', metadata_overlap: 2, target_metadata_overlap: 1, representation_preference_rank: 0 },
    { candidate_id: 'photo:garbage', media_kind: 'photo', metadata_overlap: 5, target_metadata_overlap: 0, representation_preference_rank: 0 },
    { candidate_id: 'video:weak', media_kind: 'video', metadata_overlap: 5, target_metadata_overlap: 1, representation_preference_rank: 3 },
  ],
};
const $ = () => ({ item: { json: context } });
const hash = character => character.repeat(64);
const accepted = attach({ model: 'fixture', dtype: 'q4', ranked: [
  { candidate_id: 'photo:good', score: 0.4, visual_hash: hash('a') },
  { candidate_id: 'photo:garbage', score: 0.000000001, visual_hash: hash('b') },
  { candidate_id: 'video:weak', score: 0.2, visual_hash: hash('c') },
] }, $).json.ranked_candidates;
assert.deepEqual(accepted.map(item => item.candidate_id), ['photo:good', 'photo:garbage', 'video:weak']);

const reviewCode=n4.get('Require Multimodal Visual Selection').parameters.jsCode;
const review=new Function('$json','$',reviewCode);
const reviewContext={segments:[{...context,planned_shot_count:1,visual_review_candidates:accepted}]};
const review$=name=>{assert.equal(name,'Prepare Multimodal Visual Review');return {first:()=>({json:reviewContext})}};
const selected=review({text:JSON.stringify({segments:[{segment_number:1,selected_candidate_ids:['photo:good'],reasons:{'photo:good':'visible exact subject'}}]}),model:'fixture'},review$)[0].json.ranked_candidates;
assert.deepEqual(selected.map(item=>item.candidate_id),['photo:good']);
const fallback=review({text:JSON.stringify({topic_anchor_candidate_ids:['photo:good'],segments:[{segment_number:1,selected_candidate_ids:[]}]})},review$)[0].json.ranked_candidates;
assert.equal(fallback.length,1);
assert.equal(fallback[0].candidate_id,'photo:good');
assert.match(fallback[0].multimodal_reason,/topic anchor/);
const twoShotContext={segments:[{...context,planned_shot_count:2,visual_review_candidates:accepted}]};
const twoShot$=()=>({first:()=>({json:twoShotContext})});
const expandedPool=review({text:JSON.stringify({topic_anchor_candidate_ids:['photo:good','photo:garbage','video:weak'],segments:[{segment_number:1,selected_candidate_ids:[]}]})},twoShot$)[0].json.ranked_candidates;
assert.equal(expandedPool.length,3,'assignment must receive more approved alternatives than the two required shots when available');
assert.equal(new Set(expandedPool.map(item=>item.candidate_id)).size,3);
assert.match(n4.get('Choose Visual Assignment').parameters.jsCode, /assetCount>1\)continue/);
assert.throws(()=>review({text:'not-json'},review$),/no relevant photographs/);

for (const node of [...wf02.nodes, ...wf04.nodes].filter(node => node.type === 'n8n-nodes-base.code')) {
  new Function('$input', '$', node.parameters.jsCode);
}

console.log('WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS');

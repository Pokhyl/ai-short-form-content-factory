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
assert.match(attachCode, /MIN_VISUAL_RELEVANCE=0\.01/);
assert.match(attachCode, /relevancePassed=rows\.filter/);
assert.match(attachCode, /no candidate above semantic relevance floor/);
assert.match(attachCode, /media_kind.*video.*bestStill/);

const attach = new Function('$json', '$', attachCode);
const context = {
  segment_number: 1,
  candidate_pool: [
    { candidate_id: 'photo:good', media_kind: 'photo', metadata_overlap: 2, representation_preference_rank: 0 },
    { candidate_id: 'photo:garbage', media_kind: 'photo', metadata_overlap: 5, representation_preference_rank: 0 },
    { candidate_id: 'video:weak', media_kind: 'video', metadata_overlap: 5, representation_preference_rank: 3 },
  ],
};
const $ = () => ({ item: { json: context } });
const hash = character => character.repeat(64);
const accepted = attach({ model: 'fixture', dtype: 'q4', ranked: [
  { candidate_id: 'photo:good', score: 0.4, visual_hash: hash('a') },
  { candidate_id: 'photo:garbage', score: 0.000001, visual_hash: hash('b') },
  { candidate_id: 'video:weak', score: 0.2, visual_hash: hash('c') },
] }, $).json.ranked_candidates;
assert.deepEqual(accepted.map(item => item.candidate_id), ['photo:good']);
assert.throws(() => attach({ model: 'fixture', dtype: 'q4', ranked: [
  { candidate_id: 'photo:good', score: 0.000001, visual_hash: hash('a') },
  { candidate_id: 'photo:garbage', score: 0.000002, visual_hash: hash('b') },
  { candidate_id: 'video:weak', score: 0.000003, visual_hash: hash('c') },
] }, $), /no candidate above semantic relevance floor/);

for (const node of [...wf02.nodes, ...wf04.nodes].filter(node => node.type === 'n8n-nodes-base.code')) {
  new Function('$input', '$', node.parameters.jsCode);
}

console.log('WF04_PHOTO_RELEVANCE_GATE_REGRESSION_PASS');

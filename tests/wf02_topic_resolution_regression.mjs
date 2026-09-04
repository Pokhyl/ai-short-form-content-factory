import assert from 'node:assert/strict';
import fs from 'node:fs';

const workflow = JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json', import.meta.url), 'utf8'))[0];
const nodes = new Map(workflow.nodes.map(node => [node.name, node]));
const required = [
  'Prepare Semantic Intent',
  'Resolve Topic Semantics',
  'Parse Semantic Intent',
  'Discover Candidate Evidence',
  'Build Evidence Comparison',
  'Resolve Topic From Evidence',
  'Validate Resolved Topic',
  'Research Resolved Subject',
  'Prepare Grounded Script Prompt',
];
for (const name of required) assert(nodes.has(name), `missing ${name}`);

const edge = (from, to) => workflow.connections[from]?.main?.[0]?.some(item => item.node === to);
for (let index = 0; index < required.length - 1; index++) {
  assert(edge(required[index], required[index + 1]), `missing edge ${required[index]} -> ${required[index + 1]}`);
}

const source = fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json', import.meta.url), 'utf8');
assert(!/Ходор|Hodor|Khodorkovsky/u.test(source), 'workflow contains a topic-specific name');
assert.match(source, /evidence-grounded-topic-resolution-v1/);
assert.match(nodes.get('Persist Grounded AI Narration').parameters.query, /topic_resolution/);
assert.match(nodes.get('Persist Grounded AI Narration').parameters.query, /reasoning_evidence_ids/);

for (const node of workflow.nodes.filter(node => node.type === 'n8n-nodes-base.code')) {
  new Function('$input', '$', node.parameters.jsCode);
}

const validate = new Function('$input', '$', nodes.get('Validate Resolved Topic').parameters.jsCode);
const matrix = [
  { raw: 'Ходор', language: 'ru', chosen: ['Hodor', 'fictional_character', 'Game of Thrones'], rejected: 'Mikhail Khodorkovsky' },
  { raw: 'why is the sky blue', language: 'ru', chosen: ['Rayleigh scattering', 'scientific_question', 'atmospheric optics'] },
  { raw: 'how does a refrigerator work', language: 'uk', chosen: ['Refrigerator', 'technical_question', 'vapor-compression refrigeration'] },
  { raw: 'почему извергаются вулканы', language: 'pl', chosen: ['Volcanic eruption', 'scientific_question', 'volcanology'] },
  { raw: 'Mercury', language: 'en', chosen: ['Mercury', 'planet', 'Solar System'], rejected: 'chemical element' },
  { raw: 'How do vaccines train the immune system?', language: 'en', chosen: ['Vaccination', 'medical_question', 'adaptive immune response'] },
  { raw: 'Apple', language: 'pl', chosen: ['Apple Inc.', 'company', 'consumer technology'], rejected: 'fruit' },
];

for (const test of matrix) {
  const alternatives = test.rejected
    ? [{ candidate_id: 'C2', canonical_name: test.rejected, subject_type: 'alternative', context: 'alternative context', interpretation: 'alternative meaning', discovery_query: `${test.rejected} facts` }]
    : [];
  const candidates = [
    { candidate_id: 'C1', canonical_name: test.chosen[0], subject_type: test.chosen[1], context: test.chosen[2], interpretation: `Meaning of ${test.raw}`, discovery_query: `${test.chosen[0]} ${test.chosen[2]}` },
    ...alternatives,
  ];
  const base = {
    job_id: '11111111-1111-4111-8111-111111111111',
    topic: test.raw,
    raw_topic: test.raw,
    language_code: test.language,
    target_duration_seconds: 30,
    topic_language: 'auto',
    topic_kind: test.chosen[1].includes('question') ? 'question' : 'entity',
    semantic_candidates: candidates,
    discovery_evidence: [
      { evidence_id: 'D-C1-1', candidate_id: 'C1', title: `${test.chosen[0]} reference`, snippet: `${test.chosen[0]} in ${test.chosen[2]}`, url: 'https://example.invalid/1' },
      { evidence_id: 'D-C1-2', candidate_id: 'C1', title: `${test.chosen[0]} overview`, snippet: `Independent overview of ${test.chosen[0]}`, url: 'https://example.invalid/2' },
    ],
  };
  const model = {
    text: JSON.stringify({
      selected_candidate_id: 'C1',
      resolved_subject: test.chosen[0],
      canonical_name: test.chosen[0],
      subject_type: test.chosen[1],
      context: test.chosen[2],
      user_intent: `Explain ${test.chosen[0]}`,
      research_query_en: `${test.chosen[0]} ${test.chosen[2]} facts`,
      confidence: 0.88,
      runner_up_candidate_id: alternatives.length ? 'C2' : null,
      score_margin: alternatives.length ? 0.42 : 0.8,
      reasoning_evidence_ids: ['D-C1-1', 'D-C1-2'],
      resolution_reason: 'Direct name and context evidence support this meaning.',
    }),
    model: 'fixture-model',
  };
  const $ = name => ({ first: () => ({ json: name === 'Build Evidence Comparison' ? base : {} }) });
  const [result] = validate({ first: () => ({ json: model }) }, $);
  assert.equal(result.json.topic_resolution.raw_topic, test.raw);
  assert.equal(result.json.topic_resolution.resolved_subject, test.chosen[0]);
  assert.equal(result.json.topic_resolution.subject_type, test.chosen[1]);
  assert.equal(result.json.language_code, test.language);
  if (test.rejected) assert.notEqual(result.json.canonical_subject, test.rejected);
}

console.log('WF02_TOPIC_RESOLUTION_REGRESSION_PASS', matrix.length);

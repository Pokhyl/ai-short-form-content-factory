import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const raw = JSON.parse(readFileSync('n8n/workflows/WF04-visual-sourcing.json', 'utf8'));
const workflow = Array.isArray(raw) ? raw[0] : raw;
const persist = workflow.nodes.find((node) => node.name === 'Persist Visual Result');
assert(persist?.parameters?.query, 'Persist Visual Result query is missing');

const query = persist.parameters.query;
assert.match(query, /RETURNING id,visual_segment_id/);
assert.match(
  query,
  /EXISTS\(SELECT 1 FROM inserted i WHERE i\.visual_segment_id=vs\.id\)/,
);
assert.match(
  query,
  /\(SELECT count\(\*\) FROM public\.visual_shots sh WHERE sh\.visual_segment_id=vs\.id\)\s*\+\(SELECT count\(\*\) FROM inserted i WHERE i\.visual_segment_id=vs\.id\)/,
);
assert.doesNotMatch(
  query,
  /WHERE vs\.id=s\.id AND \(SELECT count\(\*\) FROM public\.visual_shots sh WHERE sh\.visual_segment_id=vs\.id\)=s\.planned_shot_count/,
);

const replacement = persist.parameters.options?.queryReplacement ?? '';
assert.match(replacement, /\$json\.selection_score/);
assert.match(query, /EXISTS\(SELECT 1 FROM inserted\) AS persisted/);
assert.match(query, /EXISTS\(SELECT 1 FROM completed\) AS segment_completed/);

console.log('WF04_SEGMENT_COMPLETION_REGRESSION_PASS');

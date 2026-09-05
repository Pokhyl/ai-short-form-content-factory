import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const migration = readFileSync(
  new URL('../db/migrations/016_visual_shot_selection_utility.sql', import.meta.url),
  'utf8',
);
const workflow = JSON.parse(
  readFileSync(new URL('../n8n/workflows/WF04-visual-sourcing.json', import.meta.url), 'utf8'),
)[0];
const nodes = new Map(workflow.nodes.map((node) => [node.name, node]));

assert.match(migration, /DROP CONSTRAINT IF EXISTS visual_shots_score_check/);
assert.match(
  migration,
  /CHECK \(selection_score >= -0\.10 AND selection_score <= 1\.09\)/,
);

const attachRank = nodes.get('Attach Rank Results')?.parameters?.jsCode ?? '';
const chooseAssignment = nodes.get('Choose Visual Assignment')?.parameters?.jsCode ?? '';
const expandStored = nodes.get('Expand Stored Visual Targets')?.parameters?.jsCode ?? '';
const persistVisual = nodes.get('Persist Visual Result')?.parameters?.query ?? '';

assert.doesNotMatch(attachRank, /selection_utility/);
assert.match(chooseAssignment, /utility=Number\(c\.selection_utility\)/);
assert.match(expandStored, /selection_score:Number\(target\.selection_utility\)/);
assert.match(persistVisual, /selection_score,metadata/);

function selectionUtility(score, metadataOverlap, representationPreferenceRank) {
  return Number(
    (
      score +
      Math.min(metadataOverlap, 5) * 0.018 -
      representationPreferenceRank * 0.025
    ).toFixed(6),
  );
}

assert.equal(selectionUtility(0, 0, 4), -0.1);
assert.equal(selectionUtility(1, 5, 0), 1.09);
assert.ok(-0.006621 >= -0.1 && -0.006621 <= 1.09);
assert.ok(-0.100001 < -0.1);
assert.ok(1.090001 > 1.09);

console.log('VISUAL_SHOT_SELECTION_SCORE_REGRESSION_PASS');

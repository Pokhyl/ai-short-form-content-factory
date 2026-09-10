import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const w=Array.isArray(raw)?raw[0]:raw;
const by=new Map(w.nodes.map(n=>[n.name,n]));
for(const retired of ['Prepare Pre-Claim Review Batches','Inline Pre-Claim Candidate Images','Review Pre-Claim Visual Inventory','Select Pre-Claim Visual Inventory']) {
  assert.equal(by.has(retired),false,`retired mandatory visual-review node returned: ${retired}`);
}
assert.ok(by.has('Prepare Storyboard Director'));
assert.ok(by.has('Direct Storyboard'));
assert.ok(by.has('Freeze Storyboard Feasibility'));
const serialized=JSON.stringify(w).toLowerCase();
assert.equal(serialized.includes('inline-review-images'),false);
assert.equal(serialized.includes('visual fact reviewer'),false);
console.log('V6_VISUAL_REVIEW_PATH_RETIRED_PASS');

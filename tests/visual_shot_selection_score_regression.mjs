import assert from 'node:assert/strict';import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
assert(!by.has('Choose Visual Assignment'),'post-freeze semantic assignment must be retired');
const persist=by.get('Persist Reserved Visual').parameters.query;
assert.match(persist,/selection_score,metadata/);assert.match(persist,/1\.0/);
const verify=by.get('Verify Reserved Visual Identity').parameters.jsCode;assert.match(verify,/preview_to_stored_hamming/);
console.log('VISUAL_SHOT_SELECTION_SCORE_REGRESSION_PASS');

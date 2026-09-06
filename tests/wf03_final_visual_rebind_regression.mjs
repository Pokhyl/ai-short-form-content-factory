import assert from 'node:assert/strict';import fs from 'node:fs';
const one=p=>{const r=JSON.parse(fs.readFileSync(p,'utf8'));return Array.isArray(r)?r[0]:r};
const w3=one('n8n/workflows/WF03-natural-edge-voice.json'),w4=one('n8n/workflows/WF04-visual-sourcing.json');const n3=new Set(w3.nodes.map(n=>n.name)),n4=new Set(w4.nodes.map(n=>n.name));
for(const x of ['Final Narration Needs Visual Rebind','Prepare Final Visual Rebind','Rebind Visual Queries To Final Beats','Apply Final Visual Rebind'])assert(!n3.has(x),`${x} must be removed`);
assert(n4.has('Expand Reserved Story Assets'));assert(!n4.has('Fetch Canonical Media'));assert(!n4.has('Fetch Conflict Recovery Candidates'));
console.log('WF03_LATE_VISUAL_REBIND_RETIRED_REGRESSION_PASS');

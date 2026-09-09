import assert from 'node:assert/strict';import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw,by=new Map(wf.nodes.map(n=>[n.name,n]));
const code=by.get('Apply Duration Rewrite').parameters.jsCode;
assert.match(code,/model unavailable or invalid after bounded gateway recovery/);
assert(!/deterministicShorten|deterministic_overlength_fallback/u.test(code),'duration fallback must not truncate frozen story units');
assert.match(code,/changed frozen unit identity/);assert.match(code,/missing frozen grounded claim/);
console.log('WF03_DURATION_GATEWAY_FAIL_CLOSED_REGRESSION_PASS');

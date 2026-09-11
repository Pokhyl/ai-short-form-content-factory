import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/V6-model-gateway.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const by=new Map(wf.nodes.map(n=>[n.name,n]));
const build=by.get('Build Request').parameters.jsCode;
assert.match(build,/route==='storyboard'\?'inclusionai\/ling-3\.0-flash-sante:free'/);
assert.equal(by.get('Kilo Free Model').parameters.options.timeout,"={{ $json.route === 'storyboard' ? 65000 : 50000 }}");
console.log('V6_STORYBOARD_LING_ROUTE_PASS');

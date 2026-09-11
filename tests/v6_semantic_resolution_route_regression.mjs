import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const by=new Map(wf.nodes.map(n=>[n.name,n]));
assert.match(by.get('Resolve Topic Semantics').parameters.jsonBody,/route: \"semantic\"/);
assert.match(by.get('Resolve Topic Semantics').parameters.jsonBody,/response_format: \"json\"/);
assert.match(by.get('Resolve Topic From Evidence').parameters.jsonBody,/route: \"resolution\"/);
assert.match(by.get('Resolve Topic From Evidence').parameters.jsonBody,/response_format: \"json\"/);
console.log('V6_SEMANTIC_RESOLUTION_ROUTE_PASS');

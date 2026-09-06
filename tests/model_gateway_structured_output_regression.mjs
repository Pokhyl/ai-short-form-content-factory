import assert from 'node:assert/strict';import fs from 'node:fs';
const files=['n8n/workflows/WF02-plan-script-and-scenes.json','n8n/workflows/WF03-natural-edge-voice.json','n8n/workflows/WF04-visual-sourcing.json'];
let checked=0;
for(const file of files){const raw=JSON.parse(fs.readFileSync(file,'utf8')),wf=Array.isArray(raw)?raw[0]:raw;for(const n of wf.nodes){const body=String(n.parameters?.jsonBody??'');if(n.type==='n8n-nodes-base.httpRequest'&&String(n.parameters?.url??'').includes('v4-model-gateway')&&/input:\s*\$json\.input/u.test(body)){checked++;assert.match(body,/response_format:\s*'json'/,`${n.name} must request structured JSON`);assert.match(body,/response_schema/,`${n.name} must send a schema`);}}}
assert(checked>=1);console.log('MODEL_GATEWAY_STRUCTURED_OUTPUT_REGRESSION_PASS',checked);

import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/V6-model-gateway.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map((node)=>[node.name,node]));
assert.equal(wf.name,'V6 — Free-Only Text Model Gateway');
assert.equal(by.get('Webhook')?.parameters?.path,'v6-model-gateway');
assert.ok(Array.isArray(wf.shared)&&wf.shared.some((s)=>s.role==='workflow:owner'),'V6 gateway must preserve owner ACL');
const serialized=JSON.stringify(wf).toLowerCase();
for(const forbidden of ['gemini','generativelanguage.googleapis.com','google_gemini','openai/','anthropic/','stepfun/step-3.7-flash']) assert.equal(serialized.includes(forbidden),false,`V6 gateway contains forbidden provider marker: ${forbidden}`);
const build=by.get('Build Request')?.parameters?.jsCode??'';
assert.match(build,/nex-agi\/nex-n2\.5-pro:free/);
assert.match(build,/nvidia\/nemotron-3-super-120b-a12b:free/);
assert.match(build,/text-only/);
for(const nodeName of ['Nex Free Model','Nemotron Free Fallback']){
  assert.equal(by.get(nodeName)?.parameters?.url,'https://api.kilo.ai/api/gateway/chat/completions');
  assert.ok(Number(by.get(nodeName)?.parameters?.options?.timeout)<=90000,`${nodeName} timeout must stay bounded`);
}
const branches=wf.connections?.['Nex Succeeded?']?.main??[];
assert.equal(branches?.[0]?.[0]?.node,'Normalize Nex Success');
assert.equal(branches?.[1]?.[0]?.node,'Nemotron Free Fallback');
assert.equal(wf.connections?.['Normalize Nemotron Response']?.main?.[0]?.[0]?.node,'Respond');
const fallbackCode=by.get('Normalize Nemotron Response')?.parameters?.jsCode??'';
assert.match(fallbackCode,/provider_exhausted:!success/);
console.log('V6_FREE_ONLY_MODEL_GATEWAY_REGRESSION_PASS');

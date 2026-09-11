import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/V6-model-gateway.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const by=new Map(wf.nodes.map(n=>[n.name,n]));
const gate=by.get('Use Semantic Fallback?');assert.ok(gate);assert.match(JSON.stringify(gate.parameters),/free_model_success/);assert.match(JSON.stringify(gate.parameters),/route === 'semantic'/);
const build=by.get('Build Semantic Fallback Request');assert.match(build.parameters.jsCode,/cohere\/north-mini-code:free/);assert.match(build.parameters.jsCode,/max_tokens:4096/);
const http=by.get('Kilo Semantic Fallback');assert.equal(http.parameters.url,'https://api.kilo.ai/api/gateway/chat/completions');assert.equal(Number(http.parameters.options.timeout),30000);
const norm=by.get('Normalize Semantic Fallback');assert.match(norm.parameters.jsCode,/kilo-semantic-fallback/);assert.match(norm.parameters.jsCode,/provider_attempts/);assert.doesNotMatch(JSON.stringify(wf).toLowerCase(),/settimeout|sleep\(|gemini|openai\//);
assert.equal(wf.connections['Normalize Free Model Response'].main[0][0].node,'Use Semantic Fallback?');assert.equal(wf.connections['Use Semantic Fallback?'].main[0][0].node,'Build Semantic Fallback Request');assert.equal(wf.connections['Use Semantic Fallback?'].main[1][0].node,'Respond');assert.equal(wf.connections['Normalize Semantic Fallback'].main[0][0].node,'Respond');
console.log('V6_SEMANTIC_FREE_FAILOVER_PASS');

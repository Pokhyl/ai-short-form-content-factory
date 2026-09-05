import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';

const policy = JSON.parse(fs.readFileSync('config/production-dependency-policy.json','utf8'));
assert.equal(policy.baseline,'self_hosted_no_quota_ai');
assert.equal(policy.orchestrator,'n8n');
assert.equal(policy.hosted_ai_fallback_allowed,false);
assert.equal(policy.mandatory_model_provider,'ollama_self_hosted');

const files = new Map(policy.n8n_workflows.map((p)=>[p,fs.readFileSync(p,'utf8')]));
for (const [file,text] of files) {
  for (const host of policy.forbidden_required_ai_hosts) {
    assert(!text.includes(host),`${file} contains forbidden required hosted AI host ${host}`);
  }
}

const parseWorkflow=(p)=>{const d=JSON.parse(files.get(p));return Array.isArray(d)?d[0]:d;};
const gateway=parseWorkflow('n8n/workflows/V4-model-gateway.json');
const gatewayHttp=gateway.nodes.find((n)=>n.type==='n8n-nodes-base.httpRequest');
assert(gatewayHttp,'model gateway HTTP node missing');
assert.equal(gatewayHttp.parameters.url,policy.mandatory_model_endpoint);
assert(!gateway.nodes.some((n)=>/gemini|openai|anthropic|grok/i.test(n.name)),'hosted AI node remains in required model gateway');
assert(!gateway.nodes.some((n)=>n.type==='n8n-nodes-base.wait'),'required model gateway may not sleep for provider quotas');
assert(!gatewayHttp.retryOnFail,'required model gateway may not retry around hosted quota failures');
assert(!gatewayHttp.credentials,'required local model node must not retain hosted-provider credentials');

const wf03=parseWorkflow('n8n/workflows/WF03-natural-edge-voice.json');
const wf03Text=JSON.stringify(wf03);
assert(!/Gemini|google_gemini|v4-tts-gateway/i.test(wf03Text),'WF03 required TTS path still depends on Gemini');
assert(wf03.nodes.some((n)=>n.name==='Generate Edge Voiceover'),'WF03 Edge baseline node missing');
assert(!wf03.nodes.some((n)=>n.type==='n8n-nodes-base.wait'),'WF03 may not wait for hosted provider quota');

const wf04=parseWorkflow('n8n/workflows/WF04-visual-sourcing.json');
const review=wf04.nodes.find((n)=>n.name==='Review Actual Candidate Images');
assert(review,'WF04 actual-image review node missing');
assert.equal(review.parameters.url,'http://127.0.0.1:5678/webhook/v4-model-gateway');

console.log('PRODUCTION_DEPENDENCY_CONTRACT_REGRESSION_PASS');

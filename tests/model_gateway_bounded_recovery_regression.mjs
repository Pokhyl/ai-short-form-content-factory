import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const gateway=JSON.parse(fs.readFileSync(path.join(here,'../n8n/workflows/V4-model-gateway.json'),'utf8'))[0];
const node=gateway.nodes.find(n=>n.name==='Local Model Worker');
assert.ok(node,'self-hosted model worker node missing');
assert.equal(node.parameters.url,'http://model-worker:3002/generate');
assert.ok(!node.retryOnFail,'required local model path must not hide failures behind quota-style retries');
assert.ok(Number(node.parameters?.options?.timeout)<=160000,'local model request timeout must remain bounded');
assert.ok(!gateway.nodes.some(n=>n.type==='n8n-nodes-base.wait'),'model gateway must not contain provider quota waits');
assert.ok(!JSON.stringify(gateway).includes('generativelanguage.googleapis.com'));
assert.ok(!JSON.stringify(gateway).includes('gemini-3.1-flash-lite'));
for(const file of fs.readdirSync(path.join(here,'../n8n/workflows')).filter(x=>x.endsWith('.json'))){
  const full=path.join(here,'../n8n/workflows',file);
  let wf; try{const parsed=JSON.parse(fs.readFileSync(full,'utf8'));wf=Array.isArray(parsed)?parsed[0]:parsed}catch{continue}
  for(const n of wf.nodes??[]){
    if(String(n.parameters?.url??'').includes('v4-model-gateway')){
      assert.ok(Number(n.parameters?.options?.timeout)>=180000,`${file}/${n.name} caller timeout is shorter than the bounded local gateway budget`);
    }
  }
}
console.log('MODEL_GATEWAY_BOUNDED_RECOVERY_REGRESSION_PASS');

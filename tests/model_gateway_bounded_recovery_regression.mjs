import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const gateway=JSON.parse(fs.readFileSync(path.join(here,'../n8n/workflows/V4-model-gateway.json'),'utf8'))[0];
const node=gateway.nodes.find(n=>n.name==='Gemini');
assert.ok(node,'Gemini node missing');
assert.equal(node.retryOnFail,true,'model gateway must recover transient failures');
assert.equal(node.maxTries,2,'model gateway recovery must be bounded to one retry');
assert.equal(node.waitBetweenTries,60000,'model gateway retry interval must cover the observed free-tier minute window');
assert.ok(Number(node.parameters?.options?.timeout)<=90000,'each model request timeout must remain bounded');
for(const file of fs.readdirSync(path.join(here,'../n8n/workflows')).filter(x=>x.endsWith('.json'))){
  const full=path.join(here,'../n8n/workflows',file);
  let wf; try{wf=JSON.parse(fs.readFileSync(full,'utf8'))[0]}catch{continue}
  for(const n of wf.nodes??[]){
    if(String(n.parameters?.url??'').includes('v4-model-gateway')){
      assert.ok(Number(n.parameters?.options?.timeout)>=180000,`${file}/${n.name} caller timeout is too short for the bounded gateway retry`);
    }
  }
}
console.log('MODEL_GATEWAY_BOUNDED_RECOVERY_REGRESSION_PASS');

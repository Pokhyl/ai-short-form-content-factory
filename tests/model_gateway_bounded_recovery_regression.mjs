import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const gateway=JSON.parse(fs.readFileSync(path.join(here,'../n8n/workflows/V4-model-gateway.json'),'utf8'))[0];
const by=Object.fromEntries((gateway.nodes??[]).map(n=>[n.name,n]));
const kilo=by['Kilo Free Model'];
const gemini=by['Gemini'];
const build=by['Build Request'];
const decide=by['Kilo Succeeded?'];
assert.ok(kilo&&gemini&&build&&decide,'provider failover nodes missing');
assert.equal(kilo.parameters?.url,'https://api.kilo.ai/api/gateway/chat/completions');
assert.ok(String(build.parameters?.jsCode??'').includes('stepfun/step-3.7-flash:free'),'Kilo free model must be explicit');
assert.ok(String(build.parameters?.jsCode??'').includes("type:'image_url'"),'gateway must adapt inline review images to OpenAI-compatible vision input');
assert.ok(Number(kilo.parameters?.options?.timeout)<=90000,'Kilo request timeout must remain bounded');
assert.equal(kilo.retryOnFail,undefined,'quota recovery must use provider failover, not request retry sleeps');
assert.equal(gemini.retryOnFail,undefined,'Gemini quota recovery must use provider failover, not retry sleeps');
assert.ok(Number(gemini.parameters?.options?.timeout)<=90000,'Gemini request timeout must remain bounded');
assert.equal(String(kilo.onError),'continueRegularOutput','Kilo failure must be normalized for fallback');
assert.equal(String(gemini.onError),'continueRegularOutput','Gemini failure must be normalized and fail closed at the caller');
const branches=gateway.connections?.['Kilo Succeeded?']?.main??[];
assert.equal(branches?.[0]?.[0]?.node,'Normalize Kilo Success','Kilo success path must return immediately');
assert.equal(branches?.[1]?.[0]?.node,'Gemini','Kilo failure path must use independent Gemini fallback');
const source=JSON.stringify(gateway).toLowerCase();
assert.ok(!source.includes('ollama'),'model gateway must not contain Ollama architecture');
assert.ok(!source.includes('model-worker'),'model gateway must not contain a model-worker dependency');
for(const file of fs.readdirSync(path.join(here,'../n8n/workflows')).filter(x=>x.endsWith('.json'))){
  const full=path.join(here,'../n8n/workflows',file);
  let wf; try{wf=JSON.parse(fs.readFileSync(full,'utf8'))[0]}catch{continue}
  for(const n of wf.nodes??[]){
    if(String(n.parameters?.url??'').includes('v4-model-gateway')){
      assert.ok(Number(n.parameters?.options?.timeout)>=180000,`${file}/${n.name} caller timeout is too short for bounded provider failover`);
    }
  }
}
console.log('MODEL_GATEWAY_BOUNDED_PROVIDER_FAILOVER_REGRESSION_PASS');

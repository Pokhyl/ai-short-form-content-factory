import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=(f)=>{const r=JSON.parse(fs.readFileSync(f,'utf8'));return Array.isArray(r)?r[0]:r};
const w2=read('n8n/workflows/WF02-plan-script-and-scenes.json');
const n2=new Map(w2.nodes.map(n=>[n.name,n]));
for(const name of ['Draft Candidate Claims','Write Inventory Grounded Story']){
  const body=String(n2.get('Build '+name+' Request')?.parameters?.jsCode??'');
  assert.equal(n2.get(name).parameters.jsonBody,'={{ $json.model_request }}');
  assert.match(body,/response_format:\s*'json'/,`${name} must request JSON object output`);
  assert.match(body,/response_schema/,`${name} must provide response schema`);
}
const recovery=String(n2.get('Prepare Planner Failure')?.parameters?.jsCode??'');
assert.match(recovery,/Prepare Candidate Claims/,'planner failure must recover job_id from stable upstream claim context');
for(const [name,conn] of Object.entries(w2.connections??{})){
  const error=(conn?.main??[])[1]??[];
  if(error.some(x=>x.node==='Prepare Planner Failure')){
    assert.equal(n2.get(name)?.onError,'continueErrorOutput',`${name} must emit error output to planner failure handler`);
  }
}
const w3=read('n8n/workflows/WF03-natural-edge-voice.json');
const rewrite=w3.nodes.find(n=>n.name==='Rewrite Narration For Exact Duration');
assert.equal(rewrite.parameters.jsonBody,'={{ $json.model_request }}');
const body=w3.nodes.find(n=>n.name==='Build Rewrite Narration For Exact Duration Request').parameters.jsCode;
assert.match(body,/response_format:\s*'json'/);
assert.match(body,/response_schema/);
console.log('INVENTORY_MODEL_CONTRACT_AND_FAILURE_PERSISTENCE_REGRESSION_PASS');

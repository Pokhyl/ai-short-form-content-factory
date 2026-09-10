const fs=require('node:fs');
const assert=require('node:assert/strict');
const {Expression}=require('/usr/local/lib/node_modules/n8n/node_modules/n8n-workflow');
const evaluator=new Expression('UTC');
const fixture={exploration_prompt:'Exploration fixture',claim_prompt:'Candidate fixture',story_prompt:'Story fixture',rewrite_prompt:'Rewrite fixture',unit_order:['U1','U2','U3'],desired_word_target:18,min_unit_words:6,input:[{type:'text',text:'Review fixture'}]};
let checked=0;const checkedNames=[];
for(const file of fs.readdirSync('n8n/workflows').filter(f=>f.endsWith('.json'))){
 const raw=JSON.parse(fs.readFileSync('n8n/workflows/'+file,'utf8'));
 for(const w of Array.isArray(raw)?raw:[raw])for(const node of w.nodes){
  if(node.parameters?.jsonBody!=='={{ $json.model_request }}')continue;
  const builder=w.nodes.find(n=>n.name==='Build '+node.name+' Request');
  assert(builder,`Missing builder for ${node.name}`);
  const item=new Function('$json',builder.parameters.jsCode)(fixture).json;
  const resolved=evaluator.renderExpression(node.parameters.jsonBody.slice(1),{$json:item});
  assert.deepEqual(JSON.parse(JSON.stringify(resolved)),item.model_request);
  assert.equal(resolved.response_format,'json');
  assert.equal(resolved.response_schema.type,'object');
  assert(resolved.prompt||resolved.input);
  const direct=(w.connections[builder.name]?.main?.[0]||[]).some(e=>e.node===node.name);
  const serial=(w.connections[builder.name]?.main?.[0]||[]).some(e=>{const loop=w.nodes.find(n=>n.name===e.node);return loop?.type==='n8n-nodes-base.splitInBatches'&&loop.typeVersion===3&&Number(loop.parameters?.batchSize)===1&&(w.connections[loop.name]?.main?.[1]||[]).some(x=>x.node===node.name);});
  assert(direct||serial,`Structured call ${builder.name} does not reach ${node.name} directly or through a serial review loop`);
  // The compact schema literal reproduces the production defect on this engine.
  const broken='{{ {response_schema:'+JSON.stringify(resolved.response_schema)+'} }}';
  assert.throws(()=>evaluator.renderExpression(broken,{$json:fixture}),/invalid syntax/);
  checked++;checkedNames.push(node.name);
 }
}
const expectedStructuredCalls=['Draft Candidate Claims','Draft Visual Exploration','Review Pre-Claim Visual Inventory','Rewrite Narration For Exact Duration','Write Inventory Grounded Story'].sort();
assert.deepEqual(checkedNames.sort(),expectedStructuredCalls,'V6 must keep exactly the intended structured model calls; the retired second visual review must not return');
assert.equal(checked,5,'Every V6 structured call must be exercised');
console.log('MODEL_INVOCATION_CONTRACT_PASS',checked,checkedNames.join(','));

const wf04=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json'))[0];
const storeHeader=wf04.nodes.find(n=>n.name==='Store Reserved Visual').parameters.headerParameters.parameters.find(p=>p.name==='Content-Type').value;
for(const mime of ['image/jpeg','image/png','video/mp4'])assert.equal(evaluator.renderExpression(storeHeader.slice(1),{$binary:{data:{mimeType:mime}}}),mime);
console.log('RESERVED_VISUAL_BINARY_HEADER_CONTRACT_PASS');

// Run against the installed n8n component, without importing a workflow or
// making provider calls: node this-file.cjs /absolute/path/to/SplitInBatchesV3.node.js
const assert=require('node:assert/strict');
const {SplitInBatchesV3}=require(process.argv[2]);
(async()=>{
 const state={};let input=Array.from({length:5},(_,i)=>({json:{shot_key:`S${i+1}-A`},pairedItem:{item:i}}));
 let source={previousNode:'Build Gemini Vision Request',previousNodeOutput:0,previousNodeRun:0};
 const ctx={getInputData:()=>input,getContext:()=>state,getNodeParameter:name=>name==='batchSize'?1:{},getInputSourceData:()=>source};
 const execute=()=>SplitInBatchesV3.prototype.execute.call(ctx);
 let outputs=await execute();
 for(let i=0;i<5;i++){
  assert.equal(outputs[0].length,0);
  assert.equal(outputs[1].length,1);
  assert.equal(outputs[1][0].json.shot_key,`S${i+1}-A`);
  input=[{json:{...outputs[1][0].json,evaluations:[{vision_pass:true}]}}];
  source={previousNode:'Parse Gemini Vision Result',previousNodeOutput:0,previousNodeRun:i};
  outputs=await execute();
 }
 assert.equal(outputs[1].length,0);
 assert.deepEqual(outputs[0].map(x=>x.json.shot_key),['S1-A','S2-A','S3-A','S4-A','S5-A']);
 assert(outputs[0].every(x=>x.json.evaluations[0].vision_pass));
 assert.equal(state.done,true);
 console.log('Installed n8n splitInBatches v3: five single-scene iterations, exact completed collection PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});

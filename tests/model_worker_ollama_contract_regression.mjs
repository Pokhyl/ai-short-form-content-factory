import assert from 'node:assert/strict';
import { buildOllamaRequest, callOllama } from '../services/model-worker/src/ollama-adapter.mjs';

const text = buildOllamaRequest({ prompt:'Return JSON only', temperature:0.2, textModel:'qwen3:14b', visionModel:'qwen3-vl:8b-instruct' });
assert.equal(text.model,'qwen3:14b');
assert.equal(text.imageCount,0);
assert.equal(text.request.think,false);
assert.equal(text.request.stream,false);
assert.equal(text.request.options.temperature,0.2);

const vision = buildOllamaRequest({ input:[
  {type:'text',text:'Candidate A'},
  {type:'image',data:'YWJj',mime_type:'image/jpeg'},
  {type:'text',text:'Candidate B'},
  {type:'image',data:'ZGVm',mime_type:'image/jpeg'},
], textModel:'qwen3:14b', visionModel:'qwen3-vl:8b-instruct' });
assert.equal(vision.model,'qwen3-vl:8b-instruct');
assert.equal(vision.imageCount,2);
assert.deepEqual(vision.request.messages[0].images,['YWJj','ZGVm']);
assert.match(vision.request.messages[0].content,/Candidate A/);
assert.match(vision.request.messages[0].content,/\[IMAGE_1\]/);
assert.match(vision.request.messages[0].content,/Candidate B/);
assert.match(vision.request.messages[0].content,/\[IMAGE_2\]/);

const fakeFetch = async (_url, options) => ({
  ok:true,
  status:200,
  text:async()=>JSON.stringify({model:'qwen3:14b',message:{content:'{"ok":true}'},done_reason:'stop',total_duration:123,eval_count:5}),
});
const response = await callOllama({ baseUrl:'http://127.0.0.1:11434', request:text.request, fetchImpl:fakeFetch, timeoutMs:1000 });
assert.equal(response.provider,'ollama_self_hosted');
assert.equal(response.text,'{"ok":true}');
console.log('MODEL_WORKER_OLLAMA_CONTRACT_REGRESSION_PASS');

'use strict';
// Run in the deployed n8n image with network disabled. Only HTTP transport is mocked.
const assert = require('assert'), fs = require('fs'), path = require('path');
const {HttpRequestV3} = require('/usr/local/lib/node_modules/n8n/node_modules/n8n-nodes-base/dist/nodes/HttpRequest/V3/HttpRequestV3.node.js');
const workflow = JSON.parse(fs.readFileSync(path.join(process.argv[2], 'workflows/VIDEO-V3-Credential-Gateway.json')));
const body = {systemInstruction:{parts:[{text:'Controlled instruction'}]},
  contents:[{role:'user',parts:[{text:'Żółty цветок 🌼'}]}],
  generationConfig:{responseMimeType:'application/json',responseJsonSchema:{type:'object',properties:{ok:{type:'boolean'}},required:['ok']},candidateCount:1,maxOutputTokens:128}};
const payload = {method:'POST',url:'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent',body};
const node = workflow.nodes.find(n=>n.name==='Upstream gemini');
let captured;
const context = {
  getInputData:()=>[{json:payload}], getNode:()=>node,
  getNodeParameter(name,index,fallback) {
    let value=name.split('.').reduce((v,k)=>v?.[k],node.parameters);
    if(value===undefined) return fallback;
    if(typeof value==='string' && value.startsWith('={{'))
      return new Function('$json','return ('+value.slice(3,-2)+');')(payload);
    return value;
  },
  getCredentials:async()=>({apiKey:'controlled-not-a-key'}),
  continueOnFail:()=>false, getMode:()=> 'webhook', isToolExecution:()=>false,
  sendMessageToUI:()=>{}, addExecutionHints:()=>{},
  logger:{debug:()=>{},warn:()=>{}},
  helpers:{requestWithAuthentication:async function(type,options) {
    assert.strictEqual(type,'googlePalmApi');
    captured=structuredClone(options);
    return {statusCode:200,headers:{'content-type':'application/json'},body:'{"ok":true}'};
  }},
};
(async()=>{
  const result=await new HttpRequestV3().execute.call(context);
  assert(captured);
  const sent=typeof captured.body==='string'?JSON.parse(captured.body):captured.body;
  assert.deepStrictEqual(sent,body);
  assert.strictEqual(captured.method,'POST');
  assert(captured.json === true || Object.entries(captured.headers||{}).some(
    ([key,value])=>key.toLowerCase()==='content-type' && value==='application/json'));
  assert.strictEqual(captured.uri,payload.url);
  assert.strictEqual(result[0][0].json.body,'{"ok":true}');
  let sends=0;
  context.continueOnFail=()=>node.onError==='continueRegularOutput';
  context.helpers.requestWithAuthentication=async()=>{sends++;throw new Error('read ECONNRESET');};
  const failed=await new HttpRequestV3().execute.call(context);
  assert.strictEqual(sends,1);
  const code=workflow.nodes.find(n=>n.name==='Sanitize receipt').parameters.jsCode;
  const receipt=new Function('$input','$execution',code)({first:()=>failed[0][0]},{id:'controlled-transport'})[0].json;
  assert.strictEqual(receipt.status,502);
  assert.strictEqual(receipt.error_status,'UNKNOWN_PROVIDER_RESULT');
  assert.strictEqual(receipt.error_reason,'UPSTREAM_CONNECTION_RESET');
  assert.strictEqual(receipt.body,null);
  console.log(JSON.stringify({status:'passed',native_http_execute:true,native_transport_failure_receipt:true,transport_sends:sends,provider_calls:0,production_mutations:0}));
})().catch(error=>{console.error(error);process.exitCode=1});

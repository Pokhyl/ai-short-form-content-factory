'use strict';
const assert = require('assert'), fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..');
const {validateProviderRequest: validate} = require(path.join(root,'factory_v3/gateway_validate.js'));
const workflow = JSON.parse(fs.readFileSync(path.join(root,'workflows/VIDEO-V3-Credential-Gateway.json'),'utf8'));
const good = {
  pixabay:{query:{q:'controlled',per_page:8,safesearch:'true',image_type:'photo',lang:'en',orientation:'vertical'}},
  pexels:{query:{query:'controlled',per_page:8}},
  gemini:{body:{contents:[{parts:[{text:'controlled'}]}],generationConfig:{
    candidateCount:1,maxOutputTokens:8192,responseMimeType:'application/json',responseJsonSchema:{type:'object'}}}},
  google_tts:{body:{input:{text:'Controlled test.'},voice:{languageCode:'pl-PL',name:'pl-PL-Chirp3-HD-Enceladus'},
    audioConfig:{audioEncoding:'MP3'}}},
  gemini_info:{},
  google_metadata:{operation:'project',body:{project_number:'123456789'}}
};
for (const [provider,request] of Object.entries(good)) {
  const result=validate({provider,request});
  assert.strictEqual(result.provider,provider);
  assert(result.url.startsWith('https://'));
}
assert.throws(()=>validate({provider:'unknown',request:{}}));
assert.throws(()=>validate({provider:'pixabay',request:{query:{...good.pixabay.query,key:'not-allowed'}}}));
assert.throws(()=>validate({provider:'google_tts',request:{body:{...good.google_tts.body,audioConfig:{audioEncoding:'MP3',speakingRate:1.2}}}}));
assert.throws(()=>validate({provider:'google_tts',request:{body:{...good.google_tts.body,input:{ssml:'<speak>not allowed</speak>'}}}}));
assert.throws(()=>validate({provider:'gemini',request:{body:{...good.gemini.body,tools:[{googleSearch:{}}]}}}));
assert.throws(()=>validate({provider:'google_metadata',request:{operation:'delete',body:{project_number:'123456789'}}}));
const billing = validate({provider:'google_metadata',request:{operation:'billing',
  body:{project_id:'controlled-project'},headers:{Authorization:'caller-forged',
    'x-goog-user-project':'wrong-project'}}});
assert.deepStrictEqual(billing.headers,{'x-goog-user-project':'controlled-project'});
assert.throws(()=>validate({provider:'google_metadata',request:{operation:'billing',
  body:{project_id:'controlled-project\r\nAuthorization: forged'}}}));
const metadataNode = workflow.nodes.find(n=>n.name==='Upstream google_metadata');
assert.strictEqual(metadataNode.parameters.sendHeaders,true);
assert.strictEqual(metadataNode.parameters.specifyHeaders,'json');
assert.strictEqual(metadataNode.parameters.jsonHeaders,'={{ $json.headers || {} }}');
for (const provider of ['gemini','google_tts','gemini_info']) {
  assert.strictEqual(validate({provider,request:good[provider]}).headers,undefined);
  assert.notStrictEqual(workflow.nodes.find(n=>n.name==='Upstream '+provider).parameters.sendHeaders,true);
}
for (const n of workflow.nodes.filter(n=>n.type.endsWith('.httpRequest'))) {
  if (n.parameters.sendQuery) assert.strictEqual(n.parameters.specifyQuery,'json');
  assert.strictEqual(n.retryOnFail,false);
  assert.strictEqual(n.parameters.options.response.response.neverError,true);
}
const normalize = workflow.nodes.find(n=>n.name==='Sanitize receipt').parameters.jsCode;
const normalizeResponse = data => new Function('$input','$execution',normalize)(
  {first:()=>({json:data})},{id:'controlled'});
const secret='controlled_secret_token_abcdefghijklmnopqrstuvwxyz';
const result=normalizeResponse({statusCode:400,headers:{'X-RateLimit-Remaining':'0','Set-Cookie':'secret'},
  body:JSON.stringify({error:{status:'INVALID_ARGUMENT',message:'Unknown response field; ?key='+secret+' and Bearer '+secret}})})[0].json;
assert.strictEqual(result.status,400);
assert.strictEqual(result.body,null);
assert.strictEqual(result.headers['x-ratelimit-remaining'],'0');
assert.strictEqual(result.headers['set-cookie'],undefined);
assert(!JSON.stringify(result).includes(secret));
assert(result.error_message.includes('Unknown response field'));
console.log(JSON.stringify({status:'passed',controlled_gateway_guards:true,safe_error_receipt:true,
  no_upstream_retries:true,actual_provider_calls:0,production_mutations:0}));

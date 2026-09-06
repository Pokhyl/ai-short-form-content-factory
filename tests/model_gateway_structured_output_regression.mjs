import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const gateway=JSON.parse(fs.readFileSync(path.join(here,'../n8n/workflows/V4-model-gateway.json'),'utf8'))[0];
const wf04=JSON.parse(fs.readFileSync(path.join(here,'../n8n/workflows/WF04-visual-sourcing.json'),'utf8'))[0];
const by=Object.fromEntries((gateway.nodes??[]).map(n=>[n.name,n]));
const buildFn=new Function('$json',String(by['Build Request'].parameters.jsCode));
const schema={type:'object',properties:{segments:{type:'array',items:{type:'object',properties:{segment_number:{type:'integer'},verdicts:{type:'array',items:{type:'object',properties:{review_id:{type:'string'},relevant:{type:'boolean'},visible_description:{type:'string'}},required:['review_id','relevant','visible_description']}}},required:['segment_number','verdicts']}}},required:['segments']};
const structured=buildFn({body:{prompt:'Return JSON',response_format:'json',response_schema:schema}})[0].json;
assert.equal(structured.expects_json,true);
assert.deepEqual(structured.kilo_request_body.response_format,{type:'json_object'});
assert.equal(structured.gemini_request_body.response_format?.type,'text');
assert.equal(structured.gemini_request_body.response_format?.mime_type,'application/json');
assert.deepEqual(structured.gemini_request_body.response_format?.schema,schema);
const plain=buildFn({body:{prompt:'Plain text'}})[0].json;
assert.equal(plain.expects_json,false);
assert.equal(plain.kilo_request_body.response_format,undefined);
assert.equal(plain.gemini_request_body.response_format,undefined);

const kiloFn=new Function('$json','$',String(by['Normalize Kilo Response'].parameters.jsCode));
const buildDollar=()=>({first:()=>({json:structured})});
const kiloMalformed=kiloFn({choices:[{finish_reason:'stop',message:{content:'{"segments":['}}],model:'stepfun/step-3.7-flash:free'},buildDollar)[0].json;
assert.equal(kiloMalformed.kilo_success,false,'structured Kilo malformed JSON must fall through');
assert.match(String(kiloMalformed.provider_attempts?.[0]?.error??''),/invalid json output/);
const kiloValid=kiloFn({choices:[{finish_reason:'stop',message:{content:'{"segments":[]}'}}],model:'stepfun/step-3.7-flash:free'},buildDollar)[0].json;
assert.equal(kiloValid.kilo_success,true,'valid structured Kilo JSON should remain usable');

const geminiFn=new Function('$json','$',String(by['Normalize Gemini Response'].parameters.jsCode));
const geminiDollar=(ctx)=>()=>({first:()=>({json:ctx})});
const baseCtx={...structured,provider_attempts:kiloMalformed.provider_attempts};
const badGemini=geminiFn({status:'completed',model:'gemini-3.1-flash-lite',steps:[{type:'model_output',content:[{type:'text',text:'{"segments":[{"segment_number":1}'}]}]},geminiDollar(baseCtx))[0].json;
assert.equal(badGemini.provider_exhausted,true,'malformed structured Gemini JSON must fail closed');
assert.equal(badGemini.text,'');
assert.match(String(badGemini.provider_attempts?.at(-1)?.error??''),/invalid json output/);
const goodGemini=geminiFn({status:'completed',model:'gemini-3.1-flash-lite',id:'ok',steps:[{type:'model_output',content:[{type:'text',text:'{"segments":[]}'}]}]},geminiDollar(baseCtx))[0].json;
assert.equal(goodGemini.provider_exhausted,false);
assert.equal(goodGemini.provider,'google_gemini');
assert.equal(goodGemini.text,'{"segments":[]}');

const wf04By=Object.fromEntries((wf04.nodes??[]).map(n=>[n.name,n]));
for(const name of ['Review Actual Candidate Images','Review Conflict Recovery Images']){
  const body=String(wf04By[name]?.parameters?.jsonBody??'');
  assert.match(body,/response_format:\s*'json'/,`${name} must opt into structured JSON`);
  assert.match(body,/response_schema/,`${name} must send a JSON schema`);
  assert.match(body,/verdicts/,`${name} schema must constrain candidate verdicts`);
  assert.match(body,/visible_description/,`${name} schema must require grounded visible descriptions`);
}
console.log('MODEL_GATEWAY_STRUCTURED_OUTPUT_REGRESSION_PASS');

import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/V4-model-gateway.json','utf8'));const wf=Array.isArray(raw)?raw[0]:raw;const by=new Map(wf.nodes.map(n=>[n.name,n]));
const build=by.get('Build Request').parameters.jsCode,kiloCode=by.get('Normalize Kilo Response').parameters.jsCode,geminiCode=by.get('Normalize Gemini Response').parameters.jsCode;
assert.match(build,/response_schema:responseSchema/);assert.match(build,/gateway-json-schema-subset-v1/);
for(const code of [kiloCode,geminiCode]){for(const keyword of ['type','properties','required','items','enum','minItems','maxItems','minLength','maxLength','pattern'])assert(code.includes(`'${keyword}'`),`validator missing ${keyword}`);assert.match(code,/unsupported schema keyword/);assert.match(code,/schema validation failed/);}
const schema={type:'object',properties:{claims:{type:'array',minItems:1,maxItems:1,items:{type:'object',properties:{claim_id:{type:'string',minLength:2,maxLength:4,pattern:'^C[0-9]+$'},editorial_role:{type:'string',enum:['hook','establish','mechanism','detail','result','context']},relevant:{type:'boolean'}},required:['claim_id','editorial_role','relevant']}}},required:['claims']};
const ctx={kilo_request_body:{},gemini_request_body:{},provider_attempts:[],expects_json:true,response_schema:schema,schema_contract_version:'gateway-json-schema-subset-v1'};
const kiloFn=new Function('$json','$',kiloCode),geminiFn=new Function('$json','$',geminiCode);
const dollarBuild=()=>({first:()=>({json:ctx})});
const response=(payload)=>({choices:[{finish_reason:'stop',message:{content:JSON.stringify(payload)}}],model:'stepfun/step-3.7-flash:free',id:'fixture'});
const valid={claims:[{claim_id:'C1',editorial_role:'mechanism',relevant:true}]};
const validKilo=kiloFn(response(valid),dollarBuild)[0].json;assert.equal(validKilo.kilo_success,true);assert.equal(validKilo.text,JSON.stringify(valid));
const exactProductionFailure={claims:[{claim_id:'C1',editorial_role:'component',relevant:true}]};
const invalidEnum=kiloFn(response(exactProductionFailure),dollarBuild)[0].json;assert.equal(invalidEnum.kilo_success,false);assert.equal(invalidEnum.text,'');assert.match(invalidEnum.provider_attempts[0].error,/schema validation failed: \$\.claims\[0\]\.editorial_role: value is outside enum/);
const missing=kiloFn(response({claims:[{claim_id:'C1',editorial_role:'mechanism'}]}),dollarBuild)[0].json;assert.equal(missing.kilo_success,false);assert.match(missing.provider_attempts[0].error,/relevant: required property missing/);
const badPattern=kiloFn(response({claims:[{claim_id:'X1',editorial_role:'mechanism',relevant:true}]}),dollarBuild)[0].json;assert.equal(badPattern.kilo_success,false);assert.match(badPattern.provider_attempts[0].error,/does not match pattern/);
const tooMany=kiloFn(response({claims:[valid.claims[0],valid.claims[0]]}),dollarBuild)[0].json;assert.equal(tooMany.kilo_success,false);assert.match(tooMany.provider_attempts[0].error,/longer than maxItems/);
const unsupportedCtx={...ctx,response_schema:{type:'object',additionalProperties:false}};const unsupported=kiloFn(response({}),()=>({first:()=>({json:unsupportedCtx})}))[0].json;assert.equal(unsupported.kilo_success,false);assert.match(unsupported.provider_attempts[0].error,/unsupported schema keyword additionalProperties/);
const kiloFailedCtx=invalidEnum;
const geminiDollar=(name)=>{assert.equal(name,'Normalize Kilo Response');return {first:()=>({json:kiloFailedCtx})}};
const geminiResp=(payload)=>({status:'completed',model:'gemini-3.1-flash-lite',id:'g1',steps:[{type:'model_output',content:[{type:'text',text:JSON.stringify(payload)}]}]});
const validGemini=geminiFn(geminiResp(valid),geminiDollar)[0].json;assert.equal(validGemini.provider_exhausted,false);assert.equal(validGemini.provider,'google_gemini');assert.equal(validGemini.provider_attempts.length,2);assert.equal(validGemini.provider_attempts[1].success,true);
const invalidGemini=geminiFn(geminiResp(exactProductionFailure),geminiDollar)[0].json;assert.equal(invalidGemini.provider_exhausted,true);assert.equal(invalidGemini.text,'');assert.match(invalidGemini.provider_attempts[1].error,/schema validation failed/);
const currentKeywords=new Set();
for(const file of fs.readdirSync('n8n/workflows').filter(f=>f.endsWith('.json'))){const rr=JSON.parse(fs.readFileSync('n8n/workflows/'+file,'utf8'));for(const w of Array.isArray(rr)?rr:[rr])for(const n of w.nodes){const c=n.parameters?.jsCode??'';if(!c.includes('response_schema'))continue;for(const k of ['type','properties','required','items','enum','minItems','maxItems','minLength','maxLength','pattern','additionalProperties','minimum','maximum','oneOf','anyOf','allOf','$ref'])if(c.includes(`"${k}"`)||c.includes(`${k}:`))currentKeywords.add(k);}}
const supported=new Set(['type','properties','required','items','enum','minItems','maxItems','minLength','maxLength','pattern']);for(const k of currentKeywords)assert(supported.has(k),`current product schema uses unsupported keyword ${k}`);
console.log('MODEL_GATEWAY_SCHEMA_CONTRACT_REGRESSION_PASS');

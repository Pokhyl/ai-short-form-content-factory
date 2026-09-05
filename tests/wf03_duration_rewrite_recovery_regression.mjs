import assert from 'node:assert/strict';
import fs from 'node:fs';

const workflow=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF03-natural-edge-voice.json',import.meta.url),'utf8'))[0];
const code=workflow.nodes.find(node=>node.name==='Apply Duration Rewrite').parameters.jsCode;
const sentence=n=>Array.from({length:n},(_,i)=>`слово${i}`).join(' ')+'.';
const original=[sentence(18),sentence(18),sentence(18),sentence(18),sentence(18),sentence(18),sentence(18)].join(' ');
const base={job_id:'00000000-0000-4000-8000-000000000001',language_code:'ru',target_duration_seconds:60,provider:'microsoft_edge_readaloud',model:'edge_neural',voice:'ru-RU-DmitryNeural',script_text:original,script_support:[{evidence_id:'E1'}],desired_word_min:110,desired_word_max:124,next_fit_pass:1,max_fit_passes:2};
const short=sentence(94);
const run=new Function('$input','$',code);
const result=run({first:()=>({json:{text:JSON.stringify({script:short})}})},name=>{assert.equal(name,'Prepare Duration Rewrite');return{first:()=>({json:base})};})[0].json;
const count=result.script_text.match(/[\p{L}\p{N}]+(?:[’'\-][\p{L}\p{N}]+)*/gu)?.length??0;
assert.ok(count>=102&&count<=132,`recovered count ${count} is outside broad target`);
assert.notEqual(result.script_text,short);
assert.ok(result.script_support.length>0);
console.log('WF03_DURATION_REWRITE_RECOVERY_REGRESSION_PASS');

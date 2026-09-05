import assert from 'node:assert/strict';
import fs from 'node:fs';

const wf02=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF02-plan-script-and-scenes.json',import.meta.url),'utf8'))[0];
const wf03=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF03-natural-edge-voice.json',import.meta.url),'utf8'))[0];
const n2=new Map(wf02.nodes.map(n=>[n.name,n]));
const n3=new Map(wf03.nodes.map(n=>[n.name,n]));

const buildFinal=n2.get('Build Final Grounded Script').parameters.jsCode;
assert.match(buildFinal,/replace\(\/\\s\+\\\/\\s\+\/gu,' '\)/,'WF02 final narration must strip spaced slash separators before persistence');
assert.match(n2.get('Prepare Grounded Script Prompt').parameters.jsCode,/must not use slash separators/i);
assert.match(n2.get('Prepare Script Validation').parameters.jsCode,/must not use slash separators/i);

const eligibility=n3.get('Require Eligible Voiceover Job').parameters.jsCode;
assert.match(eligibility,/unsafe spoken formatting separators/,'WF03 must fail closed if unsafe separators somehow reach TTS');
const rewritePrompt=n3.get('Prepare Duration Rewrite').parameters.jsCode;
assert.match(rewritePrompt,/do not use slash separators/i);

const applyCode=n3.get('Apply Duration Rewrite').parameters.jsCode;
assert.match(applyCode,/speechSafe/);
const apply=new Function('$input','$',applyCode);
const base={
  job_id:'00000000-0000-4000-8000-000000000001',
  language_code:'ru',target_duration_seconds:15,provider:'google_gemini',model:'fixture',voice:'Kore',edge_fallback_voice:'ru-RU-DmitryNeural',
  script_text:'Как работает вода? / Поток вращает турбину / и генератор создаёт электричество.',
  script_support:[{evidence_id:'S1'}],fit_pass:0,max_fit_passes:2,duration_seconds:18,
  desired_word_min:8,desired_word_max:18,next_fit_pass:1,
};
const $=name=>{assert.equal(name,'Prepare Duration Rewrite');return {first:()=>({json:base})};};
const result=apply({first:()=>({json:{text:JSON.stringify({script:'Как работает вода? / Поток вращает турбину / и генератор создаёт электричество для дома каждый день.'})}})},$)[0].json;
assert.doesNotMatch(result.script_text,/\s\/\s/);
assert.equal(result.script_text,'Как работает вода? Поток вращает турбину и генератор создаёт электричество для дома каждый день.');
assert.ok(result.script_support.every(s=>!s.text.includes('/')));

for(const node of [...wf02.nodes,...wf03.nodes].filter(n=>n.type==='n8n-nodes-base.code')) new Function('$input','$',node.parameters.jsCode);
console.log('NARRATION_SPEECH_SAFETY_REGRESSION_PASS');

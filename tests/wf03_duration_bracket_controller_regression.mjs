import assert from 'node:assert/strict';
import fs from 'node:fs';

const workflow=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF03-natural-edge-voice.json',import.meta.url),'utf8'))[0];
const prepareCode=workflow.nodes.find(node=>node.name==='Prepare Duration Rewrite').parameters.jsCode;
const run=new Function('$input',prepareCode);

const current='Мощный поток воды вращает турбину плотины. Движение передается на вал генератора, где благодаря электромагнитной индукции возникает ток, который затем поступает в электрическую сеть вашего города.';
const row={
  job_id:'00000000-0000-4000-8000-000000000001',
  language_code:'ru',
  target_duration_seconds:15,
  duration_seconds:13.272,
  script_text:current,
  script_support:[{evidence_id:'E1'}],
  fit_pass:2,
  max_fit_passes:3,
  fit_history:[
    {fit_pass:0,duration_seconds:20.808,word_count:29,script_text:'long'},
    {fit_pass:1,duration_seconds:11.568,word_count:20,script_text:'short'},
    {fit_pass:2,duration_seconds:13.272,word_count:25,script_text:current},
  ],
};
const result=run({first:()=>({json:row})})[0].json;
assert.equal(result.duration_controller_mode,'measured_bracket_interpolation');
assert.equal(result.next_fit_pass,3);
assert.equal(result.max_fit_passes,3);
assert.ok(result.desired_word_target>=26&&result.desired_word_target<=27,`unexpected interpolated target ${result.desired_word_target}`);
assert.ok(result.desired_word_min<=result.desired_word_target&&result.desired_word_max>=result.desired_word_target);
assert.match(result.rewrite_prompt,/29 words -> 20\.808s/);
assert.match(result.rewrite_prompt,/25 words -> 13\.272s/);
assert.match(result.rewrite_prompt,/measured_bracket_interpolation/);

const noBracket=run({first:()=>({json:{...row,fit_pass:0,max_fit_passes:3,duration_seconds:20.808,script_text:'Один два три четыре пять шесть семь восемь девять десять одиннадцать двенадцать тринадцать четырнадцать пятнадцать шестнадцать семнадцать восемнадцать девятнадцать двадцать двадцатьодин двадцатьдва двадцатьтри двадцатьчетыре двадцатьпять двадцатьшесть двадцатьсемь двадцатьвосемь двадцатьдевять.',fit_history:[{fit_pass:0,duration_seconds:20.808,word_count:29,script_text:'long'}]}})})[0].json;
assert.equal(noBracket.duration_controller_mode,'proportional_measured_duration');
assert.equal(noBracket.next_fit_pass,1);

assert.throws(()=>run({first:()=>({json:{...row,fit_pass:3,max_fit_passes:3}})}),/outside target after 3 script rewrites/);
console.log('WF03_DURATION_BRACKET_CONTROLLER_REGRESSION_PASS');

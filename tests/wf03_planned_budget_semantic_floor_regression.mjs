import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF03-natural-edge-voice.json','utf8')),wf=Array.isArray(raw)?raw[0]:raw;
const code=wf.nodes.find(n=>n.name==='Prepare Duration Rewrite').parameters.jsCode;
const units=[
 {unit_id:'U1',claim_id:'C1',grounded_claim:'The Panama Canal uses locks as water lifts to raise ships 85 feet to Gatun Lake.',narration:'Панамский канал использует систему шлюзов, которые работают как гигантские водяные лифты, поднимая суда на высоту 85 футов до уровня озера Гатун.',evidence_ids:['S1'],asset_id:'A1',editorial_role:'establish'},
 {unit_id:'U2',claim_id:'C3',grounded_claim:'Water flows through culverts between chambers to equalize levels.',narration:'Вода перемещается между камерами через массивные водопропускные трубы, выравнивая уровни и позволяя кораблям безопасно следовать из одного океана в другой.',evidence_ids:['S2'],asset_id:'A2',editorial_role:'mechanism'},
 {unit_id:'U3',claim_id:'C6',grounded_claim:'Massive concrete lock chamber walls accommodate large maritime vessels.',narration:'Массивные бетонные стены шлюзовых камер создают герметичное пространство, необходимое для удержания огромного объема воды при подъеме и спуске морских судов.',evidence_ids:['S3'],asset_id:'A3',editorial_role:'context'}
];
const story={version:'inventory-first-story-v1',units,assets:[{asset_id:'A1'},{asset_id:'A2'},{asset_id:'A3'}]};
const script_text=units.map(u=>u.narration).join(' ');
const words=script_text.match(/[\p{L}\p{N}]+(?:[’'\-][\p{L}\p{N}]+)*/gu)?.length??0;
assert.equal(words,61,'fixture must reproduce the 61-word production draft');
const common={fit_pass:0,max_fit_passes:1,story_package:story,script_text,language_code:'ru',target_duration_seconds:15,duration_seconds:28.220333,fit_history:[],job_id:'00000000-0000-4000-8000-000000000032',provider:'microsoft_edge_readaloud',model:'edge_neural',voice:'ru-RU-DmitryNeural',edge_fallback_voice:'ru-RU-DmitryNeural'};
const run=x=>new Function('$input',code)({first:()=>({json:x})})[0].json;
const planned=run({...common,planned_word_min:30,planned_word_max:42});
assert.equal(planned.semantic_word_baseline,42,'draft verbosity above the planned max must not inflate semantic baseline');
assert.equal(planned.semantic_word_floor,28,'65% guard must be retained against the planned baseline');
assert.equal(planned.desired_word_target,30,'single-pass overlong correction must target the safe lower bound');
assert.equal(planned.planned_word_max,42);
assert.equal(planned.max_fit_passes,1);
assert.match(planned.duration_controller_mode,/overlong_lower_bound$/);
const skyStory={version:'storyboard-first-v1',units:[1,2,3,4].map(i=>({unit_id:`U${i}`,claim_id:`C${i}`,grounded_claim:`Claim ${i}`,narration:'Короткое полное предложение.',evidence_ids:[`S${i}`],asset_id:`A${i}`,editorial_role:'explain'})),assets:[]};
const sky=run({...common,story_package:skyStory,script_text:Array(37).fill('слово').join(' '),duration_seconds:18.195333,planned_word_min:30,planned_word_max:42});
assert.equal(sky.semantic_word_floor,25);assert.equal(sky.desired_word_min,29);assert.equal(sky.desired_word_max,33);assert.equal(sky.desired_word_target,29);assert.match(sky.duration_controller_mode,/overlong_lower_bound$/);
const legacy=run(common);
assert.equal(legacy.semantic_word_baseline,61,'contexts without a planned budget retain the previous baseline');
assert.equal(legacy.semantic_word_floor,40,'legacy fallback behavior must remain stable');
assert.equal(legacy.desired_word_target,40);
assert.match(legacy.duration_controller_mode,/semantic_floor$/);
console.log('WF03_PLANNED_BUDGET_SEMANTIC_FLOOR_REGRESSION_PASS');

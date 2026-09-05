import assert from 'node:assert/strict';
import fs from 'node:fs';

const workflow=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF03-natural-edge-voice.json',import.meta.url),'utf8'))[0];
const code=workflow.nodes.find(n=>n.name==='Apply Duration Rewrite').parameters.jsCode;
const run=new Function('$input','$',code);
function exercise(base, expectedRange){
  const result=run({first:()=>({json:{}})},name=>{assert.equal(name,'Prepare Duration Rewrite');return{first:()=>({json:base})};})[0].json;
  const wc=result.script_text.match(/[\p{L}\p{N}]+(?:[’'\-][\p{L}\p{N}]+)*/gu)?.length??0;
  assert.equal(result.duration_rewrite_mode,'deterministic_overlength_fallback');
  assert.ok(wc>=expectedRange[0]&&wc<=expectedRange[1],`fallback word count ${wc} outside ${expectedRange.join('-')}`);
  assert.notEqual(result.script_text,base.script_text,'overlong fallback must actually shorten the narration');
  assert.ok(/[.!?…]$/u.test(result.script_text),'fallback must end at a natural punctuation boundary');
  assert.ok(result.script_support.length>0,'fallback must preserve evidence provenance');
}
exercise({
  job_id:'00000000-0000-4000-8000-000000000001',language_code:'ru',target_duration_seconds:15,
  provider:'microsoft_edge_readaloud',model:'edge_neural',voice:'ru-RU-DmitryNeural',edge_fallback_voice:'ru-RU-DmitryNeural',
  script_text:'Как работает ГЭС? Вода из водохранилища падает вниз, превращая энергию в кинетическую. Поток вращает турбину, запуская генератор. Так энергия воды становится электричеством, которое по проводам поступает в наши дома.',
  script_support:[{evidence_id:'E1'}],desired_word_min:23,desired_word_max:25,next_fit_pass:2,max_fit_passes:2,duration_seconds:17.472
},[19,29]);
exercise({
  job_id:'00000000-0000-4000-8000-000000000002',language_code:'uk',target_duration_seconds:60,
  provider:'microsoft_edge_readaloud',model:'edge_neural',voice:'uk-UA-OstapNeural',edge_fallback_voice:'uk-UA-OstapNeural',
  script_text:'Чи замислювалися ви, як народжується дощ? Усе починається з сонячного тепла, що прогріває поверхню нашої планети. Нагріте повітря, насичене водяною парою, починає стрімко підійматися вгору. На великій висоті температура повітря суттєво знижується. У таких умовах водяна пара починає активно конденсуватися. Згодом вона перетворюється на мільярди мікроскопічних крапель води. Ці краплі групуються, формуючи видимі нам пухнасті хмари. З часом дрібні частинки всередині хмари починають постійно зливатися. Вони поступово стають занадто великими та масивними. Повітряні потоки вже не можуть утримувати цей обтяжений шар. Тоді в дію вступає неминуча земна гравітація. Важкі краплі спрямовуються вниз, випадаючи на землю дощем. Це складний фізичний цикл, що постійно живить життя на Землі. Без цього механізму наша планета стала б пустелею. Природа постійно проводить глобальне оновлення водних запасів світу. Кожен дощ є частиною цього вічного та життєдайного природного колообігу.',
  script_support:[{evidence_id:'E1'},{evidence_id:'E2'}],desired_word_min:96,desired_word_max:108,next_fit_pass:1,max_fit_passes:2,duration_seconds:76.104
},[92,112]);
console.log('WF03_DURATION_GATEWAY_FALLBACK_REGRESSION_PASS');

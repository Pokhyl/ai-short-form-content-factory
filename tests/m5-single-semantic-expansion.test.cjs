const assert = require('node:assert/strict');
const fs = require('node:fs');
const {test} = require('node:test');

const workflow = JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json', 'utf8'));
const byName = Object.fromEntries(workflow.nodes.map(n => [n.name, n]));
const code = name => byName[name].parameters.jsCode;

const evidence = [
  {evidence_ref:'E1', evidence_uuid:'00000000-0000-4000-8000-000000000001', title:'Mechanism', source_domain:'example.org', source_url:'https://example.org/1', snippet:'A physical instrument has a measurable response.', content:'A pressure change moves the indicator.'},
  {evidence_ref:'E2', evidence_uuid:'00000000-0000-4000-8000-000000000002', title:'Other', source_domain:'example.org', source_url:'https://example.org/2', snippet:'Uncited detail.', content:'Uncited detail.'},
  {evidence_ref:'E3', evidence_uuid:'00000000-0000-4000-8000-000000000003', title:'More', source_domain:'example.org', source_url:'https://example.org/3', snippet:'More source material.', content:'More source material.'},
];

function build(language_code, target_duration_seconds) {
  return new Function('$json', code('Build Script Prompt'))({
    script_run_id:'00000000-0000-4000-8000-000000000004',
    topic:'how does a measuring instrument work?',
    language_code, target_duration_seconds, evidence_json:evidence,
  }).json;
}

test('initial Ukrainian 30-second request uses observed sentence cadence and word budget without changing the audio gate', () => {
  const uk30 = build('uk',30);
  assert.equal(uk30.target_words,52);
  assert.deepEqual([uk30.word_min,uk30.word_max],[18,72]);
  assert.deepEqual(uk30.scene_word_targets,[6,6,6,6,6,6,6,4,6]);
  assert.equal(build('uk',45).target_words,68);
  assert.equal(build('pl',30).target_words,54);
  assert.match(uk30.user_message,/specific causal details from those sources/);
  assert.match(uk30.user_message,/prefer 7-9 natural complete sentences/);
  assert.match(uk30.user_message,/count the narration words before returning JSON; target about 52 words/);
  assert.doesNotMatch(uk30.user_message,/target exactly 52 words/);
});

test('one measured expansion stays within scene capacity and supplies only cited research', () => {
  const ctx={...build('uk',30),topic:'general pressure instrument'};
  const scenes=Array.from({length:9},(_,i)=>({scene_id:'S'+(i+1),narration:'Оригінальна думка тиску для механізму.',evidence_ids:['E1'],shots:[{shot_id:'S'+(i+1)+'-A'}]}));
  const measured={
    script_run_id:'run',model:'gemini',measured_duration_ms:22584,
    target_duration_ms:30000,usage:{},storyboard:{
      narration:scenes.map(s=>s.narration).join(' '),scenes,
    },
  };
  const $=name=>{assert.equal(name,'Build Script Prompt');return {first:()=>({json:ctx})};};
  const out=new Function('$','$json',code('Build Timing Repair'))($,measured).json;
  assert.match(out.user_message,/one semantic-safe rewrite/);
  assert.match(out.user_message,/CITED RESEARCH EVIDENCE/);
  assert.match(out.user_message,/A pressure change moves the indicator/);
  assert.doesNotMatch(out.user_message,/Uncited detail/);
  assert.match(out.user_message,/never add unsupported facts, generic praise, filler/);
  const target=Number(out.user_message.match(/MEASURED TARGET WORD COUNT: about (\d+) words/)[1]);
  assert.equal(target,58, '45 words at 22.584s recalibrates to the measured voice; added lexical words may include grammar while new facts remain bounded per scene');
  assert.match(out.user_message,/at most one NEW meaning-bearing word per short scene/);
});

test('the failed mixed-script draft is rejected even before another voiceover is synthesized', () => {
  const js=code('Validate Timing Repair');
  const begin=js.indexOf('const hasUkrainianLexicalLeak =');
  const end=js.indexOf('\n};',begin);
  assert.ok(begin>=0 && end>begin);
  const detect=new Function(js.slice(begin,end+3)+'\nreturn hasUkrainianLexicalLeak;')();
  assert.equal(detect('Барометр працює з ртуттю.'),false);
  assert.equal(detect('Барометр прогнозує погоdy.'),true);
  assert.equal(detect('Поgоdy залежать від тиску.'),true);
  assert.equal(workflow.connections['Validate Timing Repair'].main[1][0].node,'Build Timing Repair 2');
  assert.equal(workflow.connections['Validate Timing Repair 2'].main[1][0].node,'Prepare Script Failure');
  for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2','Validate Timing Repair','Validate Narration Language Repair']) {
    assert.match(code(name),/Script=Cyrillic/,name);
  }
});

test('short measured Ukrainian speech asks for supported causal detail without lowering audio sanity', () => {
  const ctx=build('uk',30);
  const scenes=Array.from({length:9},(_,i)=>({
    scene_id:'S'+(i+1),narration:i===0
      ? 'Реальний механізм швидко реагує на тиск.'
      : 'Реальний механізм реагує на тиск.',
    evidence_ids:['E1'],shots:[{shot_id:'S'+(i+1)+'-A'}],
  }));
  const measured={script_run_id:'run',model:'gemini',measured_duration_ms:24504,
    target_duration_ms:30000,usage:{},storyboard:{
      narration:scenes.map(s=>s.narration).join(' '),scenes,
    }};
  const $=name=>({first:()=>({json:ctx})});
  const request=new Function('$','$json',code('Build Timing Repair'))($,measured).json;
  assert.match(request.user_message,/MEASURED TARGET WORD COUNT: about 55 words/);
  assert.match(request.user_message,/at most one NEW meaning-bearing word per short scene/);
  assert.match(request.user_message,/never add unsupported facts, generic praise, filler/);
  const gates=code('Normalize Timing Probe 2');
  assert.match(gates,/28464/);
  assert.match(gates,/34000/);
});

const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

const scenes=[
  'Барометр — це прилад для вимірювання',
  'атмосферного тиску, який створює сила',
  'повітря на поверхню Землі. Принцип',
  'роботи ртутного барометра заснований на',
  'залежності висоти стовпа ртуті від',
  'зовнішнього тиску. Сучасні анероїди використовують',
  'металеву коробку, яка деформується від',
  'коливань тиску. Електронні датчики точно',
  'визначають зміни погоди для прогнозу.',
];
const storyboard={
  narration:scenes.join(' '),
  scenes:scenes.map((narration,index)=>({
    scene_id:'S'+(index+1),
    narration,
    evidence_ids:['E1'],
    shots:[{shot_id:'S'+(index+1)+'-A'}],
  })),
};
const ctx={
  topic:'як працює барометр',
  language_code:'uk',
  target_duration_seconds:30,
  target_scenes:9,
  target_shots:9,
  word_min:18,
  word_max:72,
  user_message:'',
};
const p1={
  script_run_id:'run',
  model:'gemini',
  storyboard,
  measured_duration_ms:23616,
  target_duration_ms:30000,
  tolerance_ms:2000,
  narration_word_count:46,
  usage:{},
};

test('short sparse-punctuation narration enters cadence-first repair before lexical padding',()=>{
  const $=name=>{
    assert.equal(name,'Build Script Prompt');
    return {first:()=>({json:ctx})};
  };
  const out=new Function('$','$json',code('Build Timing Repair'))($,p1).json;

  assert.match(out.system_message,/cadence-first repair/i);
  assert.match(out.system_message,/avoid descriptive modifiers, intensifiers and filler/i);
  assert.match(out.user_message,/CURRENT SENTENCE ENDS: 4/);
  assert.match(out.user_message,/CADENCE-FIRST PASS:/);
  assert.match(out.user_message,/KEEP LEXICAL CONTENT close to the current 46 words/);
  assert.match(out.user_message,/split long clauses into natural short sentences/i);
});

test('second timing repair respects LONGER direction and stays cadence-first when pauses are sparse',()=>{
  const p2={...p1,measured_duration_ms:22944};
  const $=name=>{
    if(name==='Build Script Prompt') return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe') return {first:()=>({json:p1})};
    if(name==='Normalize Timing Stability B') return {all:()=>{throw new Error('not executed')}};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code('Build Timing Repair 2'))($,p2).json;

  assert.match(out.system_message,/cadence-first/i);
  assert.match(out.system_message,/never use filler adjectives\/adverbs or invented detail/i);
  assert.doesNotMatch(out.system_message,/Shorten wording/);
  assert.match(out.user_message,/current sentence ends: 4/);
  assert.match(out.user_message,/direction from current version: make narration LONGER/);
  assert.match(out.user_message,/CADENCE-FIRST PASS:/);
});

test('second timing repair keeps explicit shortening instruction when measured narration is too long',()=>{
  const p2={...p1,measured_duration_ms:33000};
  const $=name=>{
    if(name==='Build Script Prompt') return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe') return {first:()=>({json:p1})};
    if(name==='Normalize Timing Stability B') return {all:()=>{throw new Error('not executed')}};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code('Build Timing Repair 2'))($,p2).json;

  assert.match(out.system_message,/Shorten wording without deleting a necessary argument/i);
  assert.doesNotMatch(out.system_message,/This is cadence-first/i);
  assert.match(out.user_message,/direction from current version: make narration SHORTER/);
});

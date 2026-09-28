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

test('short narration gets one bounded semantic expansion aimed inside the observed window',()=>{
  const $=name=>{
    assert.equal(name,'Build Script Prompt');
    return {first:()=>({json:ctx})};
  };
  const out=new Function('$','$json',code('Build Timing Repair'))($,p1).json;

  assert.match(out.system_message,/Lengthen only through natural same-proposition grammar/);
  assert.match(out.system_message,/Never pad with descriptive modifiers/);
  assert.match(out.user_message,/ACCEPTABLE AUDIO DURATION: 28464\.\.34000 ms/);
  assert.match(out.user_message,/MEASURED TARGET WORD COUNT: about 57 words/);
  assert.match(out.user_message,/one semantic-safe rewrite/);
  assert.match(out.user_message,/calibrated from this exact measured voice/);
  assert.match(out.user_message,/never add unsupported facts, generic praise, filler/);
  assert.match(out.user_message,/never delete a verb to make space for a modifier/);
  assert.doesNotMatch(out.user_message,/CADENCE-FIRST PASS/);
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

test('real 11116 short voice recalibrates to measured speech rate rather than one-word-per-scene cap',()=>{
  const source={...p1,measured_duration_ms:21936,narration_word_count:43,storyboard:{...storyboard,narration:'Барометр — це вимірювальний прилад для визначення атмосферного тиску на поверхню Землі. Традиційний ртутний прилад складається зі скляної трубки з ртуттю. Атмосферний тиск штовхає рідину вгору, утворюючи стовп певної висоти. Існують також анероїди з металевою коробкою, що змінює свою форму від коливань тиску.'}};
  const $=name=>({first:()=>({json:ctx})});
  const output=new Function('$','$json',code('Build Timing Repair'))($,source).json;
  assert.match(output.user_message,/CURRENT MEASURED TTS: 21936 ms/);
  assert.match(output.user_message,/CURRENT WORDS: 43/);
  assert.match(output.user_message,/MEASURED TARGET WORD COUNT: about 57 words/);
  assert.doesNotMatch(output.user_message,/CADENCE-FIRST PASS/);
});

test('rejected first timing rewrite gets one bounded retry from original narration',()=>{
  const original={...p1,measured_duration_ms:35736,narration_word_count:55};
  const $=name=>{
    if(name==='Build Script Prompt')return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe')return {first:()=>({json:original})};
    if(name==='Normalize Timing Stability B')return {all:()=>{throw new Error('not executed')}};
    if(name==='Build Timing Repair')return {first:()=>({json:{prior_usage:{}}})};
    if(name==='Repair Storyboard Timing')return {first:()=>({json:{body:{usageMetadata:{promptTokenCount:100}}}})};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code('Build Timing Repair 2'))($,{error:'4, minimum 6 [line 177]'}).json;
  assert.equal(out.semantic_fallback_from_first_repair,true);
  assert.match(out.user_message,/SEMANTIC FALLBACK: the previous timing rewrite was rejected before TTS/);
  assert.match(out.system_message,/Shorten wording/);
  assert.match(out.user_message,/make narration SHORTER/);
  assert.equal(out.target_scene_word_counts.reduce((a,b)=>a+b,0),out.target_precision_words);
  assert.ok(out.target_scene_word_counts.at(-1)>=6);
  assert.equal(workflow.connections['Validate Timing Repair'].main[1][0].node,'Build Timing Repair 2');
  assert.equal(workflow.connections['Validate Timing Repair 2'].main[1][0].node,'Prepare Script Failure');
  assert.throws(()=>new Function('$','$json',code('Build Timing Repair 2'))($,{error:'Gemini provider unavailable'}),/outside bounded structural\/semantic retry/);
  assert.throws(()=>new Function('$','$json',code('Build Timing Repair 2'))($,{error:'semantic preservation violation'}),/outside bounded structural\/semantic retry/);
});


test('11358 regression: excessive novel words get one bounded semantic fallback without filler',()=>{
  const original={...p1,measured_duration_ms:24792,narration_word_count:47};
  const $=name=>{
    if(name==='Build Script Prompt')return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe')return {first:()=>({json:original})};
    if(name==='Normalize Timing Stability B')return {all:()=>{throw new Error('not executed')}};
    if(name==='Build Timing Repair')return {first:()=>({json:{prior_usage:{}}})};
    if(name==='Repair Storyboard Timing')return {first:()=>({json:{body:{usageMetadata:{promptTokenCount:100}}}})};
    throw new Error('unexpected node '+name);
  };
  const first=new Function('$','$json',code('Build Timing Repair'))($,original).json;
  assert.match(first.user_message,/at most one NEW meaning-bearing word per short scene/);
  const build=new Function('$','$json',code('Build Timing Repair 2'));
  const second=build($,{error:'3, allowed 1 [line 603]'}).json;
  assert.equal(second.semantic_fallback_from_first_repair,true);
  assert.match(second.user_message,/at most one NEW meaning-bearing word per scene/);
  assert.match(second.user_message,/No intensifier, decorative adjective, redundant adverb or unsupported detail/);
  assert.equal(workflow.connections['Validate Timing Repair 2'].main[1][0].node,'Prepare Script Failure');
  assert.throws(()=>build($,{error:'unexpected semantic rewrite'}),/outside bounded structural\/semantic retry/);
});

test('11274 regression moves two adjacent visual cuts without rewriting the narration',()=>{
 const parts=[
  'Вода випаровується з поверхні планети, піднімаючись',
  'вгору невидимою парою.',
  'Рухаючись вище, повітря охолоджується.',
  'Тиск падає, викликаючи адіабатичне розширення.',
  'Волога досягає точки роси.',
  'Частинки пилу стають ядрами конденсації.',
  'Пара осідає на центрах.',
  'Краплі утворюють хмару.',
  'Важкі краплі випадають дощем.',
 ];
 for(const name of ['Validate Timing Repair','Validate Timing Repair 2']){
  const script=code(name);
  const start=script.indexOf('// A visual cut may move while the spoken narration stays byte-for-byte intact.');
  const end=script.indexOf('if (scenes.length !== Number(ctx.target_scenes))',start);
  assert.ok(start>=0 && end>start,name);
  const scenes=parts.map(narration=>({narration}));
  const narration=parts.join(' ');
  new Function('ctx','scenes','narration','clean',script.slice(start,end))(
   {target_duration_seconds:30},scenes,narration,value=>String(value).replace(/\s+/g,' ').trim());
  assert.equal(scenes.map(scene=>scene.narration).join(' '),narration,name);
  assert.deepEqual(scenes.slice(6).map(scene=>scene.narration.split(/\s+/u).length),[3,2,6],name);
  assert.equal(scenes[8].narration,'утворюють хмару. Важкі краплі випадають дощем.',name);
 }
});

test('11226 timing replies preserve every spoken word when repairing a short final visual cut',()=>{
 const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m5-11226-timing-boundary.json'));
 for(const [name,provider] of [['Validate Timing Repair','Repair Storyboard Timing'],['Validate Timing Repair 2','Repair Storyboard Timing 2']]){
  const candidate=JSON.parse(fixture[provider].body.candidates[0].content.parts[0].text);
  const $=key=>({first:()=>({json:fixture[key]})});
  const result=new Function('$','$json',code(name))($,fixture[provider]).json;
  assert.equal(result.storyboard.narration,candidate.narration);
  assert.equal(result.storyboard.scenes.map(scene=>scene.narration).join(' '),candidate.narration);
  assert.ok(result.storyboard.scenes[8].narration.split(/\s+/u).length>=6);
 }
});


test('11230 semantic coverage failure gets one bounded retry from original, provider failures remain terminal',()=>{
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-11230-semantic-coverage.json'));
 const $=name=>{if(!f[name])throw new Error('unavailable node '+name);return {first:()=>({json:f[name]})};};
 const build=new Function('$','$json',code('Build Timing Repair 2'));
 const out=build($,f.incoming).json;
 assert.equal(out.semantic_fallback_from_first_repair,true);
 assert.match(out.user_message,/coverage 0\.400, required >= 0\.600/);
 assert.match(out.user_message,/Односторонній клапан|поршневого механізму/u);
 assert.equal(out.target_scene_word_counts.at(-1)>=6,true);
 assert.throws(()=>build($,{error:{description:'Gemini provider unavailable'}}),/outside bounded structural\/semantic retry/);
});

test('slightly overlong narration repairs toward upper accepted window without erasing meaning',()=>{
  const overlong={...p1,measured_duration_ms:34256,narration_word_count:58};
  const $=name=>{
    if(name==='Build Script Prompt') return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe') return {first:()=>({json:overlong})};
    if(name==='Normalize Timing Stability B') return {all:()=>{throw new Error('not executed')}};
    if(name==='Build Timing Repair') return {first:()=>({json:{prior_usage:{}}})};
    if(name==='Repair Storyboard Timing') return {first:()=>({json:{body:{usageMetadata:{}}}})};
    throw new Error('unexpected node '+name);
  };
  const first=new Function('$','$json',code('Build Timing Repair'))($,overlong).json;
  assert.match(first.user_message,/REQUIRED DIRECTION: make narration SHORTER/);
  assert.match(first.user_message,/MEASURED TARGET WORD COUNT: about 43 words/);
  const second=new Function('$','$json',code('Build Timing Repair 2'))($,{error:'coverage 0.500, required >= 0.600 [line 588]'}).json;
  assert.equal(second.semantic_fallback_from_first_repair,true);
  assert.ok(second.target_precision_words>=43,second.target_precision_words);
  assert.match(second.user_message,/direction from current version: make narration SHORTER/);
});

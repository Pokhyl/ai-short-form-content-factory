const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));
const code=(name)=>byName[name].parameters.jsCode;

const narrationScenes=[
  'Pompka rowerowa to narzędzie służące do',
  'wtłaczania powietrza do opon rowerowych, co',
  'zapewnia prawidłowe ciśnienie i bezpieczeństwo jazdy.',
  'W pompce ręcznej tłok porusza się',
  'w cylindrze sprężając powietrze i kierując',
  'je do opony przez wentyl. Istotne',
  'jest, aby końcówka pompki odpowiadała rodzajowi',
  'wentyla Presta lub Schrader, co zapewnia',
  'szczelność i skuteczność pompowania opony rowerowej.',
];

const storyboard={
  narration:narrationScenes.join(' '),
  scenes:narrationScenes.map((narration,index)=>({
    scene_id:'S'+(index+1),
    narration,
    evidence_ids:['E1'],
    evidence_uuids:['69416ecd-47b3-484e-b98b-79b2e56da540'],
    shots:[{shot_id:'S'+(index+1)+'-A'}],
  })),
};

const ctx={
  topic:'jak działa pompka rowerowa',
  language_code:'pl',
  target_duration_seconds:30,
  target_scenes:9,
  target_shots:9,
  word_min:18,
  word_max:72,
  user_message:'SOURCE\nEVIDENCE:\n'+JSON.stringify([{
    id:'E1',
    title:'Pompka rowerowa',
    snippet:'Tłok porusza się w cylindrze i wtłacza powietrze do opony.',
    content:'Tłok porusza się w cylindrze, sprężając powietrze i kierując je do opony przez wentyl.',
  }]),
};

const measured={
  script_run_id:'run-11613',
  model:'gemini',
  storyboard,
  measured_duration_ms:24576,
  target_duration_ms:30000,
  tolerance_ms:1500,
  narration_word_count:54,
  usage:{},
};

function extractBudget(message){
  const lines=String(message).split('\n');
  const markerIndex=lines.findIndex((line)=>line.startsWith('ORIGINAL CONTENT WORDS BY SCENE'));
  assert.ok(markerIndex>=0,'lexical budget marker missing');
  return JSON.parse(lines[markerIndex+1]);
}

test('11613 first timing repair exposes validator-aligned per-scene lexical budget',()=>{
  const $=name=>{
    assert.equal(name,'Build Script Prompt');
    return {first:()=>({json:ctx})};
  };
  const out=new Function('$','$json',code('Build Timing Repair'))($,measured).json;
  const budget=extractBudget(out.user_message);
  const s4=budget.find((row)=>row.scene_id==='S4');
  assert.ok(s4);
  assert.ok(s4.content_words.includes('pompce'));
  assert.ok(s4.content_words.includes('recznej'));
  assert.ok(s4.content_words.includes('tłok'));
  assert.ok(s4.content_words.includes('porusza'));
  assert.equal(s4.content_words.includes('w'),false);
  assert.equal(s4.content_words.includes('sie'),false);
  assert.equal(s4.content_words.includes('dynamicznie'),false);
  assert.equal(s4.content_words.includes('wewnetrzny'),false);
  assert.match(out.user_message,/HARD CONTENT-WORD BUDGET/);
  assert.match(out.user_message,/add at most one other meaning-bearing word per scene/);
});

test('11613 excessive-novel retry receives the same immutable lexical budget',()=>{
  const first$=name=>{
    assert.equal(name,'Build Script Prompt');
    return {first:()=>({json:ctx})};
  };
  const first=new Function('$','$json',code('Build Timing Repair'))(first$,measured).json;
  const $=name=>{
    if(name==='Build Script Prompt')return {first:()=>({json:ctx})};
    if(name==='Normalize Timing Probe')return {first:()=>({json:measured})};
    if(name==='Normalize Timing Stability B')return {all:()=>{throw new Error('not executed')}};
    if(name==='Build Timing Repair')return {first:()=>({json:first})};
    if(name==='Repair Storyboard Timing')return {first:()=>({json:{body:{usageMetadata:{promptTokenCount:100}}}})};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code('Build Timing Repair 2'))(
    $,
    {error:'2, allowed 1 [line 603]'}
  ).json;
  assert.equal(out.semantic_fallback_from_first_repair,true);
  assert.deepEqual(extractBudget(out.user_message),extractBudget(first.user_message));
  assert.match(out.user_message,/HARD CONTENT-WORD BUDGET/);
  assert.match(out.user_message,/previous timing rewrite was rejected before TTS/);
});

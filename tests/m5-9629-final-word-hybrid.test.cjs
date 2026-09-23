const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const code=workflow.nodes.find(
  n=>n.name==='Validate Final Word Count Retry'
).parameters.jsCode;

const immutable=[
  'Specjalna zapora spiętrza wodę w zbiorniku.',
  'Strumień ten spada w dół,',
  'kręci turbinę,',
  'uruchamia generator',
  'i wytwarza prąd trafiający do sieci.',
];

const base=[
  'Specjalna wielka zapora skutecznie spiętrza wodę w zbiorniku.',
  'Strumień ten potężnie spada w dół,',
  'kręci wielką turbinę,',
  'uruchamia generator',
  'i wytwarza silny prąd trafiający bezpośrednio do sieci.',
];

const preFinal=[
  'Specjalna zapora spiętrza wodę w dużym zbiorniku.',
  'Strumień ten spada w dół z siłą,',
  'Kręci turbinę,',
  'Uruchamia generator.',
  'I wytwarza prąd, który trafia do sieci.',
];

function storyboard(lines){
  return {
    narration:lines.join(' '),
    scenes:lines.map((narration,i)=>({
      scene_id:'S'+(i+1),
      narration,
      shots:[{shot_key:'S'+(i+1)+'-A'}],
    })),
  };
}

function run9629(){
  const rows={
    'Build Final Word Count Retry':{
      script_run_id:'2a2f9f43-4fd6-4f0b-af2e-6a7cfbcf500b',
      model:'gemini-3.5-flash-lite',
      base_storyboard:storyboard(base),
      prior_usage:{promptTokenCount:100,candidatesTokenCount:20,totalTokenCount:120},
      target_words:31,
      target_scene_word_counts:[9,7,3,3,9],
    },
    'Build Final Duration Repair':{
      base_storyboard:storyboard(preFinal),
    },
    'Build Script Prompt':{
      language_code:'pl',
      target_duration_seconds:15,
    },
    'Normalize Timing Probe':{
      storyboard:storyboard(immutable),
    },
  };
  const $=name=>{
    if(!(name in rows)) throw new Error('unexpected node '+name);
    return {first:()=>({json:rows[name]})};
  };
  const response={
    statusCode:200,
    body:{
      candidates:[{
        content:{parts:[{text:JSON.stringify({narrations:immutable})}]},
      }],
      usageMetadata:{promptTokenCount:540,candidatesTokenCount:75,totalTokenCount:615},
    },
  };
  return new Function('$','$json',code)($,response).json;
}

test('9629 regression: semantic-invalid base/pre-final options cannot poison exact-word hybrid',()=>{
  const out=run9629();
  assert.equal(out.scene_count,5);
  assert.equal(out.deterministic_word_hybrid_used,true);
  assert.ok(out.narration_word_count>0);

  // The exact provider retry is immutable-original text and must remain a
  // valid fallback. Filler variants that violate the semantic guard cannot
  // be reintroduced only to get numerically closer to 31 words.
  assert.ok(
    [immutable[4],preFinal[4]].includes(out.storyboard.scenes[4].narration)
  );
  assert.doesNotMatch(out.storyboard.narration,/\bsilny\b/u);
  assert.doesNotMatch(out.storyboard.narration,/\bbezpośrednio\b/u);
  assert.doesNotMatch(out.storyboard.narration,/\bpotężnie\b/u);
});

test('exact-word DP is explicitly semantic-filtered before state expansion',()=>{
  assert.match(code,/const addSemanticOption = \(text,count,source\)/);
  assert.match(code,/assertSemanticPreservation\(\s*originalSemanticScenes\[i\]\?\.narration/s);
  assert.match(code,/has no semantic-valid narration option/);
});

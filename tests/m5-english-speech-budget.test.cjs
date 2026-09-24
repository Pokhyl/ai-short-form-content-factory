const fs=require('node:fs');
const test=require('node:test');
const assert=require('node:assert/strict');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8')
);
const code=workflow.nodes.find(n=>n.name==='Build Script Prompt').parameters.jsCode;

const evidence=[1,2,3].map(i=>({
  evidence_ref:'E'+i,
  evidence_uuid:'00000000-0000-4000-8000-00000000000'+i,
  source_domain:'example.com',
  title:'Evidence '+i,
  source_url:'https://example.com/'+i,
  snippet:'supported fact '+i,
  content:'supported fact '+i,
}));

function build(language_code,target_duration_seconds){
  return new Function('$json',code)({
    script_run_id:'11111111-1111-4111-8111-111111111111',
    topic:'how does a lighthouse work?',
    language_code,
    target_duration_seconds,
    evidence_json:evidence,
  }).json;
}

test('English initial word budget matches measured production TTS pace',()=>{
  const expected={
    15:[36,42,38],
    30:[72,84,77],
    45:[108,126,115],
    60:[144,168,153],
  };
  for(const [duration,values] of Object.entries(expected)){
    const out=build('en',Number(duration));
    assert.deepEqual(
      [out.word_min,out.word_max,out.target_words],
      values,
      'duration '+duration
    );
    assert.match(
      out.user_message,
      new RegExp('NARRATION WORD RANGE: '+values[0]+'-'+values[1]+' words')
    );
    assert.match(
      out.user_message,
      new RegExp('TARGET NARRATION WORD COUNT: exactly '+values[2]+' words')
    );
  }
});

test('non-English speech budgets are unchanged by English calibration',()=>{
  const pl=build('pl',15);
  const ru=build('ru',15);
  const uk=build('uk',15);
  assert.deepEqual([pl.word_min,pl.word_max,pl.target_words],[21,33,27]);
  assert.deepEqual([ru.word_min,ru.word_max,ru.target_words],[20,31,26]);
  assert.deepEqual([uk.word_min,uk.word_max,uk.target_words],[9,36,23]);
});

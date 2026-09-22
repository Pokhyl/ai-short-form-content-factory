const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

function run9537(fixture){
  const code=byName['Validate Repaired Storyboard 2'].parameters.jsCode;
  const $=name=>({
    first:()=>({json:fixture[name]}),
  });
  return new Function('$','$json',code)($,fixture.response).json;
}

test('9537 regression: visual scenes may be contiguous fragments of one natural narration',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const out=run9537(fixture);

  assert.equal(out.scene_count,5);
  assert.equal(out.shot_count,5);
  assert.equal(out.narration_word_count,22);
  assert.equal(
    out.storyboard.narration,
    'Woda gromadzi się za tamą i spływa w dół. Ten ruch obracający turbinę generuje prąd. Wytworzona energia elektryczna trafia do sieci przesyłowej.'
  );
  assert.equal(out.storyboard.scenes[1].narration,'Ten ruch obracający turbinę');
  assert.equal(out.storyboard.scenes[2].narration,'generuje prąd.');
  assert.equal(out.storyboard.scenes[3].narration,'Wytworzona energia elektryczna trafia');
  assert.equal(out.storyboard.scenes[4].narration,'do sieci przesyłowej.');
});

test('joined narration, not every visual segment, must be a complete utterance',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const body=fixture.response.body;
  const parsed=JSON.parse(body.candidates[0].content.parts[0].text);
  parsed.scenes[4].narration='do sieci przesyłowej';
  body.candidates[0].content.parts[0].text=JSON.stringify(parsed);

  assert.throws(
    ()=>run9537(fixture),
    /canonical continuous narration must start normally and end as a complete utterance/
  );
});

test('M5 prompt defines scenes as visual cut segments of continuous narration',()=>{
  const code=byName['Build Script Prompt'].parameters.jsCode;
  assert.match(code,/scene boundaries MAY occur inside a sentence/);
  assert.match(code,/joined scene narrations must form natural complete narration/);
  assert.doesNotMatch(code,/never split one sentence across scenes/);
});

test('all storyboard/timing validators removed per-scene standalone sentence gates',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
    'Validate Timing Repair',
    'Validate Timing Repair 2',
    'Validate Timing Precision Retry',
    'Validate Final Duration Repair',
    'Validate Final Word Count Retry',
    'Validate Final Measured Correction',
    'Validate Final Measured Word Count Retry',
    'Canonicalize Final Storyboard',
  ]){
    const code=byName[name].parameters.jsCode;
    assert.doesNotMatch(code,/must (?:start|end )?as a standalone sentence/,name);
    assert.doesNotMatch(code,/must be a standalone sentence/,name);
  }
});

test('final canonicalizer still requires one complete continuous narration',()=>{
  const code=byName['Canonicalize Final Storyboard'].parameters.jsCode;
  assert.match(code,/final continuous narration must start normally and end as a complete utterance/);
  assert.match(code,/final narration segment has no lexical content/);
});

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


test('anaphoric scene cannot switch visual primary away from previous scene subject',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );

  parsed.scenes[3].narration='A ruch obrotowy napędza generator,';
  parsed.scenes[3].shots[0].visual_intent=
    'Large hydroelectric generator inside power station';
  parsed.scenes[3].shots[0].must_show=['electrical generator'];
  parsed.scenes[3].shots[0].queries_en=[
    'electrical generator in power plant',
    'hydroelectric generator machine hall',
    'electrical generator'
  ];

  parsed.scenes[4].narration='Który wytwarza prąd.';
  parsed.scenes[4].shots[0].visual_intent=
    'High voltage power transformer and electric grid lines';
  parsed.scenes[4].shots[0].must_show=['power transformer'];
  parsed.scenes[4].shots[0].queries_en=[
    'power transformer electric substation',
    'high voltage transformer station',
    'power transformer'
  ];
  parsed.narration=parsed.scenes.map(s=>s.narration).join(' ');
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  assert.throws(
    ()=>run9537(fixture),
    /anaphoric scene visual subject must preserve previous scene primary subject/
  );
});

test('anaphoric scene may keep the same concrete visual primary with a normal synonym',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );

  parsed.scenes[3].narration='A ruch obrotowy napędza generator,';
  parsed.scenes[3].shots[0].visual_intent=
    'Large hydroelectric generator inside power station';
  parsed.scenes[3].shots[0].must_show=['electrical generator'];
  parsed.scenes[3].shots[0].queries_en=[
    'electrical generator in power plant',
    'hydroelectric generator machine hall',
    'electrical generator'
  ];

  parsed.scenes[4].narration='Który wytwarza prąd.';
  parsed.scenes[4].shots[0].visual_intent=
    'Electric generator producing power inside a power station';
  parsed.scenes[4].shots[0].must_show=['electric generator'];
  parsed.scenes[4].shots[0].queries_en=[
    'electric generator producing power',
    'power station electric generator',
    'electric generator'
  ];
  parsed.narration=parsed.scenes.map(s=>s.narration).join(' ');
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  const out=run9537(fixture);
  assert.equal(out.storyboard.scenes[4].shots[0].must_show[0],'electric generator');
});

test('final visual-cut punctuation normalizer removes comma-period artifacts without deleting clause punctuation',()=>{
  const code=byName['Canonicalize Final Storyboard'].parameters.jsCode;
  const match=code.match(
    /function normalizeVisualCutPunctuation\(value,isLastScene\) \{[\s\S]*?\n\}/
  );
  assert.ok(match,'normalizeVisualCutPunctuation helper missing');
  const normalize=new Function(match[0]+'; return normalizeVisualCutPunctuation;')();

  assert.equal(normalize('Spadająca rzeka uderza w łopatki turbiny,.',false),
    'Spadająca rzeka uderza w łopatki turbiny,');
  assert.equal(normalize('A ruch obrotowy napędza generator,.',false),
    'A ruch obrotowy napędza generator,');
  assert.equal(normalize('Który wytwarza prąd,.',true),
    'Który wytwarza prąd.');
});

test('repair prompts preserve continuous visual-cut contract and resolve inherited referents',()=>{
  for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
    const code=byName[name].parameters.jsCode;
    assert.match(code,/MAY start as a continuation fragment/);
    assert.match(code,/resolve the inherited subject from the immediately previous scene/);
    assert.doesNotMatch(code,/must not start as a continuation fragment/);
  }
});

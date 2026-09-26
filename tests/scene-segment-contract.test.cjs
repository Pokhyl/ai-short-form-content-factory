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
    /anaphoric scene visual subject must preserve the likely inherited previous primary or explicitly name a new current primary/
  );
});

test('9613 regression: leading pronoun may refer to a later previous-clause noun instead of previous visual primary',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );

  parsed.scenes[2].narration=
    'Następnie generator wytwarza prąd elektryczny,';
  parsed.scenes[2].shots[0].visual_intent=
    'Large electrical generator driven by turbine in power station';
  parsed.scenes[2].shots[0].must_show=[
    'electrical generator',
    'turbine shaft'
  ];
  parsed.scenes[2].shots[0].queries_en=[
    'hydroelectric generator machine',
    'electric generator in power plant',
    'electrical generator'
  ];

  parsed.scenes[3].narration='który trafia do sieci';
  parsed.scenes[3].shots[0].visual_intent=
    'Power substation equipment and transmission lines connected to power grid';
  parsed.scenes[3].shots[0].must_show=[
    'power substation',
    'transmission lines'
  ];
  parsed.scenes[3].shots[0].queries_en=[
    'power substation equipment',
    'electrical transmission grid',
    'power substation'
  ];

  parsed.narration=parsed.scenes.map(s=>s.narration).join(' ');
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  const out=run9537(fixture);
  assert.equal(
    out.storyboard.scenes[3].shots[0].must_show[0],
    'power substation'
  );
});

test('9609 regression: anaphoric segment may switch to a new primary explicitly named in current narration',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );

  parsed.scenes[2].narration='na łopatki turbiny,';
  parsed.scenes[2].shots[0].visual_intent=
    'Water turbine runner blades inside a hydro plant';
  parsed.scenes[2].shots[0].must_show=['water turbine'];
  parsed.scenes[2].shots[0].queries_en=[
    'water turbine runner blades',
    'hydroelectric turbine mechanism',
    'water turbine'
  ];

  parsed.scenes[3].narration='która wprawia w ruch generator';
  parsed.scenes[3].shots[0].visual_intent=
    'Electric generator machine inside a power station';
  parsed.scenes[3].shots[0].must_show=['electric generator'];
  parsed.scenes[3].shots[0].queries_en=[
    'electric generator turbine room',
    'hydroelectric generator equipment',
    'electric generator'
  ];

  parsed.narration=parsed.scenes.map(s=>s.narration).join(' ');
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  const out=run9537(fixture);
  assert.equal(
    out.storyboard.scenes[3].shots[0].must_show[0],
    'electric generator'
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
    assert.match(code,/resolve its actual antecedent from the previous narration/);
    assert.match(code,/do not force the previous shot primary/);
    assert.match(code,/never use an object unrelated to the actual antecedent\/current clause/);
    assert.doesNotMatch(code,/must not start as a continuation fragment/);
  }
});


test('9633 regression: cross-language no-match cannot invent previous visual primary as antecedent',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  fixture['Build Script Prompt'].word_min=18;
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );

  parsed.scenes[0].narration='Ogromny zbiornik wodny gromadzi wodę,';
  parsed.scenes[0].shots[0].visual_intent=
    'Large water reservoir behind a concrete dam capturing river water';
  parsed.scenes[0].shots[0].must_show=['water reservoir','concrete dam'];
  parsed.scenes[0].shots[0].must_not_show=['turbines','generators'];
  parsed.scenes[0].shots[0].queries_en=[
    'large water reservoir behind concrete dam',
    'aerial view hydroelectric reservoir',
    'water reservoir'
  ];

  parsed.scenes[1].narration='która spada z wysokości.';
  parsed.scenes[1].shots[0].visual_intent=
    'Water falling through a massive penstock pipe in a hydroelectric facility';
  parsed.scenes[1].shots[0].must_show=['penstock pipe'];
  parsed.scenes[1].shots[0].must_not_show=['turbines','generators'];
  parsed.scenes[1].shots[0].queries_en=[
    'water falling through penstock pipe',
    'hydroelectric penstock pipe',
    'penstock pipe'
  ];

  parsed.narration=parsed.scenes.map(s=>s.narration).join(' ');
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  const out=run9537(fixture);
  assert.deepEqual(
    out.storyboard.scenes[1].shots[0].must_show,
    ['penstock pipe']
  );
});

test('all storyboard validators require positive lexical evidence before inherited-primary restriction',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
  ]){
    const code=byName[name].parameters.jsCode;
    assert.match(
      code,
      /if \(!matchingIndexes\.length\) return false;/,
      name
    );
    assert.match(
      code,
      /return Math\.max\(\.\.\.matchingIndexes\) === narrationTerms\.length - 1;/,
      name
    );
  }
});


test('9699 repair builders expand stripped anaphoric validator errors generically',()=>{
  const ctx={
    script_run_id:'run-9699',
    model:'gemini-3.5-flash-lite',
    system_message:'SYSTEM',
    user_message:'BASE USER MESSAGE',
    target_scenes:5,
    target_shots:5,
    target_words:27,
  };
  const response=text=>({
    statusCode:200,
    body:{candidates:[{content:{parts:[{text}]}}]},
  });
  const run=(name,$json,values)=>{
    const $=nodeName=>({
      first:()=>({json:values[nodeName]}),
    });
    return new Function('$','$json',byName[name].parameters.jsCode)($,$json).json;
  };
  const stripped='previous machine '+String.fromCharCode(45,62)+' unrelated object [line 698]';

  const first=run(
    'Build Storyboard Repair',
    {error:stripped},
    {
      'Build Script Prompt':ctx,
      'Generate Storyboard':response('{"narration":"x","scenes":[]}'),
    }
  );
  assert.match(first.user_message,/Anaphoric visual-primary mismatch/);
  assert.match(first.user_message,/previous primary "previous machine"/);
  assert.match(first.user_message,/Rejected current primary: "unrelated object"/);

  const second=run(
    'Build Storyboard Repair 2',
    {error:stripped},
    {
      'Build Script Prompt':ctx,
      'Repair Storyboard':response('{"narration":"x","scenes":[]}'),
      'Generate Storyboard':response('{"narration":"x","scenes":[]}'),
      'Validate Storyboard':{error:'first validation failed'},
    }
  );
  assert.match(second.user_message,/Anaphoric visual-primary mismatch/);
  assert.match(second.user_message,/do not merely rename the unrelated object/);

  const unrelated=run(
    'Build Storyboard Repair',
    {error:'visual metadata must be English'},
    {
      'Build Script Prompt':ctx,
      'Generate Storyboard':response('{"narration":"x","scenes":[]}'),
    }
  );
  assert.match(unrelated.user_message,/visual metadata must be English/);
  assert.doesNotMatch(unrelated.user_message,/Anaphoric visual-primary mismatch/);
});


test('photo storyboard guard allows diagrams only when shown on a physical display surface',()=>{
  for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2','Validate Narration Language Repair']){
    const code=byName[name].parameters.jsCode;
    assert.match(code,/representationalPattern = \/\\b\(diagram\|schematic\|infographic\|flowchart\)\\b\/i/,name);
    assert.match(code,/physicalPresentationPattern = \/\\b\(screen\|monitor\|display\|whiteboard\|projection\|projector\)\\b\/i/,name);
    assert.match(code,/hasRepresentationalContent && !representedOnPhysicalSurface/,name);
  }
});


test('photo-only visual contract rejects hidden compact-object interiors without an explicit visible view',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );
  parsed.scenes[1].shots[0]={
    shot_id:'S2-A',
    visual_intent:'water turbine interior showing runner blades and shaft',
    must_show:['water turbine'],
    must_not_show:['solar panel'],
    queries_en:[
      'water turbine runner blades',
      'hydroelectric water turbine',
      'water turbine',
    ],
    preferred_media_type:'photo',
  };
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  assert.throws(
    ()=>run9537(fixture),
    /photo visual_intent requests hidden\/internal detail without an explicit open, cutaway, exposed, transparent, or disassembled view/
  );
});

test('photo-only visual contract allows explicit cutaway and ordinary spatial inside context',()=>{
  const fixture=JSON.parse(
    fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json')
  );
  const parsed=JSON.parse(
    fixture.response.body.candidates[0].content.parts[0].text
  );
  parsed.scenes[1].shots[0]={
    shot_id:'S2-A',
    visual_intent:'water turbine cutaway showing runner blades and shaft',
    must_show:['water turbine'],
    must_not_show:['solar panel'],
    queries_en:[
      'water turbine runner blades',
      'hydroelectric water turbine',
      'water turbine',
    ],
    preferred_media_type:'photo',
  };
  fixture.response.body.candidates[0].content.parts[0].text=
    JSON.stringify(parsed);

  const out=run9537(fixture);
  assert.equal(out.scene_count,5);
  assert.match(
    out.storyboard.scenes[2].shots[0].visual_intent,
    /inside a power station hall/
  );
});

test('all M5 visual acceptance paths enforce the hidden-internal photo retrievability guard',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
    'Canonicalize Final Storyboard',
    'Validate Narration Language Repair',
  ]){
    const code=byName[name].parameters.jsCode;
    assert.match(code,/requestsHiddenInternalView/,name);
    assert.match(code,/explicitlyInsidePrimary/,name);
    assert.match(code,/photo visual_intent requests hidden\/internal detail/,name);
  }
});

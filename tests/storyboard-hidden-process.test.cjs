const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodeCode=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function helper(name){
  const src=nodeCode(name);
  const start=src.indexOf('function dependentSecondaryAnchors');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' helper missing');
  return new Function(src.slice(start,end)+'; return normalizeMustShowAnchors;')();
}

function hiddenIntentHelper(name){
  const src=nodeCode(name);
  const start=src.indexOf('function dependentSecondaryAnchors');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' hidden intent helper missing');
  return new Function(src.slice(start,end)+'; return canonicalizeHiddenPrimaryPhotoIntent;')();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard'
]){
  test(name+': closed penstock promotes equipment over hidden flowing-water process',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['flowing water','penstock'],
        'Water falling down through a penstock in a hydroelectric plant'
      ),
      ['penstock']
    );
  });

  test(name+': transparent conduit keeps actually visible material as primary',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['flowing water','glass tube'],
        'Flowing water visible through a transparent glass tube'
      ),
      ['flowing water','glass tube']
    );
  });

  test(name+': clear water does not make a closed penstock transparent',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['flowing water','penstock'],
        'Clear flowing water moving through a penstock'
      ),
      ['penstock']
    );
  });

  test(name+': open visible process is not rewritten just because a second object exists',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['flowing water','spillway'],
        'Flowing water cascading over an open spillway'
      ),
      ['flowing water','spillway']
    );
  });


  test(name+': closed penstock primary drops hidden flowing-water secondary gate',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['penstock pipe','flowing water'],
        'Large penstock pipe directing water downward in a power plant'
      ),
      ['penstock pipe']
    );
  });

  test(name+': exposed penstock may keep a genuinely visible flowing-water secondary',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['penstock pipe','flowing water'],
        'Exposed cutaway penstock pipe with visibly flowing water'
      ),
      ['penstock pipe','flowing water']
    );
  });

  test(name+': electric current inside cable promotes the visible cable',()=>{
    const normalize=helper(name);
    assert.deepEqual(
      normalize(
        ['electric current','power cable'],
        'Electric current moving through a power cable'
      ),
      ['power cable']
    );
  });
}


for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard'
]){
  test(name+': fan motor hidden functional intent canonicalizes to the visible primary',()=>{
    const canonicalize=hiddenIntentHelper(name);
    assert.equal(
      canonicalize(
        ['electric motor'],
        'An electric motor inside a fan providing rotational energy to the rotor'
      ),
      'A clear photo of electric motor.'
    );
  });

  test(name+': power station hall remains ordinary spatial context',()=>{
    const canonicalize=hiddenIntentHelper(name);
    const intent='A generator inside a power station hall beside control equipment';
    assert.equal(canonicalize(['generator'],intent),intent);
  });

  test(name+': explicitly exposed fan motor remains a contextual photo intent',()=>{
    const canonicalize=hiddenIntentHelper(name);
    const intent='An exposed electric motor inside an open fan housing beside the rotor';
    assert.equal(canonicalize(['electric motor'],intent),intent);
  });

  test(name+': independent second subject prevents primary-only hidden-process collapse',()=>{
    const canonicalize=hiddenIntentHelper(name);
    const intent='An electric motor driving a visible rotor with a belt';
    assert.equal(canonicalize(['electric motor','drive belt'],intent),intent);
  });
}

test('generation and storyboard repair prompts explicitly forbid hidden-process hard visual gates',()=>{
  assert.match(nodeCode('Build Script Prompt'),/CLOSED conduit or machine/);
  for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
    assert.match(nodeCode(name),/hidden inside a closed conduit or machine/);
  }
});

test('generation and repair keep rarely photographed actions in narration instead of making them photo gates',()=>{
  for(const name of ['Build Script Prompt','Build Storyboard Repair','Build Storyboard Repair 2']){
    const src=nodeCode(name);
    assert.match(src,/short-lived, hidden, or rarely photographed action/);
    assert.match(src,/leave the action in narration unless a real photograph of that action is realistically searchable/);
    assert.match(src,/Do not demand the action in visual_intent merely because narration describes it/);
  }
});

test('photo-only storyboard rejects diagrammatic depictions as well as diagrams',()=>{
  for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2','Validate Narration Language Repair']){
    const src=nodeCode(name);
    const match=src.match(/const representationalPattern = (\/[^;]+\/i);/);
    assert.ok(match,name+' representational guard missing');
    const pattern=Function('return '+match[1])();
    assert.ok(pattern.test('diagrammatic representation of a magnetic field'));
    assert.ok(pattern.test('schematic representation of a circuit'));
    assert.equal(pattern.test('physical globe showing a compass'),false);
  }
});

test('final visual scene has enough spoken words for independent ASR coverage',()=>{
  for(const name of [
    'Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2',
    'Validate Timing Repair','Validate Timing Repair 2','Validate Narration Language Repair'
  ]){
    const src=nodeCode(name);
    assert.match(src,/const minSceneWords = i === scenes.length - 1 && Number\(ctx.target_duration_seconds\) === 30 \? 6 : 2;/);
    assert.doesNotThrow(()=>new Function(src),name+' JS syntax');
  }
  for(const name of [
    'Build Script Prompt','Build Storyboard Repair','Build Storyboard Repair 2',
    'Build Timing Repair','Build Timing Repair 2'
  ]){
    const src=nodeCode(name);
    assert.match(src,/For 30-second videos, the final scene narration must contain at least 6 spoken words/);
    assert.doesNotThrow(()=>new Function(src),name+' JS syntax');
  }
});

test('30-second word plan reserves six words for the terminal scene without adding speech',()=>{
  const src=nodeCode('Build Script Prompt');
  const start=src.indexOf('const sceneWordTargets =');
  const end=src.indexOf('const maxSegmentWords =',start);
  assert.ok(start>=0 && end>start);
  const allocate=new Function('targetWords','density','duration',src.slice(start,end)+'; return sceneWordTargets;');
  const long=allocate(53,{targetScenes:9},30);
  assert.equal(long.reduce((a,b)=>a+b,0),53);
  assert.equal(long.at(-1),6);
  assert.equal(long.at(-2),5);
  const short=allocate(27,{targetScenes:5},15);
  assert.equal(short.reduce((a,b)=>a+b,0),27);
  assert.deepEqual(short,[6,6,5,5,5]);
});

test('final canonicalizer reanchors queries to the normalized primary subject',()=>{
  const src=nodeCode('Canonicalize Final Storyboard');
  assert.match(src,/const mustShow = normalizeMustShowAnchors\(rawMustShow, visualIntent, shotId\)/);
  assert.match(src,/return primary;/);
  assert.match(src,/shot\.queries_en = queries;/);
});


test('exact v54 S2 final canonicalization makes penstock the searchable subject',()=>{
  const code=nodeCode('Canonicalize Final Storyboard');
  const source={
    storyboard:{
      narration:'Następnie spada w dół.',
      scenes:[{
        scene_id:'S1',
        narration:'Następnie spada w dół.',
        evidence_ids:['E1'],
        shots:[{
          shot_id:'S1-A',
          visual_intent:'Water falling down through a penstock in a hydroelectric plant',
          must_show:['flowing water','penstock'],
          must_not_show:['steam turbine','wind turbine'],
          queries_en:[
            'flowing water falling through penstock',
            'water dropping inside hydroelectric plant',
            'flowing water'
          ],
          preferred_media_type:'photo',
        }],
      }],
    },
  };
  const $=name=>{
    if(name==='Build Script Prompt')return {first:()=>({json:{
      language_code:'pl',
      target_duration_seconds:15,
      target_scenes:1,
      word_min:2,
      word_max:10,
    }})};
    if(name==='Normalize Timing Probe')return {first:()=>({json:{
      storyboard:{scenes:[{narration:'Następnie spada w dół.'}]},
    }})};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code)($,source).json.storyboard.scenes[0].shots[0];
  assert.deepEqual(out.must_show,['penstock']);
  assert.deepEqual(out.queries_en,[
    'flowing water falling through penstock',
    'water dropping inside hydroelectric plant penstock',
    'penstock'
  ]);
});

test('11342 cosmic background signal remains photographable but digital map and decorative background fail',()=>{
  const validators=[
    'Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2',
    'Validate Timing Repair','Validate Timing Repair 2',
    'Validate Narration Language Repair','Validate Narration Language Repair Retry',
  ];
  for(const name of validators){
    const src=nodeCode(name);
    const begin=src.indexOf('const queryFillerPattern =');
    const end=src.indexOf('const antiSelectionText =',begin);
    assert.ok(begin>=0 && end>begin,name+' visual guard missing');
    const validate=new Function('visualIntent','queries','mustShow','shotId',src.slice(begin,end));
    const instrument='Astrophysical antenna instrument pointing to the sky capturing cosmic background signals';
    assert.doesNotThrow(()=>validate(instrument,[
      'astrophysical antenna instrument sky',
      'radio telescope background signals',
      'astrophysical antenna',
    ],['astrophysical antenna'],'S6-A'),name+' physical signal');
    assert.throws(()=>validate('Cosmic microwave background radiation map showing temperature fluctuations across the sky',[
      'cosmic microwave background radiation map',
      'microwave background sky fluctuations',
      'microwave background',
    ],['microwave background'],'S6-A'),/generic\/non-photographic/,name+' digital map');
    assert.throws(()=>validate(instrument,['beautiful background landscape'],['astrophysical antenna'],'S6-A'),
      /generic\/non-photographic/,name+' decorative background');
  }
});

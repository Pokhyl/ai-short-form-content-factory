const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodeCode=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function helper(name){
  const src=nodeCode(name);
  const start=src.indexOf('function normalizeMustShowAnchors');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' helper missing');
  return new Function(src.slice(start,end)+'; return normalizeMustShowAnchors;')();
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

test('generation and storyboard repair prompts explicitly forbid hidden-process hard visual gates',()=>{
  assert.match(nodeCode('Build Script Prompt'),/CLOSED conduit or machine/);
  for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
    assert.match(nodeCode(name),/hidden inside a closed conduit or machine/);
  }
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

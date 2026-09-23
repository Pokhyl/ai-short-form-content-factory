const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

const pairs=[
  ['Generate Storyboard','Validate Storyboard'],
  ['Repair Storyboard','Validate Repaired Storyboard'],
  ['Repair Storyboard 2','Validate Repaired Storyboard 2'],
  ['Repair Storyboard Timing','Validate Timing Repair'],
  ['Repair Storyboard Timing 2','Validate Timing Repair 2'],
  ['Repair Timing Precision Retry','Validate Timing Precision Retry'],
  ['Repair Final Duration','Validate Final Duration Repair'],
  ['Repair Final Word Count','Validate Final Word Count Retry'],
  ['Repair Final Measured Correction','Validate Final Measured Correction'],
  ['Repair Final Measured Word Count','Validate Final Measured Word Count Retry'],
  ['Repair Final Measured Word Count Compliance','Validate Final Measured Word Count Compliance Retry'],
];

test('all Gemini HTTP nodes expose errors on main output so n8n retry detector can see json.error',()=>{
  for(const [httpName] of pairs){
    const node=byName[httpName];
    assert.equal(node.type,'n8n-nodes-base.httpRequest',httpName);
    assert.equal(node.retryOnFail,true,httpName);
    assert.equal(node.maxTries,5,httpName);
    assert.equal(node.waitBetweenTries,10000,httpName);
    assert.equal(node.onError,'continueRegularOutput',httpName);
  }
});

test('all Gemini validators preserve provider failure after transient retries and stay inside existing bounded error routing',()=>{
  const expectedErrorTargets={
    'Validate Storyboard':'Build Storyboard Repair',
    'Validate Repaired Storyboard':'Build Storyboard Repair 2',
    'Validate Repaired Storyboard 2':'Prepare Script Failure',
    'Validate Timing Repair':'Build Timing Repair 2',
    'Validate Timing Repair 2':'Build Timing Precision Retry',
    'Validate Timing Precision Retry':'Prepare Script Failure',
    'Validate Final Duration Repair':'Prepare Script Failure',
    'Validate Final Word Count Retry':'Prepare Script Failure',
    'Validate Final Measured Correction':'Prepare Script Failure',
    'Validate Final Measured Word Count Retry':'Classify Final Measured Word Count Retry Failure',
    'Validate Final Measured Word Count Compliance Retry':'Prepare Script Failure',
  };

  for(const [httpName,validatorName] of pairs){
    const validator=byName[validatorName];
    assert.match(
      validator.parameters.jsCode,
      /Gemini provider failed after transient retries/,
      validatorName
    );
    assert.equal(validator.onError,'continueErrorOutput',validatorName);

    const branches=workflow.connections[validatorName]?.main;
    assert.ok(Array.isArray(branches),validatorName);
    assert.equal(
      branches[1]?.[0]?.node,
      expectedErrorTargets[validatorName],
      validatorName+' bounded error output'
    );

    const httpBranches=workflow.connections[httpName]?.main;
    assert.equal(
      httpBranches[0]?.[0]?.node,
      validatorName,
      httpName+' main output'
    );
  }
});

test('provider guard surfaces exact final provider message instead of hiding it as a parse error',()=>{
  const code=byName['Validate Storyboard'].parameters.jsCode;
  const marker='const ctx =';
  const cut=code.indexOf(marker);
  assert.ok(cut>0);
  const guard=code.slice(0,cut);

  assert.throws(
    ()=>new Function('$json',guard+'return true;')({
      error:{
        description:'This model is currently experiencing high demand.',
        message:'Service unavailable',
      },
    }),
    /Gemini provider failed after transient retries: This model is currently experiencing high demand/
  );

  assert.equal(
    new Function('$json',guard+'return true;')({body:{}}),
    true
  );
});


test('execution 9499 regression: second storyboard repair falls back to original successful draft after repair provider 503',()=>{
  const code=byName['Build Storyboard Repair 2'].parameters.jsCode;
  const originalText='{"narration":"four scenes","scenes":[1,2,3,4]}';
  const refs={
    'Build Script Prompt':{
      script_run_id:'run-9499',
      model:'gemini-3.5-flash-lite',
      system_message:'SYSTEM',
      user_message:'USER',
      target_scenes:5,
      target_shots:5,
      target_words:28,
      language_code:'pl',
    },
    'Repair Storyboard':{
      error:{
        description:'This model is currently experiencing high demand.',
        message:'Service unavailable',
      },
    },
    'Generate Storyboard':{
      body:{
        candidates:[{
          content:{parts:[{text:originalText}]},
        }],
      },
    },
    'Validate Storyboard':{
      error:'4, required exactly 5 [line 140]',
    },
  };
  const $=name=>({first:()=>({json:refs[name]})});

  const out=new Function('$','$json',code)(
    $,
    {
      error:{
        description:'This model is currently experiencing high demand.',
        message:'Service unavailable',
      },
    }
  ).json;

  assert.equal(out.script_run_id,'run-9499');
  assert.match(out.user_message,/4, required exactly 5/);
  assert.match(
    out.user_message,
    /Previous repair provider failed after retries: This model is currently experiencing high demand/
  );
  assert.match(out.user_message,/\{"narration":"four scenes"/);
  assert.doesNotMatch(out.user_message,/first Gemini output is empty/);
});

test('second storyboard repair prefers a usable first repair draft over the original draft',()=>{
  const code=byName['Build Storyboard Repair 2'].parameters.jsCode;
  const refs={
    'Build Script Prompt':{
      script_run_id:'run-x',
      model:'gemini',
      system_message:'SYSTEM',
      user_message:'USER',
      target_scenes:5,
      target_shots:5,
      target_words:28,
      language_code:'pl',
    },
    'Repair Storyboard':{
      body:{candidates:[{content:{parts:[{text:'REPAIR_DRAFT'}]}}]},
    },
    'Generate Storyboard':{
      body:{candidates:[{content:{parts:[{text:'ORIGINAL_DRAFT'}]}}]},
    },
    'Validate Storyboard':{error:'original error'},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {error:'repair validation error'}
  ).json;
  assert.match(out.user_message,/REPAIR_DRAFT/);
  assert.doesNotMatch(out.user_message,/ORIGINAL_DRAFT/);
  assert.match(out.user_message,/repair validation error/);
});

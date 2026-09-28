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

const helper=JSON.parse(
  fs.readFileSync('workflows/VIDEO-Gemini-Resilient-Call.json')
);
const helperByName=Object.fromEntries(helper.nodes.map(n=>[n.name,n]));

test('all Gemini call sites delegate to the shared resilient helper without changing node names',()=>{
  for(const [callName] of pairs){
    const node=byName[callName];
    assert.equal(node.type,'n8n-nodes-base.executeWorkflow',callName);
    assert.equal(node.parameters.workflowId.value,'VideoGeminiResilient001',callName);
    assert.equal(node.parameters.workflowInputs.value.request_label,callName);
    assert.match(node.parameters.workflowInputs.value.request_body,/JSON\.stringify/,callName);
  }
});

test('shared Gemini helper uses bounded model rotation with transient-only backoff',()=>{
  for(const name of ['Gemini Primary','Gemini Fallback','Gemini Final','Gemini Reserve 3.6','Gemini Reserve 3.7','Gemini Recovery 3.8']){
    const node=helperByName[name];
    assert.equal(node.type,'n8n-nodes-base.httpRequest',name);
    assert.equal(node.retryOnFail,false,name);
    assert.equal(node.maxTries,1,name);
    assert.equal(node.parameters.options.timeout,45000,name);
    assert.equal(node.onError,'continueRegularOutput',name);
    assert.equal(node.parameters.body,"={{ $('When Executed by Another Workflow').first().json.request_body }}",name);
  }
  assert.equal(helperByName['Wait 30s'].parameters.amount,30);
  assert.equal(helperByName['Wait 30s'].parameters.unit,'seconds');
  assert.equal(helperByName['Wait 60s'].parameters.amount,60);
  assert.equal(helperByName['Wait 60s'].parameters.unit,'seconds');
  assert.equal(helperByName['Wait 120s Reserve 1'].parameters.amount,120);
  assert.equal(helperByName['Wait 240s Reserve 2'].parameters.amount,240);
  assert.equal(helperByName['Wait 600s Recovery'].parameters.amount,600);
  assert.match(helperByName['Gemini Fallback'].parameters.url,/gemini-3\.1-flash-lite/);
  assert.match(helperByName['Gemini Primary'].parameters.url,/primary_model/);
  assert.match(helperByName['Gemini Final'].parameters.url,/gemini-3\.8-flash/);
  assert.match(helperByName['Gemini Reserve 3.6'].parameters.url,/gemini-3\.6-flash/);
  assert.match(helperByName['Gemini Reserve 3.7'].parameters.url,/gemini-3\.7-flash/);
  assert.match(helperByName['Gemini Recovery 3.8'].parameters.url,/gemini-3\.8-flash/);
});

test('shared helper retries only transient provider failures and preserves successful or non-transient responses',()=>{
  const code=helperByName['Classify Primary Result'].parameters.jsCode;
  const run=value=>new Function('$json',code)(value).json;

  const highDemand=run({error:{description:'This model is currently experiencing high demand.'}});
  assert.equal(highDemand._provider_transient,true);

  const unavailable=run({error:{httpCode:503,message:'Service unavailable'}});
  assert.equal(unavailable._provider_transient,true);

  const badRequest=run({error:{httpCode:400,description:'Request contains an invalid argument.'}});
  assert.equal(badRequest._provider_transient,false);

  const ok=run({statusCode:200,body:{candidates:[{content:{parts:[{text:'{}'}]}}]}});
  assert.equal(ok._provider_transient,false);

  assert.equal(helper.connections['Retry Primary?'].main[0][0].node,'Wait 30s');
  assert.equal(helper.connections['Retry Primary?'].main[1][0].node,'Return Provider Result');
  assert.equal(helper.connections['Retry Fallback?'].main[0][0].node,'Wait 60s');
  assert.equal(helper.connections['Retry Fallback?'].main[1][0].node,'Return Provider Result');
  assert.equal(helper.connections['Retry Final?'].main[0][0].node,'Wait 120s Reserve 1');
  assert.equal(helper.connections['Retry Final?'].main[1][0].node,'Return Provider Result');
  assert.equal(helper.connections['Retry Reserve 3.6?'].main[0][0].node,'Wait 240s Reserve 2');
  assert.equal(helper.connections['Retry Reserve 3.6?'].main[1][0].node,'Return Provider Result');
  assert.equal(helper.connections['Gemini Reserve 3.7'].main[0][0].node,'Classify Reserve 3.7 Result');
  assert.equal(helper.connections['Retry Reserve 3.7?'].main[0][0].node,'Wait 600s Recovery');
  assert.equal(helper.connections['Retry Reserve 3.7?'].main[1][0].node,'Return Provider Result');
  assert.equal(helper.connections['Wait 600s Recovery'].main[0][0].node,'Gemini Recovery 3.8');
  assert.equal(helper.connections['Gemini Recovery 3.8'].main[0][0].node,'Return Provider Result');
});

test('shared helper returns the original provider response shape without internal retry metadata',()=>{
  const code=helperByName['Return Provider Result'].parameters.jsCode;
  const input={
    statusCode:200,
    body:{candidates:[{content:{parts:[{text:'{"ok":true}'}]}}]},
    _provider_transient:false,
  };
  const out=new Function('$json',code)(input).json;
  assert.equal(out.statusCode,200);
  assert.deepEqual(out.body,input.body);
  assert.equal(Object.hasOwn(out,'_provider_transient'),false);
});

test('all Gemini validators preserve provider failure after transient retries and stay inside existing bounded error routing',()=>{
  const expectedErrorTargets={
    'Validate Storyboard':'Build Storyboard Repair',
    'Validate Repaired Storyboard':'Build Storyboard Repair 2',
    'Validate Repaired Storyboard 2':'Prepare Script Failure',
    'Validate Timing Repair':'Build Timing Repair 2',
    'Validate Timing Repair 2':'Prepare Script Failure',
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

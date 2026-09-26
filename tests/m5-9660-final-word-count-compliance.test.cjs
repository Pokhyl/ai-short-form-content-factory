const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')
);
const fixture=JSON.parse(
  fs.readFileSync('tests/fixtures/m5-9660-final-word-count-compliance.json')
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));
const code=name=>byName[name].parameters.jsCode;

function runCode(name,$json,values){
  const $=nodeName=>{
    if(!(nodeName in values)) throw new Error('missing mock node '+nodeName);
    return {first:()=>({json:values[nodeName]})};
  };
  return new Function('$','$json',code(name))($,$json).json;
}

test('9660 failure is classified for exactly one compliance retry',()=>{
  const retry=runCode(
    'Classify Final Measured Word Count Retry Failure',
    {error:{message:fixture.source.failure}},
    {}
  );
  assert.equal(retry.compliance_retry,true);

  const execution9687=runCode(
    'Classify Final Measured Word Count Retry Failure',
    {error:'got 27, target 31, allowed delta 2 [line 431]'},
    {}
  );
  assert.equal(execution9687.compliance_retry,true);
  assert.equal(
    execution9687.compliance_retry_error_message,
    'got 27, target 31, allowed delta 2 [line 431]'
  );

  const other=runCode(
    'Classify Final Measured Word Count Retry Failure',
    {error:{message:'semantic content changed'}},
    {}
  );
  assert.equal(other.compliance_retry,false);

  const unrelatedString=runCode(
    'Classify Final Measured Word Count Retry Failure',
    {error:'Gemini HTTP 503: overloaded'},
    {}
  );
  assert.equal(unrelatedString.compliance_retry,false);
});

test('9660 compliance builder reports the exact failed provider counts and hard targets',()=>{
  const out=runCode(
    'Build Final Measured Word Count Compliance Retry',
    {compliance_retry:true},
    {
      'Build Final Measured Word Count Retry':
        fixture.build_final_measured_word_count_retry,
      'Repair Final Measured Word Count':
        fixture.repair_final_measured_word_count,
      'Normalize Timing Probe':
        fixture.normalize_timing_probe,
      'Build Script Prompt':
        fixture.build_script_prompt,
    }
  );

  assert.equal(out.target_words,29);
  assert.deepEqual(out.target_scene_word_counts,[10,6,4,4,5]);
  assert.equal(out.previous_returned_words,22);
  assert.deepEqual(
    out.previous_returned_scene_word_counts,
    [8,4,3,3,4]
  );
  assert.match(out.user_message,/PREVIOUS ATTEMPT FAILED THE WORD-COUNT CONTRACT/);
  assert.match(out.user_message,/REQUIRED TOTAL WORDS \(HARD\): exactly 29/);
  assert.match(
    out.user_message,
    /REQUIRED PER-SCENE WORD COUNTS \(HARD\): \[10,6,4,4,5\]/
  );
  assert.match(out.system_message,/never move or borrow content words from adjacent scenes/);
  assert.match(out.user_message,/do not move or borrow content words from the previous or next scene/);
  assert.doesNotMatch(out.user_message,/adjacent scene boundaries MAY move/);
  assert.match(out.system_message,/expand the SAME already-stated proposition/);
  assert.match(out.user_message,/rewrite the same proposition naturally/);
  assert.match(out.user_message,/never reach the count with intensifiers, decorative adjectives\/adverbs, generic qualifiers, or redundant closing phrases/);
  assert.match(out.system_message,/ONLY semantic source/);
  assert.match(out.user_message,/output only the narration_words JSON object/);
  assert.doesNotMatch(out.system_message,/key named narrations/);
  assert.doesNotMatch(out.user_message,/return exactly .* strings/);
  assert.doesNotMatch(out.user_message,/five strings/);
  assert.doesNotMatch(out.user_message,/CURRENT SEMANTIC-VALID FULL NARRATION/);
  assert.doesNotMatch(out.user_message,/current_narration/);
  assert.doesNotMatch(out.user_message,/previous_attempt"/);
});

test('9660 compliance validator accepts a semantic-valid exact 29-word repair',()=>{
  const build=runCode(
    'Build Final Measured Word Count Compliance Retry',
    {compliance_retry:true},
    {
      'Build Final Measured Word Count Retry':
        fixture.build_final_measured_word_count_retry,
      'Repair Final Measured Word Count':
        fixture.repair_final_measured_word_count,
      'Normalize Timing Probe':
        fixture.normalize_timing_probe,
      'Build Script Prompt':
        fixture.build_script_prompt,
    }
  );

  const narrations=[
    'Woda gromadzi się w specjalnym zbiorniku znajdującym się za tamą.',
    'Następnie spada w dół z wysokości,',
    'poruszając tę turbinę wodną,',
    'która napędza ten generator',
    'i skutecznie wytwarza prąd elektryczny.',
  ];
  assert.deepEqual(
    narrations.map(x=>x.trim().split(/\s+/u).length),
    [10,6,4,4,5]
  );

  const response={
    statusCode:200,
    body:{
      candidates:[{
        content:{parts:[{text:JSON.stringify({narrations})}]},
      }],
      usageMetadata:{
        promptTokenCount:600,
        candidatesTokenCount:80,
        totalTokenCount:680,
      },
    },
  };

  const out=runCode(
    'Validate Final Measured Word Count Compliance Retry',
    response,
    {
      'Build Final Measured Word Count Compliance Retry':build,
      'Build Script Prompt':fixture.build_script_prompt,
      'Build Final Measured Correction':
        fixture.build_final_measured_correction,
      'Normalize Timing Probe':fixture.normalize_timing_probe,
    }
  );

  assert.equal(out.narration_word_count,29);
  assert.equal(out.target_word_count,29);
  assert.equal(out.word_count_exact,true);
  assert.equal(out.scene_count,5);
  assert.equal(out.storyboard.scenes.length,5);
});

test('9822-style over-limit scene is excluded and recovered from semantic-valid drafts',()=>{
  const build=runCode(
    'Build Final Measured Word Count Compliance Retry',
    {compliance_retry:true},
    {
      'Build Final Measured Word Count Retry':
        fixture.build_final_measured_word_count_retry,
      'Repair Final Measured Word Count':
        fixture.repair_final_measured_word_count,
      'Normalize Timing Probe':
        fixture.normalize_timing_probe,
      'Build Script Prompt':
        fixture.build_script_prompt,
    }
  );

  const narrations=[
    'Woda właśnie gromadzi się w specjalnym zbiorniku znajdującym się za tamą.',
    'Następnie spada w dół z wysokości,',
    'poruszając tę turbinę wodną,',
    'która napędza ten generator',
    'i skutecznie wytwarza prąd elektryczny.',
  ];
  assert.deepEqual(
    narrations.map(x=>x.trim().split(/\s+/u).length),
    [11,6,4,4,5]
  );

  const response={
    statusCode:200,
    body:{
      candidates:[{
        content:{parts:[{text:JSON.stringify({narrations})}]},
      }],
      usageMetadata:{promptTokenCount:600,candidatesTokenCount:80,totalTokenCount:680},
    },
  };

  const out=runCode(
    'Validate Final Measured Word Count Compliance Retry',
    response,
    {
      'Build Final Measured Word Count Compliance Retry':build,
      'Build Script Prompt':fixture.build_script_prompt,
      'Build Final Measured Correction':
        fixture.build_final_measured_correction,
      'Normalize Timing Probe':fixture.normalize_timing_probe,
    }
  );

  assert.equal(out.narration_word_count,29);
  assert.equal(out.word_count_exact,true);
  assert.equal(out.deterministic_word_hybrid_used,true);
  assert.equal(
    out.storyboard.scenes[0].narration,
    fixture.build_final_measured_word_count_retry.base_storyboard.scenes[0].narration
  );
  assert.ok(
    out.storyboard.scenes.every(
      scene=>scene.narration.trim().split(/\s+/u).length<=10
    )
  );
});

test('9660 compliance retry remains bounded: another 22-word response still fails closed',()=>{
  const build=runCode(
    'Build Final Measured Word Count Compliance Retry',
    {compliance_retry:true},
    {
      'Build Final Measured Word Count Retry':
        fixture.build_final_measured_word_count_retry,
      'Repair Final Measured Word Count':
        fixture.repair_final_measured_word_count,
      'Normalize Timing Probe':
        fixture.normalize_timing_probe,
      'Build Script Prompt':
        fixture.build_script_prompt,
    }
  );

  assert.throws(
    ()=>runCode(
      'Validate Final Measured Word Count Compliance Retry',
      fixture.repair_final_measured_word_count,
      {
        'Build Final Measured Word Count Compliance Retry':build,
        'Build Script Prompt':fixture.build_script_prompt,
        'Build Final Measured Correction':
          fixture.build_final_measured_correction,
        'Normalize Timing Probe':fixture.normalize_timing_probe,
      }
    ),
    /too far from target before TTS: got 26, target 29, allowed delta 2/
  );
});

test('M5 graph has one bounded compliance branch and no retry loop',()=>{
  const c=workflow.connections;

  assert.deepEqual(
    c['Validate Final Measured Word Count Retry'].main[1],
    [{
      node:'Classify Final Measured Word Count Retry Failure',
      type:'main',
      index:0,
    }]
  );

  assert.deepEqual(
    c['Route Final Measured Word Count Compliance Retry'].main[0],
    [{
      node:'Build Final Measured Word Count Compliance Retry',
      type:'main',
      index:0,
    }]
  );

  assert.deepEqual(
    c['Validate Final Measured Word Count Compliance Retry'].main[0],
    [{
      node:'Prepare Timing Probe 5',
      type:'main',
      index:0,
    }]
  );

  assert.deepEqual(
    c['Validate Final Measured Word Count Compliance Retry'].main[1],
    [{
      node:'Prepare Script Failure',
      type:'main',
      index:0,
    }]
  );

  const allTargets=Object.values(c)
    .flatMap(x=>x.main||[])
    .flat()
    .map(x=>x.node);

  assert.ok(
    !c['Validate Final Measured Word Count Compliance Retry'].main
      .flat()
      .some(x=>x.node==='Build Final Measured Word Count Compliance Retry')
  );
  assert.ok(allTargets.includes('Prepare Timing Probe 5'));
});


test('10902-style exact-count semantic miss is routed into the semantic-safe hybrid',()=>{
  const build=runCode(
    'Build Final Measured Word Count Compliance Retry',
    {compliance_retry:true},
    {
      'Build Final Measured Word Count Retry':fixture.build_final_measured_word_count_retry,
      'Repair Final Measured Word Count':fixture.repair_final_measured_word_count,
      'Normalize Timing Probe':fixture.normalize_timing_probe,
      'Build Script Prompt':fixture.build_script_prompt,
    }
  );

  const good=[
    'Woda gromadzi się w specjalnym zbiorniku znajdującym się za tamą.',
    'Następnie spada w dół z wysokości,',
    'poruszając tę turbinę wodną,',
    'która napędza ten generator',
    'i skutecznie wytwarza prąd elektryczny.',
  ];
  const bad=[
    'Samochód jedzie szybko przez miasto obok domu podczas jasnego dnia.',
    ...good.slice(1),
  ];
  assert.deepEqual(bad.map(x=>x.trim().split(/\s+/u).length),[10,6,4,4,5]);

  const measuredStoryboard=JSON.parse(JSON.stringify(fixture.normalize_timing_probe.storyboard));
  measuredStoryboard.scenes=measuredStoryboard.scenes.map((scene,index)=>({
    ...scene,
    narration:good[index],
  }));
  measuredStoryboard.narration=good.join(' ');

  const response={
    statusCode:200,
    body:{
      candidates:[{content:{parts:[{text:JSON.stringify({narrations:bad})}]}}],
      usageMetadata:{promptTokenCount:600,candidatesTokenCount:80,totalTokenCount:680},
    },
  };

  const out=runCode(
    'Validate Final Measured Word Count Compliance Retry',
    response,
    {
      'Build Final Measured Word Count Compliance Retry':build,
      'Build Script Prompt':fixture.build_script_prompt,
      'Build Final Measured Correction':fixture.build_final_measured_correction,
      'Normalize Timing Probe':fixture.normalize_timing_probe,
      'Normalize Timing Probe 2':{storyboard:measuredStoryboard},
    }
  );

  assert.equal(out.narration_word_count,29);
  assert.equal(out.word_count_exact,true);
  assert.equal(out.deterministic_word_hybrid_used,true);
  assert.equal(out.storyboard.scenes[0].narration,good[0]);
  assert.notEqual(out.storyboard.scenes[0].narration,bad[0]);
});

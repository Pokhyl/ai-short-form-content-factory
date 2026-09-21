const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {test} = require('node:test');

const workflow = JSON.parse(
  fs.readFileSync(path.join(__dirname,'../workflows/VIDEO-M5-Script-Storyboard.json'))
);
const byName = Object.fromEntries(workflow.nodes.map(n => [n.name,n]));

function semanticGuard() {
  const code = byName['Validate Timing Precision Retry'].parameters.jsCode;
  const start = code.indexOf('// SEMANTIC_PRESERVATION_GUARD_START');
  const end = code.indexOf('// SEMANTIC_PRESERVATION_GUARD_END');
  assert.ok(start >= 0 && end > start);
  const helper = code.slice(start,end + '// SEMANTIC_PRESERVATION_GUARD_END'.length);
  return new Function(helper + '\nreturn assertSemanticPreservation;')();
}
const guard = semanticGuard();

const originalS1 =
  'Elektrownia wodna wykorzystuje energię wody do wytwarzania energii elektrycznej.';
const originalS2 =
  'Woda gromadzi się w zbiorniku za tamą.';

test('semantic guard accepts compact wording that preserves water-to-electricity mechanism', () => {
  assert.doesNotThrow(() =>
    guard(
      originalS1,
      'Elektrownia wodna wytwarza prąd z energii wody.',
      'S1',
      'pl'
    )
  );
});

test('semantic guard rejects current v84 precision corruption using force of current', () => {
  assert.throws(
    () => guard(
      originalS1,
      'Elektrownia wodna wykorzystuje siłę prądu do wytwarzania energii.',
      'S1',
      'pl'
    ),
    /semantic content|new content words/
  );
});

test('semantic guard rejects vague motion replacement from execution 9047', () => {
  assert.throws(
    () => guard(
      originalS1,
      'Elektrownia wodna wytwarza energię z ruchu.',
      'S1',
      'pl'
    ),
    /semantic content/
  );
});

test('semantic guard rejects adjective padding that drops dam context', () => {
  assert.throws(
    () => guard(
      originalS2,
      'Ogromna woda gromadzi się w wielkim zbiorniku.',
      'S2',
      'pl'
    ),
    /new content words/
  );
});

test('semantic guard accepts concise dam sentence that retains the actual relation', () => {
  assert.doesNotThrow(() =>
    guard(
      originalS2,
      'Woda gromadzi się za tamą.',
      'S2',
      'pl'
    )
  );
});

test('semantic guard rejects changed numbers and negation polarity', () => {
  assert.throws(
    () => guard('Generator ma 30 turbin.', 'Generator ma 40 turbin.','num','pl'),
    /numeric facts/
  );
  assert.throws(
    () => guard('Generator wytwarza prąd.', 'Generator nie wytwarza prądu.','neg','pl'),
    /negation polarity/
  );
});


test('v85 precision response filler and lost reservoir are rejected', () => {
  assert.throws(
    () => guard(
      'Zapora spiętrza rzekę, tworząc zbiornik.',
      'Ogromna zapora spiętrza rzekę.',
      'S2',
      'pl'
    ),
    /semantic content|filler/
  );
  assert.throws(
    () => guard(
      'Generator produkuje prąd elektryczny.',
      'Wydajny generator produkuje prąd.',
      'S4',
      'pl'
    ),
    /filler/
  );
  assert.throws(
    () => guard(
      'Prąd trafia do domów.',
      'Czysty prąd trafia domów.',
      'S5',
      'pl'
    ),
    /filler/
  );
});


test('9065 compact dam causality at 60 percent content coverage is accepted', () => {
  assert.doesNotThrow(() =>
    guard(
      'Zapora zatrzymuje rzekę, tworząc zbiornik.',
      'Zapora tworzy zbiornik.',
      'S2',
      'pl'
    )
  );
});

test('first timing validator is semantic fail-closed and rejects duplicate scene rewrites', () => {
  const code=byName['Validate Timing Repair'].parameters.jsCode;
  assert.match(code,/SEMANTIC_PRESERVATION_GUARD_START/);
  assert.match(code,/first timing repair produced duplicate scene narration/);
});

test('first timing validation failure routes to Repair 2 before another TTS probe', () => {
  const outputs=workflow.connections['Validate Timing Repair'].main;
  assert.equal(outputs[1][0].node,'Build Timing Repair 2');
  assert.equal(outputs[0][0].node,'Prepare Timing Probe 2');
});

test('initial storyboard prompt keeps every scene on the user topic and mechanism', () => {
  const code=byName['Build Script Prompt'].parameters.jsCode;
  assert.match(code,/every scene must directly advance the answer to TOPIC/);
  assert.match(code,/generic praise, benefits, environmental\/economic impact/);
  assert.match(code,/last scene must complete that mechanism\/result/);
  assert.match(code,/each scene must add a distinct necessary fact/);
});

test('Repair 2 fallback regenerates from immutable original without consuming failed draft as truth', () => {
  const code=byName['Build Timing Repair 2'].parameters.jsCode;
  const original=[
    'Elektrownia wodna zamienia energię spiętrzonej wody na prąd.',
    'Zapora zatrzymuje rzekę, tworząc zbiornik.',
    'Spadająca woda napędza turbinę.',
    'Generator wytwarza prąd elektryczny.',
    'Prąd trafia do domów.',
  ];
  const p1={
    storyboard:{narration:original.join(' '),scenes:original.map(narration=>({narration}))},
    measured_duration_ms:17424,
    target_duration_ms:15000,
    tolerance_ms:750,
    narration_word_count:28,
    script_run_id:'run',
    model:'gemini',
    usage:{promptTokenCount:10,candidatesTokenCount:20,totalTokenCount:30},
  };
  const ctx={
    topic:'jak działa elektrownia wodna?',
    language_code:'pl',
    target_duration_seconds:15,
    target_scenes:5,
    target_shots:5,
    word_min:21,
    word_max:33,
    user_message:'base',
  };
  const rows={
    'Normalize Timing Probe':p1,
    'Build Script Prompt':ctx,
    'Build Timing Repair':{prior_usage:{promptTokenCount:10,candidatesTokenCount:20,totalTokenCount:30}},
    'Repair Storyboard Timing':{body:{usageMetadata:{promptTokenCount:7,candidatesTokenCount:5,totalTokenCount:12}}},
  };
  const $=name=>{
    if(name==='Normalize Timing Stability B') return {all:()=>{throw Error('not executed')}};
    return {first:()=>({json:rows[name]})};
  };
  const out=new Function('$','$json',code)($,{error:{message:'semantic reject'}}).json;
  assert.equal(out.semantic_fallback_from_first_repair,true);
  assert.match(out.user_message,/SEMANTIC FALLBACK/);
  assert.ok(out.user_message.includes(original[0]));
  assert.equal(out.prior_usage.totalTokenCount,42);
  assert.ok(out.target_precision_words>=10 && out.target_precision_words<=50);
});

test('all late timing builders carry immutable original narration', () => {
  for (const name of [
    'Build Timing Repair 2',
    'Build Timing Precision Retry',
    'Build Final Duration Repair',
    'Build Final Word Count Retry',
    'Build Final Measured Correction',
    'Build Final Measured Word Count Retry',
  ]) {
    const code = byName[name].parameters.jsCode;
    assert.match(code,/original_narration|ORIGINAL MEANING TO PRESERVE/);
  }
});

test('all acceptance-path late validators have semantic guard', () => {
  for (const name of [
    'Validate Timing Repair 2',
    'Validate Timing Precision Retry',
    'Validate Final Duration Repair',
    'Validate Final Word Count Retry',
    'Validate Final Measured Correction',
    'Validate Final Measured Word Count Retry',
    'Canonicalize Final Storyboard',
  ]) {
    assert.match(
      byName[name].parameters.jsCode,
      /SEMANTIC_PRESERVATION_GUARD_START/,
      name
    );
  }
});

test('word-count targets remain guidance until measured TTS proves final correction is required', () => {
  assert.match(
    byName['Build Timing Precision Retry'].parameters.jsCode,
    /preferred word counts by scene/
  );
  assert.doesNotMatch(
    byName['Validate Timing Precision Retry'].parameters.jsCode,
    /exact word count mismatch|exact total word count mismatch/
  );
  assert.doesNotMatch(
    byName['Validate Final Word Count Retry'].parameters.jsCode,
    /final measured exact-word retry missed required total before TTS/
  );
  assert.match(
    byName['Build Final Measured Word Count Retry'].parameters.jsCode,
    /TARGET TOTAL WORDS \(HARD\): exactly/
  );
  assert.match(
    byName['Build Final Measured Word Count Retry'].parameters.jsCode,
    /combined total across all strings MUST equal exactly/
  );
  assert.match(
    byName['Validate Final Measured Word Count Retry'].parameters.jsCode,
    /final measured exact-word retry missed required total before TTS/
  );
});


test('9137 regression: final measured retry cannot send a 30-word nearest hybrid into TTS when target is 26', () => {
  const code=byName['Validate Final Measured Word Count Retry'].parameters.jsCode;
  assert.match(code,/const exact = states\.get\(targetWords\)/);
  assert.match(code,/nearestTotal = completed\.length \? Number\(completed\[0\]\[0\]\) : totalWords/);
  assert.match(code,/final measured exact-word retry missed required total before TTS/);
  assert.doesNotMatch(code,/narrations = nearest\.lines;/);
});

test('final duration target allocation uses original scene weights and semantic floors', () => {
  for (const name of ['Build Final Duration Repair','Build Final Measured Correction']) {
    const code = byName[name].parameters.jsCode;
    assert.match(code,/originalSceneWords/);
    assert.match(code,/semanticFloors/);
    assert.doesNotMatch(code,/sceneCurrentWords/);
  }
});


function runLateFinalValidator(name,builderName,candidateNarrations) {
  const code=byName[name].parameters.jsCode;
  const originalNarrations=[
    'Woda gromadzi się za tamą.',
    'Woda napędza turbinę wodną.',
    'Turbina obraca generator prądu.',
    'Transformator przekazuje energię dalej.',
    'Prąd trafia do sieci.',
  ];
  const total=candidateNarrations.join(' ').split(/\s+/u).filter(Boolean).length;
  const baseStoryboard={
    narration:originalNarrations.join(' '),
    scenes:originalNarrations.map((narration,i)=>({
      narration,
      shots:[{shot_key:'S'+(i+1)+'-A'}],
    })),
  };
  const builder={
    script_run_id:'run',
    model:'gemini',
    base_storyboard:baseStoryboard,
    prior_usage:{},
    target_words:total,
  };
  const buildCtx={
    language_code:'pl',
    target_duration_seconds:15,
    word_min:20,
    word_max:40,
  };
  const $=nodeName=>{
    if(nodeName===builderName) return {first:()=>({json:builder})};
    if(nodeName==='Build Script Prompt') return {first:()=>({json:buildCtx})};
    if(nodeName==='Normalize Timing Probe') {
      return {first:()=>({json:{storyboard:baseStoryboard}})};
    }
    throw new Error('unexpected node '+nodeName);
  };
  const response={
    statusCode:200,
    body:{
      candidates:[{content:{parts:[{text:JSON.stringify({narrations:candidateNarrations})}]}}],
      usageMetadata:{},
    },
  };
  return new Function('$','$json',code)($,response).json;
}

test('9192 regression: first final duration semantic miss is routed into the existing bounded retry',()=>{
  const candidate=[
    'Ogromna woda spokojnie gromadzi się za tamą.',
    'Woda napędza turbinę wodną.',
    'Turbina obraca generator prądu.',
    'Transformator przekazuje energię dalej.',
    'Prąd trafia do sieci.',
  ];
  const out=runLateFinalValidator(
    'Validate Final Duration Repair',
    'Build Final Duration Repair',
    candidate
  );
  assert.equal(out.word_count_exact,true);
  assert.equal(out.semantic_valid,false);
  assert.match(out.semantic_validation_error,/introduced too many new content words/);

  const route=byName['Route Final Duration Word Count'].parameters.conditions.conditions[0].leftValue;
  assert.match(route,/semantic_valid/);
  assert.equal(workflow.connections['Route Final Duration Word Count'].main[1][0].node,'Build Final Word Count Retry');
});

test('late measured correction semantic miss also uses its single bounded retry',()=>{
  const candidate=[
    'Ogromna woda spokojnie gromadzi się za tamą.',
    'Woda napędza turbinę wodną.',
    'Turbina obraca generator prądu.',
    'Transformator przekazuje energię dalej.',
    'Prąd trafia do sieci.',
  ];
  const out=runLateFinalValidator(
    'Validate Final Measured Correction',
    'Build Final Measured Correction',
    candidate
  );
  assert.equal(out.word_count_exact,true);
  assert.equal(out.semantic_valid,false);
  assert.match(out.semantic_validation_error,/introduced too many new content words/);

  const route=byName['Route Final Measured Word Count'].parameters.conditions.conditions[0].leftValue;
  assert.match(route,/semantic_valid/);
  assert.equal(workflow.connections['Route Final Measured Word Count'].main[1][0].node,'Build Final Measured Word Count Retry');
});

test('bounded retry validators remain semantic fail-closed',()=>{
  for(const name of ['Validate Final Word Count Retry','Validate Final Measured Word Count Retry']) {
    const code=byName[name].parameters.jsCode;
    assert.match(code,/SEMANTIC_PRESERVATION_GUARD_START/);
    assert.doesNotMatch(code,/semanticValidationError =/);
  }
});

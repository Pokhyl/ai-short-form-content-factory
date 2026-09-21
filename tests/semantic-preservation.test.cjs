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

test('word-count targets remain guidance while real TTS is authoritative', () => {
  assert.match(
    byName['Build Timing Precision Retry'].parameters.jsCode,
    /preferred word counts by scene/
  );
  assert.doesNotMatch(
    byName['Validate Timing Precision Retry'].parameters.jsCode,
    /exact word count mismatch|exact total word count mismatch/
  );
  for (const name of [
    'Validate Final Word Count Retry',
    'Validate Final Measured Word Count Retry',
  ]) {
    assert.doesNotMatch(
      byName[name].parameters.jsCode,
      /could not produce requested total before TTS/,
      name
    );
  }
});

test('final duration target allocation uses original scene weights and semantic floors', () => {
  for (const name of ['Build Final Duration Repair','Build Final Measured Correction']) {
    const code = byName[name].parameters.jsCode;
    assert.match(code,/originalSceneWords/);
    assert.match(code,/semanticFloors/);
    assert.doesNotMatch(code,/sceneCurrentWords/);
  }
});

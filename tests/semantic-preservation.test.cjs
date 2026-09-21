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

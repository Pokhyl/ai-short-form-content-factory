const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {test} = require('node:test');

const workflow=JSON.parse(
  fs.readFileSync(path.join(__dirname,'../workflows/VIDEO-M5-Script-Storyboard.json'))
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

function visualGuard(name='Validate Storyboard') {
  const code=byName[name].parameters.jsCode;
  const start=code.indexOf('// ENGLISH_VISUAL_METADATA_GUARD_START');
  const end=code.indexOf('// ENGLISH_VISUAL_METADATA_GUARD_END');
  assert.ok(start>=0 && end>start,name);
  const helper=code.slice(start,end+'// ENGLISH_VISUAL_METADATA_GUARD_END'.length);
  return new Function(helper+'\nreturn assertEnglishVisualMetadata;')();
}

const guard=visualGuard();

test('PL ASCII visual anchors cannot masquerade as English metadata',()=>{
  assert.throws(
    ()=>guard(
      {language_code:'pl'},
      'S1-A',
      'concrete hydro plant dam holding back river water',
      ['Zapora wodna','zbiornik wodny'],
      ['dry riverbed'],
      ['Zapora wodna i zbiornik wodny','Zapora wodna na rzece','Zapora wodna']
    ),
    /visual metadata must be English/
  );
});

test('Polish diacritics in visual metadata are rejected',()=>{
  assert.throws(
    ()=>guard(
      {language_code:'pl'},
      'S1-A',
      'concrete hydro plant dam holding back river water',
      ['water dam','reservoir'],
      [],
      ['zapora spiętrzająca rzekę','water dam reservoir','water dam']
    ),
    /Polish characters detected/
  );
});

test('Cyrillic visual metadata is rejected for RU and UK narration',()=>{
  for(const language_code of ['ru','uk']) {
    assert.throws(
      ()=>guard(
        {language_code},
        'S1-A',
        'hydroelectric dam holding river water',
        ['гидроэлектростанция'],
        [],
        ['гидроэлектростанция плотина','hydroelectric dam river','hydroelectric dam']
      ),
      /Cyrillic detected/
    );
  }
});

test('English visual metadata remains valid for non-English narration',()=>{
  assert.doesNotThrow(()=>guard(
    {language_code:'pl'},
    'S1-A',
    'concrete hydro plant water dam holding back river water',
    ['water dam','reservoir'],
    ['dry riverbed'],
    ['water dam reservoir','hydroelectric water dam river','water dam']
  ));
});

test('all bounded storyboard validators enforce the same English visual contract',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
  ]) {
    const code=byName[name].parameters.jsCode;
    assert.match(code,/ENGLISH_VISUAL_METADATA_GUARD_START/,name);
    assert.match(code,/assertEnglishVisualMetadata\(/,name);
  }
});


function mustShowNormalizer(name='Validate Storyboard') {
  const code=byName[name].parameters.jsCode;
  const start=code.indexOf('// MUST_SHOW_SECONDARY_GUARD_START');
  const end=code.indexOf('// MUST_SHOW_SECONDARY_GUARD_END');
  assert.ok(start>=0 && end>start,name);
  const helper=code.slice(start,end+'// MUST_SHOW_SECONDARY_GUARD_END'.length);
  return new Function(helper+'\nreturn normalizeMustShowAnchors;')();
}

const normalizeMustShow=mustShowNormalizer();

test('secondary must_show does not restate or detail the primary object',()=>{
  assert.deepEqual(
    normalizeMustShow(['water turbine','turbine blades']),
    ['water turbine']
  );
  assert.deepEqual(
    normalizeMustShow(['electric generator','generator machinery']),
    ['electric generator']
  );
  assert.deepEqual(
    normalizeMustShow(['power transformer','transformer substation']),
    ['power transformer']
  );
});

test('independent secondary context remains mandatory',()=>{
  assert.deepEqual(
    normalizeMustShow(['water reservoir','dam']),
    ['water reservoir','dam']
  );
  assert.deepEqual(
    normalizeMustShow(['magma pool','rock cavity']),
    ['magma pool','rock cavity']
  );
  assert.deepEqual(
    normalizeMustShow(['power lines','transmission towers']),
    ['power lines','transmission towers']
  );
});

test('all bounded storyboard validators normalize redundant secondary anchors',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
  ]) {
    const code=byName[name].parameters.jsCode;
    assert.match(code,/MUST_SHOW_SECONDARY_GUARD_START/,name);
    assert.match(code,/normalizeMustShowAnchors\(rawMustShow\)/,name);
  }
});

test('initial and bounded repair prompts explicitly split narration and visual languages',()=>{
  assert.match(byName['Build Script Prompt'].parameters.jsCode,/CRITICAL LANGUAGE SPLIT/);
  for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']) {
    const code=byName[name].parameters.jsCode;
    assert.match(code,/visual_intent, every must_show item, every must_not_show item, and every queries_en item MUST be English only/,name);
    assert.match(code,/preserve narration, scene_id, shot_id, evidence_ids/,name);
  }
});

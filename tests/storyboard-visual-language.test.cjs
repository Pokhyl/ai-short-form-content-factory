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
    normalizeMustShow(['water turbine','turbine blades'],'Water turbine runner inside a power station'),
    ['water turbine']
  );
  assert.deepEqual(
    normalizeMustShow(['electric generator','generator machinery'],'Electric generator inside a hydroelectric plant'),
    ['electric generator']
  );
  assert.deepEqual(
    normalizeMustShow(['power transformer','transformer substation'],'Power transformer outside a hydroelectric plant'),
    ['power transformer']
  );
  assert.deepEqual(
    normalizeMustShow(['electric generator','industrial machinery'],'Electric generator inside a hydroelectric plant'),
    ['electric generator']
  );
  assert.deepEqual(
    normalizeMustShow(['water turbine','industrial equipment'],'Water turbine inside a hydroelectric plant'),
    ['water turbine']
  );
});

test('independent secondary context remains mandatory',()=>{
  assert.deepEqual(
    normalizeMustShow(['water reservoir','dam'],'Large water reservoir behind a concrete dam'),
    ['water reservoir','dam']
  );
  assert.deepEqual(
    normalizeMustShow(['magma pool','rock cavity'],'Large underground magma pool trapped inside a dark rock cavity'),
    ['magma pool','rock cavity']
  );
  assert.deepEqual(
    normalizeMustShow(['power lines','transmission towers'],'Electrical power lines and transmission towers distributing electricity'),
    ['power lines','transmission towers']
  );
});


test('secondary context absent from visual_intent is removed instead of becoming a hard retrieval gate',()=>{
  assert.deepEqual(
    normalizeMustShow(
      ['electric generator','turbine shaft'],
      'Electric generator machine inside a hydroelectric plant'
    ),
    ['electric generator']
  );
  assert.deepEqual(
    normalizeMustShow(
      ['water turbine','maintenance worker'],
      'Water turbine runner inside a power station'
    ),
    ['water turbine']
  );
});



test('action word alone cannot keep an unrequested secondary object as a hard visual gate',()=>{
  assert.deepEqual(
    normalizeMustShow(
      ['water turbine','spinning blades'],
      'Water turbine wheel spinning underwater in hydro plant'
    ),
    ['water turbine']
  );
  assert.deepEqual(
    normalizeMustShow(
      ['pump','rotating shaft'],
      'Industrial pump rotating inside a machine room'
    ),
    ['pump']
  );
});

test('process or state secondary anchors do not become hard visual requirements',()=>{
  assert.deepEqual(
    normalizeMustShow(
      ['penstock','water flow'],
      'Water rushing down through a large penstock pipe'
    ),
    ['penstock']
  );
  assert.deepEqual(
    normalizeMustShow(
      ['electric generator','energy generation'],
      'Electric generator inside a hydroelectric plant'
    ),
    ['electric generator']
  );
  assert.deepEqual(
    normalizeMustShow(
      ['turbine','shaft rotation'],
      'Turbine and shaft inside a power station'
    ),
    ['turbine']
  );
  assert.deepEqual(
    normalizeMustShow(
      ['spillway','falling water'],
      'Spillway with visibly falling water'
    ),
    ['spillway','falling water']
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
    assert.match(code,/normalizeMustShowAnchors\(rawMustShow, visualIntent\)/,name);
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


function shortMustShowNormalizer(name='Validate Storyboard') {
  const code=byName[name].parameters.jsCode;
  const start=code.indexOf('// SHORT_MUST_SHOW_GUARD_START');
  const end=code.indexOf('// SHORT_MUST_SHOW_GUARD_END');
  assert.ok(start>=0 && end>start,name);
  const helper=code.slice(start,end+'// SHORT_MUST_SHOW_GUARD_END'.length);
  return new Function(helper+'\nreturn normalizeShortDomainAnchor;')();
}

test('9361 regression: common leading electrical modifier pair is canonicalized before the 1-3 word anchor guard',()=>{
  const normalize=shortMustShowNormalizer('Validate Repaired Storyboard 2');
  assert.equal(normalize('high voltage power lines'),'power lines');
});

test('short-anchor canonicalization does not turn descriptive prose into a valid anchor',()=>{
  const normalize=shortMustShowNormalizer();
  const value=normalize('large concrete dam with water');
  assert.equal(value,'concrete dam with water');
  assert.equal(value.split(/\s+/u).filter(Boolean).length,4);
});

test('short-anchor canonicalization preserves already valid specific anchors',()=>{
  const normalize=shortMustShowNormalizer();
  assert.equal(normalize('electric generator'),'electric generator');
  assert.equal(normalize('turbine shaft'),'turbine shaft');
  assert.equal(normalize('residential houses'),'residential houses');
});

test('all bounded storyboard validators canonicalize permitted leading modifiers before the hard short-anchor guard',()=>{
  for(const name of [
    'Validate Storyboard',
    'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2',
  ]) {
    const code=byName[name].parameters.jsCode;
    assert.match(code,/SHORT_MUST_SHOW_GUARD_START/,name);
    assert.match(code,/\.map\(normalizeShortDomainAnchor\)/,name);
    const guardPos=code.indexOf('must_show items must be short domain anchors');
    const mapPos=code.indexOf('.map(normalizeShortDomainAnchor)');
    assert.ok(mapPos>=0 && guardPos>mapPos,name);
  }
});

const assert = require('node:assert/strict');
const {test} = require('node:test');
const workflow = require('../workflows/VIDEO-M8-Multi-Source-Visuals.json');

const shot = {
  shot_uuid: '11111111-1111-4111-8111-111111111111',
  shot_key: 'S1-A', scene_order: 1, preferred_media_type: 'photo',
  visual_intent: 'A real photograph of a vertical glass tube mercury barometer setup.',
  must_show: ['mercury barometer'], must_not_show: ['smartphone'],
  queries_en: [
    'vertical glass tube mercury barometer setup',
    'mercury barometer tube and reservoir',
    'mercury barometer',
  ],
};
const $ = name => {
  assert.equal(name, 'Begin Visuals');
  return {first: () => ({json: {
    visual_run_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    shots_json: [shot],
  }})};
};
for (const provider of ['Wikimedia', 'Pexels', 'Pixabay']) {
  test(`${provider}: bare subject fallback stays broad while precise queries retain details`, () => {
    const node = workflow.nodes.find(n => n.name === `Build ${provider} Requests`);
    const rows = new Function('$', node.parameters.jsCode)($).map(item => item.json);
    assert.equal(rows.length, 3);
    assert.match(rows[0].provider_query, /tube/);
    assert.match(rows[1].provider_query, /tube/);
    assert.equal(rows[2].query, 'mercury barometer');
    assert.equal(rows[2].provider_query, 'mercury barometer');
    assert.deepEqual(shot.must_show, ['mercury barometer']);
    assert.deepEqual(shot.must_not_show, ['smartphone']);
  });
}

test('M5 validators remove unsupported studio framing while preserving the subject', () => {
  const m5 = require('../workflows/VIDEO-M5-Script-Storyboard.json');
  const names = [
    'Validate Storyboard', 'Validate Repaired Storyboard',
    'Validate Repaired Storyboard 2', 'Validate Timing Repair',
    'Validate Timing Repair 2', 'Canonicalize Final Storyboard',
    'Validate Narration Language Repair',
  ];
  for (const name of names) {
    const source = m5.nodes.find(n => n.name === name).parameters.jsCode;
    const expression = source.match(/const visualIntent = clean\(shot\.visual_intent\)[\s\S]*?\.trim\(\);/);
    assert.ok(expression, `${name} missing visual intent normalization`);
    const normalize = new Function('shot', 'clean', `${expression[0]} return visualIntent;`);
    const result = normalize(
      {visual_intent: 'A clear studio photo of a vertical mercury barometer.'},
      value => String(value).trim(),
    );
    assert.equal(result, 'A clear photograph of a vertical mercury barometer.');
    assert.equal(normalize({visual_intent: 'A photo of a real laboratory.'}, String),
      'A photo of a real laboratory.');
  }
});

test('instrument fallback also works for a thermometer without weakening machinery detail retrieval', () => {
  const instrument = {
    ...shot, must_show: ['glass thermometer'],
    visual_intent: 'A glass thermometer with a visible scale.',
    queries_en: ['glass thermometer visible scale', 'thermometer scale markings', 'glass thermometer'],
  };
  for (const provider of ['Wikimedia', 'Pexels', 'Pixabay']) {
    const node = workflow.nodes.find(n => n.name === `Build ${provider} Requests`);
    const select = name => {
      assert.equal(name, 'Begin Visuals');
      return {first: () => ({json: {
        visual_run_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        shots_json: [instrument],
      }})};
    };
    const rows = new Function('$', node.parameters.jsCode)(select).map(item => item.json);
    assert.match(rows[0].provider_query, /scale/);
    assert.equal(rows[2].provider_query, 'glass thermometer');
  }
});

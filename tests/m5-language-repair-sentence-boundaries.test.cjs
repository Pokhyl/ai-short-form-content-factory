const assert = require('node:assert/strict');
const {test} = require('node:test');
const workflow = require('../workflows/VIDEO-M5-Script-Storyboard.json');
const validator = workflow.nodes.find(n => n.name === 'Validate Narration Language Repair').parameters.jsCode;
const repairPrelude = validator.split('const providerError =')[0];
assert.ok(repairPrelude.includes('preserveBoundaries'));

function restore(base, corrected, targetDuration = 30) {
  const repair = {
    base_storyboard: {scenes: base.map((narration, index) => ({
      scene_id: `S${index + 1}`, narration,
    }))},
    repair_scene_ids: Object.keys(corrected),
    target_duration_seconds: targetDuration,
  };
  const input = {statusCode: 200, body: {candidates: [{content: {parts: [
    {text: JSON.stringify({narrations: corrected})},
  ]}}]}};
  const result = new Function('$json', '$',
    `${repairPrelude}\nreturn JSON.parse($json.body.candidates[0].content.parts[0].text);`
  )(input, name => {
    assert.equal(name, 'Build Narration Language Repair');
    return {first: () => ({json: repair})};
  });
  return result.scenes.map(scene => scene.narration);
}

test('grammar edit preserves a sentence spanning visual cuts', () => {
  const base = [
    'Барометр це прилад для вимірювання',
    'атмосферного тиску який створює вагу',
    'повітря на земну поверхню і прогнозує',
    'зміни погоди на основі коливань цієї сили.',
    'Традиційний ртутний барометр складається зі скляної трубки.',
    'Атмосферний тиск штовхає ртуть у герметичній трубці.',
    'Сучасні анероїдні барометри використовують металеву коробку.',
    'Зміни тиску деформують камеру і передають рух на стрілку.',
    'Цифрові моделі використовують електронні датчики для точних показників.',
  ];
  const result = restore(base, {
    S1: 'Барометр — це прилад для вимірювання.',
    S2: 'Атмосферного тиску, який створює вагу.',
  });
  assert.equal(result[0], 'Барометр — це прилад для вимірювання');
  assert.equal(result[1], 'атмосферного тиску, який створює вагу');
  assert.equal(result[4], base[4]);
  assert.match(result.join(' '), /для вимірювання атмосферного тиску, який/);
});

test('a genuine run-on without enough original sentences can acquire a new sentence break', () => {
  const base = [
    'First clause continues here',
    'the second part finally finishes.',
  ];
  const result = restore(base, {S1: 'First clause ends here.'});
  assert.equal(result[0], 'First clause ends here.');
});

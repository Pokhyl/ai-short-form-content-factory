const {test} = require('node:test');
const assert = require('node:assert/strict');
const {PexelsAPI} = require('../engine-overlay/Pexels.js');
const fixture = require('./fixtures/scenes.cjs');
// Network is replaced at its boundary; ranking, language dictionaries, grounding,
// media validation, previous-scene handling, and dedup remain production code.
const {api} = require('./fixtures/api.cjs');
for (const lang of fixture.langs) test(`all eight acceptance scenes: ${lang}`, async () => {
  const result = await api().preflightScenes(fixture.scenes(lang));
  assert.deepEqual(result.map(m => m.groundedEntity), fixture.expected);
  assert.equal(new Set(result.map(m => m.mediaKey)).size, 6);
  assert.equal(result[6].subject.mode, 'previous_scene_anaphora');
  assert.equal(result[6].reuseReason, 'same_entity_no_alternative');
  assert.ok(result.every(m => m.confidence === 'high' && m.groundedEntityId));
});

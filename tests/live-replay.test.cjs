const {test} = require('node:test');
const assert = require('node:assert/strict');
const {PexelsAPI} = require('../engine-overlay/Pexels');
const fixture = require('./fixtures/scenes.cjs');
const recorded = require('./fixtures/wikimedia-uk.json');

test('real Wikimedia acceptance responses replay deterministically without network',async()=>{
  const resolver = new PexelsAPI('', {fetchJson:async url=>{
    assert.ok(recorded.requests[url],`Unrecorded Wikimedia request: ${url}`);
    return structuredClone(recorded.requests[url]);
  }});
  const result=await resolver.preflightScenes(fixture.scenes('uk'));
  assert.deepEqual(result.map(m=>m.groundedEntity),['Inner planet',...fixture.expected.slice(1)]);
  assert.equal(result[0].components.length,4);
  assert.equal(result[1].components.length,4);
  assert.equal(result[0].source,'exact_listed_members');
  assert.ok(result[5].title.includes('10 Largest Trans-Neptunian objects'));
  assert.equal(result[6].groundedEntityId,result[5].groundedEntityId);
  assert.equal(result[6].subject.antecedentScene,5);
  assert.equal(result[7].title,'File:Solar_wind_flow.gif');
  assert.ok(result.every(m=>m.confidence==='high'));
});

test('all seven previously rejected production narrations pass sequential exact-media replay',async()=>{
  const recording=require('./fixtures/production-uk-replay.json');
  const resolver=new PexelsAPI('',{fetchJson:async url=>{
    assert.ok(recording.requests[url],`Unrecorded production request: ${url}`);
    return structuredClone(recording.requests[url]);
  }});
  const result=await resolver.preflightScenes(require('./fixtures/production-uk-scenes.json'));
  assert.equal(result.length,7);
  assert.deepEqual(result[3].components.map(m=>m.groundedEntity),['Comet','Meteoroid','Cosmic dust']);
  assert.equal(result[4].components.length,2);
  assert.equal(result[5].groundedEntity,'Outer planets');
  assert.equal(result[5].source,'exact_wikidata_parts');
  assert.equal(result[5].components.length,4);
  assert.equal(result[6].groundedEntity,'Solar wind');
});

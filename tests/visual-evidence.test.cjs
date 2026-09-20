const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {test} = require('node:test');
const workflow = JSON.parse(fs.readFileSync(path.join(__dirname, '../workflows/VIDEO-M8-Multi-Source-Visuals.json')));

function normalize(provider, ctx, body, statusCode=200) {
  const code = workflow.nodes.find(n => n.name === 'Normalize ' + provider).parameters.jsCode;
  return new Function('$', '$json', code)(() => ({item:{json:ctx}}), {body,statusCode}).json;
}
const ctx = {visual_run_id:'test',shot_uuid:'test',query_index:1,endpoint_kind:'photo',
  preferred_media_type:'photo',query:'honey bee processing nectar mouthparts',
  visual_intent:'A honey bee close-up showing mouthparts processing nectar',
  must_show:['honey bee','mouthparts'],must_not_show:['flower']};
function pixabay(tags) {
  return {id:123,type:'photo',isAiGenerated:false,tags,user:'fixture',
    pageURL:'https://pixabay.com/photos/fixture-123/',
    largeImageURL:'https://pixabay.com/get/fixture.jpg',imageWidth:1080,imageHeight:1920};
}

test('tag-rich jar with provider photo/AI flags cannot establish a depicted bee', () => {
  const hit=pixabay('honey, yellow, beekeeper, nature, beekeeping, apiary, closeup, sweet, nectar, jar of honey, bee products, brown nature, brown natural, brown bee, world bee day');
  const result=normalize('Pixabay',ctx,{hits:[hit]});
  assert.equal(result.candidates.length,1); // retain diagnostic provenance
  assert.equal(result.candidates[0].rejected,true);
  assert.match(result.candidates[0].rejection_reason,/unverified_tag_only/);
});
test('poster mislabeled photo is rejected regardless of matching topical tags', () => {
  const hit=pixabay('bee, honey, honeycomb, hexagon, pattern, wax, sweet, food, colorful, cell, beehive, comb, insect, texture, hive, healthy, beeswax, macro, medicine, gold');
  const shot={...ctx,query:'honeycomb cells capped with wax',must_show:['honeycomb cells','wax capping'],must_not_show:[]};
  assert.equal(normalize('Pixabay',shot,{hits:[hit]}).candidates[0].rejected,true);
});
test('quarantine is generic, not tied to honey topics or rejected asset IDs', () => {
  const shot={...ctx,query:'power transmission pylon',visual_intent:'power transmission pylon',must_show:['transmission pylon'],must_not_show:[]};
  assert.equal(normalize('Pixabay',shot,{hits:[pixabay('power transmission pylon')]}).candidates[0].rejected,true);
});
function pexels(alt) {
  return {id:456,alt,url:'https://www.pexels.com/photo/fixture-456/',
    src:{large2x:'https://images.pexels.com/photos/456/fixture.jpg'},width:1080,height:1920};
}
test('described photographic bee remains eligible with original score gates', () => {
  const c=normalize('Pexels',ctx,{photos:[pexels('Macro close-up of honey bee mouthparts processing nectar inside a hive')]}).candidates[0];
  assert.equal(c.rejected,false);
  assert.ok(c.relevance_score>=60);
});
test('Pexels URL keywords cannot replace an absent visual description', () => {
  const hit=pexels(''); hit.url='https://www.pexels.com/photo/honey-bee-processing-nectar-mouthparts-456/';
  const c=normalize('Pexels',ctx,{photos:[hit]}).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_visual_description/);
});
test('captioned poster cannot become a photo through high topical overlap', () => {
  const c=normalize('Pexels',ctx,{photos:[pexels('Graphic design poster of honey bee mouthparts processing nectar')]}).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/non_photographic_asset/);
});
test('unrelated caption remains rejected', () => {
  assert.equal(normalize('Pexels',ctx,{photos:[pexels('Portrait of a swimmer at a blue swimming pool')]}).candidates[0].rejected,true);
});
test('provider errors preserve HTTP failure and zero candidates', () => {
  for (const provider of ['Pixabay','Pexels','Wikimedia']) {
    const r=normalize(provider,ctx,{hits:[pixabay('honey bee')],photos:[pexels('honey bee')]},403);
    assert.equal(r.http_status,403);
    assert.deepEqual(r.candidates,[]);
  }
});

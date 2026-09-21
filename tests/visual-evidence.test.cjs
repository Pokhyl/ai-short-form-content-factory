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


test('residential modifier does not block a house-and-power-lines photo', () => {
  const shot={...ctx,
    query:'houses near power lines',
    visual_intent:'Modern residential houses supplied with electricity from power grid',
    must_show:['residential houses','power lines'],
    must_not_show:['wind turbine']};
  const c=normalize(
    'Pexels',
    shot,
    {photos:[pexels('Tranquil suburban street with houses and power lines under a clear blue sky.')]}
  ).candidates[0];
  assert.equal(c.rejected,false,c.rejection_reason);
  assert.ok(c.relevance_score>=60);
});

test('residential house without required power-line context still rejects', () => {
  const shot={...ctx,
    query:'residential houses',
    visual_intent:'Modern residential houses supplied with electricity from power grid',
    must_show:['residential houses','power lines'],
    must_not_show:['wind turbine']};
  const c=normalize(
    'Pexels',
    shot,
    {photos:[pexels('A serene view of residential houses on a quiet street.')]}
  ).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_secondary_subject_context/);
});


test('fresh PL15 portable generator is rejected when shared hydroelectric context is present', () => {
  const shot={...ctx,
    query:'electrical generator equipment generating power',
    provider_query:'hydroelectric electrical generator equipment generating power',
    domain_context_terms:['hydroelectric'],
    visual_intent:'Electrical generator equipment generating electric power',
    must_show:['electrical generator'],
    must_not_show:['water pump']};
  const c=normalize(
    'Pexels',
    shot,
    {photos:[pexels('Industrial generator on wheels in a snowy outdoor environment with equipment backdrop.')]}
  ).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_storyboard_domain_context:hydroelectric/);
});

test('Pexels page title may corroborate one missing subtype term when alt already proves the object and scene context', () => {
  const shot={...ctx,
    query:'hydroelectric power plant building exterior',
    visual_intent:'Hydroelectric power plant building exterior near a river',
    must_show:['hydroelectric power plant','river'],
    must_not_show:[]};
  const hit=pexels('Picturesque scenery of power plant with flowing water located near river among green hills');
  hit.url='https://www.pexels.com/photo/hydroelectric-power-plant-in-forest-4500695/';
  const c=normalize('Pexels',shot,{photos:[hit]}).candidates[0];
  assert.equal(c.rejected,false,c.rejection_reason);
  assert.ok(c.relevance_score>=60);
});

test('Pexels page title cannot rescue an unrelated described subject', () => {
  const shot={...ctx,
    query:'hydroelectric power plant building exterior',
    visual_intent:'Hydroelectric power plant building exterior near a river',
    must_show:['hydroelectric power plant','river'],
    must_not_show:[]};
  const hit=pexels('Portrait of a swimmer standing beside a blue swimming pool');
  hit.url='https://www.pexels.com/photo/hydroelectric-power-plant-in-forest-4500695/';
  const c=normalize('Pexels',shot,{photos:[hit]}).candidates[0];
  assert.equal(c.rejected,true);
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

test('shared form word cannot satisfy a different compound subject', () => {
  const shot={...ctx,query:'nectar droplets',visual_intent:'Nectar droplets in honeycomb cells',must_show:['nectar droplets','honeycomb cells'],must_not_show:[]};
  const c=normalize('Pexels',shot,{photos:[pexels('Macro shot of water droplets glistening on brown pine needles')]}).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_primary_subject_anchor/);
});
function commons(title,description) {
  return {query:{pages:{'1':{pageid:1,index:1,title,imageinfo:[{mime:'image/jpeg',
    url:'https://upload.wikimedia.org/fixture.jpg',width:1080,height:1920,
    descriptionurl:'https://commons.wikimedia.org/wiki/'+title,
    extmetadata:{LicenseShortName:{value:'Public domain'},ObjectName:{value:title},ImageDescription:{value:description}}}]}}}};
}
test('background taxonomic mention of bees cannot turn wasp title into bee evidence', () => {
  const shot={...ctx,query:'worker bee',visual_intent:'Worker bee body and abdomen',must_show:['worker bee','bee abdomen'],must_not_show:[]};
  const c=normalize('Wikimedia',shot,commons('File:The Wasp.jpg','A wasp belongs to the order of ants, bees and wasps. It is neither a bee nor an ant. Workers have an abdomen.')).candidates[0];
  assert.equal(c.rejected,true);
});
test('background proboscis mention cannot attest the depicted insect identity', () => {
  const shot={...ctx,query:'bee proboscis drinking nectar',must_show:['proboscis','bee head'],must_not_show:[]};
  const c=normalize('Wikimedia',shot,commons('File:Stylidium schoenoides.jpg','The bee fly drinks nectar using its proboscis and moves its head.')).candidates[0];
  assert.equal(c.rejected,true);
});
test('generic form relaxation still accepts the actual distinctive subjects', () => {
  for(const [primary,title] of [['magma pool','File:Magma.jpg'],['GPS receiver','File:GPS navigation.jpg'],['water turbine runner','File:Water turbine.jpg'],['bee mouthparts','File:Bee.jpg']]) {
    const shot={...ctx,query:primary,visual_intent:primary,must_show:[primary],must_not_show:[]};
    const c=normalize('Wikimedia',shot,commons(title,primary)).candidates[0];
    assert.equal(c.rejected,false,primary);
  }
});
test('ambiguous anatomical fallback cannot select another organism', () => {
  const shot={...ctx,query:'proboscis',visual_intent:'Forager bee proboscis drinking nectar',must_show:['proboscis','bee head'],must_not_show:[]};
  const c=normalize('Pexels',shot,{photos:[pexels('Proboscis monkey eating outdoors in natural habitat')]}).candidates[0];
  assert.equal(c.rejected,true);
  assert.match(c.rejection_reason,/missing_secondary_subject_context/);
});
test('normal plural subjects do not lose their identity', () => {
  const shot={...ctx,query:'honey bee',visual_intent:'Honey bee on honeycomb',must_show:['honey bee'],must_not_show:[]};
  assert.equal(normalize('Pexels',shot,{photos:[pexels('Honey bees on a honeycomb frame')]}).candidates[0].rejected,false);
});

const {test} = require('node:test');
const assert = require('node:assert/strict');
const {api} = require('./fixtures/api.cjs');
const fixture = require('./fixtures/scenes.cjs');
const {resolveSubject, sourceLexicon, DictionaryLemmas} = require('../engine-overlay/VisualSubject');
const {PexelsAPI} = require('../engine-overlay/Pexels');
const dictionary = new DictionaryLemmas();
const subject = (text, source, lang='en', previous=null) => resolveSubject(text, lang, sourceLexicon(source, 'Reference'), dictionary, previous);
const scene = text => ({...fixture.scenes('en')[0], text});

test('main subject before later comparison is retained in all four languages', async () => {
  for (const [lang, text, links, expected] of [
    ['en', 'Blue whales are larger than domestic cats.', '[[Blue whale|blue whales]] [[Domestic cat|domestic cats]]', 'Blue whale'],
    ['uk', 'Сині кити більші, ніж домашні коти.', '[[Синій кит|сині кити]] [[Кіт свійський|домашні коти]]', 'Синій кит'],
    ['ru', 'Синие киты крупнее, чем домашние кошки.', '[[Синий кит|синие киты]] [[Домашняя кошка|домашние кошки]]', 'Синий кит'],
    ['pl', 'Płetwale błękitne są większe niż koty domowe.', '[[Płetwal błękitny|płetwale błękitne]] [[Kot domowy|koty domowe]]', 'Płetwal błękitny'],
  ]) assert.equal((await subject(text, links, lang)).title, expected);
});
test('alias groups generalize outside astronomy', async () => {
  assert.equal((await subject('Oak, beech and birch, also called deciduous trees, lose their leaves.', '[[Oak]] [[Deciduous tree|deciduous trees]]')).title, 'Deciduous tree');
});
test('named entities in relative clauses cannot displace the leading subject', async () => {
  assert.equal((await subject('The Amazon rainforest, which covers Brazil, has great biodiversity.', '[[Amazon rainforest]] [[Brazil]]')).title, 'Amazon rainforest');
});
test('locative context does not displace the current multiword subject', async () => {
  assert.equal((await subject('In Brazil there are tropical rainforests.', '[[Brazil]] [[Tropical rainforest|tropical rainforests]]')).title, 'Tropical rainforest');
});
test('unknown main subject cannot be replaced by a known object', async () => {
  await assert.rejects(subject('Uncatalogued organisms consume domestic cats.', '[[Domestic cat|domestic cats]]'), /subject/);
});
test('current entity wins over any incoming history/context', async () => {
  const result = await api().preflightScenes([{...scene('Solar wind carries particles.'), mediaContext: 'Mars', mediaHistory: 'Mars'}]);
  assert.equal(result[0].groundedEntity, 'Solar wind');
});
test('explicit anaphora uses exactly the immediately previous semantic scene', async () => {
  const result = await api().preflightScenes([scene('The asteroid belt contains rocks.'), scene('Gas giants are massive.'), scene('These are very large.')]);
  assert.equal(result[2].groundedEntity, 'Gas giant');
  assert.equal(result[2].subject.antecedentScene, 1);
});
test('stale supplied history cannot rescue an orphan anaphora', async () => {
  await assert.rejects(api().preflightScenes([{...scene('The largest of them are Pluto and Sedna.'), mediaHistory: fixture.texts.en[5]}]), /missing_antecedent/);
});
test('no implicit history inheritance and no source-topic fallback', async () => {
  await assert.rejects(api().preflightScenes([scene('Gas giants are massive.'), scene('An unknown subject emits energy.')]), /unresolved_subject/);
});
test('anaphora cannot cross a language/source boundary', async () => {
  const next = {...scene('These are large.'), searchTerms: ['visualsource::en::Another%20article::Solar%20System']};
  await assert.rejects(api().preflightScenes([scene('Gas giants are massive.'), next]), /missing_antecedent/);
});
test('a list of individuals must not choose the first member', async () => {
  await assert.rejects(api().preflightScenes([scene('Mercury, Earth and Mars.')]), /ambiguous_subject/);
});
test('one ambiguous alias shared by different entities fails', async () => {
  await assert.rejects(subject('The river bank erodes.', '[[River shore|river bank]] [[Financial institution|river bank]]'), /ambiguous_subject/);
});
test('prefix collisions and distributed token overlap are never exact grounding', async () => {
  await assert.rejects(subject('Martian winds blow.', '[[Mars]]'), /unresolved_subject/);
  await assert.rejects(subject('Giant stars illuminate gas clouds.', '[[Gas giant]]'), /unresolved_subject/);
});
test('generic/raw, direct media and old article query paths fail closed', async () => {
  for (const terms of [['Solar System'], ['wikiarticle::en::Solar%20System'], ['wikiscene::en::Mars'], ['directmedia::'+encodeURIComponent(JSON.stringify({url:'https://upload.wikimedia.org/a.jpg'}))]]) {
    await assert.rejects(api().findVideo(terms, 5), /source_required/);
  }
});
test('preflight splits sentences into distinct semantic scenes', async () => {
  const resolver = api();
  const prepared = resolver.prepareScenes([scene('The asteroid belt contains rocks. Solar wind carries plasma.')]);
  assert.equal(prepared.length, 2);
  assert.deepEqual((await resolver.preflightScenes(prepared)).map(m => m.groundedEntity), ['Asteroid belt', 'Solar wind']);
});
test('a missing exact image fails without generic source fallback', async () => {
  const resolver = api(), fetch = resolver.fetchJson;
  resolver.fetchJson = async url => {
    const data = await fetch(url);
    for (const page of Object.values(data.query?.pages || {})) delete page.thumbnail;
    return data;
  };
  await assert.rejects(resolver.preflightScenes([scene('Solar wind carries plasma.')]), /exact_media_missing/);
});
test('disambiguation pages and mismatched Wikidata identities fail', async () => {
  for (const mutate of [p => {p.pageprops.disambiguation='';}, p => {p.pageprops.wikibase_item='Q999';}]) {
    const resolver = api(), fetch = resolver.fetchJson;
    resolver.fetchJson = async url => {
      const data = await fetch(url);
      if (new URL(url).searchParams.get('prop') === 'pageimages|pageprops') for (const p of Object.values(data.query?.pages || {})) mutate(p);
      return data;
    };
    await assert.rejects(resolver.preflightScenes([scene('Solar wind carries plasma.')]), /identity_mismatch/);
  }
});
test('the same Wikimedia file under two entities is rejected', async () => {
  const resolver = api(), fetch = resolver.fetchJson;
  resolver.fetchJson = async url => {
    const data = await fetch(url);
    for (const p of Object.values(data.query?.pages || {})) {p.pageimage='Shared.jpg'; if (p.thumbnail) p.thumbnail.source='https://upload.wikimedia.org/wikipedia/commons/a/ab/Shared.jpg';}
    return data;
  };
  await assert.rejects(resolver.preflightScenes([scene('The asteroid belt contains rocks.'), scene('Solar wind carries plasma.')]), /exact_media_missing/);
});

const info = {mime:'image/jpeg', url:'https://upload.wikimedia.org/wikipedia/commons/a/ab/Solar_wind.jpg', width:1080, height:800};
function commonsAPI(titles, depicts, video=false) {
  return new PexelsAPI('', {fetchJson: async url => {
    const p = new URL(url).searchParams;
    if (new URL(url).hostname === 'www.wikidata.org') return {entities:{[p.get('ids')]:{claims:{},aliases:{}}}};
    if (p.get('generator')) return {query:{pages:Object.fromEntries(titles.map((title,i)=>[i,{pageid:i+1,title,imageinfo:[{...info,mime:video?'video/webm':'image/jpeg'}]}]))}};
    return {entities:Object.fromEntries(titles.map((_,i)=>[`M${i+1}`,{statements:{P180:depicts.map(id=>({mainsnak:{datavalue:{value:{id}}}}))}}]))};
  }});
}
test('Commons filename/search noise and co-subjects are rejected for images AND video', async () => {
  for (const video of [false,true]) {
    const ext=video?'webm':'jpg';
    const resolver=commonsAPI([`File:Solar wind on Mars.${ext}`,`File:Mars solar wind.${ext}`,`File:Solar corona.${ext}`],['Q79833'],video);
    assert.deepEqual(await resolver.commonsMedia({englishTitle:'Solar wind',qid:'Q79833'},video),[]);
  }
});
test('Commons exact filename alone is insufficient; co-depicts fails', async () => {
  for (const depicts of [[],['Q111'],['Q79833','Q111']]) assert.deepEqual(await commonsAPI(['File:Solar wind.jpg'],depicts).commonsMedia({englishTitle:'Solar wind',qid:'Q79833'},false),[]);
});
test('Commons accepts sole exact depicts with an unambiguous filename', async () => {
  const result=await commonsAPI(['File:Solar wind diagram.jpg'],['Q79833']).commonsMedia({englishTitle:'Solar wind',qid:'Q79833'},false);
  assert.equal(result.length,1);
  assert.equal(result[0].depicts,'Q79833');
});
test('repeated entities choose alternate exact media before reusing', async () => {
  const resolver=api();
  resolver.commonsMedia=async entity=>[{id:'alternate',mediaKey:'alternate.jpg',title:'File:Solar wind diagram.jpg',url:info.url,width:1080,height:800,kind:'image',extension:'.jpg',source:'exact_entity_commons',depicts:entity.qid}];
  const result=await resolver.preflightScenes([scene('Solar wind carries plasma.'),scene('Solar wind carries energy.')]);
  assert.notEqual(result[0].mediaKey,result[1].mediaKey);
  assert.equal(result[1].reuseReason,undefined);
});

test('a section redirect in the local lookup cannot become the containing topic', async () => {
  const resolver=api(), fetch=resolver.fetchJson;
  resolver.fetchJson=async url=>{
    const p=new URL(url).searchParams;
    if (p.get('titles')==='Inner planet') return {query:{redirects:[{from:'Inner planet',to:'Solar System',tofragment:'Inner planets'}],pages:{1:{pageid:1,title:'Solar System',pageprops:{wikibase_item:'Q544'}}}}};
    return fetch(url);
  };
  await assert.rejects(resolver.ground('en','Inner planet'), /identity|grounding/);
});

test('empty intervening scenes cannot silently extend anaphora history', () => {
  assert.throws(()=>api().prepareScenes([scene('Gas giants are massive.'),scene('   '),scene('These are large.')]), /empty_scene/);
});

test('local section redirect can ground only through its own exact sitelink', async () => {
  const resolver=api(), fetch=resolver.fetchJson;
  resolver.fetchJson=async url=>{
    const p=new URL(url).searchParams;
    if (p.get('sites')==='enwiki') return {entities:{Q3504248:{id:'Q3504248',sitelinks:{enwiki:{title:'Inner planet'}},claims:{}}}};
    if (p.get('titles')==='Inner planet') return {query:{redirects:[{from:'Inner planet',to:'Solar System',tofragment:'Inner planets'}],pages:{1:{pageid:1,title:'Solar System',pageprops:{wikibase_item:'Q544'}}}}};
    return fetch(url);
  };
  const grounded=await resolver.ground('en','Inner planet');
  assert.equal(grounded.qid,'Q3504248');
  assert.equal(grounded.englishTitle,'Inner planet');
  assert.equal(grounded.page,null);
});

test('an ambiguous list-member alias cannot add an unrelated montage member', async () => {
  const resolver=api(), fetch=resolver.fetchJson;
  resolver.fetchJson=async url=>{
    const data=await fetch(url);
    if (data.parse?.wikitext) data.parse.wikitext['*']+='\n[[Earth|Mercury]]';
    return data;
  };
  await assert.rejects(resolver.preflightScenes([fixture.scenes('en')[0]]), /ambiguous_group_member/);
});


test('production mixed-population narration preserves all explicit examples instead of dust or prior TNO', async () => {
  const recorded = require('./fixtures/wikimedia-uk.json');
  const source = Object.values(recorded.requests).find(data => data.parse?.wikitext).parse.wikitext['*'];
  const text = "Додатково до тисяч малих тіл у цих двох ділянках є інші популяції різноманітних дрібних тіл, як-от комети, метеороїди та космічний пил, що рухаються навколо Сонця.";
  const result = await subject(text, source, 'uk', {localTitle: "Транснептуновий об'єкт", sceneIndex: 2});
  assert.equal(result.mode, 'current_enumeration');
  assert.equal(result.listText, 'комети, метеороїди та космічний пил');
});

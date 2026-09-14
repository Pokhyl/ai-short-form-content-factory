const {test}=require('node:test');
const assert=require('node:assert/strict');
const {resolveSubject,sourceLexicon,DictionaryLemmas}=require('../engine-overlay/VisualSubject');
const dictionary=new DictionaryLemmas();
const cases=[
 ['en','In addition to forest animals there are other populations, such as river otters, domestic cats and blue whales.','[[River otter|river otters]] [[Domestic cat|domestic cats]] [[Blue whale|blue whales]]','river otters, domestic cats and blue whales'],
 ['uk','Додатково до лісових тварин є інші популяції, як-от річкові видри, домашні коти та сині кити.','[[Видра|річкові видри]] [[Кіт|домашні коти]] [[Кит|сині кити]]','річкові видри, домашні коти та сині кити'],
 ['ru','Кроме лесных животных есть другие популяции, такие как речные выдры, домашние кошки и синие киты.','[[Выдра|речные выдры]] [[Кошка|домашние кошки]] [[Кит|синие киты]]','речные выдры, домашние кошки и синие киты'],
 ['pl','Oprócz zwierząt leśnych są inne populacje, takie jak wydry rzeczne, koty domowe i płetwale błękitne.','[[Wydra|wydry rzeczne]] [[Kot|koty domowe]] [[Płetwal|płetwale błękitne]]','wydry rzeczne, koty domowe i płetwale błękitne'],
];
for(const [lang,text,source,list] of cases)test(`explicit existential examples preserve every member: ${lang}`,async()=>{
 const result=await resolveSubject(text,lang,sourceLexicon(source,'Reference'),dictionary);
 assert.equal(result.mode,'current_enumeration');assert.equal(result.listText,list);
});
test('examples of an object cannot replace a known subject',async()=>{
 const result=await resolveSubject('Blue whales eat animals, such as river otters and domestic cats.','en',sourceLexicon(cases[0][2],'Reference'),dictionary);
 assert.equal(result.title,'Blue whale');
});
test('unresolved enumeration members cannot be silently dropped',async()=>{
 await assert.rejects(resolveSubject('There are other populations, such as river otters and mystery creatures.','en',sourceLexicon(cases[0][2],'Reference'),dictionary), /unresolved_group_member/);
});

const {api}=require('./fixtures/api.cjs');
const fixture=require('./fixtures/scenes.cjs');
test('enumeration preflight selects exact media for every member',async()=>{
 const resolver=api();
 const [result]=await resolver.preflightScenes([{...fixture.scenes('en')[0], text:'There are other populations, such as Mercury, Venus and Earth.'}]);
 assert.equal(result.source,'exact_listed_members');
 assert.deepEqual(result.components.map(m=>m.groundedEntity),['Mercury (planet)','Venus','Earth']);
 assert.equal(result.components.length,3);
});

test('an explicit group in the current head has priority over its examples',async()=>{
 const result=await resolveSubject('There are other deciduous trees, such as oak and beech.','en',sourceLexicon('[[Deciduous tree|deciduous trees]] [[Oak]] [[Beech]]','Reference'),dictionary);
 assert.equal(result.title,'Deciduous tree');
});
test('descriptive apposition and a later location cannot replace the leading subject',async()=>{
 for(const [lang,text,links] of [
  ['en','Blue whales, huge animals of the ocean, travel through coastal waters.','[[Blue whale|blue whales]] [[Ocean]] [[Coastal waters|coastal waters]]'],
  ['uk','Сині кити, великі тварини океану, подорожують через прибережні води.','[[Blue whale|Сині кити]] [[Ocean|океану]] [[Coastal waters|прибережні води]]'],
  ['ru','Синие киты, огромные животные океана, проходят через прибрежные воды.','[[Blue whale|Синие киты]] [[Ocean|океана]] [[Coastal waters|прибрежные воды]]'],
  ['pl','Płetwale błękitne, wielkie zwierzęta oceanu, przemierzają wody przybrzeżne.','[[Blue whale|Płetwale błękitne]] [[Ocean|oceanu]] [[Coastal waters|wody przybrzeżne]]'],
 ]) assert.equal((await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary)).title,'Blue whale');
});
test('a comma-separated list of known phrases remains ambiguous',async()=>{
 await assert.rejects(resolveSubject('Blue whales, domestic cats, river otters.','en',sourceLexicon(cases[0][2],'Reference'),dictionary),/ambiguous_subject/);
});
test('undersized pageimage can use exact same-entity Wikidata P18 without lowering size gate',async()=>{
 const resolver=api();
 const entity={qid:'Q79833',englishTitle:'Solar wind',page:{pageimage:'Small.jpg',thumbnail:{source:'https://upload.wikimedia.org/Small.jpg',width:300,height:200}}};
 resolver.dataEntity=async()=>({claims:{P18:[{mainsnak:{datavalue:{value:'Exact.jpg'}}}]}});
 resolver.query=async()=>({query:{pages:{1:{title:'File:Exact.jpg',imageinfo:[{url:'https://upload.wikimedia.org/Exact.jpg',mime:'image/jpeg',width:1080,height:900}]}}}});
 const result=await resolver.pageImage(entity);
 assert.equal(result.title,'File:Exact.jpg');assert.equal(result.source,'exact_wikidata_p18');
});
test('quantified coordinated subjects retain both groups and exclude the object',async()=>{
 for(const [lang,text,links,list] of [
 ['en','Six domestic cats and three blue whales have parasites.','[[Cat|domestic cats]] [[Whale|blue whales]] [[Parasite|parasites]]','domestic cats, blue whales'],
 ['uk','Шість домашніх котів та три сині кити мають паразитів.','[[Cat|домашніх котів]] [[Whale|сині кити]] [[Parasite|паразитів]]','домашніх котів, сині кити'],
 ['ru','Шесть домашних кошек и три синих кита имеют паразитов.','[[Cat|домашних кошек]] [[Whale|синих кита]] [[Parasite|паразитов]]','домашних кошек, синих кита'],
 ['pl','Sześć kotów domowych i trzy płetwale błękitne mają pasożyty.','[[Cat|kotów domowych]] [[Whale|płetwale błękitne]] [[Parasite|pasożyty]]','kotów domowych, płetwale błękitne'],
 ]){const r=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(r.mode,'current_enumeration');assert.equal(r.listText,list);}
});
test('each-of subject retains the full qualified phrase',async()=>{
 const r=await resolveSubject('Кожна з зовнішніх планет оточена кільцями пилу та інших частинок.','uk',sourceLexicon('[[Outer planet|зовнішніх планет]] [[Ring|кільцями]] [[Dust|пилу]]','Reference'),dictionary);
 assert.equal(r.title,'Outer planet');
});

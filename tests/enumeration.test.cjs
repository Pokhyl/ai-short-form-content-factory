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
test('two multiword class phrases before a relative clause are treated as apposition, not an enumeration',async()=>{
 const result=await resolveSubject('Карликова планета, небесне тіло, яке обертається навколо Сонця.','uk',sourceLexicon('[[Карликова планета]] [[Астрономічний об’єкт|небесне тіло]] [[Сонце|Сонця]]','Reference'),dictionary);
 assert.equal(result.title,'Карликова планета');
 assert.notEqual(result.mode,'current_enumeration');
});
test('scene-start relative pronouns inherit only the immediate previous semantic scene',async()=>{
 for(const[lang,text]of [
  ['uk','Яке є достатньо масивним, щоб підтримувати кулясту форму.'],
  ['uk','Але яке не очистило простір своєї орбіти від планетозималей.'],
  ['ru','Которое является достаточно массивным, чтобы поддерживать сферическую форму.'],
  ['pl','Które jest wystarczająco masywne, aby zachować kulisty kształt.'],
  ['en','Which is massive enough to maintain a spherical shape.'],
 ]){
  const previous={localTitle:'Карликова планета',sceneIndex:3};
  const result=await resolveSubject(text,lang,sourceLexicon('[[Карликова планета]]','Reference'),dictionary,previous);
  assert.equal(result.title,'Карликова планета');
  assert.equal(result.mode,'previous_scene_relative_subject');
  assert.equal(result.antecedentScene,3);
 }
});
test('scene-start relative pronoun without an immediate antecedent fails closed',async()=>{
 await assert.rejects(resolveSubject('Яке є достатньо масивним, щоб підтримувати кулясту форму.','uk',sourceLexicon('[[Карликова планета]]','Reference'),dictionary),/missing_antecedent/);
});
test('leading discovery context cannot displace the later main-clause entity in UK RU PL EN',async()=>{
 for(const[lang,text,links,expected]of [
  ['uk','Після відкриття Плутона зовнішня частина Сонячної системи стала відомою.','[[Плутон|Плутона]] [[Сонячна система|Сонячної системи]]','Сонячна система'],
  ['ru','После открытия Плутона внешняя часть Солнечной системы стала известной.','[[Плутон|Плутона]] [[Солнечная система|Солнечной системы]]','Солнечная система'],
  ['pl','Po odkryciu Plutona zewnętrzna część Układu Słonecznego stała się znana.','[[Pluton|Plutona]] [[Układ Słoneczny|Układu Słonecznego]]','Układ Słoneczny'],
  ['en','After the discovery of Pluto the outer part of the Solar System became known.','[[Pluto]] [[Solar System|Solar System]]','Solar System'],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.title,expected);assert.equal(result.mode,'current_subject_after_event_context');}
});
test('generic classified objects with explicit examples keep the named examples in UK RU PL EN',async()=>{
 for(const[lang,text,links,expected]of [
  ['uk',"Інші об'єкти можуть бути класифіковані як держави, наприклад, Франція, Німеччина та Польща.",'[[Франція]] [[Німеччина]] [[Польща]] [[Держава|держави]]','Франція, Німеччина та Польща'],
  ['ru','Другие объекты могут быть классифицированы как государства, например, Франция, Германия и Польша.','[[Франция]] [[Германия]] [[Польша]] [[Государство|государства]]','Франция, Германия и Польша'],
  ['pl','Inne obiekty mogą być klasyfikowane jako państwa, na przykład, Francja, Niemcy i Polska.','[[Francja]] [[Niemcy]] [[Polska]] [[Państwo|państwa]]','Francja, Niemcy i Polska'],
  ['en','Other objects may be classified as countries, for example, France, Germany and Poland.','[[France]] [[Germany]] [[Poland]] [[Country|countries]]','France, Germany and Poland'],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.mode,'current_enumeration');assert.equal(result.listText,expected);}
});
test('example enumerations retain one explicit grounded head as lead-in evidence in UK RU PL EN',async()=>{
 for(const[lang,text,links,group]of [
  ['uk',"Додатково до малих тіл є інші об'єкти, як-от комети, метеороїди та космічний пил.","[[Малі тіла Сонячної системи|малих тіл]] [[Комета|комети]] [[Метеороїд|метеороїди]] [[Космічний пил|космічний пил]]",'Малі тіла Сонячної системи'],
  ['ru','Дополнительно к малым телам есть другие объекты, например, кометы, метеороиды и космическая пыль.','[[Малое тело Солнечной системы|малым телам]] [[Комета|кометы]] [[Метеороид|метеороиды]] [[Космическая пыль|космическая пыль]]','Малое тело Солнечной системы'],
  ['pl','Oprócz małych ciał są inne obiekty, na przykład, komety, meteoroidy i pył kosmiczny.','[[Małe ciało Układu Słonecznego|małych ciał]] [[Kometa|komety]] [[Meteoroid|meteoroidy]] [[Pył kosmiczny|pył kosmiczny]]','Małe ciało Układu Słonecznego'],
  ['en','In addition to small bodies there are other objects, for example, comets, meteoroids and cosmic dust.','[[Small Solar System body|small bodies]] [[Comet|comets]] [[Meteoroid|meteoroids]] [[Cosmic dust|cosmic dust]]','Small Solar System body'],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.mode,'current_enumeration');assert.equal(result.groupSubject?.title,group);assert.equal(text.slice(result.groupSubject.start,result.groupSubject.end),result.groupSubject.surface);}
});
test('divided-into counted enumerations keep the named categories in UK RU PL EN',async()=>{
 for(const[lang,text,links,expected]of [
  ['uk',"Усі об'єкти офіційно поділяються на три категорії, Франція, Німеччина та Польща.",'[[Франція]] [[Німеччина]] [[Польща]]','Франція, Німеччина, Польща'],
  ['ru','Все объекты официально разделяются на три категории, Франция, Германия и Польша.','[[Франция]] [[Германия]] [[Польша]]','Франция, Германия, Польша'],
  ['pl','Wszystkie obiekty oficjalnie dzielą się na trzy kategorie, Francja, Niemcy i Polska.','[[Francja]] [[Niemcy]] [[Polska]]','Francja, Niemcy, Polska'],
  ['en','All objects are officially divided into three categories, France, Germany and Poland.','[[France]] [[Germany]] [[Poland]]','France, Germany, Poland'],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.mode,'current_enumeration');assert.equal(result.listText,expected);}
});
test('counted typed enumerations keep only the named members in UK RU PL EN',async()=>{
 for(const[lang,text,links,expected]of [
  ['uk','За цим визначенням є три держави, Франція, Німеччина та Польща.','[[Франція]] [[Німеччина]] [[Польща]] [[Держава|держави]]',['Франція','Німеччина','Польща']],
  ['ru','По этому определению есть три государства, Франция, Германия и Польша.','[[Франция]] [[Германия]] [[Польша]] [[Государство|государства]]',['Франция','Германия','Польша']],
  ['pl','Według tej definicji są trzy państwa, Francja, Niemcy i Polska.','[[Francja]] [[Niemcy]] [[Polska]] [[Państwo|państwa]]',['Francja','Niemcy','Polska']],
  ['en','By this definition there are three countries, France, Germany and Poland.','[[France]] [[Germany]] [[Poland]] [[Country|countries]]',['France','Germany','Poland']],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.mode,'current_enumeration');assert.deepEqual(result.listText.split(', '),expected);}
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
test('unknown coordinated quantified subject cannot disappear behind a known subject',async()=>{
 await assert.rejects(resolveSubject('Six domestic cats and three mystery creatures have parasites.','en',sourceLexicon('[[Cat|domestic cats]] [[Parasite|parasites]]','Reference'),dictionary),/unresolved_group_member/);
});
test('missing group image can compose every exact Wikidata has-part member',async()=>{
 const resolver=api();
 resolver.dataEntity=async qid=>qid==='QGROUP'?{claims:{P527:['Q308','Q313'].map(id=>({mainsnak:{datavalue:{value:{id}}}}))}}:{sitelinks:{enwiki:{title:qid==='Q308'?'Mercury (planet)':'Venus'}}};
 const result=await resolver.structuredGroupMedia({qid:'QGROUP',englishTitle:'Verified group'},new Map());
 assert.equal(result.components.length,2);
 assert.deepEqual(result.components.map(m=>m.groundedEntityId),['Q308','Q313']);
 assert.equal(result.source,'exact_wikidata_parts');
});
test('a has-part sitelink resolving to a different identity fails closed',async()=>{
 const resolver=api();
 resolver.dataEntity=async qid=>qid==='QGROUP'?{claims:{P527:['Q308','Q313'].map(id=>({mainsnak:{datavalue:{value:{id}}}}))}}:{sitelinks:{enwiki:{title:'Earth'}}};
 await assert.rejects(resolver.structuredGroupMedia({qid:'QGROUP',englishTitle:'Verified group'},new Map()),/identity_mismatch/);
});

test('explicit copular subjects outrank anaphoric copula tokens in UK RU PL EN',async()=>{
 for(const [lang,text,links,expected] of [
  ['uk','Планета — це будь-яке тіло на орбіті.','[[Планета]]','Планета'],
  ['ru','Планета — это любое тело на орбите.','[[Планета]]','Планета'],
  ['pl','Planeta to dowolne ciało na orbicie.','[[Planeta]]','Planeta'],
  ['en','Planet is any body in orbit.','[[Planet]]','Planet'],
 ]){
  const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);
  assert.equal(result.title,expected);
  assert.equal(result.mode,'current_copular_subject');
 }
});
test('counted enumeration keeps its explicit class as lead-in evidence, not a topic fallback',async()=>{
 for(const[lang,text,links,group]of [
  ['uk','У регіоні є дві держави, Франція та Німеччина.','[[Регіон|регіоні]] [[Держава|держави]] [[Франція]] [[Німеччина]]','Держава'],
  ['ru','В регионе есть две страны, Франция и Германия.','[[Регион|регионе]] [[Страна|страны]] [[Франция]] [[Германия]]','Страна'],
  ['pl','W regionie są dwa państwa, Francja i Niemcy.','[[Region|regionie]] [[Państwo|państwa]] [[Francja]] [[Niemcy]]','Państwo'],
  ['en','In the region there are two countries, France and Germany.','[[Region|region]] [[Country|countries]] [[France]] [[Germany]]','Country'],
 ]){const result=await resolveSubject(text,lang,sourceLexicon(links,'Reference'),dictionary);assert.equal(result.groupSubject.title,group);assert.equal(text.slice(result.groupSubject.start,result.groupSubject.end),result.groupSubject.surface);}
});
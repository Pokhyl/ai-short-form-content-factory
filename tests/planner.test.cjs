const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const code=fs.readFileSync(require('node:path').join(__dirname,'../n8n/code/WF10-build-extractive.js'),'utf8');
function helpers(language,sourceText){
  const prefix=code.slice(0,code.indexOf('let best = null;'));
  return new Function('$','$json',prefix+'\nreturn {hasCoherentContext,sentences,sourceSentenceIndexes};')(
    ()=>({item:{json:{language,target_duration_seconds:60}}}),{sourceText});
}
const samples=[
 ['uk','Марія Кюрі досліджувала радіоактивні речовини.','Однак вона приховала результати дослідження.'],
 ['ru','Мария Кюри исследовала радиоактивные вещества.','Однако она скрыла результаты исследования.'],
 ['pl','Maria Curie badała substancje radioaktywne.','Jednak ona ukryła wyniki badania.'],
 ['en','Marie Curie studied radioactive materials.','However, she withheld the research results.'],
];
test('planner rejects orphan openings but retains adjacent contextual narration in UK RU PL EN',()=>{
 for(const[lang,first,next]of samples){const h=helpers(lang,first+' '+next);assert.equal(h.hasCoherentContext([1]),false);assert.equal(h.hasCoherentContext([0,1]),true);assert.equal(h.hasCoherentContext([0]),true);}
});
test('planner cannot bridge a skipped source sentence for anaphora',()=>{
 for(const[lang,first,next]of samples){const h=helpers(lang,[first,first,next].join(' '));assert.equal(h.hasCoherentContext([0,2]),false);assert.equal(h.hasCoherentContext([1,2]),true);}
});
test('filtered source sentences still break immediate contextual continuity',()=>{
 for(const[lang,first,next]of samples){const h=helpers(lang,[first,'Hi.',next].join(' '));assert.deepEqual(h.sourceSentenceIndexes,[0,2]);assert.equal(h.hasCoherentContext([0,1]),false);}
});
test('a pronoun within a self-contained sentence is not an orphan opening',()=>{
 const h=helpers('en','Marie Curie said she worked with radioactive materials.');assert.equal(h.hasCoherentContext([0]),true);
});
test('demonstrative and possessive openings require adjacent context',()=>{
 for(const[lang,opening]of [['uk','Його результати залишалися невідомими довгий час.'],['ru','Эта система имеет несколько разных компонентов.'],['pl','Jego wyniki pozostawały nieznane przez lata.'],['en','These results remained unknown for many years.']]){assert.equal(helpers(lang,opening).hasCoherentContext([0]),false);}
});
test('full planner excludes a timing-perfect orphan candidate without changing timing profile',()=>{
 const sourceText='However she withheld all the important results from every other researcher who had worked with her in the laboratory for many years before publishing them in a respected international scientific research journal.';
 const run=()=>new Function('$','$json',code)(()=>({item:{json:{language:'en',target_duration_seconds:15}}}),{sourceText});
 assert.throws(run,/cannot pre-plan/);
});
test('full planner selects a self-contained alternative instead of an equally timed orphan',()=>{
 const orphan='However she withheld all the important results from every other researcher who had worked with her in the laboratory for many years before publishing them in a respected international scientific research journal.';
 const independent=orphan.replace('However she','Marie Curie');
 const result=new Function('$','$json',code)(()=>({item:{json:{language:'en',target_duration_seconds:15}}}),{sourceText:orphan+' '+independent})[0].json;
 assert.equal(result.script,independent);
 assert.deepEqual(result.sourceData.timing_profile.accepted_narration_seconds,[13.5,15.35]);
});

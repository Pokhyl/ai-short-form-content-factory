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


test('UK 60s planner uses an empirical fast/slow character band before the one TTS request',()=>{
 const sourceText=`У Сонячній системі є дві ділянки, заповнені малими тілами. Пояс астероїдів, що розташований між Марсом і Юпітером, за складом подібний до планет земної групи, оскільки складається переважно з силікатів і металів. Найбільшими об'єктами поясу астероїдів є Церера, Паллада та Веста. За орбітою Нептуна розташовано транснептунові об'єкти, що містять багато замерзлої води, аміаку та метану. Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида. Додатково до тисяч малих тіл у цих двох ділянках є інші популяції різноманітних дрібних тіл, як-от комети, метеороїди та космічний пил, що рухаються навколо Сонця. Шість із восьми планет та три карликові планети мають природні супутники.`;
 const result=new Function('$','$json',code)(()=>({item:{json:{job_id:'test',language:'uk',target_duration_seconds:60}}}),{sourceText})[0].json;
 const profile=result.sourceData.timing_profile;
 assert.equal(profile.model,'gemini_enceladus_uk_60s_char_band_v2');
 assert.equal(profile.fast_chars_per_second,10.7);
 assert.equal(profile.slow_chars_per_second,9.9);
 assert.equal(profile.renderer_min_narration_seconds,54);
 assert.equal(profile.selection_max_narration_seconds,60.35);
 assert.ok(profile.estimated_fastest_narration_seconds>=54);
 assert.ok(profile.estimated_slowest_narration_seconds<=60.35);
 assert.ok(profile.non_space_chars>=578 && profile.non_space_chars<=597);
 assert.deepEqual(profile.accepted_narration_seconds,[54,60.35]);
});


test('UK 60s empirical band rejects the measured 571-char undershoot and 626-char overshoot but accepts the 587-char safe region',()=>{
 const prefix=code.slice(0,code.indexOf('const normalizedSpeechSource'));
 const h=new Function('$','$json',prefix+'\nreturn {estimateUk60NarrationBand,geminiUk60TimingProfile};')(
   ()=>({item:{json:{job_id:'test',language:'uk',target_duration_seconds:60}}}),{}
 );
 const band571=h.estimateUk60NarrationBand('а'.repeat(571));
 const band587=h.estimateUk60NarrationBand('а'.repeat(587));
 const band626=h.estimateUk60NarrationBand('а'.repeat(626));
 assert.ok(band571.fastestSeconds<54);
 assert.ok(band587.fastestSeconds>=54);
 assert.ok(band587.slowestSeconds<=60.35);
 assert.ok(band626.slowestSeconds>60.35);
});


test('Ukrainian copular dashes preserve an explicit semantic link across sentence boundaries',()=>{
 const prefix=code.slice(0,code.indexOf('const speechRate'));
 const h=new Function('$','$json',prefix+'\nreturn {normalizeForSpeech,normalizeUkrainianSpeech};')(()=>({item:{json:{job_id:'test',language:'uk',target_duration_seconds:60}}}),{});
 const raw="Карликова планета — небесне тіло, яке обертається навколо Сонця. Інші об'єкти, що обертаються навколо Сонця, — малі тіла Сонячної системи.";
 const normalized=h.normalizeUkrainianSpeech(h.normalizeForSpeech(raw,'uk'));
 assert.match(normalized,/Карликова планета — це небесне тіло/);
 assert.match(normalized,/Сонця, це малі тіла Сонячної системи/);
});

test('speech normalization keeps colon continuations inside one semantic sentence',()=>{
 const h=helpers('uk','Система складається з двох частин: першої частини та другої частини, які працюють разом.');
 assert.equal(h.sentences.length,1);
 assert.match(h.sentences[0],/частин, першої частини/);
});
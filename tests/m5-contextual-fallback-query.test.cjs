const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const n=Object.fromEntries(w.nodes.map(n=>[n.name,n]));
const c=JSON.parse(fs.readFileSync('tests/fixtures/m5-10042-language-repair-context.json'));
const response=storyboard=>({statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify(storyboard)}]}}]}});

test('explicit concise visual-intent context survives deterministic third-query canonicalization',()=>{
 const ctx={...c};
 const storyboard=structuredClone(c.base_storyboard);
 const s5=storyboard.scenes.find(s=>s.scene_id==='S5');
 assert.equal(s5.shots[0].queries_en[2],'internal SSD drive');
 const $=()=>({first:()=>({json:ctx})});
 const out=new Function('$','$json',n['Validate Storyboard'].parameters.jsCode)($,response(storyboard)).json;
 const actual=out.storyboard.scenes.find(s=>s.scene_id==='S5').shots[0].queries_en[2];
 assert.equal(actual,'internal SSD drive');
});

test('generic third query still canonicalizes to concrete primary fallback',()=>{
 const ctx={...c};
 const storyboard=structuredClone(c.base_storyboard);
 const s6=storyboard.scenes.find(s=>s.scene_id==='S6');
 s6.shots[0].queries_en[2]='RAM memory stick';
 const $=()=>({first:()=>({json:ctx})});
 const out=new Function('$','$json',n['Validate Storyboard'].parameters.jsCode)($,response(storyboard)).json;
 const actual=out.storyboard.scenes.find(s=>s.scene_id==='S6').shots[0].queries_en[2];
 assert.equal(actual,'RAM module');
});


test('required interaction subject cannot disappear from secondary must_show',()=>{
 for(const validatorName of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2']){
  const code=n[validatorName].parameters.jsCode;
  const start=code.indexOf('function assertRequiredInteractionSecondary');
  const end=code.indexOf('// MUST_SHOW_SECONDARY_GUARD_END');
  assert.ok(start>=0 && end>start,validatorName);
  const guard=new Function(code.slice(start,end)+'\nreturn assertRequiredInteractionSecondary;')();
  assert.throws(
   ()=>guard(['multimeter'],'A multimeter measuring voltage on a car battery.','S6-A'),
   /second independently visible interaction subject.*car battery/
  );
  assert.doesNotThrow(
   ()=>guard(['multimeter','car battery'],'A multimeter measuring voltage on a car battery.','S6-A')
  );
  assert.throws(
   ()=>guard(['multimeter'],'A multimeter measures voltage on car battery.','S6-A'),
   /second independently visible interaction subject.*car battery/
  );
  assert.doesNotThrow(
   ()=>guard(['barometer'],'A barometer instrument measuring the air pressure of the atmosphere.','S1-A')
  );
  assert.doesNotThrow(
   ()=>guard(['power substation','transmission lines'],'Power substation equipment and transmission lines connected to power grid','S4-A')
  );
  assert.throws(
   ()=>guard(['copper coil'],'A copper coil connected to an alternating current power source.','S3-A'),
   /second independently visible interaction subject.*alternating current power source/
  );
  assert.doesNotThrow(
   ()=>guard(['copper coil','power source'],'A copper coil connected to an alternating current power source.','S3-A')
  );
 }
});

test('detailed interaction queries are deterministically completed from secondary must_show',()=>{
 const runCase=(visualIntent,mustShow,queries)=>{
  const ctx={...c};
  const storyboard=structuredClone(c.base_storyboard);
  storyboard.scenes[0].shots[0]={
   shot_id:'S1-A',
   visual_intent:visualIntent,
   must_show:mustShow,
   must_not_show:[],
   queries_en:queries,
   preferred_media_type:'photo',
  };
  const $=()=>({first:()=>({json:ctx})});
  return new Function('$','$json',n['Validate Storyboard'].parameters.jsCode)($,response(storyboard)).json
   .storyboard.scenes[0].shots[0].queries_en;
 };

 const multimeter=runCase(
  'A multimeter measuring voltage on a car battery.',
  ['multimeter','car battery'],
  ['multimeter measuring car battery','digital multimeter voltage test','multimeter']
 );
 assert.equal(multimeter[0],'multimeter measuring car battery');
 assert.equal(multimeter[1],'digital multimeter voltage test car battery');

 const shifter=runCase(
  'A close-up of a bicycle gear shifter connected to a control cable',
  ['gear shifter','control cable'],
  ['bicycle gear shifter with control cable','handlebar shifter cable mechanism','gear shifter']
 );
 assert.equal(shifter[0],'bicycle gear shifter with control cable');
 assert.equal(shifter[1],'handlebar shifter cable mechanism control cable');
});

test('dependent component detail canonicalizes to primary-only photo contract',()=>{
 const ctx={...c};
 const storyboard=structuredClone(c.base_storyboard);
 storyboard.scenes[0].shots[0]={
  shot_id:'S1-A',
  visual_intent:'A close-up of a thermistor sensor tip on a digital thermometer.',
  must_show:['digital thermometer','sensor tip'],
  must_not_show:['analog scale'],
  queries_en:['digital thermometer sensor tip','thermistor sensor probe digital thermometer','sensor tip'],
  preferred_media_type:'photo',
 };
 const $=()=>({first:()=>({json:ctx})});
 const out=new Function('$','$json',n['Validate Storyboard'].parameters.jsCode)($,response(storyboard)).json;
 const shot=out.storyboard.scenes[0].shots[0];

 assert.deepEqual(shot.must_show,['digital thermometer']);
 assert.equal(shot.visual_intent,'A close-up photo of digital thermometer.');
 assert.equal(shot.queries_en[0],'digital thermometer sensor tip');
 assert.equal(shot.queries_en[1],'thermistor sensor probe digital thermometer');
 assert.equal(shot.queries_en[2],'digital thermometer');
});

test('storyboard prompt requires both visible interaction subjects in detailed queries',()=>{
 const code=n['Build Script Prompt'].parameters.jsCode;
 assert.match(code,/include the second required subject as must_show\[1\]/);
 assert.match(code,/queries_en\[0\] and queries_en\[1\] must contain distinctive terms for BOTH subjects/);
});

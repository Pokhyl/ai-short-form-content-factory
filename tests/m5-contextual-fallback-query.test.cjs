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
   ()=>guard(['multimeter'],'A multimeter measuring voltage on a car battery.',['multimeter measuring car battery','digital multimeter car battery voltage','multimeter'],'S6-A'),
   /second independently visible interaction subject.*car battery/
  );
  assert.throws(
   ()=>guard(['multimeter','car battery'],'A multimeter measuring voltage on a car battery.',['multimeter measuring car battery','digital multimeter voltage test','multimeter'],'S6-A'),
   /detailed query 2 must preserve required interaction subject.*car battery/
  );
  assert.doesNotThrow(
   ()=>guard(['multimeter','car battery'],'A multimeter measuring voltage on a car battery.',['multimeter measuring car battery','digital multimeter car battery voltage','multimeter'],'S6-A')
  );
  assert.throws(
   ()=>guard(['multimeter'],'A multimeter measures voltage on car battery.',['multimeter measuring car battery','digital multimeter car battery voltage','multimeter'],'S6-A'),
   /second independently visible interaction subject.*car battery/
  );
  assert.doesNotThrow(
   ()=>guard(['barometer'],'A barometer instrument measuring the air pressure of the atmosphere.',['barometer atmospheric pressure','barometer pressure scale','barometer'],'S1-A')
  );
  assert.doesNotThrow(
   ()=>guard(['power substation','transmission lines'],'Power substation equipment and transmission lines connected to power grid',['power substation equipment','electrical transmission grid','power substation'],'S4-A')
  );
 }
});

test('storyboard prompt requires both visible interaction subjects in detailed queries',()=>{
 const code=n['Build Script Prompt'].parameters.jsCode;
 assert.match(code,/include the second required subject as must_show\[1\]/);
 assert.match(code,/queries_en\[0\] and queries_en\[1\] must contain distinctive terms for BOTH subjects/);
});

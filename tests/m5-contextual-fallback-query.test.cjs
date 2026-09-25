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

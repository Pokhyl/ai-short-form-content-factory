const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('acceptance/2026-09-25-m8-9955-per-concept-gap.json'));
const request=f.requests.find(r=>r.shot_key==='S3-A');
const saved=f.evaluations.find(r=>r.shot_key==='S3-A');
const source=saved.evaluations.find(e=>/lacks a clearly visible focused light beam/.test(e.reason));
assert(source,'exact contradictory production evaluation missing');
const ctx={...request,candidates:[request.candidates[source.candidate_index-1]]};
const code=w.nodes.find(n=>n.name==='Parse Gemini Vision Result').parameters.jsCode;
function parse(row){return new Function('$','$json',code)(()=>({item:{json:ctx}}),{statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify({evaluations:[{...row,candidate_index:1}]})}]}}]}}).json.evaluations[0];}
const checks=[{concept_index:1,visible:true,evidence:'Fresnel lens rings and lamps are visible.'},{concept_index:2,visible:false,evidence:'No emitted light beam is visible.'}];
test('9955 old aggregate PASS without per-concept evidence fails closed',()=>{
 assert.equal(source.vision_pass,true);assert.throws(()=>parse(source),/per-concept evidence count mismatch/);
});
test('9955 absent beam overrides model aggregate true and score90 without weakening required concepts',()=>{
 const out=parse({...source,must_show_checks:checks});
 assert.equal(out.must_show_visible,false);assert.equal(out.vision_pass,false);
 assert.deepEqual(out.must_show_checks.map(c=>c.concept),request.must_show);
});
test('all required concepts visible retains score and intent gates',()=>{
 const all=checks.map(c=>({...c,visible:true,evidence:'Required concept clearly visible in the frame.'}));
 assert.equal(parse({...source,must_show_checks:all}).vision_pass,true);
 assert.equal(parse({...source,must_show_checks:all,intent_match:false}).vision_pass,false);
 assert.equal(parse({...source,must_show_checks:all,match_score:69}).vision_pass,false);
});
test('missing duplicate out-of-range or nonboolean concept checks fail closed',()=>{
 for(const bad of [checks.slice(0,1),[checks[0],checks[0]],[checks[0],{...checks[1],concept_index:3}],[checks[0],{...checks[1],visible:'true'}],[checks[0],{...checks[1],evidence:''}]]){
  assert.throws(()=>parse({...source,must_show_checks:bad}),/per-concept evidence/);
 }
});

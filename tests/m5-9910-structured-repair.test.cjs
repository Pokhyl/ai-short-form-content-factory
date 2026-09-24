const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const fixture=JSON.parse(fs.readFileSync('tests/fixtures/m5-9910-storyboard-repair.json'));
const byName=Object.fromEntries(w.nodes.map(n=>[n.name,n]));
const evidence=[1,2,3].map(i=>({evidence_ref:'E'+i,evidence_uuid:'00000000-0000-4000-8000-00000000000'+i,source_domain:'example.com',source_url:'https://example.com/'+i,title:'Evidence',snippet:'Fact',content:'Fact'}));
const ctx=new Function('$json',byName['Build Script Prompt'].parameters.jsCode)({script_run_id:'test',topic:'how does a lighthouse work?',language_code:'en',target_duration_seconds:15,evidence_json:evidence}).json;
const response=d=>({body:{candidates:[{content:{parts:[{text:JSON.stringify(d)}]}}]}});
for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
 test('9910 '+name+' exposes total underfill even behind a media-type error',()=>{
  const rows={'Build Script Prompt':ctx,'Generate Storyboard':response(fixture['Repair Storyboard']),'Repair Storyboard':response(fixture['Repair Storyboard']),'Validate Storyboard':{error:'S1-A preferred_media_type is invalid [line 708]'}};
  const $=n=>({first:()=>({json:rows[n]})});
  const out=new Function('$','$json',byName[name].parameters.jsCode)($,{error:'S1-A preferred_media_type is invalid [line 708]'}).json;
  assert.match(out.user_message,/"current_words":34,"minimum":36,"maximum":42,"target":38,"change_to_target":4,"valid":false/);
  assert.deepEqual(out.response_json_schema,ctx.response_json_schema);
 });
}
test('all three storyboard requests send constrained schema and retain evidence refusal',()=>{
 for(const name of ['Generate Storyboard','Repair Storyboard','Repair Storyboard 2']){
  const expr=byName[name].parameters.body.slice(3,-2).trim();
  const body=JSON.parse(new Function('$json','return ('+expr+')')(ctx));
  const schema=body.generationConfig.responseJsonSchema;
  assert.deepEqual(schema,ctx.response_json_schema,name);
  const story=schema.anyOf.find(x=>x.required.includes('scenes'));
  const refuse=schema.anyOf.find(x=>x.required.includes('error'));
  assert.equal(story.properties.scenes.minItems,5);
  assert.equal(story.properties.scenes.maxItems,5);
  assert.deepEqual(story.properties.scenes.items.properties.shots.items.properties.preferred_media_type.enum,['photo']);
  assert.deepEqual(refuse.properties.error.enum,['INSUFFICIENT_EVIDENCE']);
 }
});

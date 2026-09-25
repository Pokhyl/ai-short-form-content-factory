const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodes=Object.fromEntries(w.nodes.map(n=>[n.name,n]));
const evidence=[1,2,3].map(i=>({evidence_ref:'E'+i,evidence_uuid:'00000000-0000-4000-8000-00000000000'+i}));
for(const language_code of ['en','pl','ru','uk']) for(const duration of [15,30,45,60]) {
 test(`10033 compact provider grammar retains ${language_code}${duration} local contract`,()=>{
  const c=new Function('$json',nodes['Build Script Prompt'].parameters.jsCode)({script_run_id:'test',topic:'a physical process',language_code,target_duration_seconds:duration,evidence_json:evidence}).json;
  const scenes=c.response_json_schema.anyOf[0].properties.scenes;
  assert.equal(scenes.minItems,c.target_scenes);assert.equal(scenes.maxItems,c.target_scenes);
  assert.equal(c.scene_word_targets.reduce((a,b)=>a+b,0),c.target_words);
  assert.ok(!JSON.stringify(scenes.items).includes('minItems'));
  assert.ok(!JSON.stringify(scenes.items).includes('maxItems'));
  assert.ok(JSON.stringify(c.response_json_schema).length<2000);
  assert.deepEqual(scenes.items.properties.shots.items.properties.preferred_media_type.enum,['photo']);
  for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2']){
   const body={scenes:c.scene_word_targets.map((count,i)=>({scene_id:'S'+(i+1),narration_words:Array(count).fill('word')}))};
   body.scenes[body.scenes.length-1].narration_words=['word'];
   const response={statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify(body)}]}}]}};
   assert.throws(()=>new Function('$','$json',nodes[name].parameters.jsCode)(()=>({first:()=>({json:c})}),response),/word-array scene bound mismatch/);
  }
 });
}
for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2'])test('10033 provider failure survives '+name,()=>{
 assert.throws(()=>new Function('$','$json',nodes[name].parameters.jsCode)(()=>({first:()=>({json:{error:{message:'Bad request',description:'Request contains an invalid argument.'}}})}),{}),/Gemini provider failed after transient retries: Request contains an invalid argument/);
});

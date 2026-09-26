const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodes=Object.fromEntries(w.nodes.map(n=>[n.name,n]));
function make(){
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json'));
 const parsed=JSON.parse(f.response.body.candidates[0].content.parts[0].text);
 for(const scene of parsed.scenes){scene.narration_words=scene.narration.split(/\s+/u);delete scene.narration;}
 delete parsed.narration;
 f['Build Script Prompt'].scene_word_targets=parsed.scenes.map(s=>s.narration_words.length);
 return {f,parsed};
}
function run(name,f,parsed){
 f.response.body.candidates[0].content.parts[0].text=JSON.stringify(parsed);
 return new Function('$','$json',nodes[name].parameters.jsCode)(n=>({first:()=>({json:f[n]})}),f.response).json;
}
for(const name of ['Validate Storyboard','Validate Repaired Storyboard','Validate Repaired Storyboard 2']){
 test(name+' converts exact lexical arrays to unchanged internal narration',()=>{
  const {f,parsed}=make();const expected=parsed.scenes.map(s=>s.narration_words.join(' ')).join(' ');
  const out=run(name,f,parsed);
  assert.equal(out.storyboard.narration,expected);assert.equal(out.narration_word_count,22);
  assert.ok(out.storyboard.scenes.every(s=>typeof s.narration==='string'&&!('narration_words' in s)));
 });
 test(name+' accepts bounded scene-count drift and recovers punctuation-only separators',()=>{
  {
   const {f,parsed}=make();
   parsed.scenes[0].narration_words.pop();
   const out=run(name,f,parsed);
   assert.equal(out.storyboard.scenes[0].narration,parsed.scenes[0].narration_words.join(' '));
  }
  {
   const {f,parsed}=make();
   parsed.scenes[0].narration_words.splice(1,0,'—');
   const out=run(name,f,parsed);
   assert.match(out.storyboard.scenes[0].narration,/—/u);
   assert.ok(!out.storyboard.scenes[0].narration.split(/\s+/u).includes('—'));
  }
  {
   const {f,parsed}=make();
   parsed.scenes[0].narration_words[0]='two words';
   assert.throws(()=>run(name,f,parsed),/word-array/);
  }
  {
   const {f,parsed}=make();
   parsed.scenes[0].narration_words=['—','...'];
   assert.throws(()=>run(name,f,parsed),/word-array/);
  }
 });
}
test('English 15s contract allocates 38 word items across five scenes',()=>{
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-9537-scene-segments.json'));
 const source=f['Begin Script']||{};
 // Use a minimal valid evidence input, independent of the production fixture's language.
 const evidence=[1,2,3].map(i=>({evidence_ref:'E'+i,evidence_uuid:'00000000-0000-4000-8000-00000000000'+i,source_domain:'example.com',source_url:'https://example.com/'+i,title:'Evidence',snippet:'Fact',content:'Fact'}));
 const out=new Function('$json',nodes['Build Script Prompt'].parameters.jsCode)({...source,script_run_id:'test',topic:'a physical process',language_code:'en',target_duration_seconds:15,evidence_json:evidence}).json;
 assert.deepEqual(out.scene_word_targets,[8,8,8,7,7]);
 const scenes=out.response_json_schema.anyOf[0].properties.scenes;
 assert.equal(scenes.minItems,5);assert.equal(scenes.maxItems,5);
 assert.equal(scenes.items.properties.narration_words.items.type,'string');
 assert.ok(!('anyOf' in scenes.items));
});

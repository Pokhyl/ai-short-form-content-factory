const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const nodes=Object.fromEntries(workflow.nodes.map(n=>[n.name,n.parameters]));
const original=['A lighthouse is a physical structure built to','emit light from a system of lamps and','lenses to serve as a navigational beacon for','maritime pilots at sea and mark dangerous','coastlines reefs, and safe harbor entries everywhere.'];
const measured=['A lighthouse is a physical structure built specifically to','emit bright light from a system of lamps and','lenses to serve as a vital navigational beacon for',original[3],original[4]];
const storyboard=lines=>({narration:lines.join(' '),scenes:lines.map((narration,i)=>({scene_id:'S'+(i+1),narration,shots:[]}))});
function run(name,json,values){const $=n=>{if(!values[n])throw Error('absent branch');return {first:()=>({json:values[n]})};};return new Function('$','$json',nodes[name].jsCode)($,json).json;}
const response=parsed=>({statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify(parsed)}]}}]}});
for(const suffix of ['Retry','Compliance Retry']){
 const builder='Build Final Measured Word Count '+suffix;
 const validator='Validate Final Measured Word Count '+suffix;
 test('9923 comma-only failing narration cannot consume another probe: '+suffix,()=>{
  const ctx={base_storyboard:storyboard(measured),target_words:43,target_scene_word_counts:[9,9,9,8,8]};
  const values={
   [builder]:ctx,'Build Final Measured Correction':ctx,
   'Normalize Timing Probe':{storyboard:storyboard(original)},
   'Normalize Timing Probe 4':{storyboard:storyboard(measured),measured_duration_ms:13944,target_duration_ms:15000,tolerance_ms:800},
   'Build Script Prompt':{language_code:'en',target_duration_seconds:15},
  };
  const changed=[...measured];changed[4]=changed[4].replace('coastlines','coastlines,');
  assert.throws(()=>run(validator,response({narrations:changed}),values),/M5_UNCHANGED_TIMING_DRAFT/);
 });
 test('word-slot adapter preserves valid narration and rejects missing/nonlexical words: '+suffix,()=>{
  const counts=original.map(x=>x.split(' ').length);
  const ctx={base_storyboard:storyboard(original),target_words:38,target_scene_word_counts:counts};
  const values={[builder]:ctx,'Build Final Measured Correction':ctx,'Normalize Timing Probe':{storyboard:storyboard(original)},'Build Script Prompt':{language_code:'en',target_duration_seconds:15}};
  const words=Object.fromEntries(original.map((s,i)=>['S'+(i+1),s.split(' ')]));
  const out=run(validator,response({narration_words:words}),values);
  assert.equal(out.storyboard.narration,original.join(' '));
  for(const bad of ['two words','...',null]){
   const copy=structuredClone(words);copy.S1[0]=bad;
   assert.throws(()=>run(validator,response({narration_words:copy}),values),/M5_WORD_SLOT_CONTRACT/);
  }
  const short=structuredClone(words);short.S1.pop();
  assert.throws(()=>run(validator,response({narration_words:short}),values),/M5_WORD_SLOT_CONTRACT/);
 });
}
test('9923 requested 43 words are represented as exact provider array cardinalities',()=>{
 const ctx={base_storyboard:storyboard(measured),target_words:43,target_scene_word_counts:[9,9,9,8,8]};
 const values={'Build Final Measured Correction':ctx,'Normalize Timing Probe':{storyboard:storyboard(original)},'Build Script Prompt':{language_code:'en',target_duration_seconds:15}};
 const out=run('Build Final Measured Word Count Retry',{storyboard:storyboard(measured)},values);
 const props=out.response_json_schema.properties.narration_words.properties;
 assert.deepEqual(Object.values(props).map(x=>x.minItems),[9,9,9,8,8]);
 assert.deepEqual(Object.values(props).map(x=>x.maxItems),[9,9,9,8,8]);
 for(const name of ['Repair Final Measured Word Count','Repair Final Measured Word Count Compliance']){
  const body=JSON.parse(new Function('$json','return '+nodes[name].body.slice(3,-2))(out));
  assert.deepEqual(body.generationConfig.responseJsonSchema,out.response_json_schema);
 }
});

test('malformed slots use the existing single compliance branch',()=>{
 assert.equal(run('Classify Final Measured Word Count Retry Failure',{error:'M5_WORD_SLOT_CONTRACT invalid lexical slots for scene 1 [line 140]'},{}).compliance_retry,true);
});

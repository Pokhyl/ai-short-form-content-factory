const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const original=['Lighthouses use tall towers','to elevate a powerful lamp.','A specialized lens concentrates this illumination','into a bright beam, which rotates continuously','to guide ships safely past coastal hazards.'];
const base=[...original];base[4]='to guide ships safely past dangerous coastal hazards.';
const retry=[...original];retry[3]='into a bright beam, which rotates';retry[4]='continuously to guide ships safely past coastal hazards.';
const storyboard=lines=>({narration:lines.join(' '),scenes:lines.map((narration,i)=>({scene_id:'S'+(i+1),narration,shots:[]}))});
for(const [validator,builder,repair] of [
 ['Validate Final Word Count Retry','Build Final Word Count Retry','Build Final Duration Repair'],
 ['Validate Final Measured Word Count Retry','Build Final Measured Word Count Retry','Build Final Measured Correction'],
 ['Validate Final Measured Word Count Compliance Retry','Build Final Measured Word Count Compliance Retry','Build Final Measured Correction'],
]){
 test('9788 hybrid preserves continuous narration boundary: '+validator,()=>{
  const rows={
   [builder]:{base_storyboard:storyboard(base),target_words:32,target_scene_word_counts:[4,5,7,8,8],prior_usage:{}},
   [repair]:{base_storyboard:storyboard(base)},
   'Normalize Timing Probe':{storyboard:storyboard(original)},
   'Build Script Prompt':{language_code:'en',target_duration_seconds:15},
  };
  const $=name=>{if(!rows[name])throw Error('absent branch');return {first:()=>({json:rows[name]})};};
  const response={statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify({narrations:retry})}]}}]}};
  const code=workflow.nodes.find(n=>n.name===validator).parameters.jsCode;
  const out=new Function('$','$json',code)($,response).json;
  assert.doesNotMatch(out.storyboard.narration,/continuously\s+continuously/iu);
  assert.equal(out.storyboard.narration.split(/\bcontinuously\b/iu).length-1,1);
  assert.equal(out.narration_word_count,30);
 });
}

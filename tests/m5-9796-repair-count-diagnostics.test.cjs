const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const lines=['A lighthouse is a sturdy','physical tower designed to emit','light. Inside, a specialized system','of lamps and lenses creates a','powerful beam to guide maritime pilots safely past dangerous coastal hazards.'];
const response={body:{candidates:[{content:{parts:[{text:JSON.stringify({scenes:lines.map((narration,i)=>({scene_id:'S'+(i+1),narration}))})}]}}]}};
for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
 test('9796 repair receives scene identity and all count violations: '+name,()=>{
  const rows={'Build Script Prompt':{target_duration_seconds:15,target_scenes:5,target_shots:5,target_words:32,system_message:'contract',user_message:'input'},'Generate Storyboard':response,'Repair Storyboard':response,'Validate Storyboard':{error:'S1-A preferred_media_type is invalid [line 708]'}};
  const $=key=>({first:()=>({json:rows[key]})});
  const out=new Function('$','$json',w.nodes.find(n=>n.name===name).parameters.jsCode)($,{error:'11, maximum 10 [line 499]'}).json;
  assert.match(out.user_message,/"scene_id":"S5","words":11,"minimum":2,"maximum":10,"valid":false/);
  assert.match(out.user_message,/Repair ALL invalid counts/);
  assert.match(out.user_message,/"scene_id":"S1","words":5,"minimum":2,"maximum":10,"valid":true/);
 });
}

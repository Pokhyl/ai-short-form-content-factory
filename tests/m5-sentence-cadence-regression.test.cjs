const {test}=require('node:test');
const assert=require('node:assert/strict');
const workflow=require('../workflows/VIDEO-M5-Script-Storyboard.json');
const code=Object.fromEntries(workflow.nodes.map(node=>[node.name,node.parameters.jsCode]));
const provider=result=>({statusCode:200,body:{candidates:[{content:{parts:[{text:JSON.stringify(result)}]}}]}});
const sentences=[
  'A pressure sensor responds to air',
  'the flexible diaphragm moves with pressure',
  'a lever transfers that movement',
  'the calibrated pointer turns on a dial',
  'higher readings mean higher pressure',
  'lower readings mean lower pressure',
  'the visible scale shows the measurement',
  'the instrument records changing conditions',
  'the reported result is atmospheric pressure.',
];
function context(duration,shortSentences=false){
  const scenes=sentences.map((text,index)=>({scene_id:'S'+(index+1),narration:text+(shortSentences && [2,5].includes(index)?'.':''),evidence_ids:['E1'],shots:[]}));
  const source={storyboard:{scenes,narration:scenes.map(s=>s.narration).join(' ')},accepted_voiceover_candidate:{audio_sha256:'unchanged'}};
  const script={language_code:'en',target_duration_seconds:duration,topic:'pressure instrument'};
  const build=new Function('$','$json',code['Build Narration Language Review'])(()=>({first:()=>({json:script})}),source).json;
  return {script,source,build};
}
test('one continuous 30s sentence triggers one bounded full-narration language repair before TTS',()=>{
  const {script,source,build}=context(30);
  const reviewed=new Function('$','$json',code['Validate Narration Language Review'])(()=>({first:()=>({json:build})}),provider({language:'en',issues:[]})).json;
  assert.equal(reviewed.language_review.passed,false);
  assert.equal(reviewed.language_review.issues.length,9);
  assert.ok(reviewed.language_review.issues.every(issue=>issue.category==='grammar' && issue.explanation.includes('fewer than three')));
  const repair=new Function('$','$json',code['Build Narration Language Repair'])(()=>({first:()=>({json:script})}),reviewed).json;
  assert.equal(repair.repair_scene_ids.length,9);
  assert.match(repair.system_message,/at least three natural complete sentences/);
  assert.deepEqual(repair.base_storyboard,source.storyboard);
});
test('review retry and final gate fail closed on continued run-on, even when provider reports no issues',()=>{
  const {build,source}=context(30);
  for(const suffix of [' Retry',' Final']){
    const ctx={...build,source};
    const validate=new Function('$','$json',code['Validate Narration Language Review'+suffix]);
    assert.throws(()=>validate(()=>({first:()=>({json:ctx})}),provider({language:'en',issues:[]})),/M5_LANGUAGE_QA_FAILED.*fewer than three/);
  }
});
test('three complete 30s sentences and the original 15s one-sentence gate preserve narration and candidate',()=>{
  for(const [duration,short] of [[30,true],[15,false]]){
    const {source,build}=context(duration,short);
    const result=new Function('$','$json',code['Validate Narration Language Review'])(()=>({first:()=>({json:build})}),provider({language:'en',issues:[]})).json;
    assert.equal(result.language_review.passed,true);
    assert.deepEqual(result.storyboard,source.storyboard);
    assert.deepEqual(result.accepted_voiceover_candidate,source.accepted_voiceover_candidate);
  }
});

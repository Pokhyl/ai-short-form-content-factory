const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

const candidate={
  scenes:[{
    scene_id:'S1',
    narration_words:['Ostrze','posiada','ząbki','oraz','uchwyt','narzędzia.'],
    evidence_ids:['E1'],
    shots:[{
      shot_id:'S1-A',
      visual_intent:'A close-up of a saw handle connected to the metal blade.',
      must_show:['saw handle'],
      must_not_show:['power cord'],
      queries_en:['saw handle close up','hand saw handle','saw handle'],
      preferred_media_type:'photo',
    }],
  }],
};
const response={body:{candidates:[{content:{parts:[{text:JSON.stringify(candidate)}]}}]}};

for(const name of ['Build Storyboard Repair','Build Storyboard Repair 2']){
  test('11877 repair diagnostics surface hidden connected target: '+name,()=>{
    const rows={
      'Build Script Prompt':{
        target_duration_seconds:30,
        target_scenes:1,
        target_shots:1,
        target_words:6,
        word_min:6,
        word_max:20,
        scene_word_targets:[6],
        language_code:'pl',
        system_message:'contract',
        user_message:'input',
        script_run_id:'run-11877',
        model:'gemini-3.5-flash-lite',
        response_json_schema:{type:'object'},
      },
      'Generate Storyboard':response,
      'Repair Storyboard':response,
      'Validate Storyboard':{error:'S1-A must_show items must be short domain anchors [line 1392]'},
    };
    const $=key=>({first:()=>({json:rows[key]})});
    const source={error:'S1-A must_show items must be short domain anchors [line 1392]'};
    const out=new Function('$','$json',byName[name].parameters.jsCode)($,source).json;

    assert.match(out.user_message,/"missing_interaction_subject"/);
    assert.match(out.user_message,/"target":"metal blade"/);
    assert.match(out.user_message,/"must_show":\["saw handle"\]/);
    assert.match(out.user_message,/add that target as a short independent must_show anchor/);
    assert.match(out.user_message,/Never leave a named interaction target absent from must_show/);
  });
}

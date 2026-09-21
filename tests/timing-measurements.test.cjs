const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {test} = require('node:test');
const workflow=JSON.parse(fs.readFileSync(path.join(__dirname,'../workflows/VIDEO-M5-Script-Storyboard.json')));
const builders=['Build Timing Repair 2','Build Final Duration Repair','Build Final Measured Correction'];
function helper(name, row, confirmations) {
  const code=workflow.nodes.find(n=>n.name===name).parameters.jsCode;
  const prefix=code.slice(0,code.indexOf('\nconst '));
  const $=()=>({all:(_branch,run)=>{
    if (!(run in confirmations)) throw Error('not executed');
    return confirmations[run].map(json=>({json}));
  }});
  return new Function('$','row',prefix+'\nreturn withStableMeasurement(row);')($,row);
}
for(const name of builders) {
  test(name+': uses confirmed median only for identical narration',()=>{
    const row={storyboard:{narration:'Exact narration.'},measured_duration_ms:15144};
    const confirmations=[[{storyboard:{narration:'Exact narration.'},stability_median_ms:17136}],
      [{storyboard:{narration:'Other narration.'},stability_median_ms:9000}]];
    assert.equal(helper(name,row,confirmations).measured_duration_ms,17136);
    assert.equal(row.measured_duration_ms,15144); // immutable prior sample
    assert.equal(helper(name,row,[]).measured_duration_ms,15144);
  });
}

function runStabilityB(ctx,bMs) {
  const code=workflow.nodes.find(n=>n.name==='Normalize Timing Stability B').parameters.jsCode;
  const $=name=>{
    if(name==='Prepare Timing Stability Probe B') return {first:()=>({json:ctx})};
    throw new Error('unexpected node '+name);
  };
  return new Function('$','$json',code)($,{statusCode:200,body:{status:'ready',duration_ms:bMs}}).json;
}

test('M6 regression: median-only PL15 stability with one of three in-window samples is rejected',()=>{
  const out=runStabilityB({
    target_duration_ms:15000,
    stability_original_ms:15576,
    stability_a_measured_duration_ms:16704,
    requested_tolerance_ms:750,
    origin_probe_attempt:1,
    script_run_id:'run',
    model:'model',
    storyboard:{narration:'fixture'},
    narration_word_count:24,
    scene_count:5,
    shot_count:5,
    usage:{},
  },13536);
  assert.equal(out.stability_median_ms,15576);
  assert.equal(out.stability_within_final_count,1);
  assert.equal(out.stability_required_within_final,2);
  assert.equal(out.timing_stability_ok,false);
});

test('stability majority passes when two of three real TTS samples are inside final window',()=>{
  const out=runStabilityB({
    target_duration_ms:15000,
    stability_original_ms:15576,
    stability_a_measured_duration_ms:15600,
    requested_tolerance_ms:750,
    origin_probe_attempt:1,
    script_run_id:'run',
    model:'model',
    storyboard:{narration:'fixture'},
    narration_word_count:24,
    scene_count:5,
    shot_count:5,
    usage:{},
  },16704);
  assert.equal(out.stability_median_ms,15600);
  assert.equal(out.stability_within_final_count,2);
  assert.equal(out.stability_required_within_final,2);
  assert.equal(out.timing_stability_ok,true);
});

test('PL15 regression: correction interpolates from 17.136s median, not 15.144s first sample',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build Timing Repair 2').parameters.jsCode;
  const p1={storyboard:{narration:Array(26).fill('slowo').join(' '),scenes:[8,5,5,4,4].map(n=>({narration:Array(n).fill('slowo').join(' ')}))},measured_duration_ms:15144,narration_word_count:26};
  const p2={storyboard:{narration:Array(20).fill('slowo').join(' ')},measured_duration_ms:13704,narration_word_count:20,target_duration_ms:15000,tolerance_ms:750};
  const $=name=>name==='Normalize Timing Stability B'
    ? {all:(_b,r)=>{if(r)throw Error('not executed');return [{json:{storyboard:p1.storyboard,stability_median_ms:17136}}];}}
    : {first:()=>({json:name==='Normalize Timing Probe'?p1:{target_duration_seconds:15,target_scenes:5,target_shots:5,word_min:20,word_max:40}})};
  const result=new Function('$','$json',code)($,p2).json;
  assert.equal(result.target_precision_words,22);
  assert.match(result.user_message,/17136 ms/);
  assert.match(result.user_message,/15000 ms \+\/- 750 ms/);
});

test('unequal original scenes retain their relative space at 22 words',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build Timing Repair 2').parameters.jsCode;
  const original=['Elektrownia wodna zamienia energię wody na prąd elektryczny.','Zapora spiętrza rzekę, tworząc zbiornik.','Spadająca woda napędza turbinę.','Następnie generator wytwarza energię.','Prąd trafia do domów.'];
  const p1={storyboard:{narration:original.join(' '),scenes:original.map(narration=>({narration}))},measured_duration_ms:17856,narration_word_count:25};
  const p2={storyboard:{narration:'Shorter complete draft.'},measured_duration_ms:13596,narration_word_count:18,target_duration_ms:15000,tolerance_ms:750};
  const $=name=>name==='Normalize Timing Stability B'?{all:()=>{throw Error('not executed')}}:{first:()=>({json:name==='Normalize Timing Probe'?p1:{target_duration_seconds:15,target_scenes:5,target_shots:5,word_min:20,word_max:40}})};
  const out=new Function('$','$json',code)($,p2).json;
  assert.equal(out.target_scene_word_counts.reduce((a,b)=>a+b),out.target_precision_words);
  assert.ok(out.target_scene_word_counts[0]>out.target_scene_word_counts[1]);
  assert.ok(out.target_scene_word_counts.every(n=>n>=2&&n<=10));
  assert.ok(out.user_message.includes(original[0]));
});
test('precision retry sees original meaning even when failed draft lost an object',()=>{
 const original=['Elektrownia wodna zamienia energię wody na prąd elektryczny.','Zapora spiętrza rzekę, tworząc zbiornik.'];
 const failed={scenes:[{narration:'Tradycyjna elektrownia zamienia energię elektryczną.'},{narration:'Potężna zapora bardzo skutecznie spiętrza.'}]};
 const rows={
  'Build Script Prompt':{language_code:'pl'},
  'Build Timing Repair 2':{target_precision_words:12,target_scene_word_counts:[7,5]},
  'Repair Storyboard Timing 2':{candidates:[{content:{parts:[{text:JSON.stringify(failed)}]}}]},
  'Normalize Timing Probe':{storyboard:{scenes:original.map(narration=>({narration}))}},
 };
 const code=workflow.nodes.find(n=>n.name==='Build Timing Precision Retry').parameters.jsCode;
 const out=new Function('$',code)(name=>({first:()=>({json:rows[name]})})).json;
 for(const sentence of original)assert.ok(out.user_message.includes(sentence));
 assert.deepEqual(out.target_scene_word_counts,[7,5]);
 assert.deepEqual(out.base_storyboard,failed); // prompts restore meaning; no unmeasured text substitution
});

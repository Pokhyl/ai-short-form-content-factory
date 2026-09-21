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
test('PL15 regression: correction interpolates from 17.136s median, not 15.144s first sample',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build Timing Repair 2').parameters.jsCode;
  const p1={storyboard:{narration:Array(26).fill('slowo').join(' ')},measured_duration_ms:15144,narration_word_count:26};
  const p2={storyboard:{narration:Array(20).fill('slowo').join(' ')},measured_duration_ms:13704,narration_word_count:20,target_duration_ms:15000,tolerance_ms:750};
  const $=name=>name==='Normalize Timing Stability B'
    ? {all:(_b,r)=>{if(r)throw Error('not executed');return [{json:{storyboard:p1.storyboard,stability_median_ms:17136}}];}}
    : {first:()=>({json:name==='Normalize Timing Probe'?p1:{target_duration_seconds:15,target_scenes:5,target_shots:5,word_min:20,word_max:40}})};
  const result=new Function('$','$json',code)($,p2).json;
  assert.equal(result.target_precision_words,22);
  assert.match(result.user_message,/17136 ms/);
  assert.match(result.user_message,/15000 ms \+\/- 750 ms/);
});

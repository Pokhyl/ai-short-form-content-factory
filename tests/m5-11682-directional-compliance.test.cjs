const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));
const code=name=>byName[name].parameters.jsCode;

const original=[
  'Lighthouses use tall towers',
  'to elevate a powerful lamp.',
  'A specialized lens concentrates this illumination',
  'into a bright beam, which rotates continuously',
  'to guide ships safely past coastal hazards.',
];
const base=[...original];
base[4]='to guide ships safely past dangerous coastal hazards.';
const retry=[...original];
retry[3]='into a bright beam, which rotates';
retry[4]='continuously to guide ships safely past coastal hazards.';

const storyboard=lines=>({
  narration:lines.join(' '),
  scenes:lines.map((narration,i)=>({
    scene_id:'S'+(i+1),
    narration,
    shots:[],
  })),
});

test('11682 too-short measured correction rejects a nearest hybrid still below target and routes compliance',()=>{
  const rows={
    'Build Final Measured Word Count Retry':{
      base_storyboard:storyboard(base),
      target_words:32,
      target_scene_word_counts:[4,5,7,8,8],
      prior_usage:{},
    },
    'Build Final Measured Correction':{
      base_storyboard:storyboard(base),
      measured_duration_ms:27024,
      target_duration_ms:30000,
      tolerance_ms:1550,
    },
    'Normalize Timing Probe':{storyboard:storyboard(original)},
    'Build Script Prompt':{language_code:'en',target_duration_seconds:30},
  };
  const $=name=>{
    if(!(name in rows)) throw new Error('absent branch '+name);
    return {first:()=>({json:rows[name]})};
  };
  const response={
    statusCode:200,
    body:{candidates:[{content:{parts:[{text:JSON.stringify({narrations:retry})}]}}]},
  };
  assert.throws(
    ()=>new Function('$','$json',code('Validate Final Measured Word Count Retry'))($,response),
    /M5_DIRECTIONAL_WORD_MISS got 30, target 32/
  );

  const classify=new Function(
    '$json',
    code('Classify Final Measured Word Count Retry Failure')
  );
  assert.equal(
    classify({error:'M5_DIRECTIONAL_WORD_MISS got 30, target 32 [line 470]'}).json.compliance_retry,
    true
  );
});

test('11682 directional marker is not added when measured correction is already within tolerance',()=>{
  const rows={
    'Build Final Measured Word Count Retry':{
      base_storyboard:storyboard(base),
      target_words:32,
      target_scene_word_counts:[4,5,7,8,8],
      prior_usage:{},
    },
    'Build Final Measured Correction':{
      base_storyboard:storyboard(base),
      measured_duration_ms:29000,
      target_duration_ms:30000,
      tolerance_ms:1550,
    },
    'Normalize Timing Probe':{storyboard:storyboard(original)},
    'Build Script Prompt':{language_code:'en',target_duration_seconds:30},
  };
  const $=name=>{
    if(!(name in rows)) throw new Error('absent branch '+name);
    return {first:()=>({json:rows[name]})};
  };
  const response={
    statusCode:200,
    body:{candidates:[{content:{parts:[{text:JSON.stringify({narrations:retry})}]}}]},
  };
  const out=new Function('$','$json',code('Validate Final Measured Word Count Retry'))($,response).json;
  assert.equal(out.narration_word_count,30);
  assert.equal(out.word_count_exact,false);
});

test('Build Final Measured Correction persists measured duration for directional validation',()=>{
  assert.match(
    code('Build Final Measured Correction'),
    /measured_duration_ms:\s*measuredMs/
  );
});

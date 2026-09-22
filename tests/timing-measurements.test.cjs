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
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      locale:'pl-PL',
      voice_name:'pl-PL-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
      ...ctx,
    },
    'Prepare Timing Probe':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>{
    if(!(name in refs)) throw new Error('unexpected node '+name);
    return {first:()=>({json:refs[name]})};
  };
  return new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:bMs}}
  ).json;
}

test('PL15 exact-audio handoff accepts one real in-window synthesis because that exact MP3 is reused in M6',()=>{
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
  assert.equal(out.stability_required_within_final,1);
  assert.equal(out.timing_stability_ok,true);
  assert.equal(out.accepted_voiceover_candidate.source,'origin');
  assert.equal(out.accepted_voiceover_candidate.duration_ms,15576);
  assert.equal(
    out.accepted_voiceover_candidate.usage_idempotency_key,
    'm5-origin'
  );
});

test('exact-audio handoff selects the closest in-window synthesis when more than one is valid',()=>{
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
  assert.equal(out.stability_within_final_count,2);
  assert.equal(out.stability_required_within_final,1);
  assert.equal(out.timing_stability_ok,true);
  assert.equal(out.accepted_voiceover_candidate.source,'origin');
  assert.equal(out.accepted_voiceover_candidate.duration_ms,15576);
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

function runLateTimingBuilderWithSkippedProbes(name) {
  const code=workflow.nodes.find(n=>n.name===name).parameters.jsCode;
  const originalScenes=[
    'Elektrownia wodna gromadzi wodę w zbiorniku za zaporą.',
    'Spadająca ciecz napędza wirnik turbiny wodnej.',
    'Obracająca się turbina napędza generator.',
    'Wytworzony prąd trafia do sieci.',
    'Energia zasila domy.',
  ];
  const original={
    storyboard:{
      narration:originalScenes.join(' '),
      scenes:originalScenes.map(narration=>({narration})),
    },
    measured_duration_ms:17928,
    narration_word_count:29,
    target_duration_ms:15000,
    tolerance_ms:750,
    usage:{},
  };
  const currentScenes=[
    'Zapora gromadzi wodę w zbiorniku.',
    'Spadająca ciecz napędza wirnik turbiny.',
    'Turbina napędza generator.',
    'Prąd trafia do sieci.',
    'Energia zasila domy.',
  ];
  const source={
    script_run_id:'run',
    model:'model',
    storyboard:{
      narration:currentScenes.join(' '),
      scenes:currentScenes.map(narration=>({narration})),
    },
    measured_duration_ms:13368,
    narration_word_count:20,
    target_duration_ms:15000,
    tolerance_ms:750,
    usage:{},
  };
  const buildCtx={
    language_code:'pl',
    target_duration_seconds:15,
    word_min:20,
    word_max:40,
  };
  const $=nodeName=>{
    if(nodeName==='Normalize Timing Stability B') {
      return {all:()=>{throw new Error('not executed')}};
    }
    if(nodeName==='Normalize Timing Probe') {
      return {first:()=>({json:original})};
    }
    if(nodeName==='Normalize Timing Probe 2' || nodeName==='Normalize Timing Probe 3') {
      return {first:()=>{throw new Error("Node '"+nodeName+"' hasn't been executed")}};
    }
    if(nodeName==='Build Script Prompt') {
      return {first:()=>({json:buildCtx})};
    }
    throw new Error('unexpected node '+nodeName);
  };
  return new Function('$','$json',code)($,source).json;
}

test('final duration builder tolerates skipped Probe 2 after semantic fallback',()=>{
  const out=runLateTimingBuilderWithSkippedProbes('Build Final Duration Repair');
  assert.equal(out.script_run_id,'run');
  assert.equal(out.target_duration_ms,15000);
  assert.ok(Number.isInteger(out.target_words));
  assert.equal(out.target_scene_word_counts.length,5);
  assert.match(out.user_message,/CURRENT MEASURED TTS: 13368 ms/);
});

test('final measured correction tolerates skipped Probe 2 and Probe 3',()=>{
  const out=runLateTimingBuilderWithSkippedProbes('Build Final Measured Correction');
  assert.equal(out.script_run_id,'run');
  assert.equal(out.target_duration_ms,15000);
  assert.ok(Number.isInteger(out.target_words));
  assert.equal(out.target_scene_word_counts.length,5);
  assert.match(out.user_message,/CURRENT MEASURED TTS: 13368 ms/);
});


test('v96 regression: final measured correction stays inside the window instead of aiming at center',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build Final Measured Correction').parameters.jsCode;
  const mk=(words,ms,label)=>({
    storyboard:{
      narration:Array(words).fill(label).join(' '),
      scenes:[6,5,5,4,4].map((n,i)=>({narration:Array(Math.max(2,Math.round(words*[6,5,5,4,4][i]/24))).fill(label).join(' ')})),
    },
    measured_duration_ms:ms,
    narration_word_count:words,
    target_duration_ms:15000,
    tolerance_ms:750,
    usage:{},
  });
  const p2=mk(20,13536,'short');
  const p3=mk(26,15624,'longer');
  const source=mk(24,16224,'current');
  const stableP3={...p3,stability_median_ms:16656};

  const originalScenes=[
    'Ogromny zbiornik wodny gromadzi zasoby na wysokości.',
    'Spadająca woda napędza turbinę.',
    'Turbina uruchamia generator, tworząc prąd.',
    'Transformator podnosi napięcie.',
    'Prąd trafia do sieci przesyłowej.',
  ];
  const $=name=>{
    if(name==='Normalize Timing Stability B') {
      return {all:(_branch,run)=>{
        if(run===0) return [{json:stableP3}];
        throw new Error('not executed');
      }};
    }
    if(name==='Normalize Timing Probe 2') return {first:()=>({json:p2})};
    if(name==='Normalize Timing Probe 3') return {first:()=>({json:p3})};
    if(name==='Normalize Timing Probe') return {first:()=>({json:{storyboard:{scenes:originalScenes.map(narration=>({narration}))}}})};
    if(name==='Build Script Prompt') return {first:()=>({json:{language_code:'pl',target_duration_seconds:15,target_scenes:5,target_shots:5,word_min:20,word_max:40}})};
    throw new Error('unexpected node '+name);
  };
  const out=new Function('$','$json',code)($,source).json;
  assert.equal(out.repair_target_duration_ms,15375);
  assert.equal(out.target_words,23);
  assert.equal(out.target_scene_word_counts.reduce((a,b)=>a+b,0),23);
  assert.match(out.user_message,/MEASURED CORRECTION AIM: 15375 ms/);
});


test('9287 regression: measured-short final correction cannot request fewer words or characters',()=>{
  const code=workflow.nodes.find(n=>n.name==='Build Final Measured Correction').parameters.jsCode;

  const originalScenes=[
    'Zapora gromadzi wodę w dużym zbiorniku.',
    'Spadająca woda porusza potężną turbinę.',
    'Obrotowy ruch napędza generator.',
    'Generator wytwarza prąd elektryczny.',
    'Transformator przesyła go do sieci.',
  ];
  const p2Scenes=[
    'Zapora gromadzi wodę.',
    'Spadająca woda porusza turbinę.',
    'Ruch napędza generator.',
    'Generator wytwarza prąd.',
    'Transformator przesyła go.',
  ];
  const sourceScenes=[
    'Zapora gromadzi wodę w zbiorniku.',
    'Spadająca woda porusza turbinę.',
    'Obrotowy ruch napędza generator.',
    'Generator wytwarza prąd elektryczny.',
    'Transformator przesyła go do sieci.',
  ];
  const mk=(scenes,ms)=>({
    storyboard:{
      narration:scenes.join(' '),
      scenes:scenes.map(narration=>({narration})),
    },
    measured_duration_ms:ms,
    narration_word_count:scenes.join(' ').split(/\s+/u).filter(Boolean).length,
    target_duration_ms:15000,
    tolerance_ms:750,
    usage:{},
  });
  const p2=mk(p2Scenes,13344);
  const p3=mk(originalScenes,16344);
  const source=mk(sourceScenes,14208);
  source.script_run_id='run';
  source.model='model';

  const $=name=>{
    if(name==='Normalize Timing Stability B') {
      return {all:()=>{throw new Error('not executed')}};
    }
    if(name==='Normalize Timing Probe 2') return {first:()=>({json:p2})};
    if(name==='Normalize Timing Probe 3') return {first:()=>({json:p3})};
    if(name==='Normalize Timing Probe') {
      return {first:()=>({json:{storyboard:{scenes:originalScenes.map(narration=>({narration}))}}})};
    }
    if(name==='Build Script Prompt') {
      return {first:()=>({json:{
        language_code:'pl',
        target_duration_seconds:15,
        target_scenes:5,
        target_shots:5,
        word_min:20,
        word_max:40,
      }})};
    }
    throw new Error('unexpected node '+name);
  };

  const out=new Function('$','$json',code)($,source).json;
  const currentWords=source.storyboard.narration.split(/\s+/u).filter(Boolean).length;
  const currentChars=Array.from(source.storyboard.narration).length;
  assert.equal(currentWords,22);
  assert.equal(currentChars,171);
  assert.equal(out.repair_target_duration_ms,14625);
  assert.ok(out.target_words>currentWords,JSON.stringify(out));
  assert.ok(out.target_chars>currentChars,JSON.stringify(out));
  assert.match(out.user_message,/DIRECTION: make the complete narration LONGER/);
});

test('late timing targets never contradict the requested direction',()=>{
  for(const name of ['Build Final Duration Repair','Build Final Measured Correction']){
    const code=workflow.nodes.find(n=>n.name===name).parameters.jsCode;
    assert.match(code,/predictedDirectionOk/);
    assert.match(code,/makeLonger \? predicted > current : predicted < current/);
    assert.match(code,/late timing target cannot move in required direction within hard bounds/);
  }
});

test('late timing builders use optional reads for branch-dependent probes',()=>{
  const durationCode=workflow.nodes.find(n=>n.name==='Build Final Duration Repair').parameters.jsCode;
  const measuredCode=workflow.nodes.find(n=>n.name==='Build Final Measured Correction').parameters.jsCode;
  assert.match(durationCode,/optionalNodeFirst\('Normalize Timing Probe 2'\)/);
  assert.doesNotMatch(durationCode,/\$\('Normalize Timing Probe 2'\)\.first\(\)/);
  assert.match(measuredCode,/optionalNodeFirst\('Normalize Timing Probe 2'\)/);
  assert.match(measuredCode,/optionalNodeFirst\('Normalize Timing Probe 3'\)/);
  assert.doesNotMatch(measuredCode,/\$\('Normalize Timing Probe [23]'\)\.first\(\)/);
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


test('M5 still observes the third real synthesis before selecting the persisted final candidate',()=>{
  const fastRoute=workflow.connections['Route Timing Stability PASS']?.main;
  assert.equal(fastRoute?.[0]?.[0]?.node,'Prepare Timing Stability Probe B');
  assert.equal(fastRoute?.[1]?.[0]?.node,'Prepare Timing Stability Probe B');

  const majorityRoute=workflow.connections['Route Timing Stability PASS B']?.main;
  assert.equal(majorityRoute?.[0]?.[0]?.node,'Canonicalize Final Storyboard');
  assert.equal(majorityRoute?.[1]?.[0]?.node,'Route Stability Origin 1');
});

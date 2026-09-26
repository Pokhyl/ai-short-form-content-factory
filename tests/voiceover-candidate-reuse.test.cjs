const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const m5=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const m6=JSON.parse(fs.readFileSync('workflows/VIDEO-M6-One-Final-Voiceover.json'));
const m5By=Object.fromEntries(m5.nodes.map(n=>[n.name,n]));
const m6By=Object.fromEntries(m6.nodes.map(n=>[n.name,n]));

test('M5 accepts and identifies the exact in-window synthesized MP3 instead of predicting a later synthesis',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-1',
      model:'gemini',
      storyboard:{narration:'sample'},
      narration_word_count:22,
      scene_count:5,
      shot_count:5,
      usage:{},
      target_duration_ms:15000,
      requested_tolerance_ms:750,
      stability_original_ms:14736,
      stability_a_measured_duration_ms:13368,
      origin_probe_attempt:5,
      locale:'pl-PL',
      voice_name:'pl-PL-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{
      probe_usage_key:'m5-origin',
    },
    'Normalize TTS Timing Probe 5':{
      audio_base64:audio('A'),
    },
    'Prepare Timing Stability Probe':{
      stability_usage_key:'m5-a',
    },
    'Normalize TTS Timing Stability':{
      audio_base64:audio('B'),
    },
    'Normalize TTS Timing Stability B':{
      audio_base64:audio('C'),
    },
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:16248}}
  ).json;

  assert.equal(out.stability_final_tolerance_ms,800);
  assert.equal(out.stability_within_final_count,1);
  assert.equal(out.stability_required_within_final,1);
  assert.equal(out.timing_stability_ok,true);
  assert.equal(out.accepted_voiceover_candidate.source,'origin');
  assert.equal(out.accepted_voiceover_candidate.duration_ms,14736);
  assert.equal(out.accepted_voiceover_candidate.usage_idempotency_key,'m5-origin');
  assert.equal(out.accepted_voiceover_candidate.audio_base64,audio('A'));
});

test('M5 still fails timing when none of the real synthesized files is in the final M6 window',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-2',
      model:'gemini',
      storyboard:{narration:'sample'},
      narration_word_count:22,
      scene_count:5,
      shot_count:5,
      usage:{},
      target_duration_ms:15000,
      requested_tolerance_ms:750,
      stability_original_ms:13200,
      stability_a_measured_duration_ms:16200,
      origin_probe_attempt:5,
      locale:'pl-PL',
      voice_name:'pl-PL-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe 5':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:16300}}
  ).json;

  assert.equal(out.stability_within_final_count,0);
  assert.equal(out.timing_stability_ok,false);
  assert.equal(out.accepted_voiceover_candidate,null);
});



test('10935 regression: 26.976s TTS is padding-eligible for a 30s product without rewriting narration',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-10935',
      model:'gemini',
      storyboard:{narration:'sample'},
      narration_word_count:52,
      scene_count:9,
      shot_count:9,
      usage:{},
      target_duration_ms:30000,
      requested_tolerance_ms:1550,
      stability_original_ms:26976,
      stability_a_measured_duration_ms:27048,
      origin_probe_attempt:5,
      locale:'uk-UA',
      voice_name:'uk-UA-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe 5':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:26700}}
  ).json;

  assert.equal(out.stability_final_tolerance_ms,1550);
  assert.equal(out.stability_minimum_duration_ms,28450);
  assert.equal(out.stability_max_padding_ms,1500);
  assert.equal(out.timing_stability_ok,true);
  assert.equal(out.accepted_voiceover_candidate.source,'stability_a');
  assert.equal(out.accepted_voiceover_candidate.duration_ms,27048);
  assert.equal(out.accepted_voiceover_candidate.minimum_duration_ms,28450);
  assert.equal(out.accepted_voiceover_candidate.padding_ms,1402);
});

test('M5 persists the accepted audio candidate before committing the storyboard',()=>{
  assert.equal(
    m5.connections['Canonicalize Final Storyboard'].main[0][0].node,
    'Build Narration Language Review Final'
  );
  assert.equal(m5.connections['Validate Narration Language Review Final'].main[0][0].node,'Store Accepted Voiceover Candidate');
  assert.equal(
    m5.connections['Store Accepted Voiceover Candidate'].main[0][0].node,
    'Normalize Accepted Voiceover Candidate'
  );
  assert.equal(
    m5.connections['Normalize Accepted Voiceover Candidate'].main[0][0].node,
    'Register Accepted Voiceover Candidate'
  );
  assert.equal(
    m5.connections['Register Accepted Voiceover Candidate'].main[0][0].node,
    'Commit Storyboard'
  );

  const store=m5By['Store Accepted Voiceover Candidate'];
  assert.match(store.parameters.url,/voiceover-candidates/);
  assert.match(store.parameters.jsonBody,/accepted_voiceover_candidate\.audio_base64/);

  const register=m5By['Register Accepted Voiceover Candidate'];
  assert.match(register.parameters.query,/register_voiceover_candidate/);

  const commit=m5By['Commit Storyboard'];
  assert.match(
    commit.parameters.options.queryReplacement,
    /Canonicalize Final Storyboard/
  );
});

test('M6 adopts a persisted M5 candidate and bypasses new Google synthesis',()=>{
  const begin=m6By['Begin Voiceover'];
  assert.match(begin.parameters.query,/begin_voiceover_v2/);
  assert.match(begin.parameters.query,/reuse_candidate/);
  assert.equal(
    m6.connections['Begin Voiceover'].main[0][0].node,
    'Route Reusable M5 Candidate'
  );

  const route=m6.connections['Route Reusable M5 Candidate'].main;
  assert.equal(route[0][0].node,'Promote M5 Voiceover Candidate');
  assert.equal(route[1][0].node,'Google Cloud TTS');

  const promote=m6By['Promote M5 Voiceover Candidate'];
  assert.match(promote.parameters.url,/voiceover-candidates/);
  assert.match(promote.parameters.url,/promote/);
  assert.match(promote.parameters.jsonBody,/candidate_audio_sha256/);
  assert.match(promote.parameters.jsonBody,/candidate_duration_ms/);

  assert.equal(
    m6.connections['Route Promoted M5 Candidate Success'].main[0][0].node,
    'Complete Voiceover'
  );
});

test('M6 promoted-candidate normalizer requires exact persisted metadata',()=>{
  const code=m6By['Normalize Promoted M5 Candidate'].parameters.jsCode;
  const job='11111111-1111-4111-8111-111111111111';
  const sha='a'.repeat(64);
  const refs={
    'Begin Voiceover':{
      voiceover_run_id:'22222222-2222-4222-8222-222222222222',
      target_duration_seconds:15,
      reuse_candidate:true,
      candidate_audio_sha256:sha,
      candidate_bytes:12345,
      candidate_duration_ms:15336,
      candidate_sample_rate:24000,
      candidate_channels:1,
      candidate_codec:'mp3',
    },
    'When Executed by Another Workflow':{job_id:job},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {
      statusCode:201,
      body:{
        status:'ready',
        job_id:job,
        storage_path:'/data/voiceovers/'+job+'/final.mp3',
        sha256:sha,
        bytes:12345,
        duration_ms:15336,
        sample_rate:24000,
        channels:1,
        codec:'mp3',
      },
    }
  ).json;

  assert.equal(out.store_success,true);
  assert.equal(out.reused_m5_candidate,true);
  assert.equal(out.tts_consumed,true);
});

test('DB migration binds candidate reuse to committed M5 usage and exact script narration',()=>{
  const sql=fs.readFileSync('db/11-voiceover-candidate-reuse.sql','utf8');
  assert.match(sql,/CREATE TABLE IF NOT EXISTS factory\.voiceover_candidates/);
  assert.match(sql,/factory\.register_voiceover_candidate/);
  assert.match(sql,/metadata->>'stage'.*M5_TIMING_PROBE/s);
  assert.match(sql,/v_usage\.state <> 'committed'/);
  assert.match(sql,/v_usage\.amount <> char_length\(p_narration\)/);
  assert.match(sql,/factory\.begin_voiceover_v2/);
  assert.match(sql,/v_candidate\.narration <> v_script\.narration/);
  assert.match(sql,/CASE WHEN v_reuse THEN now\(\) ELSE NULL END/);
});

test('media worker provides isolated candidate store, metadata and promote routes',()=>{
  const source=fs.readFileSync('services/media-worker/server.py','utf8');
  assert.match(source,/VOICEOVER_CANDIDATE_ROOT/);
  assert.match(source,/def _handle_voiceover_candidate_post/);
  assert.match(source,/def _handle_voiceover_candidate_promote_post/);
  assert.match(source,/voiceover_candidate SHA256 mismatch|voiceover candidate SHA256 mismatch/);
  assert.match(source,/os\.link\(candidate_path, final_path\)/);
  assert.match(source,/_voiceover_candidate_job_id\("\/promote"\)/);
});


test('9621 regression: every M5 timing probe canonicalizes visual-cut punctuation before TTS usage accounting',()=>{
  const source={
    script_run_id:'9279883f-70e2-4d8c-88d8-c40452eddb00',
    model:'gemini-3.5-flash-lite',
    storyboard:{
      narration:'Woda gromadzi się w wielkim zbiorniku za tamą. Następnie spada z dużej wysokości,. Poruszając turbinę wodną,. Która napędza generator,. Wytwarzając czystą i ekologiczną energię elektryczną.',
      scenes:[
        {scene_id:'S1',narration:'Woda gromadzi się w wielkim zbiorniku za tamą.',shots:[{shot_id:'S1-A'}]},
        {scene_id:'S2',narration:'Następnie spada z dużej wysokości,.',shots:[{shot_id:'S2-A'}]},
        {scene_id:'S3',narration:'Poruszając turbinę wodną,.',shots:[{shot_id:'S3-A'}]},
        {scene_id:'S4',narration:'Która napędza generator,.',shots:[{shot_id:'S4-A'}]},
        {scene_id:'S5',narration:'Wytwarzając czystą i ekologiczną energię elektryczną.',shots:[{shot_id:'S5-A'}]},
      ],
    },
    narration_word_count:25,
    scene_count:5,
    shot_count:5,
    usage:{},
  };
  const expected='Woda gromadzi się w wielkim zbiorniku za tamą. Następnie spada z dużej wysokości, Poruszając turbinę wodną, Która napędza generator, Wytwarzając czystą i ekologiczną energię elektryczną.';
  assert.equal(expected.length,186);

  const refs={
    'Build Script Prompt':{language_code:'pl',target_duration_seconds:15},
    'When Executed by Another Workflow':{job_id:'94f5e4ff-b6b3-4ebf-b161-98deb3c7bbe7'},
  };
  const $=name=>({first:()=>({json:refs[name]})});

  for(const name of [
    'Prepare Timing Probe',
    'Prepare Timing Probe 2',
    'Prepare Timing Probe 3',
    'Prepare Timing Probe 4',
    'Prepare Timing Probe 5',
  ]){
    const out=new Function(
      '$','$json',
      m5By[name].parameters.jsCode
    )($,structuredClone(source)).json;

    assert.equal(out.storyboard.narration,expected,name);
    assert.equal(out.character_count,186,name);
    assert.equal(out.character_count,Array.from(out.storyboard.narration).length,name);
    assert.equal(
      out.storyboard.narration,
      out.storyboard.scenes.map(scene=>scene.narration).join(' '),
      name
    );
    assert.doesNotMatch(out.storyboard.narration,/[,;:]\s*[.!?…]+/u,name);
  }
});


test('M5 can pad a slightly short real TTS file into the existing final timing window',()=>{
  const m5Code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  assert.match(m5Code,/const minimumAcceptedDurationMs = targetMs - finalToleranceMs/);
  assert.match(m5Code,/const maxPaddingMs = Math\.min\(finalToleranceMs, 1500\)/);
  assert.match(m5Code,/paddingRenderable/);
  assert.match(m5Code,/minimum_duration_ms/);
  assert.match(m5By['Store Accepted Voiceover Candidate'].parameters.jsonBody,/minimum_duration_ms/);

  const db=fs.readFileSync('db/11-voiceover-candidate-reuse.sql','utf8');
  assert.match(db,/abs\(p_duration_ms - v_target_ms\) > v_tolerance_ms/);
  assert.match(db,/abs\(v_candidate\.duration_ms - v_target_ms\) > v_tolerance_ms/);
  assert.doesNotMatch(m6By['Begin Voiceover'].parameters.query,/max_render_padding_ms/);
});

test('render contract keeps audio duration separate from exact target video duration',()=>{
  const sql=fs.readFileSync('db/10-render-qa.sql','utf8');
  const m9=JSON.parse(fs.readFileSync('workflows/VIDEO-M9-Render-Machine-QA.json','utf8'));
  const m9By=Object.fromEntries(m9.nodes.map(n=>[n.name,n]));
  const worker=fs.readFileSync('services/media-worker/server.py','utf8');

  assert.doesNotMatch(sql,/audio_duration_ms integer,\s*target_duration_ms integer,/s);
  assert.match(sql,/lead\(st\.start_ms\).*?v_target_duration_ms/s);
  assert.match(sql,/v_previous_end <> v_target_duration_ms/);

  assert.match(m9By['Begin Render'].parameters.query,/target_duration_seconds \* 1000 AS target_duration_ms/);
  assert.match(m9By['Begin Render'].parameters.query,/JOIN factory\.jobs/);
  assert.match(m9By['Run Deterministic Render'].parameters.jsonBody,/target_duration_ms/);
  assert.match(m9By['Validate Render Result'].parameters.jsCode,/expectedAudioDuration/);
  assert.match(m9By['Validate Render Result'].parameters.jsCode,/expectedVideoDuration/);

  assert.match(worker,/def render_final_video\([\s\S]*?target_duration_ms,/);
  assert.match(worker,/f"\{target_duration_ms \/ 1000\.0:\.3f\}"/);
  assert.match(worker,/segment_manifest\[-1\]\["end_ms"\] == target_duration_ms/);
  assert.match(worker,/"target_duration_ms": target_duration_ms/);
});


test('10935 regression: slightly short 30s TTS is padded only to the existing final window',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-10935',
      model:'gemini',
      storyboard:{narration:'sample'},
      narration_word_count:52,
      scene_count:9,
      shot_count:9,
      usage:{},
      target_duration_ms:30000,
      requested_tolerance_ms:1550,
      stability_original_ms:26976,
      stability_a_measured_duration_ms:27048,
      origin_probe_attempt:5,
      locale:'uk-UA',
      voice_name:'uk-UA-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe 5':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:26700}}
  ).json;

  assert.equal(out.stability_final_tolerance_ms,1550);
  assert.equal(out.stability_minimum_duration_ms,28450);
  assert.equal(out.stability_max_padding_ms,1500);
  assert.equal(out.timing_stability_ok,true);
  assert.equal(out.accepted_voiceover_candidate.source,'stability_a');
  assert.equal(out.accepted_voiceover_candidate.duration_ms,27048);
  assert.equal(out.accepted_voiceover_candidate.minimum_duration_ms,28450);
  assert.equal(out.accepted_voiceover_candidate.padding_ms,1402);
  assert.equal(out.accepted_voiceover_candidate.audio_base64,audio('B'));

  const store=m5By['Store Accepted Voiceover Candidate'];
  assert.match(store.parameters.jsonBody,/minimum_duration_ms/);
});

test('M5 refuses padding that would exceed the bounded 1500ms repair cap',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=(ch)=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-too-short',
      model:'gemini',
      storyboard:{narration:'sample'},
      narration_word_count:45,
      scene_count:9,
      shot_count:9,
      usage:{},
      target_duration_ms:30000,
      requested_tolerance_ms:1550,
      stability_original_ms:26000,
      stability_a_measured_duration_ms:26500,
      origin_probe_attempt:5,
      locale:'uk-UA',
      voice_name:'uk-UA-Chirp3-HD-Enceladus',
      sku_family:'chirp3_hd',
      stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe 5':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)(
    $,
    {statusCode:200,body:{status:'ready',duration_ms:26400}}
  ).json;

  assert.equal(out.timing_stability_ok,false);
  assert.equal(out.accepted_voiceover_candidate,null);
});

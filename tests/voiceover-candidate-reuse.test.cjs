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



test('10935 regression: 26.976s cannot be silently padded into a 30s product',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run-10935',model:'gemini',storyboard:{narration:'sample'},
      narration_word_count:52,scene_count:9,shot_count:9,usage:{},
      target_duration_ms:30000,requested_tolerance_ms:1550,
      stability_original_ms:26976,stability_a_measured_duration_ms:27048,
      origin_probe_attempt:5,stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe 5':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe 5':{audio_base64:'A'.repeat(256)},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:'B'.repeat(256)},
    'Normalize TTS Timing Stability B':{audio_base64:'C'.repeat(256)},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const out=new Function('$','$json',code)($,
    {statusCode:200,body:{status:'ready',duration_ms:26700}}).json;
  assert.equal(out.stability_minimum_duration_ms,28464);
  assert.equal(out.timing_stability_ok,false);
  assert.equal(out.accepted_voiceover_candidate,null);
  assert.equal(
    m5.connections['Route Timing Within Target'].main[1][0].node,
    'Build Timing Repair'
  );
  assert.equal(
    m5.connections['Route Timing Within Target 2'].main[1][0].node,
    'Prepare Final Timing Failure'
  );
  assert.equal(
    m5.connections['Route Stability Origin 2'].main[0][0].node,
    'Prepare Final Timing Failure'
  );
  assert.equal(
    m5.connections['Validate Timing Repair'].main[1][0].node,
    'Prepare Script Failure'
  );
  const repair=m5By['Build Timing Repair'].parameters.jsCode;
  assert.match(repair,/desiredDurationMs/);
  assert.match(repair,/one semantic-safe rewrite/);
  assert.match(repair,/never add unsupported facts, generic praise, filler/);
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
      candidate_duration_ms:14736,
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
        duration_ms:14736,
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


test('M5/M6 use the same observed bounded audio window without padding',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  assert.match(code,/15000: 14208, 30000: 28464, 45000: 42864, 60000: 58176/);
  assert.doesNotMatch(code,/paddingRenderable|padding_ms|acceptedCandidate\\.minimum_duration_ms/);
  assert.doesNotMatch(
    m5By['Store Accepted Voiceover Candidate'].parameters.jsonBody,
    /minimum_duration_ms/
  );
  const worker=fs.readFileSync('services/media-worker/server.py','utf8');
  assert.doesNotMatch(worker,/def pad_mp3_to_minimum_duration/);
  assert.match(worker,/audio padding is not part of the candidate contract/);
  const candidateSql=fs.readFileSync('db/11-voiceover-candidate-reuse.sql','utf8');
  const finalSql=fs.readFileSync('db/07-voiceover.sql','utf8');
  for(const source of [candidateSql,finalSql,worker]) {
    assert.match(source,/28464/);
    assert.match(source,/58176/);
  }
  assert.match(
    m6By['Normalize Promoted M5 Candidate'].parameters.jsCode,
    /durationMs >= minimumDurationMs && durationMs <= maximumDurationMs/
  );
});

test('factory.begin_render returns both durations and extends only the visual coverage',()=>{
  const sql=fs.readFileSync('db/10-render-qa.sql','utf8');
  const m9=JSON.parse(fs.readFileSync('workflows/VIDEO-M9-Render-Machine-QA.json','utf8'));
  const by=Object.fromEntries(m9.nodes.map(n=>[n.name,n]));
  assert.match(sql,/audio_duration_ms integer,\s*target_duration_ms integer,/s);
  assert.match(sql,/lead\(st\.start_ms\).*?v_render_duration_ms/s);
  assert.match(sql,/end_ms > v_voice\.duration_ms/);
  assert.match(sql,/v_previous_end <> v_render_duration_ms/);
  assert.match(by['Begin Render'].parameters.query,/audio_duration_ms, target_duration_ms/);
  assert.match(by['Run Deterministic Render'].parameters.jsonBody,
    /target_duration_ms: target, requested_duration_ms:/);
  assert.match(by['Validate Render Result'].parameters.jsCode,
    /expectedAudioDuration/);
  assert.match(by['Validate Render Result'].parameters.jsCode,
    /expectedVideoDuration/);
  assert.match(by['Validate Render Result'].parameters.jsCode,
    /muxed_audio_duration_ms/);
  assert.match(sql,/muxed_audio_duration_ms/);
  assert.match(sql,/audio_duration_match/);
});

test('M9 machine QA compares the video to target and the audio stream to actual audio',()=>{
  const w=JSON.parse(fs.readFileSync('workflows/VIDEO-M9-Render-Machine-QA.json','utf8'));
  const code=w.nodes.find(n=>n.name==='Validate Render Result').parameters.jsCode;
  const job='11111111-1111-4111-8111-111111111111';
  const scene='22222222-2222-4222-8222-222222222222';
  const shot='33333333-3333-4333-8333-333333333333';
  const asset='44444444-4444-4444-8444-444444444444';
  const sha='a'.repeat(64);
  const segment={
    scene_uuid:scene,shot_uuid:shot,visual_asset_id:asset,asset_sha256:sha,
    segment_order:1,start_ms:0,end_ms:30000,duration_ms:30000,
  };
  const ctx={
    render_run_id:'55555555-5555-4555-8555-555555555555',
    audio_sha256:sha,audio_duration_ms:28800,target_duration_ms:30000,requested_duration_ms:30000,
    expected_scene_count:1,
    scenes_json:[{...segment,segment_start_ms:0,segment_end_ms:30000}],
  };
  const $=name=>({first:()=>({json:
    name==='Begin Render'?ctx:{job_id:job}})});
  const base={
    status:'ready',job_id:job,sha256:sha,bytes:1000,width:1080,height:1920,
    storage_path:'/data/renders/'+job+'/final.mp4',
    manifest_path:'/data/renders/'+job+'/manifest.json',
    video_codec:'h264',audio_codec:'aac',pix_fmt:'yuv420p',
    fps_num:30,fps_den:1,video_stream_count:1,audio_stream_count:1,
    audio_duration_ms:28800,muxed_audio_duration_ms:28822,
    target_duration_ms:30000,requested_duration_ms:30000,duration_ms:30000,duration_delta_ms:0,
    input_audio_sha256:sha,segments:[segment],qa_passed:true,
    qa_gates:{
      video_dimensions:true,video_codec:true,audio_codec:true,
      stream_counts:true,duration_match:true,audio_duration_match:true,
      scene_coverage:true,asset_hashes:true,source_audio_excluded:true,
    },
  };
  const run=body=>new Function('$','$json',code)($,
    {statusCode:201,body}).json.render_success;
  assert.equal(run(base),true);
  assert.equal(run({...base,duration_ms:28800,duration_delta_ms:1200}),false);
  assert.equal(run({...base,muxed_audio_duration_ms:27000}),false);
  assert.equal(run({...base,segments:[{...segment,end_ms:28800}]}),false);
  const longMs=30864;
  const longCtx={
    ...ctx, audio_duration_ms:longMs,target_duration_ms:longMs,
    scenes_json:[{...segment,segment_start_ms:0,segment_end_ms:longMs}],
  };
  const $long=name=>({first:()=>({json:
    name==='Begin Render'?longCtx:{job_id:job}})});
  const longSegment={...segment,end_ms:longMs,duration_ms:longMs};
  const longBody={
    ...base,audio_duration_ms:longMs,muxed_audio_duration_ms:longMs+22,
    target_duration_ms:longMs,duration_ms:longMs,duration_delta_ms:0,
    segments:[longSegment],
  };
  const runLong=body=>new Function('$','$json',code)($long,
    {statusCode:201,body}).json.render_success;
  assert.equal(runLong(longBody),true);
  assert.equal(runLong({...longBody,duration_ms:30000,duration_delta_ms:864}),false);
  assert.equal(runLong({...longBody,muxed_audio_duration_ms:30000}),false);
  assert.equal(runLong({...longBody,requested_duration_ms:32000}),false);

});

test('30s candidate inside production range is reused byte-for-byte with no narration rewrite',()=>{
  const code=m5By['Normalize Timing Stability B'].parameters.jsCode;
  const audio=ch=>ch.repeat(256);
  const refs={
    'Prepare Timing Stability Probe B':{
      script_run_id:'run',model:'gemini',
      storyboard:{narration:'Natural script stays unchanged'},
      narration_word_count:5,scene_count:1,shot_count:1,usage:{},
      target_duration_ms:30000,requested_tolerance_ms:1550,
      stability_original_ms:28584,stability_a_measured_duration_ms:28800,
      origin_probe_attempt:1,stability_b_usage_key:'m5-b',
    },
    'Prepare Timing Probe':{probe_usage_key:'m5-origin'},
    'Normalize TTS Timing Probe':{audio_base64:audio('A')},
    'Prepare Timing Stability Probe':{stability_usage_key:'m5-a'},
    'Normalize TTS Timing Stability':{audio_base64:audio('B')},
    'Normalize TTS Timing Stability B':{audio_base64:audio('C')},
  };
  const $=name=>({first:()=>({json:refs[name]})});
  const result=new Function('$','$json',code)($,
    {statusCode:200,body:{status:'ready',duration_ms:29000}}).json;
  assert.equal(result.timing_stability_ok,true);
  assert.equal(result.accepted_voiceover_candidate.source,'stability_b');
  assert.equal(result.accepted_voiceover_candidate.duration_ms,29000);
  assert.equal(result.accepted_voiceover_candidate.audio_base64,audio('C'));
  assert.equal(result.storyboard.narration,'Natural script stays unchanged');
});

test('M5 accepts a natural 30.864s voice and rejects beyond the 32s ceiling',()=>{
  const code=m5By['Normalize Timing Probe'].parameters.jsCode;
  const ctx={
    script_run_id:'run',model:'model',storyboard:{narration:'spoken'},
    narration_word_count:1,scene_count:1,shot_count:1,usage:{},
    target_duration_ms:30000,tolerance_ms:2000,probe_attempt:1,
  };
  const $=()=>({first:()=>({json:ctx})});
  const run=ms=>new Function('$','$json',code)($,
    {statusCode:200,body:{status:'ready',duration_ms:ms}}).json.timing_ok;
  assert.equal(run(29000),true);
  assert.equal(run(27000),false);
  assert.equal(run(30864),true);
  assert.equal(run(32001),false);
});

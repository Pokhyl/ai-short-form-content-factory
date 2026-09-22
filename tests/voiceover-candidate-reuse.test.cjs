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
      stability_original_ms:15336,
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
  assert.equal(out.accepted_voiceover_candidate.duration_ms,15336);
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
      stability_original_ms:13800,
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

test('M5 persists the accepted audio candidate before committing the storyboard',()=>{
  assert.equal(
    m5.connections['Canonicalize Final Storyboard'].main[0][0].node,
    'Store Accepted Voiceover Candidate'
  );
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

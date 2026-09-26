const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const m8 = JSON.parse(fs.readFileSync(path.join(root, 'workflows', 'VIDEO-M8-Multi-Source-Visuals.json'), 'utf8'));
const m5 = JSON.parse(fs.readFileSync(path.join(root, 'workflows', 'VIDEO-M5-Script-Storyboard.json'), 'utf8'));

function node(wf, name) {
  const found = wf.nodes.find((item) => item.name === name);
  assert.ok(found, 'missing node: ' + name);
  return found;
}

function runCode(nodeName, { json = {}, refs = {}, inputItems = [] } = {}) {
  const code = node(m8, nodeName).parameters.jsCode;
  const dollar = (name) => {
    if (!(name in refs)) throw new Error('missing ref: ' + name);
    return refs[name];
  };
  const input = {
    first: () => inputItems[0],
    all: () => inputItems,
  };
  return new Function('$json', '$', '$input', code)(json, dollar, input);
}

test('metadata mode bypasses Gemini and preserves deterministic select_visuals path', () => {
  const route = m8.connections['Route Visual Validation Mode'];
  assert.equal(route.main[0][0].node, 'Get Gemini Candidate Sets');
  assert.equal(route.main[1][0].node, 'Select Visuals');
  assert.match(node(m8, 'Select Visuals').parameters.query, /factory\.select_visuals\(\$1::uuid,55\)/);
});

test('M8 reads persisted mode from the job after selection claim', () => {
  const load = node(m8, 'Load Visual Validation Mode');
  assert.match(load.parameters.query, /visual_validation_mode/);
  assert.match(load.parameters.query, /factory\.jobs/);
  assert.equal(m8.connections['Route Selection Claim'].main[0][0].node, 'Load Visual Validation Mode');
});

test('Gemini candidate planner is capped at three candidates per shot', () => {
  const get = node(m8, 'Get Gemini Candidate Sets');
  assert.match(get.parameters.query, /get_gemini_visual_candidate_sets\(\$1::uuid,55,3\)/);
  const sql = fs.readFileSync(path.join(root, 'db', '09-visuals.sql'), 'utf8');
  assert.match(sql, /p_limit_per_shot < 1 OR p_limit_per_shot > 3/);
  assert.match(sql, /candidate_index <= p_limit_per_shot/);
});


test('Gemini candidate planner diversifies providers before taking second choices', () => {
  const sql = fs.readFileSync(path.join(root, 'db', '09-visuals.sql'), 'utf8');
  const fn = sql.match(/CREATE OR REPLACE FUNCTION factory\.get_gemini_visual_candidate_sets[\s\S]*?CREATE OR REPLACE FUNCTION factory\.commit_gemini_visual_selections/)?.[0] || '';
  assert.match(fn, /PARTITION BY provider/);
  assert.match(fn, /provider_candidate_rank,/);
  assert.match(fn, /candidate_index <= p_limit_per_shot/);
});

test('one Gemini request evaluates all candidate images for a scene at low media resolution', () => {
  const ctx = {
    visual_run_id: 'run',
    shot_uuid: 'shot',
    shot_key: 'S1-A',
    scene_order: 1,
    shot_order: 1,
    visual_intent: 'A concrete dam holding a large reservoir',
    must_show: ['concrete dam', 'water reservoir'],
    must_not_show: ['dry riverbed'],
    candidates: [
      { candidate_index: 1, candidate_id: 'c1', provider: 'pexels', provider_asset_id: 'a1' },
      { candidate_index: 2, candidate_id: 'c2', provider: 'wikimedia', provider_asset_id: 'a2' },
    ],
  };
  const result = runCode('Build Gemini Vision Request', {
    json: {
      statusCode: 200,
      body: {
        status: 'ready',
        previews: [
          { candidate_index: 1, provider_asset_id: 'a1', mime_type: 'image/jpeg', data_base64: 'YQ==', sha256: '1'.repeat(64), bytes: 1 },
          { candidate_index: 2, provider_asset_id: 'a2', mime_type: 'image/png', data_base64: 'Yg==', sha256: '2'.repeat(64), bytes: 1 },
        ],
      },
    },
    refs: {
      'Expand Gemini Candidate Sets': { item: { json: ctx } },
    },
  });

  const parts = result.json.gemini_body.contents[0].parts;
  const images = parts.filter((part) => part.inlineData);
  assert.equal(images.length, 2);
  assert.deepEqual(images.map((part) => part.mediaResolution.level), [
    'MEDIA_RESOLUTION_LOW',
    'MEDIA_RESOLUTION_LOW',
  ]);
  assert.equal(result.json.candidates.length, 2);
  const schema = result.json.gemini_body.generationConfig.responseJsonSchema;
  assert.equal(schema.type, 'object');
  assert.deepEqual(schema.required, ['evaluations']);
  assert.equal(schema.properties.evaluations.type, 'array');
  assert.deepEqual(schema.properties.evaluations.items.required, [
    'candidate_index',
    'must_show_checks',
    'must_not_show_clear',
    'intent_match',
    'match_score',
    'reason',
  ]);
  assert.equal(schema.properties.evaluations.items.additionalProperties, false);
  assert.equal(schema.additionalProperties, false);
});

test('Gemini parser recomputes pass fail-closed with a 70 score floor', () => {
  const ctx = {
    must_show:['required subject'],
    visual_run_id: 'run',
    shot_uuid: 'shot',
    shot_key: 'S1-A',
    scene_order: 1,
    shot_order: 1,
    candidates: [
      { candidate_index: 1, candidate_id: 'c1' },
      { candidate_index: 2, candidate_id: 'c2' },
    ],
    preview_fingerprints: [],
  };
  const payload = {
    evaluations: [
      { candidate_index: 1, must_show_checks:[{concept_index:1,visible:true,evidence:'Required subject visible.'}], must_not_show_clear: true, intent_match: true, match_score: 85, reason: 'Required subject is clearly visible.' },
      { candidate_index: 2, must_show_checks:[{concept_index:1,visible:true,evidence:'Subject visible but distant.'}], must_not_show_clear: true, intent_match: true, match_score: 60, reason: 'Subject is too weak and distant.' },
    ],
  };
  const result = runCode('Parse Gemini Vision Result', {
    json: {
      statusCode: 200,
      body: {
        candidates: [{ content: { parts: [{ text: JSON.stringify(payload) }] } }],
        usageMetadata: { promptTokenCount: 123 },
      },
    },
    refs: {
      'Build Gemini Vision Request': { item: { json: ctx } },
    },
  });
  assert.equal(result.json.evaluations[0].vision_pass, true);
  assert.equal(result.json.evaluations[1].vision_pass, false);
  assert.equal(result.json.model, 'gemini-3.5-flash-lite');
});

test('Gemini parser rejects malformed model JSON instead of guessing', () => {
  const ctx = {
    visual_run_id: 'run',
    shot_uuid: 'shot',
    shot_key: 'S1-A',
    scene_order: 1,
    shot_order: 1,
    candidates: [{ candidate_index: 1, candidate_id: 'c1' }],
    preview_fingerprints: [],
  };
  assert.throws(() => runCode('Parse Gemini Vision Result', {
    json: {
      statusCode: 200,
      body: { candidates: [{ content: { parts: [{ text: 'not-json' }] } }] },
    },
    refs: {
      'Build Gemini Vision Request': { item: { json: ctx } },
    },
  }), /malformed JSON/);
});

test('collector avoids reusing one provider asset across two scenes', () => {
  const rows = [
    {
      json: {
        shot_uuid: '11111111-1111-4111-8111-111111111111',
        shot_key: 'S1-A',
        scene_order: 1,
        shot_order: 1,
        model: 'gemini-3.5-flash-lite',
        candidates: [
          { candidate_index: 1, candidate_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', provider: 'wikimedia', provider_asset_id: 'same' },
          { candidate_index: 2, candidate_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', provider: 'pexels', provider_asset_id: 'alt1' },
        ],
        preview_fingerprints: [],
        evaluations: [
          { candidate_index: 1, vision_pass: true, match_score: 95, must_show_visible: true, must_not_show_clear: true, intent_match: true, reason: 'best' },
          { candidate_index: 2, vision_pass: true, match_score: 80, must_show_visible: true, must_not_show_clear: true, intent_match: true, reason: 'alt' },
        ],
      },
    },
    {
      json: {
        shot_uuid: '22222222-2222-4222-8222-222222222222',
        shot_key: 'S2-A',
        scene_order: 2,
        shot_order: 1,
        model: 'gemini-3.5-flash-lite',
        candidates: [
          { candidate_index: 1, candidate_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc', provider: 'wikimedia', provider_asset_id: 'same' },
          { candidate_index: 2, candidate_id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd', provider: 'pixabay', provider_asset_id: 'alt2' },
        ],
        preview_fingerprints: [],
        evaluations: [
          { candidate_index: 1, vision_pass: true, match_score: 99, must_show_visible: true, must_not_show_clear: true, intent_match: true, reason: 'duplicate' },
          { candidate_index: 2, vision_pass: true, match_score: 85, must_show_visible: true, must_not_show_clear: true, intent_match: true, reason: 'unique alt' },
        ],
      },
    },
  ];
  const result = runCode('Collect Gemini Selections', {
    inputItems: rows,
    refs: {
      'Begin Visuals': { first: () => ({ json: { shot_count: 2, visual_run_id: '99999999-9999-4999-8999-999999999999' } }) },
    },
  });
  assert.equal(result[0].json.selections.length, 2);
  assert.equal(result[0].json.selections[0].candidate_id, 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
  assert.equal(result[0].json.selections[1].candidate_id, 'dddddddd-dddd-4ddd-8ddd-dddddddddddd');
});


test('collector reserves a shared sole candidate for the shot that has no alternative', () => {
  const rows = [
    {
      json: {
        shot_uuid: '11111111-1111-4111-8111-111111111111',
        shot_key: 'S1-A', scene_order: 1, shot_order: 1, model: 'gemini-3.5-flash-lite',
        candidates: [
          {candidate_index:1,candidate_id:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',provider:'pexels',provider_asset_id:'shared'},
          {candidate_index:2,candidate_id:'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',provider:'pixabay',provider_asset_id:'alternative'},
        ],
        preview_fingerprints: [],
        evaluations: [
          {candidate_index:1,vision_pass:true,match_score:100,must_show_visible:true,must_not_show_clear:true,intent_match:true,reason:'best shared'},
          {candidate_index:2,vision_pass:true,match_score:90,must_show_visible:true,must_not_show_clear:true,intent_match:true,reason:'usable alternative'},
        ],
      },
    },
    {
      json: {
        shot_uuid: '22222222-2222-4222-8222-222222222222',
        shot_key: 'S2-A', scene_order: 2, shot_order: 1, model: 'gemini-3.5-flash-lite',
        candidates: [
          {candidate_index:1,candidate_id:'cccccccc-cccc-4ccc-8ccc-cccccccccccc',provider:'pexels',provider_asset_id:'shared'},
        ],
        preview_fingerprints: [],
        evaluations: [
          {candidate_index:1,vision_pass:true,match_score:100,must_show_visible:true,must_not_show_clear:true,intent_match:true,reason:'only valid asset'},
        ],
      },
    },
  ];
  const result=runCode('Collect Gemini Selections',{
    inputItems:rows,
    refs:{'Begin Visuals':{first:()=>({json:{shot_count:2,visual_run_id:'99999999-9999-4999-8999-999999999999'}})}},
  });
  assert.equal(result[0].json.selections[0].candidate_id,'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb');
  assert.equal(result[0].json.selections[1].candidate_id,'cccccccc-cccc-4ccc-8ccc-cccccccccccc');
});

test('collector fails when a scene has no Gemini-approved candidate', () => {
  const rows = [{
    json: {
      shot_uuid: '11111111-1111-4111-8111-111111111111',
      shot_key: 'S1-A',
      scene_order: 1,
      shot_order: 1,
      model: 'gemini-3.5-flash-lite',
      candidates: [{ candidate_index: 1, candidate_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', provider: 'pexels', provider_asset_id: 'a1' }],
      preview_fingerprints: [],
      evaluations: [{ candidate_index: 1, vision_pass: false, match_score: 40, must_show_visible: false, must_not_show_clear: true, intent_match: false, reason: 'wrong object' }],
    },
  }];
  assert.throws(() => runCode('Collect Gemini Selections', {
    inputItems: rows,
    refs: {
      'Begin Visuals': { first: () => ({ json: { shot_count: 1, visual_run_id: '99999999-9999-4999-8999-999999999999' } }) },
    },
  }), /no Gemini-approved unique visual candidate/);
});

test('M8 Gemini Vision reuses the existing Gemini credential', () => {
  const m8Credential = node(m8, 'Gemini Validate Visuals').credentials.googlePalmApi;
  const m5Credential = node(m5, 'Generate Storyboard').credentials.googlePalmApi;
  assert.deepEqual(m8Credential, m5Credential);
});

test('media worker preview endpoint is bounded and image-only', () => {
  const source = fs.readFileSync(path.join(root, 'services', 'media-worker', 'server.py'), 'utf8');
  assert.match(source, /MAX_VISION_PREVIEW_BYTES = 3 \* 1024 \* 1024/);
  assert.match(source, /MAX_VISION_PREVIEW_TOTAL_BYTES = 8 \* 1024 \* 1024/);
  assert.match(source, /if not isinstance\(candidates, list\) or not 1 <= len\(candidates\) <= 3/);
  assert.match(source, /if self\.path == "\/visual-previews"/);
  assert.match(source, /VISION_PREVIEW_MIME_TYPES = \{'image\/jpeg', 'image\/png', 'image\/webp'\}/);
});

test('DB persists Gemini validation evidence on final visual selection', () => {
  const sql = fs.readFileSync(path.join(root, 'db', '09-visuals.sql'), 'utf8');
  assert.match(sql, /validation_mode text NOT NULL DEFAULT 'metadata'/);
  assert.match(sql, /validation_evidence jsonb NOT NULL DEFAULT '\{\}'::jsonb/);
  assert.match(sql, /factory\.commit_gemini_visual_selections/);
  assert.match(sql, /COALESCE\(\(v_evidence->>'vision_pass'\)::boolean,false\) <> true/);
  assert.match(sql, /'gemini',\s*v_evidence/s);
});


test('Gemini-only candidate review can rescue metadata semantic false negatives but stays fail-closed for hard rejects', () => {
  const sql = fs.readFileSync(path.join(root, 'db', '09-visuals.sql'), 'utf8');
  assert.match(sql, /factory\.gemini_visual_review_bucket/);
  assert.match(sql, /missing_primary_subject_anchor:%/);
  assert.match(sql, /insufficient_must_show_concept_coverage/);
  assert.match(sql, /missing_storyboard_domain_context:%/);
  assert.match(sql, /RETURN 99;/);
  assert.match(
    sql,
    /factory\.gemini_visual_review_bucket\(vc\.rejected,vc\.rejection_reason\) < 99/
  );
  assert.match(
    sql,
    /factory\.gemini_visual_review_bucket\(rejected,rejection_reason\) < 99/
  );
  assert.match(sql, /review_bucket,\s*query_bucket,\s*media_bucket/s);
  assert.doesNotMatch(
    sql.match(/CREATE OR REPLACE FUNCTION factory\.get_gemini_visual_candidate_sets[\s\S]*?CREATE OR REPLACE FUNCTION factory\.commit_gemini_visual_selections/)?.[0] || '',
    /AND vc\.rejected=false/
  );
  assert.match(
    node(m8, 'Select Visuals').parameters.query,
    /factory\.select_visuals\(\$1::uuid,55\)/
  );
});

test('Gemini selection evidence records when Vision rescued a metadata-rejected candidate', () => {
  const rows = [{
    json: {
      shot_uuid: '11111111-1111-4111-8111-111111111111',
      shot_key: 'S1-A',
      scene_order: 1,
      shot_order: 1,
      model: 'gemini-3.5-flash-lite',
      candidates: [{
        candidate_index: 1,
        candidate_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        provider: 'pexels',
        provider_asset_id: 'a1',
        metadata_rejected: true,
        metadata_rejection_reason: 'missing_primary_subject_anchor:lamp fixture; insufficient_must_show_concept_coverage',
        review_bucket: 1,
      }],
      preview_fingerprints: [{ candidate_index: 1, sha256: 'a'.repeat(64) }],
      evaluations: [{
        candidate_index: 1,
        vision_pass: true,
        match_score: 88,
        must_show_visible: true,
        must_not_show_clear: true,
        intent_match: true,
        reason: 'The required subject is visibly present.',
      }],
    },
  }];

  const result = runCode('Collect Gemini Selections', {
    inputItems: rows,
    refs: {
      'Begin Visuals': {
        first: () => ({
          json: {
            shot_count: 1,
            visual_run_id: '99999999-9999-4999-8999-999999999999',
          },
        }),
      },
    },
  });

  const evidence = result[0].json.selections[0].validation_evidence;
  assert.equal(evidence.metadata_rejected, true);
  assert.equal(evidence.review_bucket, 1);
  assert.match(evidence.metadata_rejection_reason, /missing_primary_subject_anchor/);
});


test('partial preview fetch keeps usable candidates and renumbers them for Gemini', () => {
  const ctx = {
    visual_run_id: 'run',
    shot_uuid: 'shot',
    shot_key: 'S2-A',
    scene_order: 2,
    shot_order: 1,
    visual_intent: 'Lighthouse lamp in lantern room',
    must_show: ['lamp fixture'],
    must_not_show: ['flame'],
    candidates: [
      { candidate_index: 1, candidate_id: 'c1', provider: 'wikimedia', provider_asset_id: 'w1' },
      { candidate_index: 2, candidate_id: 'c2', provider: 'pexels', provider_asset_id: 'p2' },
      { candidate_index: 3, candidate_id: 'c3', provider: 'pexels', provider_asset_id: 'p3' },
    ],
  };
  const result = runCode('Build Gemini Vision Request', {
    json: {
      statusCode: 200,
      body: {
        status: 'ready',
        requested_count: 3,
        preview_count: 2,
        failure_count: 1,
        failures: [{ candidate_index: 1, provider: 'wikimedia', provider_asset_id: 'w1', error: 'HTTP Error 429' }],
        previews: [
          { candidate_index: 2, provider_asset_id: 'p2', mime_type: 'image/jpeg', data_base64: 'YQ==', sha256: '1'.repeat(64), bytes: 1 },
          { candidate_index: 3, provider_asset_id: 'p3', mime_type: 'image/webp', data_base64: 'Yg==', sha256: '2'.repeat(64), bytes: 1 },
        ],
      },
    },
    refs: {
      'Expand Gemini Candidate Sets': { item: { json: ctx } },
    },
  });
  assert.deepEqual(result.json.candidates.map((c) => c.candidate_index), [1, 2]);
  assert.deepEqual(result.json.candidates.map((c) => c.candidate_id), ['c2', 'c3']);
  assert.equal(result.json.preview_failures.length, 1);
  assert.equal(result.json.gemini_body.contents[0].parts.filter((part) => part.inlineData).length, 2);
});

test('media worker keeps per-candidate preview failures but fails when every preview fails', () => {
  const source = fs.readFileSync(path.join(root, 'services', 'media-worker', 'server.py'), 'utf8');
  assert.match(source, /failures = \[\]/);
  assert.match(source, /failures\.append\(/);
  assert.match(source, /if not previews:/);
  assert.match(source, /raise ValueError\("no visual previews could be fetched"\)/);
  assert.match(source, /"failure_count": len\(failures\)/);
});

test('9932 provider retries run for one scene and only completed scenes reach collection', () => {
  const loop=node(m8,'Loop Gemini Scene Validation');
  assert.equal(loop.type,'n8n-nodes-base.splitInBatches');
  assert.equal(loop.typeVersion,3);
  assert.equal(loop.parameters.batchSize,1);
  assert.deepEqual(loop.parameters.options,{}); // no reset / unbounded retry loop
  assert.equal(m8.connections['Build Gemini Vision Request'].main[0][0].node,loop.name);
  assert.equal(m8.connections[loop.name].main[1][0].node,'Gemini Validate Visuals');
  assert.equal(m8.connections['Parse Gemini Vision Result'].main[0][0].node,loop.name);
  assert.equal(m8.connections[loop.name].main[0][0].node,'Collect Gemini Selections');
  assert.equal(m8.connections['Parse Gemini Vision Result'].main[1][0].node,'Prepare Visual Failure');
  const request=node(m8,'Gemini Validate Visuals');
  assert.equal(request.retryOnFail,true);
  assert.equal(request.maxTries,5);
  assert.equal(request.waitBetweenTries,5000); // installed engine maximum
  assert.equal(request.parameters.options.response.response.neverError,false);
});

test('9932 exhausted provider failures remain errors rather than semantic rejections', () => {
  const errors=[
    {statusCode:503,body:{error:{message:'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.'}}},
    {error:{message:'The connection was aborted, perhaps the server is offline'}},
  ];
  for(const json of errors){
    assert.throws(()=>runCode('Parse Gemini Vision Result',{
      json,refs:{'Build Gemini Vision Request':{item:{json:{shot_key:'S2-A',candidates:[{}]}}}},
    }),/high demand|connection was aborted/);
  }
});

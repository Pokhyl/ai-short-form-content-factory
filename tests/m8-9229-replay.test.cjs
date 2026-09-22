const assert=require('node:assert/strict');
const {test}=require('node:test');
const {spawnSync}=require('node:child_process');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');

test('execution 9229 replay: exact v53 fails S1, current M8 selects five visually accepted assets',()=>{
  const reportPath=path.join(
    os.tmpdir(),
    'm8-9229-replay-'+process.pid+'-'+Date.now()+'.json'
  );

  const result=spawnSync(process.execPath,[
    'scripts/replay_m8_9229.cjs',
    'tests/fixtures/m8-9229-workflow-v53.json',
    'workflows/VIDEO-M8-Multi-Source-Visuals.json',
    'tests/fixtures/m8-9229-saved-provider-responses.json',
    reportPath,
    'tests/fixtures/m8-9229-live-overlay-provider-responses.json',
  ],{
    cwd:process.cwd(),
    encoding:'utf8',
    maxBuffer:16*1024*1024,
  });

  try {
    assert.equal(result.status,0,result.stderr||result.stdout);
    const report=JSON.parse(fs.readFileSync(reportPath,'utf8'));

    assert.equal(report.generated_from.source.execution_id,9229);
    assert.equal(
      report.generated_from.source.workflow_version_id,
      '0953f69f-e982-467e-95e0-35161a613771'
    );
    assert.equal(report.generated_from.provider_calls,0);
    assert.equal(report.generated_from.production_mutations,0);
    assert.equal(report.generated_from.after_overlay_rows_used,27);

    assert.equal(report.before.candidate_count,335);
    assert.equal(
      report.before.production_sequence.terminal_failure,
      'no compliant relevant visual candidate for shot S1-A'
    );

    assert.equal(report.after.production_sequence.terminal_failure,null);
    assert.deepEqual(
      report.after.production_sequence.selected.map(c=>[
        c.shot,c.provider,c.id,
      ]),
      [
        ['S1-A','wikimedia','172815415'],
        ['S2-A','wikimedia','39943534'],
        ['S3-A','pexels','12270481'],
        ['S4-A','wikimedia','34396499'],
        ['S5-A','wikimedia','27207173'],
      ]
    );

    assert.deepEqual(
      report.after.per_shot.map(s=>[s.shot,s.eligible_count]),
      [
        ['S1-A',1],
        ['S2-A',5],
        ['S3-A',5],
        ['S4-A',8],
        ['S5-A',4],
      ]
    );

    const changed=new Map(
      report.changed_candidate_rows.map(row=>[
        [
          row.after.shot,
          row.after.provider,
          row.after.id,
          row.after.query_index,
        ].join(':'),
        row,
      ])
    );

    const turbineRunner=changed.get('S3-A:wikimedia:2050414:1');
    assert.ok(turbineRunner);
    assert.match(
      turbineRunner.after.rejection_reason,
      /conflicting_non_operational_context:museum/
    );

    const backgroundOnly=report.after.all_candidates.find(c=>
      c.shot_key==='S4-A' &&
      c.provider==='wikimedia' &&
      c.provider_asset_id==='37932845' &&
      c.query_index===1
    );
    assert.ok(backgroundOnly);
    assert.equal(backgroundOnly.rejected,true);
    assert.match(
      backgroundOnly.rejection_reason,
      /wikimedia_primary_background_only/
    );

    const rotorTransport=changed.get('S4-A:wikimedia:78066893:2');
    assert.ok(rotorTransport);
    assert.match(
      rotorTransport.after.rejection_reason,
      /conflicting_non_operational_context:transport/
    );

    const rotorComponent=changed.get('S4-A:wikimedia:829307:2');
    assert.ok(rotorComponent);
    assert.match(
      rotorComponent.after.rejection_reason,
      /wikimedia_unrequested_component_view:rotor/
    );
  } finally {
    try{fs.unlinkSync(reportPath);}catch{}
  }
});

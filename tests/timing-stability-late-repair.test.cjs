const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json'));
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

test('probe 4 exposes the same bounded stability-candidate window as probe 5',()=>{
  const code=byName['Normalize Timing Probe 4'].parameters.jsCode;
  assert.match(code,/timing_stability_candidate/);
  assert.match(code,/deltaMs <= Number\(ctx\.tolerance_ms\) \+ 1000/);
  const route=byName['Route Timing Within Target 4']
    .parameters.conditions.conditions[0].leftValue;
  assert.equal(route,'={{ $json.timing_ok || $json.timing_stability_candidate }}');
});

test('failed three-sample stability from origin 4 goes to measured correction, not terminal failure',()=>{
  const c3=workflow.connections['Route Stability Origin 3'].main;
  assert.equal(c3[1][0].node,'Route Stability Origin 4');

  const origin4=byName['Route Stability Origin 4'];
  assert.equal(
    origin4.parameters.conditions.conditions[0].leftValue,
    '={{ $json.origin_is_4 }}'
  );
  const c4=workflow.connections['Route Stability Origin 4'].main;
  assert.equal(c4[0][0].node,'Build Final Measured Correction');
  assert.equal(c4[1][0].node,'Prepare Final Timing Failure 5');
});

test('final measured retry uses bounded nearest semantic hybrid before real probe 5',()=>{
  const code=byName['Validate Final Measured Word Count Retry'].parameters.jsCode;
  assert.match(code,/allowedNearDelta = Math\.max\(2, Math\.ceil\(targetWords \* 0\.08\)\)/);
  assert.match(code,/narrations = nearest\.lines/);
  assert.match(code,/Probe 5 \+ stability remains the actual timing gate/);
  assert.doesNotMatch(code,/final measured exact-word retry missed required total before TTS/);
  assert.equal(
    workflow.connections['Validate Final Measured Word Count Retry'].main[0][0].node,
    'Prepare Timing Probe 5'
  );
});

test('only an in-window initial voice gets stability probes; short voices get one semantic repair',()=>{
  const first=workflow.connections['Route Timing Within Target'].main;
  const second=workflow.connections['Route Timing Within Target 2'].main;
  assert.equal(first[0][0].node,'Prepare Timing Stability Probe');
  assert.equal(first[1][0].node,'Build Timing Repair');
  assert.equal(second[0][0].node,'Prepare Timing Stability Probe');
  assert.equal(second[1][0].node,'Prepare Final Timing Failure');
  assert.equal(
    workflow.connections['Route Stability Origin 2'].main[0][0].node,
    'Prepare Final Timing Failure'
  );
});

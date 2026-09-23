const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')
);
const fixture=JSON.parse(
  fs.readFileSync('tests/fixtures/m5-9672-precision-continuity.json')
);
const code=workflow.nodes.find(
  n=>n.name==='Validate Timing Precision Retry'
).parameters.jsCode;

function runExact(){
  const rows={
    'Build Timing Precision Retry':fixture.build_timing_precision_retry,
    'Build Script Prompt':fixture.build_script_prompt,
    'Normalize Timing Probe':fixture.normalize_timing_probe,
  };
  const $=name=>{
    if(!(name in rows)) throw new Error('missing mock node '+name);
    return {first:()=>({json:rows[name]})};
  };
  return new Function('$','$json',code)(
    $,
    fixture.repair_timing_precision_retry
  ).json;
}

test('9672 regression: precision validator preserves mid-sentence visual-cut surfaces',()=>{
  const out=runExact();

  const expected=[
    'Elektrownia wodna gromadzi wodę',
    'w wielkim zbiorniku za tamą.',
    'Spadająca masa cieczy napędza',
    'turbinę wodną, która następnie',
    'porusza generator wytwarzający czysty prąd elektryczny.',
  ];

  assert.deepEqual(
    out.storyboard.scenes.map(scene=>scene.narration),
    expected
  );
  assert.equal(
    out.storyboard.narration,
    expected.join(' ')
  );
  assert.equal(
    out.storyboard.narration,
    fixture.normalize_timing_probe.storyboard.narration
  );

  assert.doesNotMatch(
    out.storyboard.narration,
    /napędza\.\s+Turbinę/u
  );
  assert.doesNotMatch(
    out.storyboard.narration,
    /następnie\.\s+Porusza/u
  );
  assert.equal(out.precision_semantic_fallback_used,false);
  assert.deepEqual(
    out.precision_semantic_sources,
    ['precision','precision','precision','precision','precision']
  );
});

test('precision validator does not force every visual segment into sentence form',()=>{
  assert.doesNotMatch(code,/normalizeSentenceSurface/);
  assert.doesNotMatch(code,/toLocaleUpperCase/);
  assert.doesNotMatch(code,/text \+= '\\.'/);
  assert.match(code,/precision joined narration must be a complete utterance/);
});

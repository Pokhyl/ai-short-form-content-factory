const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));
const code=(name)=>byName[name].parameters.jsCode;

function semanticGuard(name){
  const js=code(name);
  const start=js.indexOf('// SEMANTIC_PRESERVATION_GUARD_START');
  const end=js.indexOf('// SEMANTIC_PRESERVATION_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' semantic guard missing');
  return new Function(js.slice(start,end)+';return assertSemanticPreservation;')();
}

function applyNovelFallback(name, originalNarrations, candidateNarrations){
  const js=code(name);
  const start=js.indexOf("const originalSemanticScenes = $('Normalize Timing Probe').first().json.storyboard?.scenes;");
  const end=js.indexOf('const joinedNarration = clean(',start);
  assert.ok(start>=0 && end>start,name+' deterministic fallback block missing');
  const block=js.slice(start,end);
  const originalScenes=originalNarrations.map((narration)=>({narration}));
  const sanitizedScenes=candidateNarrations.map((narration)=>({narration}));
  const $=(nodeName)=>{
    assert.equal(nodeName,'Normalize Timing Probe');
    return {first:()=>({json:{storyboard:{scenes:originalScenes}}})};
  };
  const clean=(value)=>String(value??'').replace(/\s+/g,' ').trim();
  const guard=semanticGuard(name);
  return new Function('$','sanitizedScenes','ctx','clean','assertSemanticPreservation',block+';return sanitizedScenes;')(
    $,sanitizedScenes,{language_code:'pl'},clean,guard
  );
}

for(const name of ['Validate Timing Repair','Validate Timing Repair 2']){
  test(name+': 11642 excessive novel modifiers revert only the offending scene',()=>{
    const original=[
      'Długopis składa się z obudowy oraz rurki.',
      'Kulka obraca się w gnieździe.',
    ];
    const candidate=[
      'Długopis składa się zawsze z solidnej obudowy oraz rurki.',
      'Kulka obraca się swobodnie w gnieździe.',
    ];
    const out=applyNovelFallback(name,original,candidate);
    assert.equal(out[0].narration,original[0]);
    assert.equal(out[1].narration,candidate[1]);
  });

  test(name+': deterministic fallback remains fail-closed for changed numbers',()=>{
    assert.throws(
      ()=>applyNovelFallback(
        name,
        ['Długopis ma 3 części.'],
        ['Długopis ma 4 części.']
      ),
      /numeric facts/
    );
  });

  test(name+': deterministic fallback remains fail-closed for negation changes',()=>{
    assert.throws(
      ()=>applyNovelFallback(
        name,
        ['Kulka obraca się w gnieździe.'],
        ['Kulka nie obraca się w gnieździe.']
      ),
      /negation polarity/
    );
  });
}

test('11642 timing prompts require minimal lexical edits instead of broad paraphrase',()=>{
  const first=code('Build Timing Repair');
  const second=code('Build Timing Repair 2');
  assert.match(first,/smallest lexical edit possible/);
  assert.doesNotMatch(first,/do not return a near-unchanged narration when more speech is needed/);
  assert.match(second,/copy ORIGINAL scene narration as the base/);
  assert.match(second,/Do not paraphrase or replace existing content words/);
});

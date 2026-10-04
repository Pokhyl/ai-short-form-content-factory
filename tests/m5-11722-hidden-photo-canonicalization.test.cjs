const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));
const targets=[
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard',
  'Validate Narration Language Repair',
  'Validate Narration Language Repair Retry',
  'Validate Narration Language Repair Second Pass',
];

function helper(name){
  const src=byName[name].parameters.jsCode;
  const a=src.indexOf('function canonicalizeHiddenRequiredPhotoIntent');
  const b=src.indexOf('function normalizeMustShowAnchors',a);
  assert.ok(a>=0 && b>a,name+' hidden-required helper missing');
  return new Function(
    src.slice(a,b)+';return canonicalizeHiddenRequiredPhotoIntent;'
  )();
}

for(const name of targets){
  test(name+': 11722 S6 hidden placement becomes visible owner-with-subject photo',()=>{
    const fn=helper(name);
    assert.equal(
      fn(
        ['pencil sharpener','wooden pencil'],
        'A wooden pencil being rotated inside a pencil sharpener producing shavings.'
      ),
      'A clear photo of pencil sharpener with wooden pencil.'
    );
  });

  test(name+': 11722 S3 internal secondary becomes visible close-up',()=>{
    const fn=helper(name);
    assert.equal(
      fn(
        ['pencil sharpener','metal blade'],
        'A close-up view of a manual pencil sharpener showing its internal blade.'
      ),
      'A close-up photo of pencil sharpener showing metal blade.'
    );
  });

  test(name+': explicit open/cutaway disclosure is preserved',()=>{
    const fn=helper(name);
    const intent='An open cutaway view of a pencil sharpener shaving a wooden pencil.';
    assert.equal(
      fn(['pencil sharpener','wooden pencil'],intent),
      intent
    );
  });

  test(name+': truly hidden spring-loaded pins remain fail-closed',()=>{
    const fn=helper(name);
    const intent='door lock showing internal spring loaded pins';
    assert.equal(
      fn(['door lock','spring loaded pins'],intent),
      intent
    );
  });

  test(name+': ordinary spatial interiors are not rewritten',()=>{
    const fn=helper(name);
    const intent='A conveyor inside a warehouse.';
    assert.equal(
      fn(['warehouse','conveyor'],intent),
      intent
    );
  });

  test(name+': validator invokes hidden-required canonicalizer before must-show normalization',()=>{
    const src=byName[name].parameters.jsCode;
    const call=src.indexOf('visualIntent = canonicalizeHiddenRequiredPhotoIntent(rawMustShow, visualIntent);');
    const normalize=src.indexOf('const mustShow = exposedDetailAnchors || normalizeMustShowAnchors',call);
    assert.ok(call>=0 && normalize>call);
  });
}

const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function helper(name){
  const src=byName[name].parameters.jsCode;
  const start=src.indexOf('function canonicalizeTransientPhotoActionIntent');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' transient helper missing');
  return new Function(src.slice(start,end)+';return canonicalizeTransientPhotoActionIntent;')();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard',
]){
  test(name+': 11635 rotational movement becomes a static hinge photo contract',()=>{
    const canonicalize=helper(name);
    assert.equal(
      canonicalize(['door hinge'],'A photo of a door hinge during rotational movement.'),
      'A clear photo of door hinge.'
    );
  });

  test(name+': stable hinge relation without motion remains explicit',()=>{
    const canonicalize=helper(name);
    const intent='A photo of a door hinge attached to a wooden door.';
    assert.equal(canonicalize(['door hinge'],intent),intent);
  });
}

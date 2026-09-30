const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function helpers(name){
  const src=byName[name].parameters.jsCode;
  const ownerStart=src.indexOf('function canonicalizeInternalDetailOwnerPhoto');
  const transientStart=src.indexOf('function canonicalizeTransientPhotoActionIntent');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',transientStart);
  assert.ok(ownerStart>=0 && transientStart>ownerStart && end>transientStart,name+' helpers missing');
  return new Function(
    src.slice(ownerStart,end)+
    ';return {owner:canonicalizeInternalDetailOwnerPhoto,transient:canonicalizeTransientPhotoActionIntent};'
  )();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard',
]){
  test(name+': 11659 thermometer internal detail promotes concrete owner and removes transient expansion',()=>{
    const {owner,transient}=helpers(name);
    const intent='A liquid column expanding inside a thermometer capillary tube.';
    const queries=[
      'liquid column expanding inside capillary',
      'expanding liquid in thermometer',
      'glass capillary tube',
    ];
    const mustShow=owner(['liquid column','glass capillary tube'],intent,queries);
    assert.deepEqual(mustShow,['thermometer']);
    assert.equal(transient(mustShow,intent),'A clear photo of thermometer.');
  });

  test(name+': ordinary laboratory test tube is not misclassified as an owner device',()=>{
    const {owner}=helpers(name);
    const anchors=['liquid','glass test tube'];
    const intent='A liquid inside a laboratory glass test tube.';
    const queries=['liquid test tube','laboratory test tube','glass test tube'];
    assert.deepEqual(owner(anchors,intent,queries),anchors);
  });

  test(name+': static internal relation without transient action remains unchanged when no owner is present',()=>{
    const {owner,transient}=helpers(name);
    const anchors=['liquid column','glass tube'];
    const intent='A liquid column inside a glass tube.';
    const queries=['liquid column glass tube','liquid inside glass tube','glass tube'];
    assert.deepEqual(owner(anchors,intent,queries),anchors);
    assert.equal(transient(anchors,intent),intent);
  });
}

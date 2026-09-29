const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function guard(name){
  const src=byName[name].parameters.jsCode;
  const start=src.indexOf('function assertRequiredInteractionSecondary');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' interaction guard missing');
  return new Function(src.slice(start,end)+';return assertRequiredInteractionSecondary;')();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
]){
  test(name+': 11605 lock target modifiers are covered by the lock anchor',()=>{
    const check=guard(name);
    for(const target of [
      'mortise lock mechanism',
      'metal door lock',
      'metal lock mechanism',
    ]){
      assert.equal(
        check(
          ['door handle','lock'],
          'Photo of a door handle connected to a '+target+'.',
          'S3-A'
        ),
        'lock',
        target
      );
    }
  });

  test(name+': semantic-head fallback still requires the real relation subject',()=>{
    const check=guard(name);
    assert.throws(
      ()=>check(
        ['door handle','mechanism'],
        'Photo of a door handle connected to a metal lock mechanism.',
        'S3-A'
      ),
      /second independently visible interaction subject.*metal lock mechanism/
    );
  });

  test(name+': semantic-head fallback accepts a concise subtype anchor without dropping the second subject',()=>{
    const check=guard(name);
    assert.equal(
      check(
        ['multimeter','battery'],
        'A multimeter measuring voltage on a car battery.',
        'S6-A'
      ),
      'battery'
    );
  });
}

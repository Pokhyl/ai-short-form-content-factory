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

function helpers(name){
  const src=byName[name].parameters.jsCode;
  const a=src.indexOf('function dependentSecondaryAnchors');
  const normalizeAt=src.indexOf('function normalizeMustShowAnchors',a);
  const nextFn=src.indexOf('\nfunction ',normalizeAt+'function normalizeMustShowAnchors'.length);
  const b=nextFn>=0?nextFn:src.length;
  assert.ok(a>=0 && normalizeAt>a && b>normalizeAt,name+' helper block missing');
  return new Function(
    src.slice(a,b)+
    ';return {dependentSecondaryAnchors,normalizeMustShowAnchors};'
  )();
}

for(const name of targets){
  test(name+': 11718 recognizes paper guide inside paper alignment guides',()=>{
    const {dependentSecondaryAnchors,normalizeMustShowAnchors}=helpers(name);
    const must=['desktop hole punch','paper guide'];
    const intent='A close-up of paper alignment guides on a desktop hole punch.';
    assert.deepEqual(
      dependentSecondaryAnchors(must,intent,['desktop hole punch']),
      ['paper guide']
    );
    assert.deepEqual(
      normalizeMustShowAnchors(must,intent,'S4-A',['desktop hole punch']),
      ['desktop hole punch']
    );
  });

  test(name+': does not collapse a different inserted noun',()=>{
    const {dependentSecondaryAnchors}=helpers(name);
    const must=['desktop hole punch','paper guide'];
    const intent='A close-up of paper storage guides on a desktop hole punch.';
    assert.deepEqual(
      dependentSecondaryAnchors(must,intent,['desktop hole punch']),
      []
    );
  });

  test(name+': preserves exact dependent phrases',()=>{
    const {dependentSecondaryAnchors}=helpers(name);
    assert.deepEqual(
      dependentSecondaryAnchors(
        ['desktop hole punch','paper guide'],
        'A close-up of paper guide on a desktop hole punch.',
        ['desktop hole punch']
      ),
      ['paper guide']
    );
  });
}

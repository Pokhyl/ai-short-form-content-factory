const fs=require('node:fs');
const test=require('node:test');
const assert=require('node:assert/strict');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8')
);
const byName=Object.fromEntries(workflow.nodes.map(n=>[n.name,n]));

test('9892 regression: diffuse background context is not a hard must_not_show exclusion',()=>{
  const code=byName['Canonicalize Final Storyboard'].parameters.jsCode;
  const match=code.match(
    /function normalizeMustNotShow\(rawMustNotShow\) \{[\s\S]*?\n\}/
  );
  assert.ok(match,'normalizeMustNotShow helper missing');

  const clean=value=>String(value??'').replace(/\s+/g,' ').trim();
  const anchorWords=value=>String(value||'')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g,' ')
    .split(/\s+/u)
    .filter(Boolean);

  const normalize=new Function(
    'clean','anchorWords',
    match[0]+'; return normalizeMustNotShow;'
  )(clean,anchorWords);

  assert.deepEqual(
    normalize([
      'exterior landscape',
      'generic background',
      'coastal scenery',
      'wind turbine',
      'daytime scene',
      'exterior tower',
    ]),
    ['wind turbine','daytime scene','exterior tower']
  );
});

test('storyboard generation and both bounded repairs forbid diffuse-context exclusions',()=>{
  for(const name of [
    'Build Script Prompt',
    'Build Storyboard Repair',
    'Build Storyboard Repair 2',
  ]){
    const code=byName[name].parameters.jsCode;
    assert.match(code,/must_not_show/,name);
    assert.match(code,/background.*landscape.*scenery/,name);
  }
});

test('final canonicalizer applies must_not_show normalization before commit',()=>{
  const code=byName['Canonicalize Final Storyboard'].parameters.jsCode;
  assert.match(
    code,
    /shot\.must_not_show = normalizeMustNotShow\(shot\.must_not_show\)/u
  );
});

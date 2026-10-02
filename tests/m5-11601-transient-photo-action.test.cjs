const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function helper(name){
  const src=byName[name].parameters.jsCode;
  const start=src.indexOf('function canonicalizeTransientPhotoActionIntent');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' transient photo helper missing');
  return new Function(src.slice(start,end)+';return canonicalizeTransientPhotoActionIntent;')();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard',
]){
  test(name+': 11601 stapler action becomes a static searchable photo contract',()=>{
    const canonicalize=helper(name);
    assert.equal(
      canonicalize(
        ['office stapler','paper sheets'],
        'Office stapler joining stacked paper sheets together on a workspace table.'
      ),
      'A clear photo of office stapler with paper sheets.'
    );
  });

  test(name+': zipper opening action becomes a static object photo contract',()=>{
    const canonicalize=helper(name);
    assert.equal(
      canonicalize(
        ['zipper'],
        'A zipper being opened by moving the slider downwards.'
      ),
      'A clear photo of zipper.'
    );
  });

  test(name+': 11778 wrench engagement becomes a static searchable photo contract',()=>{
    const canonicalize=helper(name);
    assert.equal(
      canonicalize(
        ['open end wrench','nut'],
        'An open end wrench engaging a nut in a restricted space.'
      ),
      'A clear photo of open end wrench with nut.'
    );
  });

  test(name+': 11819 clamp stabilization becomes a static searchable photo contract',()=>{
    const canonicalize=helper(name);
    assert.equal(
      canonicalize(
        ['woodworking clamp'],
        'A photograph of a stable woodworking clamp stabilizing wood pieces during precise workshop tasks.'
      ),
      'A clear photo of woodworking clamp.'
    );
  });

  test(name+': visible human action remains explicit',()=>{
    const canonicalize=helper(name);
    const intent='Hands pressing an office stapler onto paper sheets.';
    assert.equal(
      canonicalize(['hands','office stapler','paper sheets'],intent),
      intent
    );
  });

  test(name+': visible human stabilization remains explicit',()=>{
    const canonicalize=helper(name);
    const intent='Hands stabilizing wood pieces with a woodworking clamp.';
    assert.equal(
      canonicalize(['hands','woodworking clamp'],intent),
      intent
    );
  });

  test(name+': stable connected relation remains explicit',()=>{
    const canonicalize=helper(name);
    const intent='A steel cable connected to a bicycle brake lever.';
    assert.equal(
      canonicalize(['bicycle brake lever','steel cable'],intent),
      intent
    );
  });

  test(name+': validator calls transient action canonicalizer',()=>{
    const src=byName[name].parameters.jsCode;
    assert.match(
      src,
      /visualIntent = canonicalizeTransientPhotoActionIntent\(mustShow, visualIntent\);/
    );
  });
}

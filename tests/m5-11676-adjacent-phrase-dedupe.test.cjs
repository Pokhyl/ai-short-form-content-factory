const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function dedupe(name){
  const src=byName[name].parameters.jsCode;
  const start=src.indexOf('function canonicalizeAdjacentPhraseDuplication');
  const end=src.indexOf('for (const scene of sanitizedScenes)',start);
  assert.ok(start>=0 && end>start,name+' dedupe helper missing');
  const clean=(value)=>String(value??'').replace(/\s+/g,' ').trim();
  return new Function('clean',src.slice(start,end)+';return canonicalizeAdjacentPhraseDuplication;')(clean);
}

for(const name of [
  'Validate Narration Language Repair',
  'Validate Narration Language Repair Retry',
  'Validate Narration Language Repair Second Pass',
]){
  test(name+': 11676 removes exact adjacent multiword duplication',()=>{
    const fn=dedupe(name);
    assert.equal(
      fn('złącznego podczas obrotu podczas obrotu narzędzia.'),
      'złącznego podczas obrotu narzędzia.'
    );
  });

  test(name+': preserves ordinary single-word repetition and non-adjacent wording',()=>{
    const fn=dedupe(name);
    assert.equal(fn('bardzo bardzo ważny element.'),'bardzo bardzo ważny element.');
    assert.equal(
      fn('obrót narzędzia powoduje ruch, a później obrót narzędzia kończy pracę.'),
      'obrót narzędzia powoduje ruch, a później obrót narzędzia kończy pracę.'
    );
  });

  test(name+': preserves terminal punctuation when repeated phrase ends the sentence',()=>{
    const fn=dedupe(name);
    assert.equal(
      fn('mechanizm działa podczas obrotu podczas obrotu.'),
      'mechanizm działa podczas obrotu.'
    );
  });
}

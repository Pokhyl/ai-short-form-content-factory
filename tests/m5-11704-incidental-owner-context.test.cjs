const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json','utf8'));
const code=name=>workflow.nodes.find(n=>n.name===name).parameters.jsCode;

function helpers(name){
  const src=code(name);
  const start=src.indexOf('function dependentSecondaryAnchors');
  const end=src.indexOf('// MUST_SHOW_SECONDARY_GUARD_END',start);
  assert.ok(start>=0 && end>start,name+' secondary helper block missing');
  return new Function(
    src.slice(start,end)+
    ';return {dependentSecondaryAnchors,normalizeMustShowAnchors};'
  )();
}

for(const name of [
  'Validate Storyboard',
  'Validate Repaired Storyboard',
  'Validate Repaired Storyboard 2',
  'Canonicalize Final Storyboard',
]){
  test(name+': 11704 repeated nearby owner is retrieval context, not a second hard subject',()=>{
    const {dependentSecondaryAnchors,normalizeMustShowAnchors}=helpers(name);
    const anchors=['metal wire staple','desktop stapler'];
    const intent='A metal wire staple placed near a desktop stapler';
    const repeated=['desktop stapler'];

    assert.deepEqual(
      dependentSecondaryAnchors(anchors,intent,repeated),
      ['desktop stapler']
    );
    assert.deepEqual(
      normalizeMustShowAnchors(anchors,intent,'S3-A',repeated),
      ['metal wire staple']
    );
  });

  test(name+': 11747 mid-sentence proximity continuation is context, not a second hard subject',()=>{
    const {dependentSecondaryAnchors,normalizeMustShowAnchors}=helpers(name);
    const anchors=['hex key','threaded fastener'];
    const intent='An L-shaped hex key positioned next to a threaded fastener in a workshop';
    const current='L. Jego głównym zadaniem jest obsługa';
    const next='śrub posiadających odpowiednie gniazdo sześciokątne w';

    assert.deepEqual(
      dependentSecondaryAnchors(anchors,intent,[],current,next),
      ['threaded fastener']
    );
    assert.deepEqual(
      normalizeMustShowAnchors(anchors,intent,'S3-A',[],current,next),
      ['hex key']
    );
  });

  test(name+': complete-sentence proximity still keeps an unrelated second subject hard',()=>{
    const {dependentSecondaryAnchors,normalizeMustShowAnchors}=helpers(name);
    const anchors=['hex key','threaded fastener'];
    const intent='An L-shaped hex key positioned next to a threaded fastener in a workshop';
    const current='Klucz imbusowy leży obok śruby.';
    const next='Następna scena zaczyna nowe zdanie.';

    assert.deepEqual(
      dependentSecondaryAnchors(anchors,intent,[],current,next),
      []
    );
    assert.deepEqual(
      normalizeMustShowAnchors(anchors,intent,'S3-A',[],current,next),
      anchors
    );
  });

  test(name+': mid-sentence proximity does not collapse when the next scene starts a new sentence',()=>{
    const {dependentSecondaryAnchors}=helpers(name);
    assert.deepEqual(
      dependentSecondaryAnchors(
        ['hex key','threaded fastener'],
        'A hex key next to a threaded fastener',
        [],
        'Klucz imbusowy służy do obsługi',
        'Śruba ma gniazdo sześciokątne.'
      ),
      []
    );
  });

  test(name+': repeated owner proximity supports beside and next to but not generic with',()=>{
    const {dependentSecondaryAnchors}=helpers(name);
    const repeated=['desktop stapler'];
    assert.deepEqual(
      dependentSecondaryAnchors(
        ['metal wire staple','desktop stapler'],
        'A metal wire staple beside a desktop stapler',
        repeated
      ),
      ['desktop stapler']
    );
    assert.deepEqual(
      dependentSecondaryAnchors(
        ['metal wire staple','desktop stapler'],
        'A metal wire staple next to a desktop stapler',
        repeated
      ),
      ['desktop stapler']
    );
    assert.deepEqual(
      dependentSecondaryAnchors(
        ['metal wire staple','desktop stapler'],
        'A metal wire staple with a desktop stapler',
        repeated
      ),
      []
    );
  });

  test(name+': continuation context is threaded into both sanitizer calls',()=>{
    const src=code(name);
    assert.match(
      src,
      /dependentSecondaryAnchors\(rawMustShow, visualIntent, repeatedPrimaryAnchors,/
    );
    assert.match(
      src,
      /normalizeMustShowAnchors\(rawMustShow, visualIntent, shotId, repeatedPrimaryAnchors,/
    );
    assert.match(src,/count >= 2/);
  });
}

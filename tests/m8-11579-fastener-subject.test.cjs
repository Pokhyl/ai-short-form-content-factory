const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');

const workflow=JSON.parse(
  fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json','utf8')
);
const byName=Object.fromEntries(workflow.nodes.map((node)=>[node.name,node]));

function helpers(name){
  const src=byName[name].parameters.jsCode;
  const before=src.slice(0,src.indexOf('const ctx ='));
  return new Function(
    before+';return {semanticSet,subjectEvidenceSet,scoreCandidate};'
  )();
}

const exactCtx={
  query:'zipper unzipping action photo',
  visual_intent:'A zipper being opened by moving the slider downwards.',
  must_show:['zipper'],
  must_not_show:[],
  preferred_media_type:'photo',
  domain_context_terms:[],
  visual_detail_terms:[],
};

const exactMetadata=
  'Close-up of a woman unzipping the back of her elegant dress indoors. cottonbro studio';

for(const provider of ['Normalize Pexels','Normalize Pixabay','Normalize Wikimedia']){
  test(provider+': fastener action metadata can prove the zipper subject without changing query semantics',()=>{
    const h=helpers(provider);

    assert.equal(
      h.semanticSet(exactMetadata).has('zipper'),
      false,
      'general semanticSet must stay literal for query/intent scoring'
    );
    assert.equal(
      h.subjectEvidenceSet(exactMetadata).has('zipper'),
      true,
      'unzipping + dress context should prove a depicted zipper subject'
    );
    assert.equal(
      h.subjectEvidenceSet('Extract a ZIP archive file into a folder').has('zipper'),
      false,
      'generic ZIP archive context must never imply a zipper'
    );

    const scored=h.scoreCandidate(
      exactCtx,
      exactMetadata,
      'photo',
      4160,
      6240,
      1,
      '',
      exactMetadata,
      ''
    );
    assert.equal(scored.rejected,false,scored.rejection_reason);
    assert.ok(scored.relevance_score>=55,scored.relevance_score);
  });
}

test('11579 S8-A opposite zipping action stays rejected for an unzipping query',()=>{
  const h=helpers('Normalize Pexels');
  const metadata='Close-up of hands zipping a warm shearling-lined suede jacket.';
  const scored=h.scoreCandidate(
    exactCtx,
    metadata,
    'photo',
    4160,
    6240,
    1,
    '',
    metadata,
    ''
  );
  assert.equal(scored.rejected,true);
  assert.match(scored.rejection_reason,/insufficient_query_intent_metadata_match/);
});

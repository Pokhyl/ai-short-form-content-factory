const {test}=require('node:test');
const {replay}=require('../scripts/replay_m8_release.cjs');
test('current native parser and global collector preserve all original contracts across nine saved scene responses',()=>{replay();});
const assert=require('node:assert/strict'),fs=require('node:fs');
const {samePreviewSources}=require('../scripts/visual_preview_identity.cjs');
test('actual SQL S8 third-candidate replacement cannot reuse original three-preview bytes',()=>{
 const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12108-fastening-contract.json'));
 const before=f.original_candidate_sets.find(s=>s.shot_key==='S8-A').candidates;
 const after=f.ranking_replay.candidate_sets.find(s=>s.shot_key==='S8-A').candidates;
 assert.equal(samePreviewSources(before,after),false);
});
test('unchanged ordered sources may reuse previews; changed URL, source or order invalidates the cache',()=>{
 const a=[{provider:'source-a',provider_asset_id:'one',media_type:'photo',preview_url:'https://example.test/a',download_url:'https://example.test/full-a'},{provider:'source-b',provider_asset_id:'two',media_type:'photo',preview_url:'https://example.test/b',download_url:'https://example.test/full-b'}];
 assert.equal(samePreviewSources(a,structuredClone(a)),true);
 for(const change of [b=>b.reverse(),b=>b[1].provider_asset_id='three',b=>b[1].preview_url='https://example.test/other']){const b=structuredClone(a);change(b);assert.equal(samePreviewSources(a,b),false);}
});

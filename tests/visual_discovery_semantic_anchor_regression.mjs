import assert from 'node:assert/strict';
import { discoverVisualCandidates, recoverVisualConflictCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const ok = payload => ({ ok: true, status: 200, json: async () => payload });
const commonsPage = (id, description) => ({
  title:`File:${id}.jpg`,
  imageinfo:[{
    mime:'image/jpeg', width:1400, height:900,
    url:`https://upload.wikimedia.org/${id}.jpg`,
    thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,
    descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,
    extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}},
  }],
});

function payloadFor(query, host) {
  const nuclear = query === 'early 20th century nuclear physics laboratory equipment';
  const rna = query === 'self-replicating RNA molecule schematic model';
  if (host === 'commons.wikimedia.org') {
    if (nuclear) return {query:{pages:[commonsPage('nuclear-laboratory','nuclear physics laboratory apparatus and measurement equipment')]}};
    if (rna) return {query:{pages:[commonsPage('rna-replication','self replicating RNA molecule schematic model')]}};
    return {query:{pages:[]}};
  }
  if (host === 'pixabay.com') {
    if (nuclear) return {hits:[
      {id:2554273,largeImageURL:'https://cdn.pixabay.com/school.jpg',webformatURL:'https://cdn.pixabay.com/school-small.jpg',imageWidth:1200,imageHeight:1800,tags:'cyprus athienou school neoclassic architecture building 20th century colonnade',pageURL:'https://pixabay.com/photos/cyprus-athienou-school-neoclassic-2554273/',user:'fixture'},
    ]};
    if (rna) return {hits:[
      {id:877773,largeImageURL:'https://cdn.pixabay.com/molecule.jpg',webformatURL:'https://cdn.pixabay.com/molecule-small.jpg',imageWidth:1200,imageHeight:900,tags:'molecule chemistry science dome model',pageURL:'https://pixabay.com/photos/molecule-877773/',user:'fixture'},
    ]};
    return {hits:[]};
  }
  if (host === 'api.pexels.com') {
    if (nuclear) return {photos:[{id:91,width:1400,height:900,url:'https://www.pexels.com/photo/nuclear-lab-91/',photographer:'fixture',alt:'nuclear physics laboratory equipment detector apparatus',src:{original:'https://images.pexels.com/nuclear.jpg',large2x:'https://images.pexels.com/nuclear2.jpg',medium:'https://images.pexels.com/nuclearm.jpg'}}]};
    if (rna) return {photos:[{id:92,width:1400,height:900,url:'https://www.pexels.com/photo/rna-92/',photographer:'fixture',alt:'self replicating RNA molecule schematic model',src:{original:'https://images.pexels.com/rna.jpg',large2x:'https://images.pexels.com/rna2.jpg',medium:'https://images.pexels.com/rnam.jpg'}}]};
    return {photos:[]};
  }
  throw new Error(`unexpected host ${host}`);
}

async function fakeFetch(input) {
  const url = new URL(String(input));
  if (url.hostname.endsWith('.wikipedia.org')) return ok({query:{pages:[]}});
  const query = url.searchParams.get('gsrsearch') ?? url.searchParams.get('q') ?? url.searchParams.get('query') ?? '';
  return ok(payloadFor(query, url.hostname));
}

const nuclearTarget='early 20th century nuclear physics laboratory equipment';
const discovered=await discoverVisualCandidates({
  canonicalSource:{language:'en',title:'Nuclear physics'},
  timedBeats:Array.from({length:4},(_,i)=>({scene_number:i+1,narration:'Nuclear physics opened a new scientific era.',narration_support_evidence_ids:['S1'],beat_start_seconds:i,beat_end_seconds:i+1,duration_seconds:1})),
  visualQueriesEn:[nuclearTarget,nuclearTarget,nuclearTarget,nuclearTarget],pixabayApiKey:'pix',pexelsApiKey:'pex',fetchImpl:fakeFetch,
});
const initialIds=discovered.visual_segments[0].candidates.map(c=>c.candidate_id);
assert.ok(initialIds.some(id=>id==='pexels:91'));
assert.ok(initialIds.some(id=>String(id).startsWith('wikimedia:')));
assert.ok(!initialIds.includes('pixabay:2554273'),'20th-century school metadata must not pass a nuclear-laboratory target');
assert.ok(discovered.visual_segments[0].candidates.every(c=>c.target_anchor_pass===true));

const recoveredNuclear=await recoverVisualConflictCandidates({visualTarget:nuclearTarget,canonicalSubject:'Nuclear physics',pixabayApiKey:'pix',pexelsApiKey:'pex',fetchImpl:fakeFetch});
assert.ok(!recoveredNuclear.candidates.some(c=>c.candidate_id==='pixabay:2554273'));
assert.ok(recoveredNuclear.semantic_rejected_candidate_count>=1);
assert.ok(recoveredNuclear.candidates.some(c=>c.candidate_id==='pexels:91'));

const rnaTarget='self-replicating RNA molecule schematic model';
const recoveredRna=await recoverVisualConflictCandidates({visualTarget:rnaTarget,canonicalSubject:'Abiogenesis',pixabayApiKey:'pix',pexelsApiKey:'pex',fetchImpl:fakeFetch});
assert.ok(!recoveredRna.candidates.some(c=>c.candidate_id==='pixabay:877773'),'generic molecule metadata must not satisfy a self-replicating RNA target');
assert.ok(recoveredRna.candidates.some(c=>c.candidate_id==='pexels:92'));
assert.ok(recoveredRna.candidates.every(c=>c.target_anchor_hits>=c.target_anchor_required));

console.log('VISUAL_DISCOVERY_SEMANTIC_ANCHOR_REGRESSION_PASS');

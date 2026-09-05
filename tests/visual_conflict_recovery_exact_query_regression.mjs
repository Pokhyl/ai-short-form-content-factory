import assert from 'node:assert/strict';
import { recoverVisualConflictCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const requests=[];
const ok=(payload)=>({ok:true,status:200,json:async()=>payload});
function commonsPage(title,description){
  return {
    title:`File:${title}.jpg`,
    imageinfo:[{
      mime:'image/jpeg',width:1200,height:800,
      url:`https://upload.wikimedia.org/${title}.jpg`,
      thumburl:`https://upload.wikimedia.org/${title}-thumb.jpg`,
      descriptionurl:`https://commons.wikimedia.org/wiki/File:${title}.jpg`,
      extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}},
    }],
  };
}
async function fakeFetch(input){
  const url=new URL(String(input));
  const query=url.searchParams.get('gsrsearch')??url.searchParams.get('q')??url.searchParams.get('query')??'';
  requests.push({host:url.hostname,path:url.pathname,query});
  if(url.hostname==='commons.wikimedia.org'){
    return ok({query:{pages:[commonsPage('new-commons','water cycle diagram')]}});
  }
  if(url.hostname==='pixabay.com'){
    return ok({hits:[
      {id:101,largeImageURL:'https://cdn.pixabay.com/excluded.jpg',webformatURL:'https://cdn.pixabay.com/excluded-small.jpg',imageWidth:1600,imageHeight:1000,tags:'water cycle diagram',pageURL:'https://pixabay.com/photos/excluded',user:'fixture'},
      {id:102,largeImageURL:'https://cdn.pixabay.com/new.jpg',webformatURL:'https://cdn.pixabay.com/new-small.jpg',imageWidth:1600,imageHeight:1000,tags:'water cycle diagram',pageURL:'https://pixabay.com/photos/new',user:'fixture'},
    ]});
  }
  if(url.hostname==='api.pexels.com'){
    assert.equal(url.pathname,'/v1/search');
    return ok({photos:[{id:301,width:1600,height:1000,url:'https://www.pexels.com/photo/new-301/',photographer:'fixture',alt:'water cycle diagram',src:{original:'https://images.pexels.com/new.jpg',large2x:'https://images.pexels.com/new2.jpg',medium:'https://images.pexels.com/newm.jpg'}}]});
  }
  throw new Error(`unexpected ${url}`);
}

const exactTarget='water cycle diagram';
const result=await recoverVisualConflictCandidates({
  visualTarget:exactTarget,
  excludeCandidateIds:['pixabay:101'],
  pixabayApiKey:'pix',
  pexelsApiKey:'pex',
  fetchImpl:fakeFetch,
});
assert.equal(result.provider_query,exactTarget);
assert.equal(result.visual_target,exactTarget);
assert.equal(result.bounded_global_conflict_recovery,true);
assert.equal(result.excluded_candidate_count,1);
assert.equal(result.provider_errors.length,0);
assert.equal(requests.length,3,'conflict recovery must issue exactly one provider set');
assert.deepEqual(new Set(requests.map(r=>r.host)),new Set(['commons.wikimedia.org','pixabay.com','api.pexels.com']));
assert.ok(requests.every(r=>r.query===exactTarget),'conflict recovery must use only the exact current-beat target');
assert.ok(!result.candidates.some(c=>c.candidate_id==='pixabay:101'),'previously considered asset must be excluded');
assert.ok(result.candidates.some(c=>c.candidate_id==='pixabay:102'));
assert.ok(result.candidates.some(c=>c.candidate_id==='pexels:301'));
assert.ok(result.candidates.some(c=>String(c.candidate_id).startsWith('wikimedia:')));
console.log('VISUAL_CONFLICT_RECOVERY_EXACT_QUERY_REGRESSION_PASS');

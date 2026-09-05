import assert from 'node:assert/strict';
import { discoverVisualCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const requests=[];
const ok=payload=>({ok:true,status:200,json:async()=>payload});
function commonsPage(id,description){return {title:`File:${id}.jpg`,imageinfo:[{mime:'image/jpeg',width:1200,height:800,url:`https://upload.wikimedia.org/${id}.jpg`,thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}}}]};}
async function fakeFetch(input){
  const url=new URL(String(input));
  const query=url.searchParams.get('gsrsearch')??url.searchParams.get('q')??url.searchParams.get('query')??'';
  requests.push({host:url.hostname,path:url.pathname,query});
  if(url.hostname.endsWith('.wikipedia.org'))return ok({query:{pages:[]}});
  const recovery=query==='Alexander Fleming portrait'||query==='water cycle diagram';
  const stable=query.startsWith('stable exact target');
  if(url.hostname==='commons.wikimedia.org'){
    return ok({query:{pages:[(recovery||stable)?commonsPage(`relevant-${query.replaceAll(' ','-')}`,query):commonsPage('wrong-alexander','Alexander Hamilton historical monument')]}});
  }
  if(url.hostname==='pixabay.com'){
    return ok({hits:[{id:recovery?101:201,largeImageURL:'https://cdn.pixabay.com/a.jpg',webformatURL:'https://cdn.pixabay.com/b.jpg',imageWidth:1600,imageHeight:1000,tags:(recovery||stable)?query:'Alexander Hamilton monument rain window',pageURL:'https://pixabay.com/photos/x',user:'fixture'}]});
  }
  if(url.hostname==='api.pexels.com'){
    assert.equal(url.pathname,'/v1/search');
    return ok({photos:[{id:recovery?301:401,width:1600,height:1000,url:'https://www.pexels.com/photo/x-1/',photographer:'fixture',alt:(recovery||stable)?query:'Alexander Hamilton statue rain on glass',src:{original:'https://images.pexels.com/x.jpg',large2x:'https://images.pexels.com/x2.jpg',medium:'https://images.pexels.com/xm.jpg'}}]});
  }
  throw new Error(`unexpected ${url}`);
}

async function runCase({title,query}){
  const before=requests.length;
  const result=await discoverVisualCandidates({
    canonicalSource:{language:'en',title},
    timedBeats:[
      {scene_number:1,narration:'fixture narration one',narration_support_evidence_ids:['S1'],beat_start_seconds:0,beat_end_seconds:1,duration_seconds:1},
      {scene_number:2,narration:'fixture narration two',narration_support_evidence_ids:['S1'],beat_start_seconds:1,beat_end_seconds:2,duration_seconds:1},
      {scene_number:3,narration:'fixture narration three',narration_support_evidence_ids:['S1'],beat_start_seconds:2,beat_end_seconds:3,duration_seconds:1},
      {scene_number:4,narration:'fixture narration four',narration_support_evidence_ids:['S1'],beat_start_seconds:3,beat_end_seconds:4,duration_seconds:1},
    ],
    visualQueriesEn:[query,'stable exact target two','stable exact target three','stable exact target four'],pixabayApiKey:'pix',pexelsApiKey:'pex',fetchImpl:fakeFetch,
  });
  const segment=result.visual_segments[0];
  assert.equal(result.visual_segments.length,4);
  const issued=requests.slice(before).filter(r=>['commons.wikimedia.org','pixabay.com','api.pexels.com'].includes(r.host));
  return {result,segment,issued};
}

const person=await runCase({title:'Discovery of penicillin by Alexander Fleming',query:'Alexander Fleming historical portrait'});
assert.equal(person.segment.bounded_query_recovery_used,true);
assert.deepEqual(person.segment.provider_queries,['Alexander Fleming historical portrait','Alexander Fleming portrait']);
assert.equal(person.result.provider_counts.segment_recovery_query_count,1);
assert.equal(person.issued.length,15,'four exact provider sets plus one bounded recovery provider set');
assert.ok(person.segment.candidates.some(c=>c.metadata?.bounded_query_recovery===true&&String(c.title).toLowerCase().includes('alexander fleming')));
assert.ok(!person.segment.provider_queries.some(q=>q==='Discovery of penicillin by Alexander Fleming'),'recovery must not fall back to generic topic query');

const process=await runCase({title:'Meteorological process of cloud formation and precipitation',query:'water cycle diagram showing evaporation condensation and precipitation'});
assert.equal(process.segment.bounded_query_recovery_used,true);
assert.deepEqual(process.segment.provider_queries,['water cycle diagram showing evaporation condensation and precipitation','water cycle diagram']);
assert.ok(process.issued.length>=6&&process.issued.length<=15,'cached exact searches may reduce the second call but recovery stays bounded');
assert.ok(process.segment.candidates.some(c=>c.metadata?.bounded_query_recovery===true&&String(c.title).toLowerCase().includes('water cycle diagram')));
for(const r of [...person.issued,...process.issued])assert.ok(r.query.length<=90);

console.log('VISUAL_DISCOVERY_BOUNDED_QUERY_RECOVERY_REGRESSION_PASS');

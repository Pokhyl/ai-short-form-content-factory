import assert from 'node:assert/strict';
import {discoverVisualCandidates} from '../services/media-worker/src/visual-discovery.mjs';
const page=(id,description)=>({title:`File:${id}.jpg`,imageinfo:[{mime:'image/jpeg',width:1400,height:900,url:`https://upload.wikimedia.org/${id}.jpg`,thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}}}]});
const queries=[];
const result=await discoverVisualCandidates({
 canonicalSource:{language:'en',title:'North Harbor lock system'},
 explorationQueries:[{query_number:1,search_query_en:'North Harbor lock culvert',observable_target:'North Harbor lock culvert',retrieval_rationale:'Grounded physical component'}],
 fetchImpl:async input=>{
  const u=new URL(String(input));
  if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
  if(u.hostname==='commons.wikimedia.org'){
   const q=u.searchParams.get('gsrsearch');queries.push(q);
   return new Response(JSON.stringify({query:{pages:[page('north-harbor-culvert','North Harbor lock culvert wall construction'),page('generic-valve','generic water valve and pipe') ]}}));
  }
  if(u.hostname==='pixabay.com')return new Response(JSON.stringify({hits:[]}));
  if(u.hostname==='api.pexels.com')return new Response(JSON.stringify({photos:[]}));
  throw new Error(`unexpected host ${u.hostname}`);
 }
});
assert.equal(result.exploration_version,'pre-claim-visual-exploration-v1');
assert.equal(result.exploration_queries.length,1);
const row=result.exploration_queries[0];
assert.equal(row.query_number,1);
assert(row.provider_queries.length>=1&&row.provider_queries.length<=5,'exploration retrieval must stay bounded');
assert(row.candidates.some(x=>x.provider_asset_id==='File:north-harbor-culvert.jpg'),'subject-identified component must survive exploration');
assert(!row.candidates.some(x=>x.provider_asset_id==='File:generic-valve.jpg'),'generic detail without named-subject identity must be rejected before vision review');
assert(row.candidates.every(x=>x.inventory_subject_anchor_pass===true));
assert.equal(result.provider_counts.exploration_query_count,1);
console.log('VISUAL_EXPLORATION_INVENTORY_REGRESSION_PASS');

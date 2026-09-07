import assert from 'node:assert/strict';
import { discoverVisualCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const queries=[];
const page=(id,description)=>({title:`File:${id}.jpg`,imageinfo:[{mime:'image/jpeg',width:1200,height:800,url:`https://upload.wikimedia.org/${id}.jpg`,thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}}}]});
const run=async(subject,detail)=>{
 const query=`${subject} ${detail} internal structure`;
 const target=`${subject} ${detail} showing its internal structure`;
 const result=await discoverVisualCandidates({canonicalSource:{language:'en',title:subject},inventoryClaims:[{claim_number:1,claim:'A supported factual claim.',visual_target:target,search_query_en:query}],fetchImpl:async input=>{
  const u=new URL(String(input));
  if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
  const q=u.searchParams.get('gsrsearch');queries.push(q);
  const pages=q===`${subject} ${detail}`?[page(`${subject}-specific`,`${subject} ${detail} internal structure`)]:Array.from({length:5},(_,i)=>page(`${subject}-generic-${i}`,`${subject} exterior photograph`));
  return new Response(JSON.stringify({query:{pages}}));
 }});
 const c=result.inventory_claims[0];
 assert.deepEqual(c.provider_queries,[query,`${subject} ${detail}`],'generic subject hits must not suppress detail retrieval');
 assert.equal(c.candidates[0].provider_asset_id,`File:${subject}-specific.jpg`,'detail match must precede generic photos before reviewer truncates candidates');
 assert.equal(c.candidates[0].inventory_detail_hits,3);
 assert.equal(c.visual_target,target,'acceptance target must remain intact');
 assert(c.candidates.every(x=>x.target_anchor_pass===true));
};
await run('Mechanical clock','escapement');
await run('Radio telescope','receiver');
assert.equal(queries.length,4,'at most two provider queries per inventory claim');
console.log('INVENTORY_DETAIL_RETRIEVAL_REGRESSION_PASS');

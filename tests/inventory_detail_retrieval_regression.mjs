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
 assert.equal(c.candidates[0].inventory_detail_hits,1,'detail score must follow the acceptance target rather than extra query wording');
 assert.equal(c.candidates[0].inventory_subject_anchor_pass,true);
 assert.equal(c.candidates[0].inventory_subject_anchor_hits,2);
 assert.equal(c.visual_target,target,'acceptance target must remain intact');
 assert(c.candidates.every(x=>x.target_anchor_pass===true));
};
await run('Mechanical clock','escapement');
await run('Radio telescope','receiver');

const recoveryQueries=[];
const recovery=await discoverVisualCandidates({canonicalSource:{language:'en',title:'North Harbor'},inventoryClaims:[{claim_number:1,claim:'Grounded towing fact.',visual_target:'Electric towing locomotive beside a vessel',search_query_en:'North Harbor vessel towing locomotive tractors'},{claim_number:2,claim:'Grounded water fact.',visual_target:'Technical diagram showing water valves in a chamber',search_query_en:'North Harbor gravity water system diagram'}],fetchImpl:async input=>{
 const u=new URL(String(input));
 if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
 const q=u.searchParams.get('gsrsearch');recoveryQueries.push(q);return new Response(JSON.stringify({query:{pages:[]}}));
}});
const towingQueries=recovery.inventory_claims[0].provider_queries;assert.deepEqual(towingQueries.slice(0,2),['North Harbor vessel towing locomotive tractors','North Harbor locomotive vessel']);assert(towingQueries.includes('North Harbor locomotive'));assert(towingQueries.includes('North Harbor vessel'));assert(towingQueries.length<=5,'inventory recovery must remain bounded to exact + primary + at most three fallbacks');
const waterQueries=recovery.inventory_claims[1].provider_queries;assert.equal(waterQueries[0],'North Harbor gravity water system diagram');assert(waterQueries[1].includes('water')&&waterQueries[1].includes('chamber')&&waterQueries[1].includes('diagram'),'primary recovery must preserve visible target detail and media type');assert(waterQueries.includes('North Harbor chamber'));assert(waterQueries.length<=5);
assert(queries.length<=8,'inventory detail retrieval must remain bounded even when fallback expansion is needed');
assert(recoveryQueries.length<=10,'inventory recovery must remain bounded to at most five provider queries per claim');
const targetOnlyQueries=[];
const targetOnly=await discoverVisualCandidates({canonicalSource:{language:'en',title:'North Harbor'},inventoryClaims:[{claim_number:1,claim:'Grounded water fact.',visual_target:'North Harbor culvert chamber',search_query_en:'North Harbor gravity water system'}],fetchImpl:async input=>{
 const u=new URL(String(input));
 if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
 const q=u.searchParams.get('gsrsearch');targetOnlyQueries.push(q);
 const pages=q?.includes('culvert')?[page('culvert-specific','North Harbor culvert chamber')]:Array.from({length:5},(_,i)=>page(`harbor-generic-${i}`,'North Harbor water exterior'));
 return new Response(JSON.stringify({query:{pages}}));
}});
assert(targetOnly.inventory_claims[0].provider_queries.some(q=>q.includes('culvert')),'recovery must recover a distinguishing target term omitted by the model search query');
assert.equal(targetOnly.inventory_claims[0].candidates[0].provider_asset_id,'File:culvert-specific.jpg','target-derived detail must rank above generic subject imagery');
console.log('INVENTORY_DETAIL_RETRIEVAL_REGRESSION_PASS');

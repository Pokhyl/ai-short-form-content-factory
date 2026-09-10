import assert from 'node:assert/strict';
import { discoverVisualCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const exactQuery='North Harbor cross section diagram';
const seen=[];
const page=(id,description)=>({title:`File:${id}.jpg`,imageinfo:[{mime:'image/jpeg',width:1400,height:900,url:`https://upload.wikimedia.org/${id}.jpg`,thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,extmetadata:{ImageDescription:{value:description},LicenseShortName:{value:'CC BY'}}}]});
const generic=Array.from({length:6},(_,i)=>page(`generic-${i}`,`North Harbor lock exterior photograph ${i}`));
const strong=[page('elevation-1','North Harbor lock chamber water elevation schematic diagram'),page('elevation-2','North Harbor chamber elevation cross section diagram')];
const result=await discoverVisualCandidates({
  canonicalSource:{language:'en',title:'North Harbor lock system'},
  explorationQueries:[{query_number:1,query_id:'Q1',search_query_en:exactQuery,observable_target:'lock chamber water elevation schematic',visual_form:'diagram',evidence_ids:['S1'],retrieval_rationale:'research:S1'}],
  fetchImpl:async input=>{
    const u=new URL(String(input));
    if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
    if(u.hostname==='commons.wikimedia.org'){
      const q=u.searchParams.get('gsrsearch');seen.push(q);
      return new Response(JSON.stringify({query:{pages:q===exactQuery?generic:strong}}));
    }
    if(u.hostname==='pixabay.com')return new Response(JSON.stringify({hits:[]}));
    if(u.hostname==='api.pexels.com')return new Response(JSON.stringify({photos:[]}));
    throw new Error(`unexpected host ${u.hostname}`);
  }
});
const row=result.exploration_queries[0];
assert.equal(row.provider_queries[0],exactQuery);
assert.equal(row.bounded_query_recovery_used,true,'six generic subject hits with only one weak detail token must not suppress recovery');
assert(row.provider_queries.length>1&&row.provider_queries.length<=5,'strong-detail recovery must remain bounded');
assert(row.candidates.some(c=>c.provider_asset_id==='File:elevation-1.jpg'||c.provider_asset_id==='File:elevation-2.jpg'),'recovery must add target-specific candidates');
const genericCandidate=row.candidates.find(c=>String(c.provider_asset_id).includes('generic-'));
assert(genericCandidate,'generic candidate should remain available as context');
assert.equal(genericCandidate.inventory_detail_required,2);
assert(genericCandidate.inventory_detail_hits<genericCandidate.inventory_detail_required,'one weak target hit must not count as adequate detail coverage');
const strongCandidate=row.candidates.find(c=>String(c.provider_asset_id).includes('elevation-'));
assert(strongCandidate.inventory_detail_hits>=strongCandidate.inventory_detail_required,'specific recovery candidate must satisfy strong detail coverage');


const culvertExact='North Harbor culvert and water valve system';
const culvertSeen=[];
const culvertResult=await discoverVisualCandidates({
  canonicalSource:{language:'en',title:'North Harbor lock system'},
  explorationQueries:[{query_number:1,query_id:'Q1',search_query_en:culvertExact,observable_target:'water control valves and concrete conduits',visual_form:'illustration',evidence_ids:['S1'],retrieval_rationale:'research:S1'}],
  fetchImpl:async input=>{
    const u=new URL(String(input));
    if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
    if(u.hostname==='commons.wikimedia.org'){
      const q=u.searchParams.get('gsrsearch');culvertSeen.push(q);
      const pages=q!==culvertExact&&/culvert/iu.test(q)?[page('culvert-specific','North Harbor culvert with concrete conduit and water valves')]:generic;
      return new Response(JSON.stringify({query:{pages}}));
    }
    if(u.hostname==='pixabay.com')return new Response(JSON.stringify({hits:[]}));
    if(u.hostname==='api.pexels.com')return new Response(JSON.stringify({photos:[]}));
    throw new Error(`unexpected host ${u.hostname}`);
  }
});
const culvertRow=culvertResult.exploration_queries[0];
assert(culvertRow.provider_queries.slice(1).some(q=>/culvert/iu.test(q)),'bounded fallback must preserve a distinguishing exact-query term omitted by target wording');
const culvertSpecific=culvertRow.candidates.find(c=>c.provider_asset_id==='File:culvert-specific.jpg');
assert(culvertSpecific,'query-only culvert fallback must recover the target-specific asset');
assert(culvertSpecific.inventory_detail_hits>=culvertSpecific.inventory_detail_required);

console.log('VISUAL_EXPLORATION_STRONG_DETAIL_RECOVERY_REGRESSION_PASS');

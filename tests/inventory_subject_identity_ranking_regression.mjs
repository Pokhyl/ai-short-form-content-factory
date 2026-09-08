import assert from 'node:assert/strict';
import {discoverVisualCandidates} from '../services/media-worker/src/visual-discovery.mjs';
const page=(id,desc)=>({title:`File:${id}.jpg`,imageinfo:[{mime:'image/jpeg',width:1200,height:800,url:`https://upload.wikimedia.org/${id}.jpg`,thumburl:`https://upload.wikimedia.org/${id}-thumb.jpg`,descriptionurl:`https://commons.wikimedia.org/wiki/File:${id}.jpg`,extmetadata:{ImageDescription:{value:desc},LicenseShortName:{value:'CC BY'}}}]});
const result=await discoverVisualCandidates({canonicalSource:{language:'en',title:'North Harbor lock mechanism'},inventoryClaims:[{claim_number:1,claim:'Grounded gate fact.',visual_target:'Steel miter lock gates meeting in the center',search_query_en:'North Harbor miter lock gates design'}],fetchImpl:async input=>{
 const u=new URL(String(input));
 if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
 const q=u.searchParams.get('gsrsearch');
 if(q==='North Harbor miter lock gates design')return new Response(JSON.stringify({query:{pages:[page('generic-gates','Canal lock miter gates design'),page('north-harbor-gates','North Harbor lock miter gates')]}}));
 return new Response(JSON.stringify({query:{pages:[]}}));
}});
const c=result.inventory_claims[0].candidates;
assert.equal(c[0].provider_asset_id,'File:north-harbor-gates.jpg','named-subject identity must outrank a generic detail-only match');
assert.equal(c[0].inventory_subject_anchor_pass,true);
assert.equal(c[0].inventory_subject_anchor_hits,2);
assert.equal(c[1].inventory_subject_anchor_pass,false);
assert.equal(c[1].inventory_subject_anchor_hits,0);
console.log('INVENTORY_SUBJECT_IDENTITY_RANKING_REGRESSION_PASS');

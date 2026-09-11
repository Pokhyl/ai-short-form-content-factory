import assert from 'node:assert/strict';
import fs from 'node:fs';
import {discoverVisualCandidates} from '../services/media-worker/src/visual-discovery.mjs';

const wfRaw=JSON.parse(fs.readFileSync('n8n/workflows/WF02-plan-script-and-scenes.json','utf8'));
const wf=Array.isArray(wfRaw)?wfRaw[0]:wfRaw;
const build=wf.nodes.find(n=>n.name==='Build Storyboard Discovery Request').parameters.jsCode;
assert.match(build,/observable_target:s\.search_query_en/);
assert.match(build,/crop_policy:s\.crop_policy/);

const seen=[];
const result=await discoverVisualCandidates({
  canonicalSource:{language:'en',title:'Blue sky'},
  explorationQueries:[{query_number:1,query_id:'S1A',search_query_en:'blue sky person',observable_target:'blue sky person',identity_mode:'semantic_topic',crop_policy:'portrait_required',retrieval_rationale:'storyboard:S1A'}],
  pixabayApiKey:'test-pixabay',pexelsApiKey:'test-pexels',
  fetchImpl:async input=>{
    const u=new URL(String(input));
    if(u.hostname.endsWith('.wikipedia.org'))return new Response(JSON.stringify({query:{pages:[]}}));
    if(u.hostname==='commons.wikimedia.org')return new Response(JSON.stringify({query:{pages:[]}}));
    if(u.hostname==='pixabay.com'){
      seen.push(['pixabay',u.searchParams.get('orientation')]);
      return new Response(JSON.stringify({hits:[{id:101,largeImageURL:'https://img.example/101.jpg',webformatURL:'https://img.example/101-preview.jpg',imageWidth:1000,imageHeight:1800,tags:'blue sky person looking up',pageURL:'https://pixabay.com/101',user:'tester'}]}));
    }
    if(u.hostname==='api.pexels.com'){
      seen.push(['pexels',u.searchParams.get('orientation')]);
      return new Response(JSON.stringify({photos:[{id:202,width:1000,height:1700,url:'https://pexels.com/photo/202',alt:'blue sky person looking up',photographer:'tester',src:{large2x:'https://img.example/202.jpg',medium:'https://img.example/202-preview.jpg'}}]}));
    }
    throw new Error(`unexpected host ${u.hostname}`);
  }
});
assert(seen.some(([p,o])=>p==='pixabay'&&o==='vertical'),'Pixabay exploration must request vertical stock for portrait_required shots');
assert(seen.some(([p,o])=>p==='pexels'&&o==='portrait'),'Pexels exploration must request portrait stock for portrait_required shots');
const row=result.exploration_queries[0];
assert(row.candidates.some(c=>c.provider==='pixabay'&&c.metadata.source_height>c.metadata.source_width));
assert(row.candidates.some(c=>c.provider==='pexels'&&c.metadata.source_height>c.metadata.source_width));
assert(row.candidates.filter(c=>['pixabay','pexels'].includes(c.provider)).every(c=>c.inventory_detail_hits>=c.inventory_detail_required));
console.log('V6_STORYBOARD_PORTRAIT_DISCOVERY_PASS');

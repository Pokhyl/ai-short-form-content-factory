// Offline connected-contract replay; no network, DB or product mutations.
const fs=require('node:fs'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const m5=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')),m8=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-m8-12126-contract.json')),cache=JSON.parse(fs.readFileSync('tests/fixtures/m8-12126-source-responses.json'));
const code=(w,n)=>w.nodes.find(x=>x.name===n).parameters.jsCode;
// Match the frozen Search-node parameter serialization, not just a query word.
const stable=value=>Array.isArray(value)?'['+value.map(stable).join(', ')+']':value&&typeof value==='object'?'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+': '+stable(value[k])).join(', ')+'}':JSON.stringify(value);
for(const provider of ['Pixabay','Pexels','Wikimedia']){const params=m8.nodes.find(n=>n.name===provider+' Search').parameters;const hash=crypto.createHash('sha256').update(stable(params)).digest('hex');assert.equal(hash,cache.provenance.search_parameter_hashes[provider],provider+' source request settings changed; cached responses cannot be reused');}

let initialError;try{new Function('$','$json',code(m5,'Validate Storyboard'))(()=>({first:()=>({json:f.context})}),f.generate_response);}catch(e){initialError=e.message;}
assert.match(initialError,/standalone closure filler/);
const response=structuredClone(f.repair_response),part=response.body.candidates[0].content.parts.find(p=>typeof p.text==='string'),draft=JSON.parse(part.text);
// Synthetic one-word control isolates visual contracts; never substitutes product narration.
for(const scene of draft.scenes)scene.narration_words=scene.narration_words.map(w=>w==='Koniec.'?'biurowych.':w);part.text=JSON.stringify(draft);
const after=new Function('$','$json',code(m5,'Validate Repaired Storyboard'))(name=>({first:()=>({json:name==='Build Script Prompt'?f.context:name==='Generate Storyboard'?f.generate_response:{error:initialError}})}),response).json;
const begin=structuredClone(f.visual_begin);
for(const shot of begin.shots_json){const authored=after.storyboard.scenes.flatMap(s=>s.shots).find(s=>s.shot_id===shot.shot_key);assert.ok(authored);for(const k of ['visual_intent','must_show','must_not_show','queries_en','preferred_media_type'])shot[k]=authored[k];}
const key=(provider,ctx,orientation)=>JSON.stringify([provider,ctx.endpoint_kind||'photo',ctx.provider_query,orientation||null]);
const report={provenance:{failed_job:f.provenance.job_id,synthetic_narration_control:f.provenance.synthetic_control,method:'Current native M5 -> M8 builders -> exact cached source request -> current native normalizer',provider_calls:0,production_mutations:0,provider_acceptance:false,search_settings_guard:true},begin,matched:[],missing:[],normalized:[]};
for(const provider of ['Pixabay','Pexels','Wikimedia']){
 const requests=new Function('$',code(m8,'Build '+provider+' Requests'))(()=>({first:()=>({json:begin})})).map(i=>i.json);
 for(const ctx of requests){const orientation=provider==='Pexels'?(ctx.endpoint_kind==='photo'&&ctx.fastened_result_context?'landscape':'portrait'):null;
  const matches=cache.entries.filter(r=>key(provider,r.ctx,r.orientation)===key(provider,ctx,orientation));const saved=matches.find(r=>r.ctx.shot_key===ctx.shot_key)||matches[0];
  if(!saved){report.missing.push({provider,shot:ctx.shot_key,query_index:ctx.query_index,provider_query:ctx.provider_query,orientation});continue;}
  const result=new Function('$','$json',code(m8,'Normalize '+provider))(()=>({item:{json:ctx}}),saved.response).json;
  report.matched.push({provider,shot:ctx.shot_key,query_index:ctx.query_index,provider_query:ctx.provider_query,orientation,candidate_count:result.candidates.length,source_provenance:saved.provenance});report.normalized.push({ctx,result,source_provenance:saved.provenance});
 }
}
report.summary={requests:report.matched.length+report.missing.length,exact_saved_matches:report.matched.length,missing:report.missing.length,unique_missing_requests:[...new Set(report.missing.map(r=>JSON.stringify([r.provider,r.provider_query,r.orientation])))]};
const path=process.argv[2]||'acceptance/release-coverage/12126-cached-source-replay.json';fs.writeFileSync(path,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.summary,null,2));console.log('UNMATCHED',JSON.stringify(report.missing));console.log('SAVED',path);

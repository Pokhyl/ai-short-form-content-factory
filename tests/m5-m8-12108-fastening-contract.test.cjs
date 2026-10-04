const assert=require('node:assert/strict'),{test}=require('node:test'),fs=require('node:fs');
const f=JSON.parse(fs.readFileSync('tests/fixtures/m8-12108-fastening-contract.json'));
const m5=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')),m8=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=(w,name)=>w.nodes.find(n=>n.name===name).parameters.jsCode;
const helper=(src,name)=>{const start=src.indexOf('function '+name+'(');assert.ok(start>=0);let depth=0,seen=false,end=start;for(;end<src.length;end++){if(src[end]==='{'){depth++;seen=true;}else if(src[end]==='}'&&!--depth&&seen){end++;break;}}return src.slice(start,end);};
const validators=m5.nodes.filter(n=>n.parameters.jsCode?.includes('function authoredFasteningPair'));
test('exact saved native repaired storyboard preserves the independently authored surface and relation',()=>{
 const run=src=>new Function('$','$json',src)(n=>({first:()=>({json:f.m5_contexts[n]})}),f.m5_repair_response).json;
 const before=run(f.baseline_m5_nodes['Validate Repaired Storyboard']),after=run(code(m5,'Validate Repaired Storyboard'));
 assert.deepEqual(before,f.m5_before);assert.deepEqual(after,f.m5_after);
 const shot=r=>r.storyboard.scenes.find(s=>s.scene_id==='S9').shots[0];
 assert.deepEqual(shot(before).must_show,['wire staples']);assert.deepEqual(shot(after).must_show,['wire staples','paper documents']);
 assert.equal(shot(after).visual_intent,'A photo of wire staples binding a neat stack of office reports on a desk.');
 assert.equal(before.storyboard.narration,after.storyboard.narration);
});
test('all four native validators retain the same generic fastening helper',()=>{
 assert.equal(validators.length,4);const expected=helper(validators[0].parameters.jsCode,'authoredFasteningPair');
 for(const n of validators)assert.equal(helper(n.parameters.jsCode,'authoredFasteningPair'),expected,n.name);
});
test('generic bolts and metal plates retain both independently authored objects',()=>{
 for(const n of validators){
  const run=new Function(helper(n.parameters.jsCode,'authoredFasteningPair')+';return authoredFasteningPair;')();
  const anchors=['steel bolts','metal plates'],queries=['steel bolts securing metal panels','metal plates bolt joint','steel bolts'];
  assert.deepEqual(run(anchors,'Steel bolts securing connected metal panels.',queries),{connector:'bolt',connector_anchor:'steel bolts',surface_anchor:'metal plates'});
 }
});
test('missing query grounding, unconnected proximity and unrelated surfaces never invent an anchor',()=>{
 const run=new Function(helper(validators[0].parameters.jsCode,'authoredFasteningPair')+';return authoredFasteningPair;')();
 for(const [anchors,intent,queries] of [
  [['wire staples','paper documents'],'Wire staples binding office reports.',[]],
  [['wire staples','paper documents'],'Wire staples beside office reports.',['wire staples','paper documents']],
  [['metal bolts','paper documents'],'Metal bolts securing wooden panels.',['metal bolts','paper documents']],
  [['office stapler','paper documents'],'An office stapler on a desk.',['office stapler','paper documents']],
 ])assert.equal(run(anchors,intent,queries),null);
});
const requests=(provider,begin=f.grounded_begin,src=code(m8,'Build '+provider+' Requests'))=>new Function('$',src)(()=>({first:()=>({json:begin})})).map(r=>r.json);
test('only final connector-first fallback broadens; every shot contract and detailed query remains authored',()=>{
 for(const provider of ['Pexels','Pixabay','Wikimedia']){
  const after=requests(provider),before=requests(provider,f.grounded_begin,f.baseline_m8_nodes['Build '+provider+' Requests']);
  assert.equal(after.length,27);
  for(let i=0;i<after.length;i++){
   for(const key of ['query','visual_intent','must_show','must_not_show'])assert.deepEqual(after[i][key],before[i][key]);
   if(after[i].query_index<=2)assert.deepEqual(after[i],before[i]);
  }
  assert.equal(after.find(c=>c.shot_key==='S9-A'&&c.query_index===3).provider_query,provider==='Pexels'?'stapled paper':'stapled documents');
 }
});
test('wire material compression affects only final paired retrieval and preserves original pixel requirements',()=>{
 const after=requests('Wikimedia').find(c=>c.shot_key==='S6-A'&&c.query_index===3);
 assert.equal(after.provider_query,'staple paper');assert.deepEqual(after.must_show,['wire staples','paper sheets']);
 assert.deepEqual(after.must_not_show,['plastic folders']);
 const begin=structuredClone(f.grounded_begin),s=begin.shots_json.find(s=>s.shot_key==='S6-A');
 Object.assign(s,{must_show:['wire nails','wooden planks'],visual_intent:'Wire nails beside wooden planks.',queries_en:['wire nails wooden planks','nails beside planks','wooden planks']});
 assert.equal(requests('Wikimedia',begin).find(c=>c.shot_key==='S6-A'&&c.query_index===3).provider_query,'nail plank');
});
test('bare fasteners and absence of a required surface retain baseline retrieval',()=>{
 for(const provider of ['Pexels','Pixabay','Wikimedia']){
  const begin=structuredClone(f.grounded_begin),s=begin.shots_json.find(s=>s.shot_key==='S9-A');
  s.must_show=['wire staples'];s.visual_intent='A clear photo of wire staples.';
  assert.deepEqual(requests(provider,begin).filter(c=>c.shot_key==='S9-A'),requests(provider,begin,f.baseline_m8_nodes['Build '+provider+' Requests']).filter(c=>c.shot_key==='S9-A'));
 }
});
const commonsBundle=shot=>f.current_normalized_entries.find(b=>b.ctx.provider==='wikimedia'&&b.ctx.shot_key===shot&&b.ctx.query_index===3);
const singlePage=(bundle,id)=>{const r=structuredClone(bundle.response);r.body.query.pages={[id]:r.body.query.pages[id]};return r;};
const normalizeCommons=(ctx,response)=>new Function('$','$json',code(m8,'Normalize Wikimedia'))(()=>({item:{json:ctx}}),response).json.candidates;
test('a physical object photograph beside documents is not rejected as a document scan',()=>{
 const b=commonsBundle('S6-A'),r=singlePage(b,'77734699'),c=normalizeCommons(b.ctx,r)[0];
 assert.equal(c.metadata.paired_subject_review,true);assert.equal(c.rejected,true);assert.doesNotMatch(c.rejection_reason,/wikimedia_non_photographic_asset/);
 const page=r.body.query.pages['77734699'];page.title='File:Scanned documents.jpg';page.imageinfo[0].extmetadata.ObjectName={value:'Scanned documents'};page.imageinfo[0].extmetadata.ImageDescription={value:'A scanned document page.'};page.imageinfo[0].extmetadata.Categories={value:'2023 documents'};
 const scan=normalizeCommons(b.ctx,r)[0];assert.match(scan.rejection_reason,/wikimedia_non_photographic_asset/);assert.notEqual(scan.metadata.paired_subject_review,true);
});
test('one completed-state category plus direct connector caption nominates but never approves a result',()=>{
 const b=commonsBundle('S9-A'),r=singlePage(b,'854970'),c=normalizeCommons(b.ctx,r)[0];
 assert.equal(c.metadata.paired_subject_review,true);assert.equal(c.rejected,true);assert.ok(c.relevance_score>=55);assert.match(c.rejection_reason,/missing_primary_subject_anchor/);
 r.body.query.pages['854970'].imageinfo[0].extmetadata.Categories={value:'Stapled objects|Paper documents'};
 assert.notEqual(normalizeCommons(b.ctx,r)[0].metadata.paired_subject_review,true);
});
test('diagram, SVG and unrequested packaging never become physical result nominees',()=>{
 const b=commonsBundle('S9-A');
 for(const kind of ['diagram','svg','packaging']){
  const r=singlePage(b,'854970'),page=r.body.query.pages['854970'];
  if(kind==='diagram')page.title='File:Staple diagram.jpg';
  if(kind==='svg')page.imageinfo[0].mime='image/svg+xml';
  if(kind==='packaging'){page.title='File:Box of staples.jpg';page.imageinfo[0].extmetadata.ObjectName={value:'Box of staples'};}
  assert.notEqual(normalizeCommons(b.ctx,r)[0]?.metadata.paired_subject_review,true,kind);
 }
});
test('completed bolted plates nomination uses the same generic rule without full material proof',()=>{
 const b=commonsBundle('S9-A'),r=singlePage(b,'854970'),page=r.body.query.pages['854970'];
 page.title='File:Bolts.jpg';page.imageinfo[0].extmetadata.ObjectName={value:'Bolts'};page.imageinfo[0].extmetadata.ImageDescription={value:''};page.imageinfo[0].extmetadata.Categories={value:'Bolted plates'};
 const ctx={...b.ctx,query:'steel bolts',provider_query:'bolted plates',must_show:['steel bolts','metal plates'],must_not_show:[],visual_intent:'Steel bolts fastening metal plates.',fastened_result_context:{state:'bolted',connector:'bolt',surface_terms:['plate']}};
 const c=normalizeCommons(ctx,r)[0];assert.equal(c.metadata.paired_subject_review,true);assert.equal(c.rejected,true);
});
test('actual production paperclip false positive is rejected by current native parser',()=>{
 const n=f.identity_negative_control,p=new Function('$','$json',code(m8,'Parse Gemini Vision Result'))(()=>({item:{json:n.ctx}}),n.response).json;
 assert.deepEqual(p,n.parsed);const c=p.candidates.find(c=>c.provider==='pexels'&&c.provider_asset_id==='6077915'),e=p.evaluations.find(e=>e.candidate_index===c.candidate_index);
 assert.equal(e.vision_pass,false);assert.equal(e.must_show_checks[0].visible,false);
 const text=code(m8,'Build Gemini Vision Request');assert.match(text,/continuous returning wire loop/);assert.match(text,/two terminal legs/);
});
test('direct semantic nominees precede cross-shot novelty while final asset uniqueness remains solved globally',()=>{
 const sql=fs.readFileSync('db/09-visuals.sql','utf8'),s=sql.slice(sql.indexOf('coverage_choice(step'));
 assert.ok(s.indexOf("d.metadata->>'paired_subject_review'")<s.indexOf('CASE WHEN mode.needs_query_coverage THEN d.cross_shot_asset_bucket'));
 assert.match(code(m8,'Collect Gemini Selections'),/Solve uniqueness globally/);
});
test('Pexels widens orientation only for the final physical fastening photo fallback',()=>{
 const param=m8.nodes.find(n=>n.name==='Pexels Search').parameters.queryParameters.parameters.find(p=>p.name==='orientation');
 const run=ctx=>new Function('$json','return '+param.value.slice(3,-2).trim())(ctx);
 for(const ctx of requests('Pexels')){
  assert.equal(run(ctx),ctx.endpoint_kind==='photo'&&ctx.fastened_result_context?'landscape':'portrait');
  if(ctx.query_index<=2)assert.equal(run(ctx),'portrait');
 }
 assert.equal(run({endpoint_kind:'video',fastened_result_context:{state:'bolted'}}),'portrait');
 const ctx=requests('Pexels').find(c=>c.shot_key==='S7-A'&&c.query_index===3);
 assert.equal(ctx.provider_query,'stapled paper');assert.equal(run(ctx),'landscape');assert.deepEqual(ctx.must_show,['wire staples','paper documents']);
 const observed=f.landscape_query_probe.normalized.candidates.find(c=>c.provider_asset_id==='6991328');assert.ok(observed.width>observed.height);assert.equal(observed.metadata.paired_subject_review,true);assert.equal(observed.rejected,true);assert.ok(observed.relevance_score>=55);
});
test('concrete surface fallback preserves steel bolts and metal plates as independent pixel requirements',()=>{
 const begin=structuredClone(f.grounded_begin),shot=structuredClone(begin.shots_json.find(s=>s.shot_key==='S9-A'));
 Object.assign(shot,{must_show:['steel bolts','metal plates'],must_not_show:[],visual_intent:'Steel bolts securing connected metal plates.',queries_en:['steel bolts securing metal plates','metal plates bolted together','steel bolts']});begin.shots_json=[shot];
 const ctx=requests('Pexels',begin).find(c=>c.query_index===3);assert.match(ctx.provider_query,/^bolted plates?$/);assert.deepEqual(ctx.must_show,['steel bolts','metal plates']);
});
test('secondary loaded-container fallback retrieves its authored owner without dropping either independent anchor',()=>{
 const after=requests('Wikimedia').filter(c=>c.shot_key==='S4-A'),before=requests('Wikimedia',f.grounded_begin,f.baseline_m8_nodes['Build Wikimedia Requests']).filter(c=>c.shot_key==='S4-A');
 assert.deepEqual(after.slice(0,2),before.slice(0,2));assert.equal(after[2].provider_query,'open stapler');assert.equal(after[2].component_owner_query,'stapler');assert.equal(after[2].contained_component_pair,true);
 for(const key of ['query','visual_intent','must_show','must_not_show'])assert.deepEqual(after[2][key],before[2][key]);
});
test('loaded coils and motor housing use the same owner fallback; proximity or missing grounding cannot enable it',()=>{
 const begin=structuredClone(f.grounded_begin),shot=structuredClone(begin.shots_json.find(s=>s.shot_key==='S4-A'));
 Object.assign(shot,{must_show:['copper coils','motor housing'],must_not_show:[],visual_intent:'Copper coils contained inside an open motor housing.',queries_en:['copper coils inside motor housing','motor housing containing copper coils','motor housing']});begin.shots_json=[shot];
 const get=()=>requests('Wikimedia',begin).find(c=>c.query_index===3);
 assert.equal(get().provider_query,'open motor');assert.deepEqual(get().must_show,['copper coils','motor housing']);
 shot.visual_intent='Copper coils beside a motor housing.';assert.notEqual(get().contained_component_pair,true);
 shot.visual_intent='Copper coils contained inside a motor housing.';shot.queries_en=['copper coils inside workshop','motor housing','motor housing'];assert.notEqual(get().contained_component_pair,true);
});
test('actual closed-stapler negative does not prove loaded wire staples inside its magazine',()=>{
 const n=f.closed_loaded_container_negative,p=new Function('$','$json',code(m8,'Parse Gemini Vision Result'))(()=>({item:{json:n.ctx}}),n.response).json;
 assert.deepEqual(p,n.parsed);const c=p.candidates.find(c=>c.provider==='pixabay'&&c.provider_asset_id==='2350695'),e=p.evaluations.find(e=>e.candidate_index===c.candidate_index);
 assert.equal(e.vision_pass,false);assert.equal(e.must_show_checks[0].visible,false);assert.deepEqual(n.ctx.must_show,['wire staples','stapler magazine']);
});

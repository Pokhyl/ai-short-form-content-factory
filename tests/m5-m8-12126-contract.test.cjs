const fs=require('node:fs'),assert=require('node:assert/strict'),{test}=require('node:test');
const f=JSON.parse(fs.readFileSync('tests/fixtures/m5-m8-12126-contract.json'));
const m5=JSON.parse(fs.readFileSync('workflows/VIDEO-M5-Script-Storyboard.json')),m8=JSON.parse(fs.readFileSync('workflows/VIDEO-M8-Multi-Source-Visuals.json'));
const code=(w,n)=>w.nodes.find(x=>x.name===n).parameters.jsCode;
const runM5=(response,initial=f.validate_initial)=>new Function('$','$json',code(m5,'Validate Repaired Storyboard'))(name=>({first:()=>({json:name==='Build Script Prompt'?f.context:name==='Generate Storyboard'?f.generate_response:initial})}),response).json;
const cleanResponse=()=>{const r=structuredClone(f.repair_response);const part=r.body.candidates[0].content.parts.find(p=>typeof p.text==='string');const d=JSON.parse(part.text);for(const s of d.scenes) s.narration_words=s.narration_words.map(w=>w==='Koniec.'?'biurowych.':w);part.text=JSON.stringify(d);return r;};
test('exact production accepted filler must fail validation before TTS',()=>assert.throws(()=>runM5(f.repair_response),/standalone closure filler/));
test('native repaired storyboard retains all explicitly open authored detail requirements',()=>{
 const response=cleanResponse(),raw=JSON.parse(response.body.candidates[0].content.parts.find(p=>p.text).text),after=runM5(response,{error:'continuous narration contains standalone closure filler: koniec'});
 for(const id of ['S2','S3','S4']){const before=raw.scenes.find(s=>s.scene_id===id).shots[0],actual=after.storyboard.scenes.find(s=>s.scene_id===id).shots[0];assert.deepEqual(actual.must_show,before.must_show,id);assert.equal(actual.visual_intent,before.visual_intent,id);assert.deepEqual(actual.queries_en.slice(0,2),before.queries_en.slice(0,2));}
 assert.equal(after.storyboard.narration,raw.scenes.flatMap(s=>s.narration_words).join(' '));
});
const requests=(provider,begin=f.visual_begin)=>new Function('$',code(m8,'Build '+provider+' Requests'))(()=>({first:()=>({json:begin})})).map(x=>x.json);
test('surface-first bound-result fallback carries both required subjects on every adapter',()=>{
 for(const provider of ['Pixabay','Pexels','Wikimedia']){const rows=requests(provider).filter(x=>x.shot_key==='S9-A');assert.equal(rows.length,3);assert.ok(rows[2].fastened_result_context,provider);assert.equal(rows[2].fastened_result_context.connector,'staple');assert.match(rows[2].provider_query,/^stapled /);for(const r of rows){assert.deepEqual(r.must_show,['paper sheets','metal staple']);assert.deepEqual(r.must_not_show,['staple remover']);}assert.equal(rows[0].query,'bound paper sheets with staple');assert.equal(rows[1].query,'stapled document papers stack paper sheets');}
});
test('generic result query is invariant to anchor order for bolts and plates',()=>{
 for(const provider of ['Pixabay','Pexels','Wikimedia']) for(const reverse of [false,true]){
  const begin=structuredClone(f.visual_begin),shot=begin.shots_json.find(s=>s.shot_key==='S9-A');Object.assign(shot,{must_show:reverse?['metal plates','steel bolts']:['steel bolts','metal plates'],visual_intent:'Steel bolts securing connected metal plates.',queries_en:['steel bolts securing metal plates','metal plates bolt joint','steel bolts'],must_not_show:[]});
  const row=requests(provider,begin).find(r=>r.shot_key==='S9-A'&&r.query_index===3);assert.ok(row.fastened_result_context,provider+' reverse='+reverse);assert.equal(row.fastened_result_context.connector,'bolt');assert.match(row.provider_query,/^bolted /);
 }
});

const targets=m5.nodes.filter(n=>n.parameters.jsCode?.includes('function authoredExposedDetailAnchors('));
const helper=(source,name)=>{const a=source.indexOf('function '+name+'('),b=source.indexOf('\nfunction ',a+9);assert.ok(a>=0&&b>a);return new Function(source.slice(a,b)+';return '+name+';')();};
test('all seven normalization boundaries preserve only explicitly exposed intent/query grounded details',()=>{
 assert.equal(targets.length,7);
 for(const n of targets){const run=helper(n.parameters.jsCode,'authoredExposedDetailAnchors');
  const anchors=['electric motor','copper coil'],queries=['electric motor copper coil','exposed motor coil','electric motor'];
  assert.deepEqual(run(anchors,'Copper coil inside an open electric motor.',queries),anchors,n.name);
  assert.equal(run(anchors,'Copper coil inside a closed electric motor.',queries),null,n.name);
  assert.equal(run(anchors,'Copper coil inside an open electric motor.',['electric motor']),null,n.name);
  assert.equal(run(['electric motor','rotation'],'Rotation inside an open electric motor.',['motor rotation','electric motor']),null,n.name);
  assert.match(n.parameters.jsCode,/const dependentSecondary = exposedDetailAnchors \? \[\] :/);
  assert.match(n.parameters.jsCode,/const mustShow = exposedDetailAnchors \|\|/);
 }
});
test('all seven boundaries reject closure filler in PL EN RU UK but allow real closing sentences',()=>{
 for(const n of targets){const run=helper(n.parameters.jsCode,'assertNoClosureFiller');for(const text of ['Complete explanation. The end.','Pełne wyjaśnienie. Koniec.','Полное объяснение. Конец.','Повне пояснення. Кінець.'])assert.throws(()=>run(text),/standalone closure filler/,n.name);for(const text of ['The end plate holds the bolt.','Koniec przewodu jest połączony.','Конец провода соединён.','Кінець дроту з’єднаний.'])assert.doesNotThrow(()=>run(text),n.name);assert.match(n.parameters.jsCode,/assertNoClosureFiller\((?:narration|storyboard\.scenes)/);}
});
test('mere proximity cannot claim completed fastening state in either anchor order',()=>{
 for(const provider of ['Pixabay','Pexels','Wikimedia']) for(const anchors of [['steel bolts','metal plates'],['metal plates','steel bolts']]){
  const begin=structuredClone(f.visual_begin),s=begin.shots_json.find(s=>s.shot_key==='S9-A');Object.assign(s,{must_show:anchors,visual_intent:'Steel bolts beside metal plates.',queries_en:['steel bolts beside metal plates','metal plates with bolts',anchors[1]],must_not_show:[]});
  assert.equal(requests(provider,begin).find(r=>r.shot_key==='S9-A'&&r.query_index===3).fastened_result_context,undefined);
 }
});

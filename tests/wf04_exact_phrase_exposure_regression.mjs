import assert from 'node:assert/strict';
import fs from 'node:fs';

const wf=JSON.parse(fs.readFileSync(new URL('../n8n/workflows/WF04-visual-sourcing.json',import.meta.url),'utf8'))[0];
const code=wf.nodes.find(n=>n.name==='Build Deterministic Visual Plans').parameters.jsCode;
const run=new Function('$input','$',code);
const wrong=Array.from({length:12},(_,i)=>({
  candidate_id:`wikimedia:wrong-${i}`,
  provider:'wikimedia',provider_asset_id:`wrong-${i}`,media_kind:'diagram',
  preview_urls:[`https://upload.wikimedia.org/wrong-${i}.jpg`],preview_url:`https://upload.wikimedia.org/wrong-${i}.jpg`,download_url:`https://upload.wikimedia.org/wrong-${i}.jpg`,
  title:`Ocean carbon cycle global water schematic ${i}`,
  description:'global schematic showing ocean carbon cycle and water processes',categories:'global water carbon cycle schematic',
  metadata:{retrieval_source:'commons_search_bounded_recovery',source_title:`Ocean carbon cycle global water schematic ${i}`,source_description:'global schematic showing ocean carbon cycle and water processes',source_tags:'global water carbon cycle schematic'}
}));
const correct={
  candidate_id:'wikimedia:water-cycle',provider:'wikimedia',provider_asset_id:'water-cycle',media_kind:'diagram',
  preview_urls:['https://upload.wikimedia.org/water-cycle.jpg'],preview_url:'https://upload.wikimedia.org/water-cycle.jpg',download_url:'https://upload.wikimedia.org/water-cycle.jpg',
  title:'Water Cycle Diagram',description:'Water cycle diagram',categories:'water cycle diagram',
  metadata:{retrieval_source:'commons_search_bounded_recovery',source_title:'Water Cycle Diagram',source_description:'Water cycle diagram',source_tags:'water cycle diagram'}
};
const discovery={canonical_source:{english_title:'Atmospheric water cycle'},segmentation_version:'narration-beat-visual-segments-v4',provider_errors:[],visual_segments:[{
  segment_number:1,first_scene_number:1,last_scene_number:1,start_seconds:0,end_seconds:3,duration_seconds:3,narration:'The water cycle starts again.',support_evidence_ids:['S1'],planned_shot_count:2,search_terms:['schematic diagram of the global water cycle'],provider_query:'schematic diagram of the global water cycle',candidates:[...wrong,correct]
}]};
const job={job_id:'00000000-0000-4000-8000-000000000001',fact_primary_title:'Atmospheric water cycle',voiceover_duration_seconds:3,evidence:[{evidence_id:'S1',evidence_text:'The atmospheric water cycle continuously circulates water.'}],script_support:[{evidence_id:'S1',text:'The water cycle starts again.'}]};
const $=name=>{assert.equal(name,'Require Eligible Visual Job');return{first:()=>({json:job})};};
const result=run({first:()=>({json:discovery})},$)[0].json;
const pool=result.plans[0].candidate_pool;
assert.equal(pool.length,10);
assert.ok(pool.some(c=>c.candidate_id==='wikimedia:water-cycle'),'exact target phrase candidate must survive bounded local exposure pool');
const picked=pool.find(c=>c.candidate_id==='wikimedia:water-cycle');
assert.ok(Number(picked.target_phrase_overlap)>=1);
console.log('WF04_EXACT_PHRASE_EXPOSURE_REGRESSION_PASS');

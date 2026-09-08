import assert from 'node:assert/strict';
import fs from 'node:fs';
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const by=new Map(wf.nodes.map(n=>[n.name,n]));
const code=by.get('Expand Reserved Story Assets').parameters.jsCode;
const durations=[4.688,5.918,5.814];
let cursor=0;
const scenes=durations.map((d,i)=>{const start=cursor;cursor+=d;return {scene_id:`scene-${i+1}`,scene_number:i+1,narration:`Unit ${i+1}.`,beat_start_seconds:start,beat_end_seconds:cursor,duration_seconds:d};});
const units=[];const bundles=[];const identities=new Set();
for(let i=0;i<3;i++){
  const shot_assets=[];
  for(let p=0;p<2;p++){
    const n=i*2+p+1,asset_id=`A${n}`,provider_asset_id=`asset-${n}`,visual_hash=n.toString(16).padStart(64,'0');
    identities.add(`wikimedia:${provider_asset_id}`);
    shot_assets.push({asset_id,provider:'wikimedia',provider_asset_id,candidate_id:`wikimedia:${provider_asset_id}`,source_url:`https://example.test/${n}`,download_url:`https://example.test/${n}.jpg`,media_kind:'photo',visual_hash,visual_cluster_key:`preview:${visual_hash}`,visible_description:`Verified photo ${n}.`,metadata:{source_width:1920,source_height:1080}});
  }
  units.push({unit_id:`U${i+1}`,claim_id:`C${i+1}`,narration:`Unit ${i+1}.`,evidence_ids:[`S${i+1}`],asset_id:shot_assets[0].asset_id,asset_ids:shot_assets.map(a=>a.asset_id),visual_target:`Target ${i+1}`});
  bundles.push({...shot_assets[0],claim_id:`C${i+1}`,visual_target:`Target ${i+1}`,shot_assets});
}
assert.equal(identities.size,6);
const job={job_id:'11111111-1111-4111-8111-111111111111',topic:'Fixture',fact_primary_title:'Fixture',story_package:{version:'inventory-first-story-v1',units,assets:bundles},scenes};
const $=name=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:job})};};
const out=new Function('$input','$',code)({first:()=>({json:{ready_to_run:true}})},$).map(x=>x.json);
assert.equal(out.length,6,'exact rejected 16.42s cadence must produce six visual shots');
assert.deepEqual(out.map(x=>x.shot_number),[1,2,3,4,5,6]);
assert.deepEqual(out.map(x=>x.segment_shot_number),[1,2,1,2,1,2]);
assert.deepEqual(out.map(x=>x.planned_shot_count),[2,2,2,2,2,2]);
assert.equal(new Set(out.map(x=>`${x.provider}:${x.provider_asset_id}`)).size,6,'every shot must use a distinct pre-script reserved source asset');
assert.equal(new Set(out.map(x=>x.reserved_visual_hash)).size,6,'every shot must use a distinct pre-script preview cluster');
let previous=0;
for(const x of out){assert.ok(Math.abs(x.shot_start_seconds-previous)<=1e-6);assert.ok(x.shot_duration_seconds>0);previous=x.shot_end_seconds;}
assert.ok(Math.abs(previous-16.42)<=1e-6);
assert.doesNotMatch(code,/fetch\(|http:|visual\/discover|recover/i,'post-freeze shot expansion must not search for replacement media');
console.log('WF04_HUMAN_FAIL_MULTISHOT_REGRESSION_PASS');

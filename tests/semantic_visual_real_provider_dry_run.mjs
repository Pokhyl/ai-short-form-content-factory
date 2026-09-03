import fs from 'node:fs';
import assert from 'node:assert/strict';
import { discoverVisualCandidates } from '../services/media-worker/src/visual-discovery.mjs';

const contextPath=process.env.JOB_CONTEXT_FILE;
const rankUrl=process.env.VISUAL_RANK_URL||'http://127.0.0.1:3001/visual/rank';
assert(contextPath,'JOB_CONTEXT_FILE is required');
const contexts=JSON.parse(fs.readFileSync(contextPath,'utf8'));
assert(Array.isArray(contexts)&&contexts.length,'job contexts are required');
const raw=JSON.parse(fs.readFileSync('n8n/workflows/WF04-visual-sourcing.json','utf8'));
const wf=Array.isArray(raw)?raw[0]:raw;
const byName=new Map(wf.nodes.map(n=>[n.name,n]));
for(const name of ['Prepare Canonical Media Request','Build Deterministic Visual Plans','Expand Rank Items','Attach Rank Results','Choose Visual Assignment']) assert(byName.get(name)?.parameters?.jsCode,`missing ${name}`);

function runPrepare(j){
 const code=byName.get('Prepare Canonical Media Request').parameters.jsCode;
 const $=name=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:j})}};
 return new Function('$input','$',code)({first:()=>({json:{ready_to_run:true}})},$)[0].json;
}
function runPlanner(j,discovery){
 const code=byName.get('Build Deterministic Visual Plans').parameters.jsCode;
 const $=name=>{assert.equal(name,'Require Eligible Visual Job');return {first:()=>({json:j})}};
 return new Function('$input','$',code)({first:()=>({json:discovery})},$)[0].json;
}
function expandPlans(ctx){
 const code=byName.get('Expand Rank Items').parameters.jsCode;
 const $=name=>{assert.equal(name,'Require Visual Plans');return {first:()=>({json:ctx})}};
 return new Function('$',code)($);
}
async function attachRank(expanded){
 const code=byName.get('Attach Rank Results').parameters.jsCode;
 const out=[];
 for(const item of expanded){
  const r=await fetch(rankUrl,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(item.json.local_rank_request)});
  const text=await r.text();
  if(!r.ok)throw new Error(`rank HTTP ${r.status}: ${text.slice(0,240)}`);
  const response=JSON.parse(text);
  const $=name=>{assert.equal(name,'Expand Rank Items');return {item:{json:item.json}}};
  out.push(new Function('$json','$',code)(response,$));
 }
 return out;
}
function choose(rows){
 const code=byName.get('Choose Visual Assignment').parameters.jsCode;
 return new Function('$input',code)({all:()=>rows}).map(x=>x.json);
}

const summaries=[];
for(const j of contexts){
 assert(Array.isArray(j.scenes)&&j.scenes.length,'scenes missing');
 assert(Array.isArray(j.evidence)&&j.evidence.length,'evidence missing');
 assert(Array.isArray(j.script_support)&&j.script_support.length,'script_support missing');
 const prepared=runPrepare(j);
 const discovery=await discoverVisualCandidates({
  canonicalSource:prepared.discovery_request.canonical_source,
  timedBeats:prepared.discovery_request.timed_beats,
  pixabayApiKey:process.env.PIXABAY_API_KEY||'',
  pexelsApiKey:process.env.PEXELS_API_KEY||'',
 });
 const planned=runPlanner(j,discovery);
 assert.equal(planned.planned_shot_count,planned.visual_segment_count,'default shot cardinality must equal semantic segment cardinality');
 assert.equal(planned.segmentation_version,'semantic-visual-segments-v3');
 const total=Number(j.voiceover_duration_seconds);
 const cap=Math.min(8.5,total*0.34);
 assert(planned.plans.every(p=>Number(p.duration_seconds)<=cap+0.02),`quality-constrained segment exceeds cap ${cap}`);
 const expanded=expandPlans(planned);
 assert.equal(expanded.length,planned.visual_segment_count);
 const attached=await attachRank(expanded);
 const selected=choose(attached);
 assert.equal(selected.length,planned.planned_shot_count);
 const q=selected[0]?.visual_quality_pre_render;
 assert(q?.pass===true,'pre-render visual quality did not pass');
 assert(Number(q.max_visual_cluster_duration_share)<=0.34,'duration share gate weakened');
 assert(Number(q.adjacent_visual_cluster_duplicate_count)===0,'adjacent duplicate survived');
 assert(Number(q.max_visual_cluster_occurrence_count)<=2,'cluster occurrence gate weakened');
 const providers=[...new Set(selected.map(x=>String(x.provider)))].sort();
 summaries.push({
  job_id:j.job_id,topic:j.topic,language:j.language_code,voice_seconds:total,timed_beats:j.scenes.length,
  visual_segments:planned.visual_segment_count,shots:selected.length,cap_seconds:Number(cap.toFixed(4)),
  max_shot_seconds:Number(q.max_shot_duration_seconds),clusters:Number(q.unique_visual_cluster_count),required_clusters:Number(q.required_unique_visual_cluster_count),
  adjacent:Number(q.adjacent_visual_cluster_duplicate_count),max_occurrence:Number(q.max_visual_cluster_occurrence_count),max_share:Number(q.max_visual_cluster_duration_share),
  asset_reuse_count:Number(q.asset_reuse_count),providers,provider_errors:planned.provider_errors??[],
 });
}
console.log(JSON.stringify({pass:true,cases:summaries},null,2));
